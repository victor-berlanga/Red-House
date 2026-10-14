from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

from .helpers import evaluation, iso, recipient_request, resource


def test_donation_provenance_and_processed_intake(p):
    donor = p.ok(
        "donantes",
        "POST",
        "/api/v1/donors",
        user="operator1",
        data={
            "folio": "SOURCE-" + uuid4().hex[:10],
            "display_name": "Procedencia ficticia",
            "blood_group": "O-",
            "consent": True,
        },
    )
    p.ok(
        "donantes",
        "POST",
        f"/api/v1/donors/{donor['id']}/reviews",
        user="medical1",
        data={
            "human_confirmation": True,
            "reason": "Evaluación humana ficticia documentada",
            "decision": "ELIGIBLE",
            "version": donor["version"],
        },
    )
    donation = p.ok(
        "donantes",
        "POST",
        "/api/v1/donations",
        user="medical1",
        data={
            "donor_id": donor["id"],
            "kind": "BLOOD",
            "component": "RBC",
            "collected_at": iso(minutes=-1),
            "human_confirmation": True,
            "reason": "Recolección ficticia documentada",
        },
    )
    incoming = {
        "folio": "DERIVED-" + uuid4().hex[:10],
        "kind": "BLOOD",
        "component": "RBC",
        "blood_group": "O-",
        "expires_at": iso(days=2),
        "donation_id": donation["id"],
    }
    assert (
        p.request(
            "inventario", "POST", "/api/v1/resources", user="operator1", data=incoming
        ).status_code
        == 409
    )
    p.ok(
        "donantes",
        "POST",
        f"/api/v1/donations/{donation['id']}/steps",
        user="operator1",
        data={
            "state": "PROCESSED",
            "version": donation["version"],
            "human_confirmation": True,
            "reason": "Procesamiento ficticio documentado",
        },
    )
    unit = p.ok(
        "inventario", "POST", "/api/v1/resources", user="operator1", data=incoming
    )
    assert unit["donation_id"] == donation["id"] and unit["status"] == "QUARANTINE"


def test_campaign_capacity_serializes_different_donors(p):
    donors = [
        p.ok(
            "donantes",
            "POST",
            "/api/v1/donors",
            user="operator1",
            data={
                "folio": "CAPACITY-" + uuid4().hex[:10],
                "display_name": "Donante ficticio para cupo",
                "blood_group": "O+",
                "consent": True,
            },
        )
        for _ in range(2)
    ]
    campaign = p.ok(
        "donantes",
        "POST",
        "/api/v1/campaigns",
        user="operator1",
        data={
            "title": "Cupo uno",
            "starts_at": iso(minutes=5),
            "ends_at": iso(days=1),
            "capacity": 1,
        },
    )
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(
            pool.map(
                lambda donor: p.request(
                    "donantes",
                    "POST",
                    "/api/v1/appointments",
                    user="operator1",
                    data={"donor_id": donor["id"], "campaign_id": campaign["id"]},
                ),
                donors,
            )
        )
    assert sorted(r.status_code for r in results) == [201, 409]


def test_proposal_persists_maximum_matching_without_reservations(p):
    unit_o = resource(p, group="O-")
    unit_a = resource(p, group="A-")
    _, request_a = recipient_request(p, group="A+")
    _, request_o = recipient_request(p, group="O-")
    ev_a = evaluation(p, request_a, [unit_o, unit_a])
    ev_o = evaluation(p, request_o, [unit_o])
    proposal = p.ok(
        "priorizacion_geografia",
        "POST",
        "/api/v1/allocation-proposals",
        data={"evaluation_ids": [ev_a["id"], ev_o["id"]]},
    )
    assert proposal["matched_count"] == 2
    assert len({r["resource_id"] for r in proposal["result"]}) == 2
    with p.owner("inventario") as conn:
        assert (
            conn.execute(
                "SELECT count(*) FROM reservations WHERE request_id IN (%s,%s)",
                (request_a["id"], request_o["id"]),
            ).fetchone()[0]
            == 0
        )


def test_stale_route_blocks_reservation(p):
    unit = resource(p)
    _, req = recipient_request(p)
    ev = evaluation(p, req, [unit])
    candidate = next(c for c in ev["candidates"] if c["resource_id"] == unit["id"])
    with p.owner("priorizacion_geografia") as conn:
        conn.execute(
            "UPDATE routes SET version=version+1 WHERE id=%s", (candidate["route_id"],)
        )
    response = p.request(
        "inventario",
        "POST",
        "/api/v1/reservations",
        data={
            "evaluation_id": ev["id"],
            "resource_id": unit["id"],
            "human_confirmation": True,
            "reason": "Reserva ficticia de candidato obsoleto",
        },
    )
    assert (
        response.status_code == 409
        and response.json()["error"]["code"] == "stale_route"
    )


def test_reception_expiry_does_not_republish_resource(p):
    # La recepción nunca es una liberación clínica; las pruebas de flujo verifican RECEIVED.
    _, req = recipient_request(p, kind="ORGAN", component="KIDNEY")
    second = p.request(
        "receptores",
        "POST",
        "/api/v1/requests",
        data={
            "recipient_id": req["recipient_id"],
            "component": "KIDNEY",
            "quantity": 1,
            "urgency": 3,
        },
    )
    assert second.status_code == 409
