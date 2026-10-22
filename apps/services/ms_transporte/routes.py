from datetime import datetime, timedelta, timezone
from typing import Annotated, Literal
from uuid import uuid4

from flask import g
from pydantic import Field

from redhouse.api import atomic, endpoint, listing
from redhouse.client import call
from redhouse.db import get, insert, transaction, update
from redhouse.errors import APIError
from redhouse.validation import invalid
from redhouse.decisions import record, history
from redhouse.events import emit, queue
from redhouse.models import Confirm, ID, Model, Reason, Text, utc_date


class ShipmentCreate(Confirm):
    reservation_id: ID
    transport_user_id: ID
    departure_at: Text
    eta: Text


class Evidence(Model):
    object_id: ID


class Transition(Confirm):
    state: Literal[
        "PREPARED",
        "COLLECTED",
        "IN_TRANSIT",
        "DELIVERED",
        "ACCEPTED",
        "INCIDENT",
        "CANCELLED",
    ]
    version: Annotated[int, Field(ge=1)]
    evidence: Evidence | None = None
    destination_location_id: ID | None = None


class Telemetry(Model):
    latitude: Annotated[float, Field(ge=-90, le=90)]
    longitude: Annotated[float, Field(ge=-180, le=180)]
    captured_at: Text


def shipment_access(row):
    actor = g.actor
    if str(row["region_id"]) != actor["region_id"]:
        raise APIError("forbidden", "Traslado fuera de la región.", 403)
    if actor["role"] == "TRANSPORT":
        if str(row["transport_user_id"]) != actor["id"]:
            raise APIError("forbidden", "Traslado de otro responsable.", 403)
    elif actor["role"] != "COORDINATOR" and actor["tenant_id"] not in (
        str(row["origin_id"]),
        str(row["destination_id"]),
    ):
        raise APIError("forbidden", "Traslado ajeno a la institución.", 403)


def logistics_event(
    conn, row, state, actor_id, evidence=None, destination_location_id=None
):
    sequence = row["sequence"] + 1
    event = emit(
        conn,
        "SHIPMENT_" + state,
        row["id"],
        row["origin_id"],
        targets=("auditoria", "custodia", "inventario", "alertas"),
        metadata={
            "reservation_id": str(row["reservation_id"]),
            "sequence": sequence,
            "state": state,
            "origin_id": str(row["origin_id"]),
            "destination_id": str(row["destination_id"]),
            "transport_user_id": str(row["transport_user_id"]),
            "evidence": evidence,
            "destination_location_id": destination_location_id,
        },
    )
    queue(conn, event, "mongodb")
    return sequence


def claim_shipment(identifier):
    with transaction() as conn:
        row = get(conn, "shipments", identifier)
        if not row["inventory_pending"]:
            return row
    try:
        call(
            "inventario",
            "POST",
            "/internal/v1/reservations/" + str(row["reservation_id"]) + "/claim",
            {"shipment_id": identifier},
            delegate=False,
        )
    except APIError as exc:
        if exc.status == 409:
            with transaction() as conn:
                current = get(conn, "shipments", identifier, True)
                if current["inventory_pending"]:
                    # No se registró recolección; el plan no puede avanzar.
                    update(
                        conn,
                        "shipments",
                        identifier,
                        {"status": "REJECTED", "inventory_pending": False},
                    )
                    g.actor = {
                        "id": None,
                        "tenant_id": str(current["origin_id"]),
                        "region_id": str(current["region_id"]),
                    }
                    emit(
                        conn, "SHIPMENT_PLAN_REJECTED", identifier, current["origin_id"]
                    )
            raise
        raise
    with transaction() as conn:
        current = get(conn, "shipments", identifier, True)
        if current["inventory_pending"]:
            g.actor = {
                "id": None,
                "tenant_id": str(current["origin_id"]),
                "region_id": str(current["region_id"]),
            }
            seq = logistics_event(conn, current, "PLANNED", None)
            update(
                conn,
                "shipments",
                identifier,
                {"inventory_pending": False, "sequence": seq},
            )
        return get(conn, "shipments", identifier)


def recover_shipments(limit=100):
    with transaction() as conn:
        rows = conn.execute(
            "SELECT id FROM shipments WHERE inventory_pending ORDER BY id LIMIT %s",
            (limit,),
        ).fetchall()
    recovered, pending = 0, 0
    for row in rows:
        try:
            claim_shipment(str(row["id"]))
            recovered += 1
        except APIError:
            pending += 1
    return {"recovered": recovered, "pending": pending}


def register(app):
    @endpoint(
        app,
        "/api/v1/shipments",
        "POST",
        model=ShipmentCreate,
        roles=("COORDINATOR",),
        status=202,
        summary="Planear traslado y confirmar vínculo exclusivo con Inventario",
    )
    def shipment_create(data):
        reservation = call(
            "inventario", "GET", "/internal/v1/reservations/" + data["reservation_id"]
        )
        if reservation["status"] != "RESERVED":
            raise APIError("conflict", "Reserva no confirmada.", 409)
        transport = call(
            "identidad_acceso", "GET", "/internal/v1/users/" + data["transport_user_id"]
        )
        if transport["tenant_id"] != reservation["origin_id"]:
            raise APIError(
                "forbidden",
                "Responsable debe pertenecer a la institución de origen.",
                403,
            )
        route = call(
            "priorizacion_geografia",
            "GET",
            "/internal/v1/routes/" + reservation["route_id"],
        )
        if route["version"] != reservation["route_version"]:
            raise APIError(
                "stale_route", "Revisa y reautoriza la reserva: la ruta cambió.", 409
            )
        departure, eta, expires = (
            utc_date(data["departure_at"], "departure_at"),
            utc_date(data["eta"], "eta"),
            utc_date(reservation["expires_at"]),
        )
        if departure >= eta:
            raise invalid(
                "La llegada debe ser posterior a la salida.",
                "departure_at",
                "eta",
                code="date_order",
            )
        if eta >= expires:
            raise invalid(
                "La llegada debe ser anterior a la caducidad de la reserva.",
                "eta",
                code="arrival_expiry",
            )
        if departure < datetime.now(timezone.utc) - timedelta(minutes=1):
            raise invalid(
                "La salida no puede haber ocurrido hace más de un minuto.",
                "departure_at",
                code="past_departure",
            )
        if eta < departure + timedelta(minutes=route["travel_minutes"]):
            raise invalid(
                f"La llegada debe permitir al menos {route['travel_minutes']} minutos de recorrido desde la salida.",
                "departure_at",
                "eta",
                code="route_duration",
            )

        def work(conn):
            row = insert(
                conn,
                "shipments",
                dict(
                    id=str(uuid4()),
                    reservation_id=data["reservation_id"],
                    origin_id=reservation["origin_id"],
                    destination_id=reservation["destination_id"],
                    region_id=reservation["region_id"],
                    transport_user_id=data["transport_user_id"],
                    departure_at=departure,
                    eta=eta,
                    expires_at=expires,
                ),
            )
            record(
                conn,
                row["id"],
                row["origin_id"],
                "SHIPMENT_PLAN_PENDING",
                data["reason"],
            )
            emit(conn, "SHIPMENT_PLAN_PENDING", row["id"], row["origin_id"])
            return row

        row = atomic("shipment_create", data, work)
        try:
            return claim_shipment(str(row["id"]))
        except APIError as exc:
            if exc.status == 503:
                return row
            raise

    @endpoint(
        app,
        "/api/v1/shipments",
        roles=("COORDINATOR", "TRANSPORT", "OPERATOR", "MEDICAL"),
        paginated=True,
        summary="Traslados de la región, institución o responsable",
    )
    def shipment_list():
        with transaction() as conn:
            if g.actor["role"] == "COORDINATOR":
                where, values = "region_id=%s", (g.actor["region_id"],)
            elif g.actor["role"] == "TRANSPORT":
                where, values = "transport_user_id=%s", (g.actor["id"],)
            else:
                where, values = (
                    "origin_id=%s OR destination_id=%s",
                    (g.actor["tenant_id"], g.actor["tenant_id"]),
                )
            return listing(
                conn, "shipments", where, values, order="departure_at DESC,id"
            )

    @endpoint(
        app,
        "/api/v1/shipments/<identifier>",
        roles=("COORDINATOR", "TRANSPORT", "OPERATOR", "MEDICAL"),
        summary="Estado logístico y coordinación pendiente",
    )
    def shipment_detail(identifier):
        with transaction() as conn:
            row = get(conn, "shipments", identifier)
            shipment_access(row)
            row["decisions"] = history(conn, identifier)
            row["transitions"] = conn.execute(
                "SELECT id,sequence,state,actor_id,reason,evidence,created_at FROM transitions WHERE shipment_id=%s ORDER BY sequence",
                (identifier,),
            ).fetchall()
            return row

    @endpoint(
        app,
        "/api/v1/shipments/<identifier>/transitions",
        "POST",
        model=Transition,
        roles=("COORDINATOR", "TRANSPORT", "OPERATOR"),
        summary="Registrar paso autorizado y evento de custodia durable",
    )
    def shipment_transition(identifier, data):
        if data["destination_location_id"]:
            if data["state"] != "ACCEPTED":
                raise APIError(
                    "validation",
                    "La ubicación de recepción corresponde únicamente a la aceptación.",
                )
            location = call(
                "identidad_acceso",
                "GET",
                "/internal/v1/locations/" + data["destination_location_id"],
            )
            if not location["active"]:
                raise APIError("conflict", "Ubicación receptora inactiva.", 409)

        def work(conn):
            row = get(conn, "shipments", identifier, True)
            shipment_access(row)
            if (
                row["inventory_pending"]
                or row["version"] != data["version"]
                or row["status"] in ("ACCEPTED", "CANCELLED", "REJECTED")
            ):
                raise APIError(
                    "conflict", "Traslado pendiente, obsoleto o finalizado.", 409
                )
            state, actor = data["state"], g.actor
            if state in ("PREPARED", "COLLECTED", "IN_TRANSIT", "ACCEPTED") and row[
                "expires_at"
            ] <= datetime.now(timezone.utc):
                raise APIError(
                    "expired_resource",
                    "Se superó el límite de conservación capturado. Registra una incidencia; la entrega física no permite aceptar ni cerrar la solicitud.",
                    409,
                )
            expected = {
                "PREPARED": "PLANNED",
                "COLLECTED": "PREPARED",
                "IN_TRANSIT": "COLLECTED",
                "DELIVERED": "IN_TRANSIT",
                "ACCEPTED": "DELIVERED",
            }
            if state in expected and row["status"] != expected[state]:
                raise APIError("conflict", "Paso logístico fuera de secuencia.", 409)
            if state in ("PREPARED", "ACCEPTED"):
                tenant = (
                    row["origin_id"] if state == "PREPARED" else row["destination_id"]
                )
                if actor["role"] != "OPERATOR" or actor["tenant_id"] != str(tenant):
                    raise APIError(
                        "forbidden", "Operador de origen/destino requerido.", 403
                    )
            elif state in ("COLLECTED", "IN_TRANSIT", "DELIVERED"):
                if actor["role"] != "TRANSPORT" or actor["id"] != str(
                    row["transport_user_id"]
                ):
                    raise APIError(
                        "forbidden", "Responsable de traslado requerido.", 403
                    )
            elif state == "CANCELLED":
                if actor["role"] != "COORDINATOR" or row["status"] not in (
                    "PLANNED",
                    "PREPARED",
                ):
                    raise APIError(
                        "conflict",
                        "Solo coordinación puede cancelar antes de recolección.",
                        409,
                    )
            if data["evidence"]:
                evidence_row = get(conn, "files", data["evidence"]["object_id"])
                if (
                    str(evidence_row["shipment_id"]) != identifier
                    or evidence_row["status"] != "VERIFIED"
                ):
                    raise APIError(
                        "conflict", "Evidencia no verificada para este traslado.", 409
                    )
            seq = logistics_event(
                conn,
                row,
                state,
                actor["id"],
                data["evidence"],
                data["destination_location_id"],
            )
            insert(
                conn,
                "transitions",
                dict(
                    id=str(uuid4()),
                    shipment_id=identifier,
                    sequence=seq,
                    state=state,
                    actor_id=actor["id"],
                    reason=data["reason"],
                    evidence=data["evidence"],
                ),
            )
            status = row["status"] if state == "INCIDENT" else state
            result = update(
                conn,
                "shipments",
                identifier,
                {"status": status, "version": row["version"] + 1, "sequence": seq},
            )
            return result

        return atomic("shipment_transition:" + identifier, data, work)

    @endpoint(
        app,
        "/api/v1/shipments/<identifier>/telemetry",
        "POST",
        model=Telemetry,
        roles=("TRANSPORT",),
        status=201,
        summary="Ubicación solo del responsable durante traslado activo",
    )
    def telemetry_create(identifier, data):
        captured = utc_date(data["captured_at"], "captured_at")
        if abs((datetime.now(timezone.utc) - captured).total_seconds()) > 300:
            raise invalid(
                "La fecha de ubicación debe estar a no más de cinco minutos del momento actual.",
                "captured_at",
                code="location_time",
            )

        def work(conn):
            row = get(conn, "shipments", identifier, True)
            shipment_access(row)
            if (
                row["status"] not in ("COLLECTED", "IN_TRANSIT")
                or row["inventory_pending"]
            ):
                raise APIError(
                    "conflict",
                    "No se autoriza ubicación fuera del traslado activo.",
                    409,
                )
            point = insert(
                conn,
                "telemetry",
                dict(
                    id=str(uuid4()),
                    shipment_id=identifier,
                    actor_id=g.actor["id"],
                    **dict(data, captured_at=captured),
                ),
            )
            event = emit(
                conn,
                "TELEMETRY_RECORDED",
                identifier,
                row["origin_id"],
                metadata={"point_id": str(point["id"])},
            )
            # La posición exacta solo va a la colección privada del propietario.
            private = dict(
                event,
                event_id=str(point["id"]),
                metadata=dict(data, shipment_id=identifier),
            )
            queue(conn, private, "mongodb")
            return point

        result = atomic("telemetry_create:" + identifier, data, work)
        from redhouse.security import key, redis_call

        redis_call(
            lambda r: r.set(
                key("transporte:location:" + identifier), str(result["id"]), ex=300
            )
        )
        return result

    @endpoint(
        app,
        "/api/v1/shipments/<identifier>/telemetry",
        roles=("TRANSPORT", "COORDINATOR"),
        paginated=True,
        summary="Historial de ubicación con autorización por traslado",
    )
    def telemetry_list(identifier):
        with transaction() as conn:
            shipment_access(get(conn, "shipments", identifier))
            return listing(conn, "telemetry", "shipment_id=%s", (identifier,))

    @endpoint(
        app,
        "/internal/v1/shipments/<identifier>/access",
        internal=("custodia",),
        roles=("TRANSPORT", "COORDINATOR", "OPERATOR", "MEDICAL"),
        summary="Autorizar consulta de custodia por asignación logística",
    )
    def shipment_internal(identifier):
        with transaction() as conn:
            row = get(conn, "shipments", identifier)
            shipment_access(row)
            return {"authorized": True, "id": identifier}

    from .files import register_files

    register_files(app, shipment_access)
