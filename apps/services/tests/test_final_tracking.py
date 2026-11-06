"""WebSockets reales, PostgreSQL/MongoDB/Redis aislados; sin hardware GPS."""

import json
import ssl
import threading
from uuid import uuid4

import pytest
import websocket
from werkzeug.serving import make_server

from .helpers import (
    resource,
    recipient_request,
    evaluation,
    reservation,
    plan,
    move,
    iso,
)
from ms_transporte.tracking_contracts import Message, Event, encode, decode


@pytest.fixture
def tracking(p, tmp_path):
    unit = resource(p)
    _, demand = recipient_request(p)
    allocation = reservation(p, evaluation(p, demand, [unit]), unit)
    shipment = plan(p, allocation["reservation"])
    shipment = move(p, shipment, "PREPARED", "operator1")
    device = p.ok(
        "identidad_acceso",
        "POST",
        "/api/v1/devices",
        user="admin1",
        data={
            "id": str(uuid4()),
            "user_id": p.env.state["accounts"]["transport1"]["id"],
            "source": "SIMULATOR",
            "label": "GPS sintético",
            "expires_at": iso(days=1),
        },
    )
    credential = p.ok(
        "identidad_acceso",
        "POST",
        f"/api/v1/devices/{device['id']}/credentials",
        user="admin1",
        data={
            "version": 1,
            "human_confirmation": True,
            "reason": "Credencial para integración aislada",
        },
    )
    assignment = p.ok(
        "transporte",
        "POST",
        f"/api/v1/shipments/{shipment['id']}/tracking/assignments",
        user="coordinator1",
        data={
            "device_id": device["id"],
            "starts_at": iso(minutes=-5),
            "ends_at": iso(minutes=60),
            "version": shipment["version"],
            "human_confirmation": True,
            "reason": "Rastreo autorizado de prueba",
        },
    )
    # Certificado de prueba confiado explícitamente por el cliente: WSS con verificación TLS.
    from werkzeug.serving import make_ssl_devcert

    cert, private_key = make_ssl_devcert(str(tmp_path / "tls"), host="localhost")
    app = p.apps["transporte"]
    server = make_server(
        "127.0.0.1", 0, app, threaded=True, ssl_context=(cert, private_key)
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    value = {
        "shipment": shipment,
        "device": device,
        "credential": credential,
        "assignment": assignment,
        "url": f"wss://localhost:{server.server_port}/ws/v1/tracking/",
        "cert": cert,
        "server": server,
    }
    yield value
    server.shutdown()
    server.server_close()


def connect(t, token, kind="user", fmt="json", **kwargs):
    ws = websocket.create_connection(
        t["url"] + fmt,
        timeout=8,
        suppress_origin=True,
        subprotocols=["redhouse.tracking.v1." + fmt],
        sslopt={"ca_certs": t["cert"], "cert_reqs": ssl.CERT_REQUIRED},
        **kwargs,
    )
    send(
        ws, {"type": "authenticate", "credential_kind": kind, "credential": token}, fmt
    )
    return ws


def send(ws, value, fmt="json"):
    ws.send(encode(value, fmt, Message))


def receive(ws, typ, fmt="json"):
    for _ in range(10):
        value = decode(ws.recv(), Event, fmt)
        if value["type"] == typ:
            return value
        assert value["type"] not in ("error", "resync.required"), value
    pytest.fail("No se recibió el evento esperado")


def point(t, sequence=1, **values):
    return dict(
        {
            "event_id": str(uuid4()),
            "shipment_id": t["shipment"]["id"],
            "device_id": t["device"]["id"],
            "source": "SIMULATOR",
            "sequence": sequence,
            "captured_at": iso(),
            "fix_valid": True,
            "latitude": 25.6866,
            "longitude": -100.3161,
            "accuracy_m": 8.0,
        },
        **values,
    )


def test_wss_json_xml_durable_replay_order_and_revocation(p, tracking):
    t = tracking
    publisher = connect(t, t["credential"]["credential"], "device")
    receive(publisher, "authenticated")
    subscriber = connect(t, p.tokens["coordinator1"], fmt="xml")
    receive(subscriber, "authenticated", "xml")
    send(subscriber, {"type": "subscribe", "shipment_id": t["shipment"]["id"]}, "xml")
    assert receive(subscriber, "subscribed", "xml")["cursor"] == 0
    first = point(t)
    send(publisher, {"type": "position.publish", "position": first})
    ack = receive(publisher, "position.ack")
    assert ack["state"] == "PERSISTED_SQL"
    event = receive(subscriber, "position.updated", "xml")
    assert event["position"]["event_id"] == first["event_id"]
    send(publisher, {"type": "position.publish", "position": first})
    assert receive(publisher, "position.ack")["cursor"] == ack["cursor"]
    subscriber.close()
    late = point(t, 2, captured_at=iso(minutes=-1))
    send(publisher, {"type": "position.publish", "position": late})
    assert receive(publisher, "position.ack")["cursor"] == 2
    result = p.ok(
        "transporte",
        "GET",
        f"/api/v1/shipments/{t['shipment']['id']}/tracking/snapshot?cursor=1",
        user="coordinator1",
    )
    assert result["position"]["event_id"] == first["event_id"]
    assert result["events"][0]["event_id"] == late["event_id"]
    subscriber = connect(t, p.tokens["coordinator1"])
    receive(subscriber, "authenticated")
    send(
        subscriber,
        {"type": "subscribe", "shipment_id": t["shipment"]["id"], "cursor": 1},
    )
    receive(subscriber, "subscribed")
    assert (
        receive(subscriber, "position.updated")["position"]["event_id"]
        == late["event_id"]
    )
    p.ok(
        "transporte",
        "POST",
        f"/api/v1/tracking/assignments/{t['assignment']['id']}/revoke",
        user="coordinator1",
        data={
            "version": 1,
            "human_confirmation": True,
            "reason": "Finalizar autorización de prueba",
        },
    )
    assert receive(subscriber, "error")["code"] == "tracking_closed"
    send(publisher, {"type": "position.publish", "position": point(t, 3)})
    assert receive(publisher, "error")["code"] == "unassigned_device"
    subscriber.close()
    publisher.close()
    p.drain()
    with p.owner("transporte") as conn:
        assert (
            conn.execute(
                "SELECT count(*) FROM tracking_points WHERE shipment_id=%s",
                (t["shipment"]["id"],),
            ).fetchone()[0]
            == 2
        )


@pytest.mark.parametrize("fmt", ["json", "xml"])
def test_wss_rejects_donor_device_read_invalid_and_conflicting_events(p, tracking, fmt):
    t = tracking
    donor = connect(t, p.tokens["donor1"], fmt=fmt)
    assert receive(donor, "error", fmt)["code"] == "forbidden"
    donor.close()
    device = connect(t, t["credential"]["credential"], "device", fmt)
    receive(device, "authenticated", fmt)
    first = point(t)
    send(device, {"type": "position.publish", "position": first}, fmt)
    receive(device, "position.ack", fmt)
    send(
        device,
        {"type": "position.publish", "position": dict(first, latitude=26.0)},
        fmt,
    )
    assert receive(device, "error", fmt)["code"] == "event_conflict"
    device.close()


def test_tracking_rejects_xxe_nonfinite_and_unknown_fields():
    from redhouse.errors import APIError

    for raw, fmt in [
        (
            "<!DOCTYPE request [<!ENTITY a SYSTEM 'file:///etc/passwd'>]><request>&a;</request>",
            "xml",
        ),
        ('{"type":"heartbeat","unknown":true}', "json"),
        ('{"type":"heartbeat","x":NaN}', "json"),
    ]:
        with pytest.raises(APIError):
            decode(raw, representation=fmt)


@pytest.mark.parametrize("fmt", ["json", "xml"])
def test_sync_commands_idempotency_scope_versions_and_cursor(p, tracking, fmt):
    from .test_final_quality import api

    t = tracking
    command = {
        "id": str(uuid4()),
        "shipment_id": t["shipment"]["id"],
        "device_id": t["device"]["id"],
        "expected_version": t["shipment"]["version"],
        "captured_at": iso(),
        "body": {
            "command": "TRANSPORT_OBSERVATION",
            "reason": "Observación offline sintética",
        },
    }
    first = api(p, "transporte", "/api/v1/sync/commands", command, "transport1", fmt)
    assert (
        api(p, "transporte", "/api/v1/sync/commands", command, "transport1", fmt)
        == first
    )
    assert (
        p.request(
            "transporte",
            "POST",
            "/api/v1/sync/commands",
            user="transport1",
            data=dict(command, captured_at=iso(minutes=-1)),
        ).status_code
        == 409
    )
    assert (
        p.request(
            "transporte",
            "POST",
            "/api/v1/sync/commands",
            user="transport1",
            data=dict(command, id=str(uuid4()), expected_version=1),
        ).status_code
        == 412
    )
    assert (
        p.request(
            "transporte",
            "GET",
            "/api/v1/sync/commands/" + command["id"],
            user="transport2",
        ).status_code
        == 403
    )
    assert (
        api(
            p,
            "transporte",
            "/api/v1/sync/commands/" + command["id"],
            user="transport1",
            fmt=fmt,
            method="GET",
        )
        == first
    )
    changes = api(
        p,
        "transporte",
        "/api/v1/sync/changes?cursor=" + str(first["cursor"] - 1),
        user="transport1",
        fmt=fmt,
        method="GET",
    )
    assert changes["items"] == [first]
    p.ok(
        "identidad_acceso",
        "POST",
        f"/api/v1/devices/{t['device']['id']}/revoke",
        user="admin1",
        data={
            "version": 2,
            "human_confirmation": True,
            "reason": "Revocación del dispositivo de prueba",
        },
    )
    assert (
        p.request(
            "transporte",
            "GET",
            "/api/v1/sync/commands/" + command["id"],
            user="transport1",
        ).status_code
        == 403
    )


@pytest.mark.parametrize("fmt", ["json", "xml"])
def test_executable_simulator_offline_reconnect_and_dedup(p, tracking, tmp_path, fmt):
    import subprocess
    import sys
    import sqlite3
    from pathlib import Path

    t = tracking
    config = tmp_path / "bridge.json"
    config.write_text(
        json.dumps(
            {
                "url": t["url"].rstrip("/"),
                "credential": t["credential"]["credential"],
                "shipment_id": t["shipment"]["id"],
                "device_id": t["device"]["id"],
                "ca_file": t["cert"],
            }
        )
    )
    config.chmod(0o600)
    spool = tmp_path / "pending.sqlite"
    command = [
        sys.executable,
        str(Path(__file__).resolve().parents[1] / "scripts/gps_bridge.py"),
        "--config",
        str(config),
        "--spool",
        str(spool),
        "--format",
        fmt,
        "--simulate",
        "regional",
        "--count",
        "3",
        "--interval",
        "0.1",
        "--seed",
        "7",
    ]
    offline = subprocess.run(
        command + ["--scenario", "offline"], capture_output=True, text=True, timeout=30
    )
    assert offline.returncode == 0, offline.stderr
    with sqlite3.connect(spool) as db:
        assert db.execute("SELECT count(*) FROM pending").fetchone()[0] == 3
    assert b"latitude" not in spool.read_bytes()
    subscriber = connect(t, p.tokens["coordinator1"], fmt=fmt)
    receive(subscriber, "authenticated", fmt)
    send(
        subscriber,
        {"type": "subscribe", "shipment_id": t["shipment"]["id"], "cursor": 0},
        fmt,
    )
    receive(subscriber, "subscribed", fmt)
    online = subprocess.run(
        command + ["--scenario", "duplicate"],
        capture_output=True,
        text=True,
        timeout=40,
    )
    assert online.returncode == 0, online.stderr
    assert (
        len(online.stdout.splitlines()) == 9
    )  # tres pendientes + tres eventos reenviados.
    events = [
        receive(subscriber, "position.updated", fmt)["position"] for _ in range(6)
    ]
    assert len({e["event_id"] for e in events}) == 6
    subscriber.close()
    with sqlite3.connect(spool) as db:
        assert db.execute("SELECT count(*) FROM pending").fetchone()[0] == 0
    metrics = p.ok(
        "transporte",
        "GET",
        f"/api/v1/shipments/{t['shipment']['id']}/tracking/metrics",
        user="coordinator1",
    )
    assert (
        metrics["persisted_points"] == 6 and metrics["capture_to_receive_p95_ms"] >= 0
    )


@pytest.mark.parametrize("dependency", ["redis", "postgres", "mongodb"])
def test_tracking_dependency_failure_preserves_durable_cursor(p, tracking, dependency):
    from .test_resilience import restart_dependency

    t = tracking
    publisher = connect(t, t["credential"]["credential"], "device")
    receive(publisher, "authenticated")
    first = point(t)
    send(publisher, {"type": "position.publish", "position": first})
    receive(publisher, "position.ack")
    restore = restart_dependency(p, dependency)
    second = point(t, 2)
    try:
        send(publisher, {"type": "position.publish", "position": second})
        event = receive(
            publisher, "position.ack" if dependency == "mongodb" else "error"
        )
        if dependency != "mongodb":
            assert event["code"] in ("redis_unavailable", "database_unavailable")
        else:
            assert event["cursor"] == 2
    finally:
        publisher.close()
        restore()
    publisher = connect(t, t["credential"]["credential"], "device")
    receive(publisher, "authenticated")
    send(publisher, {"type": "position.publish", "position": second})
    assert receive(publisher, "position.ack")["cursor"] == 2
    publisher.close()
    p.drain()
    result = p.ok(
        "transporte",
        "GET",
        f"/api/v1/shipments/{t['shipment']['id']}/tracking/snapshot?cursor=0",
        user="coordinator1",
    )
    assert len(result["events"]) == 2


def test_tracking_scope_origin_cursor_limits_and_device_revocation(
    p, tracking, monkeypatch
):
    t = tracking
    outsider = connect(t, p.tokens["transport2"])
    receive(outsider, "authenticated")
    send(outsider, {"type": "subscribe", "shipment_id": t["shipment"]["id"]})
    assert receive(outsider, "error")["code"] == "forbidden"
    outsider.close()
    with pytest.raises(websocket.WebSocketBadStatusException):
        websocket.create_connection(
            t["url"] + "json",
            origin="https://untrusted.invalid",
            timeout=5,
            subprotocols=["redhouse.tracking.v1.json"],
            sslopt={"ca_certs": t["cert"]},
        )
    subscriber = connect(t, p.tokens["coordinator1"])
    receive(subscriber, "authenticated")
    send(
        subscriber,
        {"type": "subscribe", "shipment_id": t["shipment"]["id"], "cursor": 999},
    )
    assert receive(subscriber, "resync.required")["code"] == "resync_required"
    send(subscriber, {"type": "subscribe", "shipment_id": t["shipment"]["id"]})
    receive(subscriber, "subscribed")
    monkeypatch.setitem(
        p.apps["transporte"].config, "TRACKING_CONNECTIONS_PER_ACTOR", 1
    )
    excess = connect(t, p.tokens["coordinator1"])
    assert receive(excess, "error")["code"] == "connection_limit"
    excess.close()
    p.ok(
        "identidad_acceso",
        "POST",
        f"/api/v1/devices/{t['device']['id']}/revoke",
        user="admin1",
        data={
            "version": 2,
            "human_confirmation": True,
            "reason": "Cierre del GPS asignado de prueba",
        },
    )
    assert receive(subscriber, "error")["code"] == "tracking_closed"
    subscriber.close()


def test_nmea_adapter_checksum_units_and_no_fix():
    from scripts.gps_bridge import nmea_rmc

    row = nmea_rmc(
        "$GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*6A"
    )
    assert row["latitude"] == pytest.approx(48.1173)
    assert row["speed_m_s"] == pytest.approx(22.4 * 1852 / 3600)
    with pytest.raises(ValueError):
        nmea_rmc("$GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*00")


@pytest.mark.parametrize("fmt", ["json", "xml"])
def test_custody_scans_receipt_sync_and_distinct_final_use(p, tracking, fmt):
    from .test_final_quality import api
    from .test_final_operations import CONFIRM

    t = tracking
    shipment = t["shipment"]
    allocation = p.ok(
        "inventario",
        "GET",
        "/api/v1/reservations/" + shipment["reservation_id"],
        user="operator1",
    )
    for state, user, handover in [
        ("COLLECTED", "transport1", "operator1"),
        ("IN_TRANSIT", "transport1", None),
        ("DELIVERED", "transport1", "operator2"),
        ("ACCEPTED", "operator2", "transport1"),
    ]:
        body = {**CONFIRM, "version": shipment["version"], "state": state}
        if handover:
            body["custody"] = {
                "scanned_resource_id": allocation["resource_id"],
                "seal": "SELLO-SINTETICO",
                "captured_at": iso(),
                "reported_handover_user_id": p.env.state["accounts"][handover]["id"],
                "electronic_acceptance": True,
            }
            invalid = dict(
                body, custody=dict(body["custody"], scanned_resource_id=str(uuid4()))
            )
            assert (
                p.request(
                    "transporte",
                    "POST",
                    f"/api/v1/shipments/{shipment['id']}/transitions",
                    user=user,
                    data=invalid,
                ).status_code
                == 409
            )
        shipment = api(
            p,
            "transporte",
            f"/api/v1/shipments/{shipment['id']}/transitions",
            body,
            user,
            fmt,
        )
        p.drain()
    changes = api(
        p,
        "transporte",
        f"/api/v1/sync/shipments/{shipment['id']}/changes?cursor=0",
        user="operator2",
        fmt=fmt,
        method="GET",
    )
    assert not changes["active"] and changes["items"][-1]["state"] == "ACCEPTED"
    assert changes["cursor"] == shipment["sequence"]
    unit = p.ok(
        "inventario",
        "GET",
        "/api/v1/resources/" + allocation["resource_id"],
        user="medical2",
    )
    assert unit["status"] == "RECEIVED"
    trace = api(
        p,
        "inventario",
        f"/api/v1/resources/{unit['id']}/trace",
        user="medical2",
        fmt=fmt,
        method="GET",
    )
    assert not trace["final_destination_recorded"]
    api(
        p,
        "inventario",
        f"/api/v1/resources/{unit['id']}/destination",
        {
            **CONFIRM,
            "version": unit["version"],
            "destination": "TRANSFUSED",
            "reference": "Registro sintético autorizado de uso",
            "occurred_at": iso(),
        },
        "medical2",
        fmt,
    )
    assert api(
        p,
        "inventario",
        f"/api/v1/resources/{unit['id']}/trace",
        user="medical2",
        fmt=fmt,
        method="GET",
    )["final_destination_recorded"]


def test_concurrent_emitters_subscribers_and_delayed_consumer(
    p, tracking, record_property
):
    from concurrent.futures import ThreadPoolExecutor
    from time import perf_counter
    from statistics import mean

    t = tracking
    subscribers = [
        connect(t, p.tokens["coordinator1"], fmt=fmt) for fmt in ("json", "xml")
    ]
    for ws, fmt in zip(subscribers, ("json", "xml")):
        receive(ws, "authenticated", fmt)
        send(ws, {"type": "subscribe", "shipment_id": t["shipment"]["id"]}, fmt)
        receive(ws, "subscribed", fmt)

    def publish_batch(offset):
        ws = connect(t, t["credential"]["credential"], "device")
        receive(ws, "authenticated")
        samples = []
        try:
            for index in range(12):
                started = perf_counter()
                send(
                    ws,
                    {"type": "position.publish", "position": point(t, offset + index)},
                )
                receive(ws, "position.ack")
                samples.append((perf_counter() - started) * 1000)
        finally:
            ws.close()
        return samples

    with ThreadPoolExecutor(2) as pool:
        samples = sum(pool.map(publish_batch, (1, 13)), [])
    # Ambos consumidores aplazan lectura mientras los dos emisores persisten.
    # La muestra prueba retraso acotado; no representa saturación sostenida.
    for ws, fmt in zip(subscribers, ("json", "xml")):
        cursors = [receive(ws, "position.updated", fmt)["cursor"] for _ in range(24)]
        assert cursors == list(range(1, 25))
        ws.close()
    record_property("publishers", 2)
    record_property("delayed_subscribers", 2)
    record_property("points", 24)
    record_property("ack_mean_ms", round(mean(samples), 3))
    record_property("ack_p95_ms", round(sorted(samples)[22], 3))


def test_two_production_wss_processes_single_and_total_outage(p, tracking, tmp_path):
    import subprocess
    import sys
    import time
    from pathlib import Path
    import requests
    from scripts.local import free_port

    t = tracking
    processes, replicas = [], []
    original_server = p.servers["transporte"]
    original_port = original_server.server_port
    original_server.shutdown()
    original_server.server_close()
    t["server"].shutdown()
    t["server"].server_close()
    try:
        for index in range(2):
            port = free_port()
            config = dict(
                p.env.configs["transporte"],
                TESTING=True,
                SERVICE_URLS=p.urls,
                WORKER_REQUIRED=False,
                TRACKING_TLS_CERT=t["cert"],
                TRACKING_TLS_KEY=str(Path(t["cert"]).with_suffix(".key")),
            )
            path = tmp_path / f"replica-{index}.json"
            path.write_text(json.dumps(config))
            path.chmod(0o600)
            log = tmp_path / f"replica-{index}.log"
            with log.open("wb") as output:
                process = subprocess.Popen(
                    [
                        sys.executable,
                        str(Path(__file__).resolve().parents[1] / "run.py"),
                        "transporte",
                        "--config",
                        str(path),
                        "--port",
                        str(port),
                    ],
                    stdout=output,
                    stderr=subprocess.STDOUT,
                )
            processes.append(process)
            for _ in range(100):
                assert process.poll() is None, log.read_text()
                try:
                    response = requests.get(
                        f"https://localhost:{port}/health/live",
                        verify=t["cert"],
                        timeout=0.3,
                    )
                    if response.status_code == 200:
                        break
                except requests.RequestException:
                    time.sleep(0.1)
            else:
                pytest.fail("Réplica WSS no inició")
            replicas.append(dict(t, url=f"wss://localhost:{port}/ws/v1/tracking/"))
        first = connect(replicas[0], t["credential"]["credential"], "device")
        receive(first, "authenticated")
        send(first, {"type": "position.publish", "position": point(t)})
        assert receive(first, "position.ack")["cursor"] == 1
        processes[0].kill()
        processes[0].wait(timeout=10)
        with pytest.raises((OSError, websocket.WebSocketException)):
            first.recv()
        first.close()
        subscriber = connect(replicas[1], p.tokens["coordinator1"], fmt="xml")
        receive(subscriber, "authenticated", "xml")
        send(
            subscriber,
            {"type": "subscribe", "shipment_id": t["shipment"]["id"], "cursor": 0},
            "xml",
        )
        receive(subscriber, "subscribed", "xml")
        assert receive(subscriber, "position.updated", "xml")["position"]["cursor"] == 1
        processes[1].kill()
        processes[1].wait(timeout=10)
        with pytest.raises((OSError, websocket.WebSocketException)):
            subscriber.recv()
        subscriber.close()
        with pytest.raises(requests.RequestException):
            requests.get(p.urls["transporte"] + "/health/live", timeout=1)
        for replica in replicas:
            with pytest.raises((OSError, websocket.WebSocketException)):
                connect(replica, p.tokens["coordinator1"])
        # Caída total de listeners WSS no detiene negocio ni borra historial.
        assert (
            p.request(
                "inventario", "GET", "/api/v1/resources", user="operator1"
            ).status_code
            == 200
        )

    finally:
        for process in processes:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=10)

        # Reabre exclusivamente la instancia temporal propia, sobre el mismo almacén.
        from .conftest import QuietHandler

        server = make_server(
            "127.0.0.1",
            original_port,
            p.apps["transporte"],
            threaded=True,
            request_handler=QuietHandler,
        )
        p.servers["transporte"] = server
        threading.Thread(target=server.serve_forever, daemon=True).start()
    assert (
        p.ok(
            "transporte",
            "GET",
            f"/api/v1/shipments/{t['shipment']['id']}/tracking/snapshot?cursor=0",
            user="coordinator1",
        )["head"]
        == 1
    )
