"""Complemento de navegador: asistencia y recordatorios persistentes."""

import json
import os
import subprocess
import threading
import hashlib
import time
from pathlib import Path
from uuid import uuid4

import pytest
from werkzeug.serving import make_server, make_ssl_devcert
from .conftest import QuietHandler
from .test_web_integration import web as web
from .test_continuity import autonomous as autonomous
from .helpers import iso


@pytest.mark.skipif(
    not os.environ.get("REDHOUSE_BROWSER_TESTS"),
    reason="Requiere Chrome y Playwright explícitamente habilitados",
)
@pytest.mark.parametrize("backend", ["http", "monolith"])
def test_attendance_reminder_browser(web, p, request, tmp_path, backend):
    if backend == "monolith":
        web = request.getfixturevalue("autonomous")
    web.config.update(
        HIGHCHARTS_ENABLED=True, PRODUCTION=True, SESSION_COOKIE_SECURE=True
    )
    from flask import request as browser_request
    from src.integration import sessions

    old_token = {}

    def near_expiry():
        sid = browser_request.cookies[web.config["JWT_COOKIE_NAME"]]
        value = sessions.load(sid)
        old_token["digest"] = hashlib.sha256(value["access_token"].encode()).hexdigest()
        value["expires_at"] = time.time() + 30
        sessions.save(sid, value)
        return {"fixture": "solo plazo de aviso web; renovación real del propietario"}

    def renewed():
        value = sessions.load(browser_request.cookies[web.config["JWT_COOKIE_NAME"]])
        return {
            "rotated": hashlib.sha256(value["access_token"].encode()).hexdigest()
            != old_token["digest"]
        }

    web.add_url_rule(
        "/test/near-expiry",
        "test_near_expiry",
        web.extensions["csrf"].exempt(near_expiry),
        methods=["POST"],
    )
    web.add_url_rule(
        "/test/renewed",
        "test_renewed",
        web.extensions["csrf"].exempt(renewed),
        methods=["POST"],
    )
    username = "agenda_" + uuid4().hex[:12]
    password = p.env.state["password"]
    p.ok(
        "identidad_acceso",
        "POST",
        "/api/v1/users",
        user="admin1",
        data={
            "username": username,
            "password": password,
            "tenant_id": p.env.state["tenants"][0],
            "role": "DONOR",
        },
    )
    auth = p.ok(
        "identidad_acceso",
        "POST",
        "/api/v1/auth/login",
        user=None,
        data={"username": username, "password": password},
    )
    p.tokens[username] = auth["access_token"]
    donor = p.ok(
        "donantes",
        "POST",
        "/api/v1/donors",
        user=username,
        data={
            "folio": "AG-" + uuid4().hex[:10],
            "display_name": "Donante ficticio agenda",
            "blood_group": "O+",
            "consent": True,
        },
    )
    site = p.ok(
        "identidad_acceso",
        "POST",
        "/api/v1/catalogues/sites",
        user="admin1",
        data={
            "name": "Sede ficticia agenda " + uuid4().hex[:8],
            "municipality": "Monterrey",
            "address": "Dirección ficticia",
        },
    )
    campaign = p.ok(
        "donantes",
        "POST",
        "/api/v1/campaigns",
        user="operator1",
        data={
            "title": "Agenda " + uuid4().hex[:8],
            "starts_at": iso(minutes=5),
            "ends_at": iso(minutes=180),
            "capacity": 5,
        },
    )
    slot = p.ok(
        "donantes",
        "POST",
        "/api/v1/campaign-slots",
        user="operator1",
        data={
            "campaign_id": campaign["id"],
            "site_id": site["id"],
            "starts_at": iso(minutes=15),
            "ends_at": iso(minutes=45),
            "capacity": 1,
        },
    )
    appointment = p.ok(
        "donantes",
        "POST",
        "/api/v1/appointments",
        user=username,
        data={
            "donor_id": donor["id"],
            "campaign_id": campaign["id"],
            "slot_id": slot["id"],
        },
    )
    from ms_donantes.agenda import reminders

    with p.apps["donantes"].app_context():
        reminders()
        reminders()
    p.drain(rounds=3)
    output = Path(os.environ["REDHOUSE_BROWSER_RESULTS"]) / ("agenda-" + backend)
    output.mkdir(parents=True, exist_ok=True)

    def manifest():
        names = subprocess.check_output(
            [
                "git",
                "ls-files",
                "--cached",
                "--others",
                "--exclude-standard",
                "--",
                "apps/services",
                "apps/web",
                "scripts",
                "data/database",
            ],
            text=True,
        ).splitlines()
        return {
            name: hashlib.sha256(Path(name).read_bytes()).hexdigest()
            for name in sorted(set(names))
            if Path(name).is_file()
        }

    sources = manifest()
    (output / "sources-before.json").write_text(json.dumps(sources, indent=2) + "\n")
    cert, key = make_ssl_devcert(str(tmp_path / "agenda-tls"), host="localhost")
    server = make_server(
        "127.0.0.1",
        0,
        web,
        threaded=True,
        ssl_context=(cert, key),
        request_handler=QuietHandler,
    )
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        result = subprocess.run(
            ["node", "scripts/verify_portal_agenda.cjs"],
            input=json.dumps(
                {
                    "base": f"https://localhost:{server.server_port}",
                    "donor": username,
                    "password": password,
                    "appointment": appointment["id"],
                    "siteName": site["name"],
                    "startsAt": slot["starts_at"],
                    "output": str(output),
                    "root": str(Path.cwd()),
                    "axe": os.environ["REDHOUSE_AXE_PATH"],
                    "backend": backend,
                }
            ),
            text=True,
            capture_output=True,
            timeout=240,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        with p.owner("donantes") as conn:
            assert (
                conn.execute(
                    "SELECT status FROM appointment_slots WHERE id=%s",
                    (appointment["id"],),
                ).fetchone()[0]
                == "ATTENDED"
            )
            assert (
                conn.execute(
                    "SELECT count(*) FROM appointment_reminders WHERE id=%s",
                    (appointment["id"],),
                ).fetchone()[0]
                == 1
            )
            assert (
                conn.execute(
                    "SELECT count(*) FROM activity_events WHERE event->>'resource_id'=%s AND event->>'action'='APPOINTMENT_REMINDER'",
                    (appointment["id"],),
                ).fetchone()[0]
                == 1
            )
        availability = p.ok(
            "donantes", "GET", "/api/v1/campaign-slots/" + slot["id"], user="operator1"
        )
        assert availability["attended"] == 1
        (output / "persistencia.json").write_text(
            json.dumps(
                {
                    "appointment": appointment["id"],
                    "status": "ATTENDED",
                    "reminders": 1,
                    "reminder_events": 1,
                    "slot": availability,
                },
                indent=2,
            )
            + "\n"
        )
        assert manifest() == sources
    finally:
        (output / "sources-after.json").write_text(
            json.dumps(manifest(), indent=2) + "\n"
        )
        p.tokens.pop(username, None)
        server.shutdown()
        server.server_close()
