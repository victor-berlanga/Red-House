from datetime import datetime, timedelta, timezone
from uuid import uuid4


MOBILE_ROLES = ("DONOR", "TRANSPORT")


def client_for(username, role=None):
    """Aplicación con la que inicia sesión una cuenta de laboratorio.

    Distribución vigente: DONOR y TRANSPORT en móvil; el resto de perfiles en el
    portal web. Sin `role`, se deduce del nombre de las cuentas sembradas
    (admin1, donor2…). Las pruebas de acceso por aplicación envían la cabecera
    explícita y no usan este valor por omisión.
    """
    role = (role or username.rstrip("0123456789")).upper()
    return "mobile" if role in MOBILE_ROLES else "web"


def iso(minutes=0, days=0):
    return (
        datetime.now(timezone.utc) + timedelta(minutes=minutes, days=days)
    ).isoformat()


def resource(p, kind="BLOOD", component="RBC", group="O-", expires=None):
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


def recipient_request(p, kind="BLOOD", component="RBC", group="A+", quantity=1):
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
    custody = None
    if state in ("COLLECTED", "DELIVERED", "ACCEPTED"):
        with p.owner("inventario") as conn:
            unit = conn.execute(
                "SELECT resource_id FROM reservations WHERE id=%s",
                (shipment["reservation_id"],),
            ).fetchone()[0]
        counterpart = (
            "transport1"
            if state == "ACCEPTED"
            else "operator1"
            if state == "COLLECTED"
            else "operator2"
        )
        custody = {
            "scanned_resource_id": str(unit),
            "seal": "Sello sintético",
            "captured_at": iso(),
            "reported_handover_user_id": p.env.state["accounts"][counterpart]["id"],
            "electronic_acceptance": True,
        }
    return p.ok(
        "transporte",
        "POST",
        f"/api/v1/shipments/{shipment['id']}/transitions",
        user=user,
        data={
            "state": state,
            "custody": custody,
            "version": shipment["version"],
            "human_confirmation": True,
            "reason": "Confirmación física ficticia del paso logístico",
        },
    )


def telemetry_body(p, shipment):
    device = p.ok(
        "identidad_acceso",
        "POST",
        "/api/v1/devices",
        user="admin1",
        data={
            "id": str(uuid4()),
            "user_id": p.env.state["accounts"]["transport1"]["id"],
            "source": "SIMULATOR",
            "label": "Simulación de prueba",
            "expires_at": iso(days=1),
        },
    )
    p.ok(
        "transporte",
        "POST",
        f"/api/v1/shipments/{shipment['id']}/tracking/assignments",
        user="coordinator1",
        data={
            "device_id": device["id"],
            "starts_at": iso(minutes=-1),
            "ends_at": iso(minutes=60),
            "version": shipment["version"],
            "human_confirmation": True,
            "reason": "Asignación sintética de prueba",
        },
    )
    return {
        "schema_version": 1,
        "event_id": str(uuid4()),
        "shipment_id": shipment["id"],
        "device_id": device["id"],
        "source": "SIMULATOR",
        "sequence": 1,
        "captured_at": iso(),
        "fix_valid": True,
        "latitude": 25.6,
        "longitude": -100.3,
    }


def park_foreign_export_jobs(p):
    """process() atiende primero el PENDING más antiguo de la base compartida.

    Los trabajos que otras pruebas dejaron pendientes se apartan como
    RETRYABLE para que el caso procese el suyo sin depender del orden.
    """
    with p.owner("documentos") as conn:
        conn.execute(
            "UPDATE export_jobs SET status='RETRYABLE', last_error='test_isolation' "
            "WHERE status='PENDING'"
        )
