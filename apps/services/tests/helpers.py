from datetime import datetime, timedelta, timezone
from uuid import uuid4


def iso(minutes=0, days=0):
    return (
        datetime.now(timezone.utc) + timedelta(minutes=minutes, days=days)
    ).isoformat()


def resource(p, kind="BLOOD", component="RBC-DEMO", group="O-", expires=None):
    row = p.ok(
        "inventario",
        "POST",
        "/api/v1/resources",
        user="operator1",
        data={
            "folio": "UNIT-" + uuid4().hex[:12],
            "kind": kind,
            "component": component,
            "blood_group": group,
            "expires_at": expires or iso(days=2),
        },
    )
    return p.ok(
        "inventario",
        "POST",
        f"/api/v1/resources/{row['id']}/release",
        user="medical1",
        data={
            "human_confirmation": True,
            "reason": "Liberación humana con datos ficticios",
            "version": row["version"],
        },
    )


def recipient_request(p, kind="BLOOD", component="RBC-DEMO", group="A+", quantity=1):
    recipient = p.ok(
        "receptores",
        "POST",
        "/api/v1/recipients",
        data={
            "folio": "PATIENT-" + uuid4().hex[:12],
            "display_name": "Paciente ficticio",
            "kind": kind,
            "blood_group": group,
            "organ_type": component if kind == "ORGAN" else None,
            "studies": "Estudios ficticios con revisión externa pendiente",
        },
    )
    request = p.ok(
        "receptores",
        "POST",
        "/api/v1/requests",
        data={
            "recipient_id": recipient["id"],
            "component": component,
            "quantity": quantity,
            "urgency": 3,
        },
    )
    return recipient, request


def route(p):
    origin, destination = p.env.state["tenants"]
    with p.owner("priorizacion_geografia") as conn:
        existing = conn.execute(
            "SELECT id FROM routes WHERE origin_id=%s AND destination_id=%s",
            (origin, destination),
        ).fetchone()
    if existing:
        return str(existing[0])
    row = p.ok(
        "priorizacion_geografia",
        "POST",
        "/api/v1/routes",
        user="coordinator1",
        data={
            "origin_id": origin,
            "destination_id": destination,
            "distance_km": 10.0,
            "travel_minutes": 15,
            "source": "Estimación manual ficticia para pruebas",
        },
    )
    return row["id"]


def evaluation(p, request, resources):
    route(p)
    result = p.ok(
        "compatibilidad",
        "POST",
        "/api/v1/evaluations",
        data={"request_id": request["id"]},
    )
    for unit in resources:
        assert any(c["resource_id"] == unit["id"] for c in result["candidates"])
        p.ok(
            "compatibilidad",
            "POST",
            f"/api/v1/evaluations/{result['id']}/reviews",
            data={
                "resource_id": unit["id"],
                "human_confirmation": True,
                "decision": "FAVORABLE",
                "reason": "Dictamen médico favorable ficticio",
            },
        )
    return result


def reservation(p, evaluation, unit, key=None):
    return p.ok(
        "inventario",
        "POST",
        "/api/v1/reservations",
        key=key,
        data={
            "evaluation_id": evaluation["id"],
            "resource_id": unit["id"],
            "human_confirmation": True,
            "reason": "Asignación humana ficticia para integración",
        },
    )


def plan(p, allocation):
    return p.ok(
        "transporte",
        "POST",
        "/api/v1/shipments",
        user="coordinator1",
        data={
            "reservation_id": allocation["id"],
            "transport_user_id": p.env.state["accounts"]["transport1"]["id"],
            "departure_at": iso(minutes=1),
            "eta": iso(minutes=30),
            "human_confirmation": True,
            "reason": "Plan de traslado ficticio aprobado",
        },
    )


def move(p, shipment, state, user):
    return p.ok(
        "transporte",
        "POST",
        f"/api/v1/shipments/{shipment['id']}/transitions",
        user=user,
        data={
            "state": state,
            "version": shipment["version"],
            "human_confirmation": True,
            "reason": "Confirmación física ficticia del paso logístico",
        },
    )
