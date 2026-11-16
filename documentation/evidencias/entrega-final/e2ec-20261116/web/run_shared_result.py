"""Consulta Chrome del resultado E2E-C conservado; no inicia infraestructura.

Usar una vez, tras el handoff de iOS/Qt y con ventana asignada. El mismo donante
enlaza cita y colecta: el modelo no contiene donations.appointment_id.
"""

import argparse
import hashlib
import json
import os
import secrets
import subprocess
import sys
import threading
from pathlib import Path
from uuid import UUID
from urllib.parse import urlparse

import psycopg
import requests
from werkzeug.serving import WSGIRequestHandler, make_server, make_ssl_devcert

ROOT = Path(__file__).resolve().parents[0]
REPO = Path.cwd()
sys.path.insert(0, str(REPO / "apps/services"))
sys.path.insert(0, str(REPO / "apps/web"))
from redhouse.config import SERVICES
from src import create_app


def save(output, name, value):
    (output / name).write_text(
        json.dumps(value, indent=2, sort_keys=True, default=str) + "\n"
    )


def manifest():
    files = (
        subprocess.check_output(
            [
                "git",
                "ls-files",
                "--cached",
                "--others",
                "--exclude-standard",
                "-z",
                "apps/services",
                "apps/web",
                "packages",
                "data/database/schema.sql",
            ]
        )
        .decode()
        .split("\0")
    )
    result = {
        name: hashlib.sha256((REPO / name).read_bytes()).hexdigest()
        for name in sorted(set(files))
        if name and (REPO / name).is_file()
    }
    for name in ("run_shared_result.py", "verify_shared_result.cjs"):
        result["private_runner/" + name] = hashlib.sha256(
            (ROOT / name).read_bytes()
        ).hexdigest()
    return result


def event(conn, identifier, action, actor, source):
    rows = conn.execute(
        "SELECT event->>'actor_id',event->>'source' FROM activity_events "
        "WHERE event->>'resource_id'=%s AND event->>'action'=%s ORDER BY id",
        (identifier, action),
    ).fetchall()
    assert rows == [(actor, source)], action


def checked_owner(state, service):
    conn = psycopg.connect(state["database_owners"][service])
    try:
        conn.execute("SET TRANSACTION READ ONLY")
        actual = Path(conn.execute("SHOW data_directory").fetchone()[0]).resolve()
        assert actual == Path(state["directory"]).resolve() / "pg", "Base ajena al fixture"
        return conn
    except BaseException:
        conn.close()
        raise


def oracle(state, handoff):
    donor_id = handoff["donor_id"]
    appointment_id = handoff["appointment_id"]
    donation_id = handoff["donation_id"]
    parent_id = handoff["parent_resource_id"]
    children_ids = sorted(handoff["child_resource_ids"])
    assert children_ids and len(children_ids) == len(set(children_ids))
    for identifier in [donor_id, appointment_id, donation_id, parent_id, *children_ids]:
        assert str(UUID(identifier)) == identifier
    operator = handoff.get("operator", "operator1")
    donor_account = handoff.get("donor_account", "donor1")
    collector = state["accounts"][handoff.get("collector", "medical1")]
    account = state["accounts"][operator]
    assert account["role"] == "OPERATOR"
    tenant, actor = account["tenant_id"], account["id"]
    assert collector["role"] == "MEDICAL" and collector["tenant_id"] == tenant
    collection_actor = collector["id"]
    with checked_owner(state, "donantes") as conn:
        donor = conn.execute(
            "SELECT id::text,tenant_id::text,user_id::text,folio,display_name,status FROM donors WHERE id=%s",
            (donor_id,),
        ).fetchone()
        assert donor and donor[1:3] == (tenant, state["accounts"][donor_account]["id"])
        appointment = conn.execute(
            "SELECT id::text,donor_id::text,tenant_id::text,status FROM appointments WHERE id=%s",
            (appointment_id,),
        ).fetchone()
        assert appointment and appointment[1:] == (donor_id, tenant, "BOOKED")
        donation = conn.execute(
            "SELECT id::text,donor_id::text,tenant_id::text,status,version FROM donations WHERE id=%s",
            (donation_id,),
        ).fetchone()
        assert donation and donation[1:4] == (donor_id, tenant, "PROCESSED")
        steps = conn.execute(
            "SELECT state,actor_id::text FROM donation_steps WHERE donation_id=%s ORDER BY created_at,id",
            (donation_id,),
        ).fetchall()
        assert steps == [("COLLECTED", collection_actor), ("PROCESSED", actor)]
        event(conn, appointment_id, "APPOINTMENT_BOOKED", donor[2], "donantes")
        event(conn, donation_id, "DONATION_COLLECTED", collection_actor, "donantes")
        event(conn, donation_id, "DONATION_PROCESSED", actor, "donantes")
    with checked_owner(state, "inventario") as conn:
        parent = conn.execute(
            "SELECT id::text,folio,donation_id::text,current_institution_id::text,status,version FROM resources WHERE id=%s",
            (parent_id,),
        ).fetchone()
        assert parent and parent[2:5] == (donation_id, tenant, "WITHDRAWN")
        children = conn.execute(
            "SELECT id::text,folio,donation_id::text,current_institution_id::text,status,component,version FROM resources WHERE id=ANY(%s::uuid[]) ORDER BY id",
            (children_ids,),
        ).fetchall()
        assert [row[0] for row in children] == children_ids
        assert len(children) == 2
        assert {row[5] for row in children} == {"RBC", "PLASMA"}
        expected_status = {"RBC": "AVAILABLE", "PLASMA": "QUARANTINE"}
        assert all(row[2:5] == (donation_id, tenant, expected_status[row[5]]) for row in children)
        released = next(row for row in children if row[5] == "RBC")
        event(conn, released[0], "RESOURCE_RELEASED", collection_actor, "inventario")
        reviews = conn.execute(
            "SELECT decision,actor_id::text FROM resource_reviews WHERE resource_id=%s",
            (released[0],),
        ).fetchall()
        assert reviews == [("RELEASED", collection_actor)]
        lineage = conn.execute(
            "SELECT parent_id::text,child_id::text,donation_id::text,tenant_id::text,author_id::text FROM resource_lineage WHERE donation_id=%s ORDER BY child_id",
            (donation_id,),
        ).fetchall()
        assert lineage == [
            (parent_id, child_id, donation_id, tenant, actor)
            for child_id in children_ids
        ]
        for action in ("RESOURCE_CREATED", "RESOURCE_FRACTIONATED"):
            event(conn, parent_id, action, actor, "inventario")
    return {
        "operator": operator,
        "actor": actor,
        "collection_actor": collection_actor,
        "tenant": tenant,
        "donor": dict(
            zip(
                ("id", "tenant", "account", "folio", "display_name", "status"),
                donor,
                strict=True,
            )
        ),
        "appointment": {"id": appointment[0], "status": appointment[3]},
        "donation": {
            "id": donation[0],
            "status": donation[3],
            "version": donation[4],
            "steps": steps,
        },
        "parent": {
            "id": parent[0],
            "folio": parent[1],
            "status": parent[4],
            "version": parent[5],
        },
        "children": [
            {
                "id": row[0],
                "folio": row[1],
                "status": row[4],
                "component": row[5],
                "version": row[6],
            }
            for row in children
        ],
        "lineage": lineage,
        "limit": "Cita y colecta enlazadas por mismo donor_id; sin FK de cita ni cierre automático demostrado.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--handoff", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    os.umask(0o077)
    args.output.mkdir(mode=0o700, parents=True, exist_ok=False)
    handoff = json.loads(args.handoff.read_text())
    fixture = Path(handoff["fixture"]).resolve(strict=True)
    assert fixture == Path("/private/tmp/red-house-ms-tests-kojcusww")
    state = json.loads((fixture / "state.json").read_text())
    assert Path(state["directory"]).resolve() == fixture
    before = manifest()
    save(args.output, "fuentes-antes.json", before)
    business_before = oracle(state, handoff)
    save(args.output, "sql-antes.json", business_before)
    ready = json.loads(Path(handoff["runtime_ready_json"]).read_text())
    assert Path(ready["fixture_root"]).resolve() == fixture
    assert Path(ready["state_json"]).resolve() == fixture / "state.json"
    service_urls = ready["service_urls"]
    assert set(service_urls) == set(SERVICES)
    for url in service_urls.values():
        parsed = urlparse(url)
        assert parsed.scheme == "http" and parsed.hostname == "127.0.0.1" and parsed.port
        assert not parsed.username and not parsed.password and not parsed.query
    overrides = ready["runtime_overrides"]
    assert set(overrides) == {"TESTING", "RATE_LIMIT", "INTERNAL_RATE_LIMIT", "WORKER_REQUIRED"}
    assert overrides["TESTING"] is True and overrides["WORKER_REQUIRED"] is False
    configs = {}
    for name in SERVICES:
        config_path = Path(ready["service_config_files"][name]).resolve(strict=True)
        assert config_path == fixture / (name + ".json")
        config = json.loads(config_path.read_text())
        config.update(overrides)
        config["SERVICE_URLS"] = service_urls
        configs[name] = config
    save(args.output, "runtime-scope.json", {
        "fixture": str(fixture), "service_urls": service_urls,
        "runtime_overrides": overrides,
        "scope": "Functional synthetic fixture; not MFA, rate-limit or capacity acceptance",
    })
    # Mismo patrón monolítico de test_continuity.autonomous; sin platform/env.init.
    web = create_app(
        {
            "SECRET_KEY": secrets.token_hex(32),
            "JWT_SECRET_KEY": secrets.token_hex(32),
            "BACKEND_MODE": "monolith",
            "TESTING": True,
            "PRODUCTION": True,
            "SESSION_COOKIE_SECURE": True,
            "HIGHCHARTS_ENABLED": False,
            "MICROSERVICES_CONFIG": {
                "SERVICE_URLS": service_urls,
                **state["web_sessions"],
                "DOMAIN_CONFIGS": configs,
            },
        }
    )
    assert web.config["BACKEND_MODE"] == "monolith"
    assert set(web.extensions["application_kernel"].apps) == set(SERVICES)
    cert, key = make_ssl_devcert(str(args.output / "portal-tls"), host="localhost")

    class QuietHandler(WSGIRequestHandler):
        def log_request(self, *_args, **_kwargs):
            pass

    server = make_server(
        "127.0.0.1",
        0,
        web,
        threaded=True,
        ssl_context=(cert, key),
        request_handler=QuietHandler,
    )
    base = f"https://localhost:{server.server_port}"
    http_attempts = []
    real_request = requests.sessions.Session.request

    def reject_backend_http(_session, method, url, *_args, **_kwargs):
        # Guardia: cualquier fallback HTTP falla; nunca responde como un propietario.
        http_attempts.append({"method": method})
        raise AssertionError("El tramo web autónomo intentó HTTP externo")

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    requests.sessions.Session.request = reject_backend_http
    thread.start()
    code = None
    child = None
    try:
        payload = {
            **business_before,
            "base": base,
            "root": str(REPO),
            "output": str(args.output),
            "password": state["password"],
        }
        with (args.output / "browser.private.log").open("x") as log:
            child = subprocess.Popen(
                ["node", str(ROOT / "verify_shared_result.cjs")],
                stdin=subprocess.PIPE,
                text=True,
                stdout=log,
                stderr=subprocess.STDOUT,
            )
            child.communicate(input=json.dumps(payload), timeout=180)
        code = child.returncode
        business_after = oracle(state, handoff)
        save(args.output, "sql-despues.json", business_after)
        assert business_after == business_before
        assert not http_attempts
        assert code == 0, "Chrome falló; conservar browser.json y log privado"
        assert json.loads((args.output / "browser.json").read_text())["passed"]
    finally:
        if child is not None and child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait(timeout=5)
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()
        requests.sessions.Session.request = real_request
        after = manifest()
        save(args.output, "fuentes-despues.json", after)
        save(
            args.output,
            "runner.json",
            {
                "browser_exit": code,
                "sources_unchanged": before == after,
                "source_count": len(before),
                "backend_mode": "monolith",
                "backend_http_attempts": http_attempts,
                "web_thread_closed": not thread.is_alive(),
                "infrastructure_created_or_stopped": False,
            },
        )
        assert before == after and not thread.is_alive()


if __name__ == "__main__":
    main()
