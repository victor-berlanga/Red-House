"""Contratos y aislamiento sin iniciar bases ni servicios de red."""

import importlib
import json
import os
import secrets
import subprocess
import sys
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from unittest.mock import patch
from uuid import uuid4

import pytest
from flask import Flask
from redhouse.config import SERVICES
from redhouse.xml_response import validate_response
from redhouse.examples import response_xml
from scripts.package_service import package

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / "web"))
from src.integration import sessions
from src.access import BusinessError


def app_for_sessions(tmp_path):
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=secrets.token_hex(32),
        WEB_SESSION_STORE=str(tmp_path / "sessions.sqlite3"),
    )
    return app


def save_session(app, sid):
    with app.app_context(), sessions.database() as conn:
        sessions.save(
            conn,
            sid,
            {
                "access_token": "old-access",
                "refresh_token": "private-refresh",
                "expires_at": time.time() + 900,
                "session_expires": time.time() + 86400,
            },
        )


def test_logout_failure_clears_credentials_and_queues_encrypted_revocation(tmp_path):
    app = app_for_sessions(tmp_path)
    sid = secrets.token_urlsafe(32)
    save_session(app, sid)
    with (
        app.app_context(),
        patch.object(sessions, "call", side_effect=BusinessError("Unavailable", 503)),
    ):
        assert sessions.logout(sid) is False
        assert sessions.load(sid) is None
        with sessions.database() as conn:
            payload = conn.execute("SELECT payload FROM revocations").fetchone()[0]
            assert b"private-refresh" not in payload and b"old-access" not in payload
    with (
        app.app_context(),
        patch.object(sessions, "call", return_value={"revoked": True}),
    ):
        assert sessions.retry_revocations() == 1
        assert sessions.load(sid) is None


def test_network_renewal_does_not_lock_other_sessions(tmp_path):
    app = app_for_sessions(tmp_path)
    first, second = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    save_session(app, first)
    waiting, finish = Event(), Event()

    def remote(*args, **kwargs):
        waiting.set()
        assert finish.wait(5)
        return {
            "access_token": "new-access",
            "refresh_token": "new-refresh",
            "expires_in": 900,
        }

    def renew():
        with app.app_context():
            return sessions.renew(first)

    with (
        patch.object(sessions, "call", side_effect=remote),
        ThreadPoolExecutor(max_workers=2) as pool,
    ):
        pending = pool.submit(renew)
        assert waiting.wait(3)
        try:
            independent = pool.submit(save_session, app, second)
            independent.result(timeout=2)
        finally:
            finish.set()
        pending.result(timeout=5)
    with app.app_context():
        assert sessions.load(first)["access_token"] == "new-access"


def test_xml_response_rejects_invalid_types_duplicates_and_missing_fields():
    schema = {
        "type": "object",
        "required": ["quantity"],
        "properties": {"quantity": {"type": "integer"}},
    }
    assert validate_response(response_xml({"quantity": 12}).encode(), schema) == {
        "quantity": 12
    }
    for xml in [
        b'<response type="object"><field name="quantity" type="integer">not-a-number</field></response>',
        b'<response type="object"><field name="quantity" type="integer">1</field><field name="quantity" type="integer">2</field></response>',
        b'<response type="object"/>',
    ]:
        with pytest.raises(ValueError):
            validate_response(xml, schema)


def test_legacy_rows_helper_does_not_truncate_after_first_hundred():
    from src.integration.routes.common import rows

    data = [{"id": str(uuid4())} for _ in range(125)]

    def page(*args, params):
        start = (params["page"] - 1) * 100
        return {"items": data[start : start + 100], "total": 125}

    with patch("src.integration.routes.common.call", side_effect=page):
        assert rows("donantes", "/api/v1/donors") == data


@pytest.mark.parametrize("service", list(SERVICES))
def test_service_artifact_loads_without_other_domain_packages(tmp_path, service):
    artifact = package(service, tmp_path / service)
    own = "servicio_monitoreo" if service == "monitoreo" else "ms_" + service
    domains = [
        p.name
        for p in artifact.iterdir()
        if p.name.startswith("ms_") or p.name == "servicio_monitoreo"
    ]
    assert domains == [own]
    program = """
import importlib,json,sys
module=sys.argv[1]
app=importlib.import_module(module).create_app({'DATABASE_URL':'unused','JWT_PUBLIC_KEY':'unused','JWT_PRIVATE_KEY':'unused'})
response=app.test_client().get('/openapi.json')
assert response.status_code==200
assert not any(k.startswith('ms_') and k.split('.')[0]!=module for k in sys.modules)
print(len(response.json['paths']))
"""
    result = subprocess.run(
        [sys.executable, "-B", "-c", program, own],
        cwd=artifact,
        env={**os.environ, "PYTHONPATH": str(artifact)},
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr


def test_catalogue_schemas_and_examples_compile_without_dependencies():
    from redhouse.codec import request_xsd
    from redhouse.examples import sample, request_xml
    from lxml import etree as E

    for service in SERVICES:
        own = "servicio_monitoreo" if service == "monitoreo" else "ms_" + service
        app = importlib.import_module(own).create_app(
            {
                "DATABASE_URL": "unused",
                "JWT_PUBLIC_KEY": "unused",
                "JWT_PRIVATE_KEY": "unused",
            }
        )
        for contract in app.extensions["contracts"]:
            model = contract["model"]
            if model:
                schema = E.XMLSchema(E.fromstring(request_xsd(model)))
                example = sample(model.model_json_schema())
                assert schema.validate(E.fromstring(request_xml(example).encode())), (
                    service,
                    contract["name"],
                    str(schema.error_log),
                )
