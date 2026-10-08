import threading
import time
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
import requests
from pymongo import MongoClient
from werkzeug.serving import make_server

from redhouse.errors import APIError
from redhouse.events import dispatch
from scripts.local import Environment

from .conftest import QuietHandler
from .helpers import (
    evaluation,
    iso,
    move,
    plan,
    recipient_request,
    reservation,
    resource,
)


def restart_dependency(p, name):
    process = next(
        process
        for process in p.env.processes
        if process.pid == p.env.state["infrastructure_pids"][name]
    )
    process.terminate()
    process.wait(timeout=15)
    p.env.processes.remove(process)

    def restore():
        replacement = p.env.launch(p.env.state["infrastructure_commands"][name], name)
        p.env.state["infrastructure_pids"][name] = replacement.pid
        if name == "mongodb":
            p.env.wait(
                lambda: MongoClient(
                    p.env.state["mongo_admin"], serverSelectionTimeoutMS=1000
                ).admin.command("ping")
            )
        elif name == "redis":
            import redis

            p.env.wait(lambda: redis.Redis.from_url(p.env.state["redis_admin"]).ping())
        else:
            import psycopg

            p.env.wait(lambda: psycopg.connect(p.env.state["database_admin"]).close())

    return restore


def test_redis_down_fails_closed_and_recovers_sessions(p):
    restore = restart_dependency(p, "redis")
    try:
        assert p.request("receptores", "GET", "/api/v1/recipients").status_code == 503
        assert (
            p.request("receptores", "GET", "/health/live", user=None).status_code == 200
        )
        assert (
            p.request("receptores", "GET", "/health/ready", user=None).status_code
            == 503
        )
    finally:
        restore()
    assert p.request("receptores", "GET", "/api/v1/recipients").status_code == 200


def test_postgresql_down_liveness_readiness_and_recovery(p):
    restore = restart_dependency(p, "postgres")
    try:
        assert p.request("receptores", "GET", "/api/v1/recipients").status_code == 503
        assert (
            p.request("receptores", "GET", "/health/database", user=None).status_code
            == 503
        )
        assert (
            p.request("receptores", "GET", "/health/live", user=None).status_code == 200
        )
    finally:
        restore()
    assert p.request("receptores", "GET", "/api/v1/recipients").status_code == 200


def test_mongodb_down_keeps_audit_durable_then_replays(p):
    restore = restart_dependency(p, "mongodb")
    try:
        resource(p)
        p.drain(rounds=2)
        assert (
            p.request("auditoria", "GET", "/api/v1/events", user="auditor1").status_code
            == 200
        )
        assert (
            p.request(
                "auditoria", "GET", "/api/v1/documentary-events", user="auditor1"
            ).status_code
            == 503
        )
        assert (
            p.request("auditoria", "GET", "/health/ready", user=None).status_code == 503
        )
        with p.owner("auditoria") as conn:
            assert (
                conn.execute(
                    "SELECT count(*) FROM outbox WHERE target='mongodb' AND delivered_at IS NULL"
                ).fetchone()[0]
                > 0
            )
    finally:
        restore()
    time.sleep(2.1)
    p.drain()
    assert (
        p.request(
            "auditoria", "GET", "/api/v1/documentary-events", user="auditor1"
        ).status_code
        == 200
    )
    with p.owner("auditoria") as conn:
        assert (
            conn.execute(
                "SELECT count(*) FROM outbox WHERE target='mongodb' AND delivered_at IS NULL"
            ).fetchone()[0]
            == 0
        )


def test_lost_confirmation_response_can_resume_without_duplicate(p, monkeypatch):
    from ms_inventario import routes

    unit = resource(p)
    _, req = recipient_request(p)
    ev = evaluation(p, req, [unit])
    real = routes.call
    lost = False

    def lose_response(service, method, path, data=None, **kwargs):
        nonlocal lost
        result = real(service, method, path, data, **kwargs)
        if (
            service == "receptores"
            and data
            and data.get("action") == "CONFIRM"
            and not lost
        ):
            lost = True
            raise APIError(
                "dependency_unavailable", "Respuesta perdida para prueba.", 503
            )
        return result

    monkeypatch.setattr(routes, "call", lose_response)
    result = reservation(p, ev, unit)
    assert result["status"] == "PENDING"
    with p.apps["inventario"].app_context():
        assert routes.recover_operations()["recovered"] >= 1
    resumed = p.ok("inventario", "GET", "/api/v1/operations/" + result["operation_id"])
    assert resumed["status"] == "COMPLETED"
    assert resumed["reservation"]["id"] == result["reservation"]["id"]


def test_local_audit_failure_rolls_back_and_compensates_hold(p, monkeypatch):
    from ms_inventario import routes

    unit = resource(p)
    _, req = recipient_request(p)
    ev = evaluation(p, req, [unit])
    real = routes.emit

    def fail(conn, action, *args, **kwargs):
        if action == "RESOURCE_RESERVED":
            raise RuntimeError("fallo de auditoría local controlado")
        return real(conn, action, *args, **kwargs)

    monkeypatch.setattr(routes, "emit", fail)
    response = p.request(
        "inventario",
        "POST",
        "/api/v1/reservations",
        data={
            "evaluation_id": ev["id"],
            "resource_id": unit["id"],
            "human_confirmation": True,
            "reason": "Reserva ficticia para comprobar rollback",
        },
    )
    assert response.status_code == 500
    with p.owner("inventario") as conn:
        assert (
            conn.execute(
                "SELECT status FROM resources WHERE id=%s", (unit["id"],)
            ).fetchone()[0]
            == "AVAILABLE"
        )
        assert (
            conn.execute(
                "SELECT count(*) FROM reservations WHERE resource_id=%s", (unit["id"],)
            ).fetchone()[0]
            == 0
        )
        conn.execute(
            "UPDATE operations SET created_at=now()-interval '65 seconds' WHERE input->>'resource_id'=%s",
            (unit["id"],),
        )
    with p.apps["inventario"].app_context():
        routes.recover_operations()
    with p.owner("receptores") as conn:
        assert (
            conn.execute(
                "SELECT status FROM holds WHERE request_id=%s", (req["id"],)
            ).fetchone()[0]
            == "RELEASED"
        )


def test_custody_service_down_does_not_lose_physical_event(p):
    unit = resource(p)
    _, req = recipient_request(p)
    ev = evaluation(p, req, [unit])
    allocated = reservation(p, ev, unit)["reservation"]
    shipment = plan(p, allocated)
    old_server = p.servers["custodia"]
    port = old_server.server_port
    old_server.shutdown()
    old_server.server_close()
    try:
        shipment = move(p, shipment, "PREPARED", "operator1")
        shipment = move(p, shipment, "COLLECTED", "transport1")
        p.drain(rounds=2)
        with p.owner("transporte") as conn:
            assert (
                conn.execute(
                    "SELECT count(*) FROM outbox WHERE target='custodia' AND delivered_at IS NULL AND event->>'resource_id'=%s",
                    (shipment["id"],),
                ).fetchone()[0]
                == 3
            )
    finally:
        server = make_server(
            "127.0.0.1",
            port,
            p.apps["custodia"],
            threaded=True,
            request_handler=QuietHandler,
        )
        p.servers["custodia"] = server
        threading.Thread(target=server.serve_forever, daemon=True).start()
    time.sleep(2.1)
    p.drain()
    chain = p.ok(
        "custodia", "GET", "/api/v1/chains/" + shipment["id"], user="transport1"
    )
    assert [e["sequence"] for e in chain["events"]] == [1, 2, 3]


def test_receipt_closes_multiunit_request_once(p):
    units = [resource(p) for _ in range(2)]
    _, req = recipient_request(p, quantity=2)
    shipments = []
    for unit in units:
        ev = evaluation(p, req, [unit])
        assigned = reservation(p, ev, unit)["reservation"]
        shipment = plan(p, assigned)
        for state, user in [
            ("PREPARED", "operator1"),
            ("COLLECTED", "transport1"),
            ("IN_TRANSIT", "transport1"),
            ("DELIVERED", "transport1"),
        ]:
            shipment = move(p, shipment, state, user)
        shipments.append(shipment)
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(lambda s: move(p, s, "ACCEPTED", "operator2"), shipments))
    p.drain()
    result = p.ok("receptores", "GET", "/api/v1/requests/" + req["id"])
    assert result["status"] == "CLOSED"
    with p.owner("receptores") as conn:
        assert (
            conn.execute(
                "SELECT count(*) FROM activity_events WHERE event->>'action'='REQUEST_CLOSED' AND event->>'resource_id'=%s",
                (req["id"],),
            ).fetchone()[0]
            == 1
        )


def test_monitoring_records_degraded_down_and_recovery(p):
    from servicio_monitoreo.routes import poll

    app = p.apps["monitoreo"]
    original = app.config["SERVICE_URLS"]["custodia"]
    app.config["SERVICE_URLS"] = dict(
        app.config["SERVICE_URLS"], custodia="http://127.0.0.1:1"
    )
    try:
        with app.app_context():
            result = poll()
        assert (
            next(c for c in result["items"] if c["service"] == "custodia")["state"]
            == "down"
        )
    finally:
        app.config["SERVICE_URLS"]["custodia"] = original
    with app.app_context():
        result = poll()
    assert (
        next(c for c in result["items"] if c["service"] == "custodia")["state"] == "up"
    )
    status = p.ok("monitoreo", "GET", "/api/v1/status", user="admin1")
    stats = next(c for c in status["statistics"] if c["service"] == "custodia")
    assert stats["errors"] >= 1 and stats["average_ms"] > 0
