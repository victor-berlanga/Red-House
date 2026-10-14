from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest

from .helpers import (
    evaluation,
    iso,
    move,
    plan,
    recipient_request,
    reservation,
    resource,
)


def test_donor_campaign_appointment_review_and_alert(p):
    donor = p.ok(
        "donantes",
        "POST",
        "/api/v1/donors",
        user="donor1",
        data={
            "folio": "DONOR-" + uuid4().hex[:8],
            "display_name": "Donante ficticio",
            "blood_group": "O-",
            "consent": True,
        },
    )
    campaign = p.ok(
        "donantes",
        "POST",
        "/api/v1/campaigns",
        user="operator1",
        data={
            "title": "Campaña ficticia",
            "starts_at": iso(minutes=10),
            "ends_at": iso(days=1),
            "capacity": 1,
        },
    )
    appointment = p.ok(
        "donantes",
        "POST",
        "/api/v1/appointments",
        user="donor1",
        data={"donor_id": donor["id"], "campaign_id": campaign["id"]},
    )
    p.ok(
        "donantes",
        "POST",
        f"/api/v1/donors/{donor['id']}/reviews",
        user="medical1",
        data={
            "human_confirmation": True,
            "reason": "Evaluación médica ficticia documentada",
            "decision": "ELIGIBLE",
            "version": donor["version"],
        },
    )
    p.drain()
    alerts = p.ok("alertas", "GET", "/api/v1/alerts", user="donor1")
    assert any(
        a["message_code"] == "APPOINTMENT_BOOKED"
        and a["resource_id"] == appointment["id"]
        for a in alerts["items"]
    )
    p.ok(
        "donantes",
        "POST",
        f"/api/v1/appointments/{appointment['id']}/cancel",
        user="donor1",
    )


@pytest.mark.parametrize(
    "kind,component,group",
    [
        ("BLOOD", "RBC", "O-"),
        ("ORGAN", "KIDNEY", "A-"),
        ("ORGAN", "LIVER", "A+"),
        ("ORGAN", "HEART", "A+"),
    ],
)
def test_resource_to_receipt_custody_audit_and_notification(p, kind, component, group):
    unit = resource(p, kind, component, group)
    patient, req = recipient_request(p, kind, component)
    evaluated = evaluation(p, req, [unit])
    ranked = p.ok(
        "priorizacion_geografia",
        "POST",
        "/api/v1/rankings",
        data={"evaluation_id": evaluated["id"]},
    )
    assert ranked["algorithm_version"] == "LOGISTICS-1.0"
    reserved = reservation(p, evaluated, unit)
    assert reserved["status"] == "COMPLETED"
    shipment = plan(p, reserved["reservation"])
    assert not shipment["inventory_pending"]
    for state, user in [
        ("PREPARED", "operator1"),
        ("COLLECTED", "transport1"),
        ("IN_TRANSIT", "transport1"),
    ]:
        shipment = move(p, shipment, state, user)
    location = p.ok(
        "transporte",
        "POST",
        f"/api/v1/shipments/{shipment['id']}/telemetry",
        user="transport1",
        data={"latitude": 25.6, "longitude": -100.3, "captured_at": iso()},
    )
    assert location["shipment_id"] == shipment["id"]
    shipment = move(p, shipment, "DELIVERED", "transport1")
    shipment = move(p, shipment, "ACCEPTED", "operator2")
    p.drain()
    closed = p.ok("receptores", "GET", f"/api/v1/requests/{req['id']}")
    assert closed["status"] == "CLOSED"
    chain = p.ok(
        "custodia", "GET", f"/api/v1/chains/{shipment['id']}", user="transport1"
    )
    assert [e["sequence"] for e in chain["events"]] == list(range(1, 7))
    assert chain["events"][-1]["event"]["metadata"]["state"] == "ACCEPTED"
    assert all("occurred_at" in e["event"] for e in chain["events"])
    with p.owner("auditoria") as conn:
        assert conn.execute(
            "SELECT 1 FROM audit_events WHERE event->>'resource_id'=%s AND action='SHIPMENT_ACCEPTED'",
            (shipment["id"],),
        ).fetchone()
    documentary = p.ok(
        "auditoria", "GET", "/api/v1/documentary-events", user="auditor1"
    )
    assert documentary["total"] > 0


def test_cancellation_before_collection_releases_request(p):
    unit = resource(p)
    _, req = recipient_request(p)
    ev = evaluation(p, req, [unit])
    reserved = reservation(p, ev, unit)["reservation"]
    shipment = plan(p, reserved)
    cancelled = move(p, shipment, "CANCELLED", "coordinator1")
    assert cancelled["status"] == "CANCELLED"
    p.drain()
    req = p.ok("receptores", "GET", f"/api/v1/requests/{req['id']}")
    assert req["status"] == "OPEN"
    inventory = p.ok(
        "inventario", "GET", "/api/v1/resources?page_size=100", user="operator1"
    )
    assert (
        next(r for r in inventory["items"] if r["id"] == unit["id"])["status"]
        == "AVAILABLE"
    )


def test_two_requests_cannot_reserve_same_resource(p):
    unit = resource(p)
    requests = [recipient_request(p)[1] for _ in range(2)]
    evaluations = [evaluation(p, req, [unit]) for req in requests]

    def attempt(ev):
        return p.request(
            "inventario",
            "POST",
            "/api/v1/reservations",
            data={
                "evaluation_id": ev["id"],
                "resource_id": unit["id"],
                "human_confirmation": True,
                "reason": "Reserva concurrente ficticia autorizada",
            },
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(attempt, evaluations))
    assert sorted(r.status_code for r in results) == [202, 409]
    with p.owner("inventario") as conn:
        assert (
            conn.execute(
                "SELECT count(*) FROM reservations WHERE resource_id=%s AND status<>'CANCELLED'",
                (unit["id"],),
            ).fetchone()[0]
            == 1
        )


def test_two_units_cannot_overfill_one_unit_request(p):
    units = [resource(p) for _ in range(2)]
    _, req = recipient_request(p)
    ev = evaluation(p, req, units)

    def attempt(unit):
        return p.request(
            "inventario",
            "POST",
            "/api/v1/reservations",
            data={
                "evaluation_id": ev["id"],
                "resource_id": unit["id"],
                "human_confirmation": True,
                "reason": "Reserva concurrente ficticia autorizada",
            },
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(attempt, units))
    assert sorted(r.status_code for r in results) == [202, 409]
    with p.owner("receptores") as conn:
        assert (
            conn.execute(
                "SELECT count(*) FROM holds WHERE request_id=%s AND status<>'RELEASED'",
                (req["id"],),
            ).fetchone()[0]
            == 1
        )


def test_idempotent_reservation_does_not_duplicate(p):
    unit = resource(p)
    _, req = recipient_request(p)
    ev = evaluation(p, req, [unit])
    key = uuid4().hex
    first = reservation(p, ev, unit, key)
    second = reservation(p, ev, unit, key)
    assert first["operation_id"] == second["operation_id"]
    assert first["reservation"]["id"] == second["reservation"]["id"]
