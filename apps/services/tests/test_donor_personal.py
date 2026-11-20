"""Edición propia JSON/XML, aislamiento, concurrencia y formulario del portal."""

from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess
import threading
from uuid import uuid4

import pytest
import requests
from jsonschema import validate
from werkzeug.serving import make_server, make_ssl_devcert

from ms_donantes.personal import DonorPersonalResult
from redhouse.examples import request_xml
from redhouse.xml_response import validate_response

from .test_web_integration import web, form, login
from .conftest import QuietHandler


@pytest.fixture(autouse=True)
def isolated_donor_accounts(p):
    # Every case owns fresh accounts: one linked donor per user is a real invariant.
    previous = {name: p.tokens[name] for name in ("donor1", "donor2")}
    p.personal_users = {}
    try:
        for alias, admin in (("donor1", "admin1"), ("donor2", "admin2")):
            owner = p.ok("identidad_acceso", "GET", "/api/v1/auth/me", user=admin)
            username = "self-" + uuid4().hex[:16] + "@redhouse.test"
            p.ok(
                "identidad_acceso",
                "POST",
                "/api/v1/users",
                user=admin,
                data={
                    "username": username,
                    "password": p.env.state["password"],
                    "role": "DONOR",
                    "tenant_id": owner["tenant_id"],
                },
            )
            response = p.request(
                "identidad_acceso",
                "POST",
                "/api/v1/auth/login",
                user=None,
                data={"username": username, "password": p.env.state["password"]},
            )
            assert response.status_code == 200
            p.tokens[alias] = response.json()["data"]["access_token"]
            p.personal_users[alias] = username
        yield
    finally:
        p.tokens.update(previous)
        del p.personal_users


def donor(p, user="donor1"):
    return p.ok(
        "donantes",
        "POST",
        "/api/v1/donors",
        user=user,
        data={
            "folio": "SELF-" + uuid4().hex[:12],
            "display_name": "Nombre sintético anterior",
            "blood_group": "O+",
            "consent": True,
        },
    )


def edit(p, row, data, fmt="json", *, user="donor1", key=None):
    mime = "application/" + fmt
    response = requests.patch(
        p.urls["donantes"] + "/api/v1/donors/" + row["id"] + "/personal",
        data=json.dumps(data) if fmt == "json" else request_xml(data),
        headers={
            "Accept": mime,
            "Content-Type": mime,
            "Authorization": "Bearer " + p.tokens[user],
            "Idempotency-Key": key or uuid4().hex,
        },
        timeout=20,
    )
    payload = (
        response.json()
        if fmt == "json"
        else validate_response(response.content, {"type": "object"})
    )
    return response.status_code, payload


@pytest.mark.parametrize("fmt", ["json", "xml"])
def test_personal_name_preserves_clinical_history_and_replays_once(p, fmt):
    row = donor(p)
    p.ok(
        "donantes",
        "POST",
        f"/api/v1/donors/{row['id']}/reviews",
        user="medical1",
        data={
            "version": row["version"],
            "decision": "DEFERRED",
            "human_confirmation": True,
            "reason": "Dictamen sintético previo conservado",
        },
    )
    before = p.ok("donantes", "GET", f"/api/v1/donors/{row['id']}", user="donor1")
    data = {"display_name": "Nombre sintético corregido", "version": before["version"]}
    key = uuid4().hex
    status, result = edit(p, row, data, fmt, key=key)
    assert status == 200
    validate(result["data"], DonorPersonalResult.model_json_schema())
    assert result["data"] == dict(data, id=row["id"], version=before["version"] + 1)
    replay_status, replay = edit(p, row, data, fmt, key=key)
    assert replay_status == 200 and replay["data"] == result["data"]
    assert edit(p, row, dict(data, display_name="Otro nombre"), fmt, key=key)[0] == 409
    assert edit(p, row, data, fmt)[0] == 409
    after = p.ok("donantes", "GET", f"/api/v1/donors/{row['id']}", user="donor1")
    for field in (
        "folio",
        "blood_group",
        "consent",
        "status",
        "restrictions",
        "background",
        "reviews",
    ):
        assert after[field] == before[field]
    assert after["display_name"] == data["display_name"]
    with p.owner("donantes") as conn:
        decisions = conn.execute(
            "SELECT changes FROM decisions WHERE resource_id=%s AND action='DONOR_PERSONAL_UPDATED'",
            (row["id"],),
        ).fetchall()
        assert len(decisions) == 1
        assert decisions[0][0]["previous_display_name"] == before["display_name"]
        events = conn.execute(
            "SELECT event FROM activity_events WHERE event->>'resource_id'=%s AND event->>'action'='DONOR_PERSONAL_UPDATED'",
            (row["id"],),
        ).fetchall()
        assert len(events) == 1
        assert data["display_name"] not in json.dumps(events[0][0])
        assert before["display_name"] not in json.dumps(events[0][0])
    p.drain()
    with p.owner("auditoria") as conn:
        assert (
            conn.execute(
                "SELECT count(*) FROM audit_events WHERE event->>'resource_id'=%s AND event->>'action'='DONOR_PERSONAL_UPDATED'",
                (row["id"],),
            ).fetchone()[0]
            == 1
        )


@pytest.mark.parametrize("fmt", ["json", "xml"])
def test_personal_edit_denies_other_owners_roles_and_protected_fields(p, fmt):
    own = donor(p)
    other_owner = donor(p, "medical1")
    other_tenant = donor(p, "donor2")
    data = {"display_name": "Nombre permitido", "version": own["version"]}
    assert edit(p, other_owner, data, fmt)[0] == 403
    assert edit(p, other_tenant, data, fmt)[0] == 403
    assert edit(p, own, data, fmt, user="medical1")[0] == 403
    for field, value in (
        ("blood_group", "AB+"),
        ("status", "ELIGIBLE"),
        ("consent", False),
        ("folio", "REPLACED"),
        ("user_id", other_tenant["user_id"]),
        ("background", "Historia alterada"),
    ):
        assert edit(p, own, dict(data, **{field: value}), fmt)[0] in (400, 422)
    unchanged = p.ok("donantes", "GET", f"/api/v1/donors/{own['id']}", user="donor1")
    assert (
        unchanged["version"] == own["version"]
        and unchanged["display_name"] == own["display_name"]
    )
    key = uuid4().hex
    assert edit(p, own, data, fmt, key=key)[0] == 200
    # Simula pérdida posterior del vínculo. El recibo guardado no debe filtrar
    # el nombre ni permitir otro efecto cuando el actor deja de ser titular.
    with p.owner("donantes") as conn:
        conn.execute("UPDATE donors SET user_id=NULL WHERE id=%s", (own["id"],))
    assert edit(p, own, data, fmt, key=key)[0] == 403


def test_personal_edit_concurrent_versions_have_one_winner(p):
    row = donor(p)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(
            pool.map(
                lambda name: edit(
                    p, row, {"display_name": name, "version": row["version"]}
                ),
                ("Primer nombre sintético", "Segundo nombre sintético"),
            )
        )
    assert sorted(status for status, _ in results) == [200, 409]
    with p.owner("donantes") as conn:
        assert (
            conn.execute(
                "SELECT version FROM donors WHERE id=%s", (row["id"],)
            ).fetchone()[0]
            == row["version"] + 1
        )
        assert (
            conn.execute(
                "SELECT count(*) FROM decisions WHERE resource_id=%s AND action='DONOR_PERSONAL_UPDATED'",
                (row["id"],),
            ).fetchone()[0]
            == 1
        )


def test_personal_portal_form_is_closed_to_donor_and_staff(web, p):
    """La edición propia del nombre pasó a la API/aplicación móvil (DONOR sin portal).

    El portal rechaza el login del donante (`client_not_allowed`) y el formulario
    `mis-datos` sigue denegado al personal institucional.
    """
    row = donor(p)
    path = f"/donantes/donor/{row['id']}/mis-datos"
    client = web.test_client()
    values = form(client, "/login")
    values.update(
        login_email=p.personal_users["donor1"], password=p.env.state["password"]
    )
    refused = client.post("/login", data=values)
    assert refused.status_code == 403 and b"aplicaci" in refused.data
    assert login(web, p, "operator1").get(path).status_code == 403


@pytest.mark.skip(
    reason="DONOR ya no usa el portal (acceso por aplicación); recorrido móvil en la tarea D"
)
def test_personal_portal_browser_renders_and_persists(web, p, tmp_path):
    row = donor(p)
    output = Path(os.environ["REDHOUSE_BROWSER_OUTPUT"]).resolve()
    output.mkdir(parents=True, exist_ok=True)
    cert, key = make_ssl_devcert(str(tmp_path / "personal-tls"), host="localhost")
    server = make_server(
        "127.0.0.1",
        0,
        web,
        threaded=True,
        ssl_context=(cert, key),
        request_handler=QuietHandler,
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        result = subprocess.run(
            ["node", "scripts/verify_donor_personal.cjs"],
            input=json.dumps(
                {
                    "base": f"https://localhost:{server.server_port}",
                    "user": p.personal_users["donor1"],
                    "password": p.env.state["password"],
                    "donorId": row["id"],
                    "previousName": row["display_name"],
                    "newName": "Nombre sintético desde navegador",
                    "output": str(output),
                    "browserRoot": os.environ["REDHOUSE_BROWSER_ROOT"],
                }
            ),
            text=True,
            capture_output=True,
            timeout=120,
        )
        (output / "browser-output.log").write_text(result.stdout)
        assert result.returncode == 0, (
            "Recorrido Chrome fallido; revisar reporte saneado"
        )
        saved = p.ok("donantes", "GET", f"/api/v1/donors/{row['id']}", user="donor1")
        assert saved["display_name"] == "Nombre sintético desde navegador"
        assert saved["version"] == row["version"] + 1
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
