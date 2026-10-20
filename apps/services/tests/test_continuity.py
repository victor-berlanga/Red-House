"""Operaciones reales del monolito sin ningún listener de API disponible."""

import json
import secrets
import threading
from contextlib import contextmanager
from uuid import uuid4

import pytest
from werkzeug.serving import make_server

from .conftest import QuietHandler
from .test_web_integration import (
    create_app,
    login,
    test_full_reservation_transport_receipt_from_web_and_xml as complete_flow,
    test_donor_campaign_appointment_processing_and_inventory_source_from_web as donation_flow,
)


@contextmanager
def stopped_apis(p):
    ports = {name: server.server_port for name, server in p.servers.items()}
    for server in p.servers.values():
        server.shutdown()
        server.server_close()
    try:
        yield
    finally:
        for name, port in ports.items():
            replacement = make_server(
                "127.0.0.1",
                port,
                p.apps[name],
                threaded=True,
                request_handler=QuietHandler,
            )
            p.servers[name] = replacement
            threading.Thread(target=replacement.serve_forever, daemon=True).start()


@pytest.fixture
def autonomous(p, tmp_path, monkeypatch):
    web = create_app(
        {
            "SECRET_KEY": secrets.token_hex(32),
            "JWT_SECRET_KEY": secrets.token_hex(32),
            "BACKEND_MODE": "monolith",
            "TESTING": True,
            "PRODUCTION": False,
            "SESSION_COOKIE_SECURE": False,
            "HIGHCHARTS_ENABLED": False,
            "MICROSERVICES_CONFIG": {
                "SERVICE_URLS": p.urls,
                **p.env.state["web_sessions"],
                "DOMAIN_CONFIGS": {
                    name: dict(app.config) for name, app in p.apps.items()
                },
            },
        }
    )
    kernel = web.extensions["application_kernel"]

    def request(
        service, method, path, *, user="medical2", data=None, key=None, headers=None
    ):
        hdr = {"Accept": "application/json", "Idempotency-Key": key or uuid4().hex}
        if user:
            hdr["Authorization"] = "Bearer " + p.tokens[user]
        if data is not None:
            hdr["Content-Type"] = "application/json"
        hdr.update(headers or {})
        return kernel.request(
            service,
            method,
            path,
            data=json.dumps(data).encode() if data is not None else None,
            headers=hdr,
        )

    with stopped_apis(p):
        with monkeypatch.context() as changes:
            changes.setattr(p, "request", request)
            changes.setattr(p, "apps", kernel.apps)
            yield web


@pytest.mark.parametrize(
    "kind,component,group", [("BLOOD", "RBC", "O+"), ("ORGAN", "KIDNEY", "O+")]
)
def test_complete_web_flow_without_apis(autonomous, p, kind, component, group):
    complete_flow(autonomous, p, kind, component, group)


def test_donation_processing_without_apis(autonomous, p):
    donation_flow(autonomous, p)


def test_monolith_redis_failure_fails_closed_and_recovers(autonomous, p, monkeypatch):
    client = login(autonomous, p, "operator1")
    assert client.get("/inventario").status_code == 200
    kernel = autonomous.extensions["application_kernel"]
    with monkeypatch.context() as changes:
        for app in kernel.apps.values():
            changes.setitem(app.config, "REDIS_URL", "redis://127.0.0.1:1/0")
        assert client.get("/inventario").status_code == 503
    assert client.get("/inventario").status_code == 200
