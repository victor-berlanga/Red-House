"""Cierre técnico del expediente: HTTP real y almacenes temporales del fixture."""

import json
from time import perf_counter
from uuid import uuid4

import psycopg
import pytest

from .helpers import (
    resource,
    recipient_request,
    evaluation,
    reservation,
    plan,
    move,
    iso,
)
from .test_final_quality import api
from .test_final_tracking import tracking as tracking
from .test_final_tracking import point, connect, send, receive
from ms_transporte.tracking_contracts import decode, Event

CONFIRM = {
    "human_confirmation": True,
    "reason": "Corrección sintética autorizada para integración",
}


def reject(p, service, path, body, user, fmt, status):
    from redhouse.examples import request_xml
    import requests

    headers = {
        "Accept": "application/" + fmt,
        "Content-Type": "application/" + fmt,
        "Authorization": "Bearer " + p.tokens[user],
        "Idempotency-Key": uuid4().hex,
    }
    response = requests.post(
        p.urls[service] + path,
        data=request_xml(body).encode() if fmt == "xml" else json.dumps(body),
        headers=headers,
        timeout=20,
    )
    assert response.status_code == status, response.text
    return response


@pytest.mark.parametrize("fmt", ["json", "xml"])
def test_destination_correction_invariants_and_history(p, fmt):
    unit = resource(p)
    path = f"/api/v1/resources/{unit['id']}/destination"
    body = dict(
        CONFIRM,
        version=unit["version"],
        destination="DISCARDED",
        reference="Acta sintética",
        occurred_at=iso(),
    )
    first = api(p, "inventario", path, body, fmt=fmt)
    for destination in ("TRANSPLANTED", "TRANSFUSED"):
        reject(
            p,
            "inventario",
            path,
            dict(
                body,
                version=unit["version"] + 1,
                supersedes=first["id"],
                destination=destination,
            ),
            "medical1",
            fmt,
            409,
        )
    with p.owner("inventario") as conn:
        assert (
            conn.execute(
                "SELECT count(*) FROM resource_destinations WHERE resource_id=%s",
                (unit["id"],),
            ).fetchone()[0]
            == 1
        )
        assert (
            conn.execute(
                "SELECT version FROM resources WHERE id=%s", (unit["id"],)
            ).fetchone()[0]
            == unit["version"] + 1
        )
    second = api(
        p,
        "inventario",
        path,
        dict(
            body,
            version=unit["version"] + 1,
            supersedes=first["id"],
            reference="Acta documental corregida",
        ),
        fmt=fmt,
    )
    assert second["version"] == 2 and second["supersedes"] == first["id"]
    assert second["author_id"] == p.env.state["accounts"]["medical1"]["id"]


def laboratory(p, unit, fmt):
    profile = api(
        p,
        "compatibilidad",
        "/api/v1/laboratory/profiles",
        dict(
            name="Perfil sintético corregible",
            kind="BLOOD",
            component="RBC",
            version=1,
            required_tests=["ABO"],
            source="Oráculo de integración sintético",
            synthetic=True,
            effective_at=iso(),
        ),
        fmt=fmt,
    )
    api(
        p,
        "inventario",
        f"/api/v1/resources/{unit['id']}/controls",
        dict(CONFIRM, version=unit["version"], lab_profile_id=profile["id"]),
        fmt=fmt,
    )
    sample = api(
        p,
        "compatibilidad",
        "/api/v1/laboratory/samples",
        dict(
            resource_id=unit["id"],
            profile_id=profile["id"],
            identifier="SYN-" + uuid4().hex,
            collected_at=iso(minutes=-5),
        ),
        user="operator1",
        fmt=fmt,
    )
    api(
        p,
        "compatibilidad",
        f"/api/v1/laboratory/samples/{sample['id']}/receive",
        dict(CONFIRM, version=1, decision="RECEIVED"),
        user="operator1",
        fmt=fmt,
    )
    body = dict(
        sample_id=sample["id"],
        test_code="ABO",
        value="O",
        method="Método sintético",
        laboratory="Laboratorio sintético",
        reference="Referencia sintética",
        measured_at=iso(minutes=-1),
    )
    result = api(
        p,
        "compatibilidad",
        "/api/v1/laboratory/results",
        body,
        user="operator1",
        fmt=fmt,
    )
    api(
        p,
        "compatibilidad",
        f"/api/v1/laboratory/results/{result['id']}/review",
        dict(CONFIRM, version=1, decision="AUTHORIZED"),
        fmt=fmt,
    )
    return profile, body, result


@pytest.mark.parametrize("fmt", ["json", "xml"])
@pytest.mark.parametrize("change", ["result", "profile"])
def test_laboratory_correction_invalidates_review_and_runtime_history(p, fmt, change):
    unit = p.ok(
        "inventario",
        "POST",
        "/api/v1/resources",
        user="operator1",
        data={
            "folio": "LAB-" + uuid4().hex[:12],
            "kind": "BLOOD",
            "component": "RBC",
            "blood_group": "O-",
            "expires_at": iso(days=2),
        },
    )
    profile, body, original = laboratory(p, unit, fmt)
    unit = api(
        p,
        "inventario",
        f"/api/v1/resources/{unit['id']}/release",
        dict(CONFIRM, version=2),
        fmt=fmt,
    )
    _, demand = recipient_request(p)
    old = evaluation(p, demand, [unit])
    if change == "profile":
        laboratory(p, unit, fmt)
        unit = api(
            p,
            "inventario",
            f"/api/v1/resources/{unit['id']}/release",
            dict(CONFIRM, version=unit["version"] + 1),
            fmt=fmt,
        )
    else:
        correction = api(
            p,
            "compatibilidad",
            "/api/v1/laboratory/results",
            dict(body, value="O corregido", supersedes=original["id"]),
            user="operator1",
            fmt=fmt,
        )
        api(
            p,
            "compatibilidad",
            f"/api/v1/laboratory/results/{correction['id']}/review",
            dict(CONFIRM, version=correction["version"], decision="AUTHORIZED"),
            fmt=fmt,
        )
    reject(
        p,
        "inventario",
        "/api/v1/reservations",
        dict(CONFIRM, evaluation_id=old["id"], resource_id=unit["id"]),
        "medical2",
        fmt,
        409,
    )
    with p.owner("inventario") as conn:
        assert (
            conn.execute(
                "SELECT count(*) FROM reservations WHERE resource_id=%s", (unit["id"],)
            ).fetchone()[0]
            == 0
        )
    with psycopg.connect(p.apps["compatibilidad"].config["DATABASE_URL"]) as conn:
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            conn.execute(
                "UPDATE lab_results SET value='sobrescrito' WHERE id=%s",
                (original["id"],),
            )
    current = p.ok(
        "inventario", "GET", f"/api/v1/resources/{unit['id']}", user="medical1"
    )
    fresh = evaluation(p, demand, [current])
    assert reservation(p, fresh, current)["reservation"]["resource_id"] == unit["id"]
    with p.owner("compatibilidad") as conn:
        assert conn.execute(
            "SELECT value,status FROM lab_results WHERE id=%s", (original["id"],)
        ).fetchone() == ("O", "AUTHORIZED")


@pytest.mark.parametrize("fmt", ["json", "xml"])
@pytest.mark.parametrize("target", ["COLLECTED", "DELIVERED", "ACCEPTED"])
def test_handover_fields_required_without_state_change(p, fmt, target):
    unit = resource(p)
    _, demand = recipient_request(p)
    shipment = plan(
        p, reservation(p, evaluation(p, demand, [unit]), unit)["reservation"]
    )
    shipment = move(p, shipment, "PREPARED", "operator1")
    for state, user in (
        ("COLLECTED", "transport1"),
        ("IN_TRANSIT", "transport1"),
        ("DELIVERED", "transport1"),
    ):
        if state == target:
            break
        shipment = move(p, shipment, state, user)
    actor = "operator2" if target == "ACCEPTED" else "transport1"
    counterpart = (
        "transport1"
        if target == "ACCEPTED"
        else "operator2"
        if target == "DELIVERED"
        else "operator1"
    )
    before = p.ok(
        "transporte", "GET", f"/api/v1/shipments/{shipment['id']}", user="coordinator1"
    )
    path = f"/api/v1/shipments/{shipment['id']}/transitions"
    custody = dict(
        scanned_resource_id=unit["id"],
        seal="Sello sintético",
        captured_at=iso(),
        reported_handover_user_id=p.env.state["accounts"][counterpart]["id"],
        electronic_acceptance=True,
    )
    body = dict(CONFIRM, state=target, version=shipment["version"], custody=custody)
    for field in ("custody", *custody):
        invalid = dict(body)
        if field == "custody":
            invalid.pop(field)
        else:
            invalid["custody"] = {k: v for k, v in custody.items() if k != field}
        reject(p, "transporte", path, invalid, actor, fmt, 422)
    stored = p.ok(
        "transporte", "GET", f"/api/v1/shipments/{shipment['id']}", user="coordinator1"
    )
    assert (
        stored["status"] == before["status"] and stored["version"] == before["version"]
    )
    assert stored["transitions"] == before["transitions"]
    moved = api(p, "transporte", path, body, user=actor, fmt=fmt)
    assert moved["status"] == target
    p.drain()
    chain = p.ok(
        "custodia", "GET", f"/api/v1/chains/{shipment['id']}", user="coordinator1"
    )
    assert chain["events"]


@pytest.mark.parametrize("fmt", ["json", "xml"])
def test_role_change_revokes_tokens_and_is_idempotent(p, fmt):
    tenant = p.env.state["tenants"][0]
    username = "role_" + uuid4().hex[:12]
    user = p.ok(
        "identidad_acceso",
        "POST",
        "/api/v1/users",
        user="admin1",
        data=dict(
            username=username,
            password=p.env.state["password"],
            tenant_id=tenant,
            role="OPERATOR",
        ),
    )
    token = p.ok(
        "identidad_acceso",
        "POST",
        "/api/v1/auth/login",
        user=None,
        data=dict(username=username, password=p.env.state["password"]),
    )["access_token"]
    path = f"/api/v1/users/{user['id']}/role"
    body = dict(CONFIRM, role="DONOR", version=1)
    reject(p, "identidad_acceso", path, body, "admin2", fmt, 403)
    reject(p, "identidad_acceso", path, dict(body, role="ADMIN"), "admin1", fmt, 403)
    changed = api(p, "identidad_acceso", path, body, user="admin1", fmt=fmt)
    assert changed["role"] == "DONOR" and changed["version"] == 2
    assert (
        p.request(
            "inventario",
            "GET",
            "/api/v1/resources",
            user=None,
            headers={"Authorization": "Bearer " + token},
        ).status_code
        == 401
    )
    reject(p, "identidad_acceso", path, body, "admin1", fmt, 412)
    key = uuid4().hex
    body = dict(body, role="OPERATOR", version=2)
    a = p.ok("identidad_acceso", "POST", path, data=body, user="admin1", key=key)
    assert (
        p.ok("identidad_acceso", "POST", path, data=body, user="admin1", key=key) == a
    )


@pytest.mark.parametrize("fmt", ["json", "xml"])
def test_normalized_http_wss_and_durable_history(p, tracking, fmt, monkeypatch):
    t = tracking
    path = f"/api/v1/shipments/{t['shipment']['id']}/telemetry"
    monkeypatch.setitem(p.apps["transporte"].config, "TRACKING_REPLAY_WINDOW", 2)
    positions = [point(t, n) for n in range(1, 7)]
    for position in positions:
        api(p, "transporte", path, position, user="transport1", fmt=fmt)
    publisher = connect(t, t["credential"]["credential"], "device")
    receive(publisher, "authenticated")
    send(publisher, {"type": "position.publish", "position": positions[0]})
    assert receive(publisher, "position.ack")["cursor"] == 1
    publisher.close()
    prefix = f"/api/v1/shipments/{t['shipment']['id']}/tracking"
    assert (
        p.request(
            "transporte", "GET", prefix + "/snapshot?cursor=0", user="coordinator1"
        ).status_code
        == 409
    )
    cursor = 0
    recovered = []
    while cursor < 6:
        result = api(
            p,
            "transporte",
            prefix + f"/history?cursor={cursor}&through=6&limit=2",
            user="coordinator1",
            fmt=fmt,
            method="GET",
        )
        recovered.extend(result["items"])
        cursor = result["cursor"]
    assert [r["event_id"] for r in recovered] == [r["event_id"] for r in positions]
    assert all(r["received_at"] and r["captured_at"] for r in recovered)
    assert (
        p.request("transporte", "GET", prefix + "/history", user="medical2").status_code
        == 200
    )  # destination is authorized
    assert (
        p.request("transporte", "GET", prefix + "/history", user="donor1").status_code
        == 403
    )
    subscriber = connect(t, p.tokens["coordinator1"], fmt=fmt)
    receive(subscriber, "authenticated", fmt)
    send(
        subscriber,
        {"type": "subscribe", "shipment_id": t["shipment"]["id"], "cursor": cursor},
        fmt,
    )
    assert receive(subscriber, "subscribed", fmt)["cursor"] == 6
    api(p, "transporte", path, point(t, 7), user="transport1", fmt=fmt)
    assert receive(subscriber, "position.updated", fmt)["cursor"] == 7
    subscriber.close()
    p.ok(
        "transporte",
        "POST",
        f"/api/v1/tracking/assignments/{t['assignment']['id']}/revoke",
        user="coordinator1",
        data=dict(CONFIRM, version=1),
    )
    reject(p, "transporte", path, point(t, 8), "transport1", fmt, 403)
    with p.owner("transporte") as conn:
        assert (
            conn.execute(
                "SELECT count(*) FROM tracking_points WHERE shipment_id=%s",
                (t["shipment"]["id"],),
            ).fetchone()[0]
            == 7
        )


@pytest.mark.parametrize("fmt", ["json", "xml"])
@pytest.mark.parametrize(
    "change", ["assignment", "reassigned", "device", "finalized", "expired", "redis"]
)
def test_replay_reauthorizes_after_each_send(p, tracking, fmt, change, monkeypatch):
    import threading
    from ms_transporte.tracking_socket import BoundedServer

    t = tracking
    for n in range(1, 5):
        p.ok(
            "transporte",
            "POST",
            f"/api/v1/shipments/{t['shipment']['id']}/telemetry",
            user="transport1",
            data=point(t, n),
        )
    sent = threading.Event()
    proceed = threading.Event()
    original = BoundedServer.send

    def delayed(socket, value):
        original(socket, value)
        if decode(value, Event, fmt)["type"] == "subscribed":
            sent.set()
            assert proceed.wait(15)

    monkeypatch.setattr(BoundedServer, "send", delayed)
    credential = p.tokens["coordinator1"]
    if change == "reassigned":
        replacement = p.ok(
            "identidad_acceso",
            "POST",
            "/api/v1/users",
            user="admin1",
            data={
                "username": "reassigned_" + uuid4().hex[:12],
                "password": p.env.state["password"],
                "tenant_id": p.env.state["tenants"][0],
                "role": "TRANSPORT",
            },
        )
        credential = p.tokens["transport1"]
    if change == "expired":
        import jwt, time

        identity = p.apps["identidad_acceso"].config
        claims = jwt.decode(credential, options={"verify_signature": False})
        claims["exp"] = int(time.time()) + 4
        credential = jwt.encode(claims, identity["JWT_PRIVATE_KEY"], algorithm="RS256")
    subscriber = connect(t, credential, fmt=fmt)
    receive(subscriber, "authenticated", fmt)
    send(
        subscriber,
        {"type": "subscribe", "shipment_id": t["shipment"]["id"], "cursor": 0},
        fmt,
    )
    try:
        assert sent.wait(10)
        if change == "assignment":
            p.ok(
                "transporte",
                "POST",
                f"/api/v1/tracking/assignments/{t['assignment']['id']}/revoke",
                user="coordinator1",
                data=dict(CONFIRM, version=1),
            )
        elif change == "reassigned":
            # Inyección controlada del cambio de autoridad: aún no existe comando público
            # para reasignar responsable. La lectura WSS debe consultar la fila vigente.
            with p.owner("transporte") as conn:
                conn.execute(
                    "UPDATE shipments SET transport_user_id=%s,version=version+1 WHERE id=%s",
                    (replacement["id"], t["shipment"]["id"]),
                )
        elif change == "device":
            p.ok(
                "identidad_acceso",
                "POST",
                f"/api/v1/devices/{t['device']['id']}/revoke",
                user="admin1",
                data=dict(CONFIRM, version=2),
            )
        elif change == "expired":
            time.sleep(max(0, claims["exp"] - time.time() + 0.2))
        elif change == "redis":
            monkeypatch.setitem(
                p.apps["transporte"].config, "REDIS_URL", "redis://127.0.0.1:1/0"
            )
        else:
            shipment = t["shipment"]
            for state, user in [
                ("COLLECTED", "transport1"),
                ("IN_TRANSIT", "transport1"),
                ("DELIVERED", "transport1"),
                ("ACCEPTED", "operator2"),
            ]:
                shipment = move(p, shipment, state, user)
        proceed.set()
        receive(subscriber, "subscribed", fmt)
        frame = decode(subscriber.recv(), Event, fmt)
        assert frame["type"] == "error" and frame["code"] == {
            "expired": "unauthorized",
            "redis": "redis_unavailable",
            "reassigned": "forbidden",
        }.get(change, "tracking_closed")
    finally:
        proceed.set()
        subscriber.close()


@pytest.mark.parametrize("fmt", ["json", "xml"])
def test_extension_search_time_sort_and_tenant(p, fmt):
    label = "Equipo " + uuid4().hex
    item = api(
        p,
        "inventario",
        "/api/v1/cold/equipment",
        dict(label=label, location="Sede de integración"),
        user="operator1",
        fmt=fmt,
    )
    from urllib.parse import urlencode

    query = urlencode(
        dict(
            q=label,
            sort="ID_ASC",
            from_at=iso(minutes=-5),
            until_at=iso(minutes=5),
            page_size=1,
        )
    )
    path = "/api/v1/cold/equipment?" + query
    result = api(p, "inventario", path, user="operator1", fmt=fmt, method="GET")
    assert result["total"] == 1 and result["items"][0]["id"] == item["id"]
    assert (
        api(p, "inventario", path, user="operator2", fmt=fmt, method="GET")["total"]
        == 0
    )
    for invalid in (
        "sort=DROP",
        "from_at=2026-10-01",
        "from_at=" + iso() + "&until_at=2000-01-01T00:00:00Z",
        "page_size=101",
        "q=a&q=b",
        "unknown=x",
    ):
        assert p.request(
            "inventario", "GET", "/api/v1/cold/equipment?" + invalid, user="operator1"
        ).status_code in (400, 422)
    p.drain()
    events = p.ok(
        "auditoria",
        "GET",
        "/api/v1/events?action=COLD_EQUIPMENT_CREATED&resource=" + item["id"],
        user="auditor1",
    )
    assert events["total"] == 1 and events["items"][0]["category"] == "BUSINESS"


def test_report_window_applies_before_limit(p):
    unit = resource(p)
    with p.owner("inventario") as conn:
        conn.execute(
            "INSERT INTO resources(id,tenant_id,current_institution_id,region_id,folio,kind,component,blood_group,expires_at,created_at) SELECT gen_random_uuid(),tenant_id,current_institution_id,region_id,'BULK-'||substr(gen_random_uuid()::text,1,12),kind,component,blood_group,now()+interval '400 days',now()-interval '400 days' FROM resources CROSS JOIN generate_series(1,1001) WHERE id=%s",
            (unit["id"],),
        )
    start, end = iso(minutes=-5), iso(minutes=5)
    job = p.ok(
        "transporte",
        "POST",
        "/api/v1/export-jobs",
        user="operator1",
        data=dict(report="INVENTORY", format="CSV", from_at=start, until_at=end),
    )
    assert job["status"] == "PENDING"
    with p.owner("documentos") as conn:
        rows = conn.execute(
            "SELECT rows FROM export_jobs WHERE id=%s", (job["id"],)
        ).fetchone()[0]
        assert any(r["id"] == unit["id"] for r in rows)
        assert all(not r["folio"].startswith("BULK-") for r in rows)


def test_empirical_forecast_positive_independent_oracle(p, record_property):
    from datetime import datetime, timedelta, timezone
    from werkzeug.security import generate_password_hash

    # Institución nueva, una unidad por uso: el oráculo parte exclusivamente
    # de estos hechos sintéticos, nunca de conteos devueltos por el algoritmo.
    tenant, author, username = str(uuid4()), str(uuid4()), "oracle_" + uuid4().hex[:12]
    with p.owner("identidad_acceso") as conn:
        conn.execute(
            "INSERT INTO institutions(id,name,region_id) VALUES(%s,'Institución sintética del oráculo',%s)",
            (tenant, p.env.state["region_id"]),
        )
        conn.execute(
            "INSERT INTO users(id,tenant_id,username,password_hash,role) VALUES(%s,%s,%s,%s,'MEDICAL')",
            (author, tenant, username, generate_password_hash(p.env.state["password"])),
        )
    p.tokens[username] = p.ok(
        "identidad_acceso",
        "POST",
        "/api/v1/auth/login",
        user=None,
        data={"username": username, "password": p.env.state["password"]},
    )["access_token"]
    now = datetime.now(timezone.utc)
    with p.owner("inventario") as conn:
        for n in range(30):
            identifier = str(uuid4())
            # 14 usos en siete días, un descarte, un uso fuera de ventana,
            # diez disponibles próximos a caducar, dos lejanos y dos en cuarentena.
            state = "WITHDRAWN" if n < 16 else "AVAILABLE" if n < 28 else "QUARANTINE"
            expiry = now + timedelta(days=20 if n in (26, 27) else 2)
            conn.execute(
                "INSERT INTO resources(id,tenant_id,current_institution_id,region_id,folio,kind,component,blood_group,expires_at,status) VALUES(%s,%s,%s,%s,%s,'BLOOD','RBC','O-',%s,%s)",
                (
                    identifier,
                    tenant,
                    tenant,
                    p.env.state["region_id"],
                    "ORACLE-" + str(n),
                    expiry,
                    state,
                ),
            )
            if n < 16:
                occurred = now - timedelta(
                    days=n // 2 + 1 if n < 14 else 1 if n == 14 else 40
                )
                conn.execute(
                    "INSERT INTO resource_destinations(id,resource_id,tenant_id,destination,reference,occurred_at,reason,author_id,version) VALUES(%s,%s,%s,%s,'SYNTHETIC-ORACLE',%s,'Historia sintética de prueba',%s,1)",
                    (
                        str(uuid4()),
                        identifier,
                        tenant,
                        "DISCARDED" if n == 14 else "TRANSFUSED",
                        occurred,
                        author,
                    ),
                )
    started = perf_counter()
    result = p.ok(
        "inventario", "GET", "/api/v1/analytics/inventory?days=30", user=username
    )
    elapsed = (perf_counter() - started) * 1000
    record_property("forecast_elapsed_ms", round(elapsed, 3))
    assert elapsed < 5000
    (product,) = result["products"]
    assert product["observed_days"] == 7 and product["observed_use"] == 14
    assert product["available"] == 12 and product["expiring_in_seven_days"] == 10
    # 14 usos / 30 días * 7 = 3.266..., cuatro unidades previstas: excedente seis.
    assert product["estimated_surplus"] == 6
    assert result["used"] == 14 and result["discarded"] == 1
    assert result["limitation"] and result["method"] == "EMPIRICAL-USE-1"
    for days in (6, 366):
        assert (
            p.request(
                "inventario",
                "GET",
                f"/api/v1/analytics/inventory?days={days}",
                user=username,
            ).status_code
            == 422
        )


@pytest.mark.parametrize("fmt", ["json", "xml"])
def test_received_quarantine_new_use_and_documentary_correction(p, fmt):
    unit = resource(p)
    _, demand = recipient_request(p)
    shipment = plan(
        p, reservation(p, evaluation(p, demand, [unit]), unit)["reservation"]
    )
    for state, user in [
        ("PREPARED", "operator1"),
        ("COLLECTED", "transport1"),
        ("IN_TRANSIT", "transport1"),
        ("DELIVERED", "transport1"),
        ("ACCEPTED", "operator2"),
    ]:
        shipment = move(p, shipment, state, user)
    p.drain()
    unit = p.ok("inventario", "GET", f"/api/v1/resources/{unit['id']}", user="medical2")
    path = f"/api/v1/resources/{unit['id']}/destination"
    body = dict(
        CONFIRM,
        version=unit["version"],
        destination="TRANSFUSED",
        occurred_at=iso(minutes=-1),
        reference="Constancia sintética",
    )
    with p.owner("inventario") as conn:
        conn.execute(
            "UPDATE resources SET status='QUARANTINE' WHERE id=%s", (unit["id"],)
        )
    reject(p, "inventario", path, body, "medical2", fmt, 409)
    with p.owner("inventario") as conn:
        assert (
            conn.execute(
                "SELECT count(*) FROM resource_destinations WHERE resource_id=%s",
                (unit["id"],),
            ).fetchone()[0]
            == 0
        )
        conn.execute(
            "UPDATE resources SET status='RECEIVED' WHERE id=%s", (unit["id"],)
        )
    first = api(p, "inventario", path, body, "medical2", fmt)
    with p.owner("inventario") as conn:
        conn.execute(
            "INSERT INTO resource_controls(id,blocked) VALUES(%s,true) ON CONFLICT(id) DO UPDATE SET blocked=true",
            (unit["id"],),
        )
        conn.execute(
            "UPDATE resources SET expires_at=now()-interval '1 minute' WHERE id=%s",
            (unit["id"],),
        )
    # Hecho clínico inalterado: documentar mejor su referencia no afirma un nuevo uso.
    corrected = api(
        p,
        "inventario",
        path,
        dict(
            body,
            version=unit["version"] + 1,
            supersedes=first["id"],
            reference="Referencia documental rectificada",
        ),
        "medical2",
        fmt,
    )
    assert (
        corrected["version"] == 2
        and corrected["author_id"] == p.env.state["accounts"]["medical2"]["id"]
    )
    reject(
        p,
        "inventario",
        path,
        dict(
            body,
            version=unit["version"] + 2,
            supersedes=corrected["id"],
            occurred_at=iso(),
        ),
        "medical2",
        fmt,
        409,
    )
    with p.owner("inventario") as conn:
        assert (
            conn.execute(
                "SELECT count(*) FROM resource_destinations WHERE resource_id=%s",
                (unit["id"],),
            ).fetchone()[0]
            == 2
        )


def test_new_event_classification_visibility_and_export(p):
    import ast
    from pathlib import Path
    from redhouse.audit_catalog import describe

    events = set()
    for path in Path(__file__).resolve().parents[1].glob("ms_*/*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "emit"
                and len(node.args) > 1
                and isinstance(node.args[1], ast.Constant)
            ):
                events.add(node.args[1].value)
    events.update(
        {
            "DONOR_CONSENT_RECORDED",
            "DONOR_CONSENT_WITHDRAWN",
            "APPOINTMENT_CONFIRM",
            "APPOINTMENT_RESCHEDULE",
            "APPOINTMENT_ATTEND",
            "APPOINTMENT_CANCEL",
            "LAB_SAMPLE_RECEIVED",
            "LAB_SAMPLE_REJECTED",
            "RESOURCE_COLD_QUARANTINE",
            "RESOURCE_COLD_GAP",
            "RESOURCE_EXPIRED",
        }
    )
    assert all(describe(action)[2] != "UNKNOWN" for action in events)
    # Ejecutar ambas operaciones antes de comprobar sus eventos reales; no fabricar emisión.
    equipment = api(
        p,
        "inventario",
        "/api/v1/cold/equipment",
        {"label": "Equipo auditable", "location": "Sede sintética"},
        "operator1",
    )
    subscription = api(
        p,
        "alertas",
        "/api/v1/alert-subscriptions",
        {"channel": "PUSH", "push_destination": "synthetic-device-destination"},
        "operator1",
    )
    api(
        p,
        "alertas",
        f"/api/v1/alert-subscriptions/{subscription['id']}/revoke",
        CONFIRM,
        "operator1",
    )
    unit = p.ok(
        "inventario",
        "POST",
        "/api/v1/resources",
        user="operator1",
        data={
            "folio": "AUDIT-" + uuid4().hex[:12],
            "kind": "BLOOD",
            "component": "RBC",
            "blood_group": "O-",
            "expires_at": iso(days=1),
        },
    )
    profile, body, result = laboratory(p, unit, "json")
    rejected_sample = api(
        p,
        "compatibilidad",
        "/api/v1/laboratory/samples",
        {
            "resource_id": unit["id"],
            "profile_id": profile["id"],
            "identifier": "REJECT-" + uuid4().hex,
            "collected_at": iso(minutes=-1),
        },
        "operator1",
    )
    api(
        p,
        "compatibilidad",
        f"/api/v1/laboratory/samples/{rejected_sample['id']}/receive",
        dict(CONFIRM, version=1, decision="REJECTED"),
        "operator1",
    )
    p.drain()
    for action, identifier in [
        ("LAB_SAMPLE_RECEIVED", body["sample_id"]),
        ("LAB_SAMPLE_REJECTED", rejected_sample["id"]),
        ("COLD_EQUIPMENT_CREATED", equipment["id"]),
        ("ALERT_SUBSCRIPTION_CREATED", subscription["id"]),
        ("ALERT_SUBSCRIPTION_REVOKED", subscription["id"]),
    ]:
        for suffix in ("", "/export"):
            rows = p.ok(
                "auditoria",
                "GET",
                f"/api/v1/events{suffix}?action={action}&resource={identifier}",
                user="auditor1",
            )
            assert rows["total"] >= 1, (action, rows)
            assert all(
                item["action"] == action and item["result_label"] != "No registrado"
                for item in rows["items"]
            )
        assert (
            p.request(
                "auditoria", "GET", f"/api/v1/events?action={action}", user="operator1"
            ).status_code
            == 403
        )
