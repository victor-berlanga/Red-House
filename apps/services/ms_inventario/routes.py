import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from typing import Annotated, Literal
from uuid import uuid4

from flask import current_app, g, request
from pydantic import Field

from redhouse.api import atomic, endpoint, listing
from redhouse.client import call
from redhouse.codec import plain
from redhouse.db import get, insert, transaction, update
from redhouse.errors import APIError
from redhouse.decisions import record, history
from redhouse.events import consume, emit
from redhouse.models import Confirm, Group, ID, Kind, Model, Text, utc_date, validate_id
from redhouse.security import key, own, redis_call
from .states import RESOURCE_FILTER


class ResourceCreate(Model):
    collected_at: Text | None = None
    location_id: ID | None = None
    folio: Annotated[
        str, Field(min_length=6, max_length=30, pattern=r"^[A-Za-z0-9_-]+$")
    ]
    kind: Kind
    component: Text
    blood_group: Group
    expires_at: Text
    donation_id: ID | None = None


class Release(Confirm):
    version: Annotated[int, Field(ge=1)]


class ReservationCreate(Confirm):
    evaluation_id: ID
    resource_id: ID


class Claim(Model):
    shipment_id: ID


def available(conn):
    return conn.execute(
        "SELECT id,folio,tenant_id,region_id,kind,component,blood_group,expires_at,status,version FROM resources "
        "WHERE region_id=%s AND status='AVAILABLE' AND expires_at>now() ORDER BY expires_at,id",
        (g.actor["region_id"],),
    ).fetchall()


def reservation_access(row):
    if str(row["region_id"]) != g.actor["region_id"]:
        raise APIError("forbidden", "Reserva fuera de la región.", 403)
    if g.actor["role"] in ("MEDICAL", "OPERATOR") and g.actor["tenant_id"] not in (
        str(row["origin_id"]),
        str(row["destination_id"]),
    ):
        raise APIError("forbidden", "Reserva ajena a la institución.", 403)


def operation_result(identifier):
    with transaction() as conn:
        operation = get(conn, "operations", identifier)
        row = conn.execute(
            "SELECT * FROM reservations WHERE operation_id=%s", (identifier,)
        ).fetchone()
        return {
            "operation_id": identifier,
            "status": operation["status"],
            "error": operation["error"],
            "reservation": row,
        }


def finalize(identifier):
    with transaction() as conn:
        op = get(conn, "operations", identifier)
        row = conn.execute(
            "SELECT * FROM reservations WHERE operation_id=%s", (identifier,)
        ).fetchone()
        hold_id = str(op["hold_id"]) if op["hold_id"] else None
    if op["status"] == "ROLLBACK_PENDING":
        if hold_id:
            call(
                "receptores",
                "POST",
                "/internal/v1/holds/" + hold_id,
                {"operation_id": identifier, "action": "RELEASE"},
                delegate=False,
            )
        with transaction() as conn:
            update(conn, "operations", identifier, {"status": "FAILED"})
        return operation_result(identifier)
    if row and row["status"] == "PENDING":
        call(
            "receptores",
            "POST",
            "/internal/v1/holds/" + str(row["hold_id"]),
            {"operation_id": identifier, "action": "CONFIRM"},
            delegate=False,
        )
        with transaction() as conn:
            current = get(conn, "reservations", str(row["id"]), True)
            if current["status"] == "PENDING":
                update(conn, "reservations", str(row["id"]), {"status": "RESERVED"})
                update(conn, "operations", identifier, {"status": "COMPLETED"})
    return operation_result(identifier)


def recover_operations(limit=100):
    with transaction() as conn:
        ids = conn.execute(
            "SELECT id,created_at,hold_id FROM operations WHERE status IN ('ROLLBACK_PENDING','PENDING') "
            "ORDER BY last_recovery_at NULLS FIRST,created_at LIMIT %s",
            (limit,),
        ).fetchall()
    recovered, pending = 0, 0
    for row in ids:
        try:
            # Tras una interrupción, el grant puede existir aunque su respuesta se perdiera.
            with transaction() as conn:
                operation = get(conn, "operations", str(row["id"]))
                update(
                    conn,
                    "operations",
                    str(row["id"]),
                    {"last_recovery_at": datetime.now(timezone.utc)},
                )
                reserved = conn.execute(
                    "SELECT 1 FROM reservations WHERE operation_id=%s", (row["id"],)
                ).fetchone()
            if not reserved and row["created_at"] < datetime.now(
                timezone.utc
            ) - timedelta(seconds=60):
                hold = call(
                    "receptores",
                    "GET",
                    "/internal/v1/holds-by-operation/" + str(row["id"]),
                    delegate=False,
                )["hold"]
                if hold:
                    with transaction() as conn:
                        locked = get(conn, "operations", str(row["id"]), True)
                        if not conn.execute(
                            "SELECT 1 FROM reservations WHERE operation_id=%s",
                            (row["id"],),
                        ).fetchone():
                            update(
                                conn,
                                "operations",
                                str(row["id"]),
                                {
                                    "hold_id": hold["id"],
                                    "status": "ROLLBACK_PENDING",
                                    "error": "interrupted_operation",
                                },
                            )
            result = finalize(str(row["id"]))
            if result["status"] in ("COMPLETED", "FAILED"):
                recovered += 1
            else:
                pending += 1
        except APIError:
            pending += 1
    return {"recovered": recovered, "pending": pending}


def reserve(data):
    idem = request.headers.get("Idempotency-Key", "")
    if not re.fullmatch(r"[A-Za-z0-9_-]{8,100}", idem):
        raise APIError("idempotency_required", "Idempotency-Key requerido.")
    fingerprint = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
    with transaction() as conn:
        lock = int.from_bytes(
            hashlib.sha256((g.actor["id"] + idem).encode()).digest()[:8],
            "big",
            signed=True,
        )
        conn.execute("SELECT pg_advisory_xact_lock(%s)", (lock,))
        op = conn.execute(
            "SELECT * FROM operations WHERE user_id=%s AND key=%s",
            (g.actor["id"], idem),
        ).fetchone()
        if op and op["fingerprint"] != fingerprint:
            raise APIError(
                "idempotency_conflict", "Clave utilizada para otro contenido.", 409
            )
        if not op:
            op = insert(
                conn,
                "operations",
                dict(
                    id=str(uuid4()),
                    user_id=g.actor["id"],
                    tenant_id=g.actor["tenant_id"],
                    key=idem,
                    fingerprint=fingerprint,
                    input=data,
                ),
            )
    identifier = str(op["id"])
    existing = operation_result(identifier)
    if existing["reservation"] or op["status"] in (
        "ROLLBACK_PENDING",
        "COMPLETED",
        "FAILED",
    ):
        try:
            return finalize(identifier)
        except APIError as exc:
            if exc.status == 503:
                return existing
            raise
    # Snapshot proveniente de su propietario; nunca aceptado del cliente.
    evaluation = call(
        "compatibilidad", "GET", "/internal/v1/evaluations/" + data["evaluation_id"]
    )
    own(evaluation["tenant_id"])
    candidate = next(
        (
            c
            for c in evaluation["candidates"]
            if c["resource_id"] == data["resource_id"]
        ),
        None,
    )
    review = next(
        (
            r
            for r in evaluation["reviews"]
            if r["resource_id"] == data["resource_id"] and r["decision"] == "FAVORABLE"
        ),
        None,
    )
    if not candidate or not review:
        raise APIError(
            "human_review_required",
            "Candidato y dictamen médico favorable obligatorios.",
            409,
        )
    route = call(
        "priorizacion_geografia", "GET", "/internal/v1/routes/" + candidate["route_id"]
    )
    if route["version"] != candidate["route_version"]:
        raise APIError("stale_route", "Ruta modificada; evalúa nuevamente.", 409)
    hold = call(
        "receptores",
        "POST",
        "/internal/v1/holds",
        {
            "operation_id": identifier,
            "request_id": evaluation["request_id"],
            "resource_id": data["resource_id"],
            "request_version": evaluation["request_version"],
            "recipient_version": evaluation["recipient_version"],
        },
    )
    with transaction() as conn:
        update(conn, "operations", identifier, {"hold_id": hold["id"]})
    try:
        with transaction() as conn:
            # Una segunda petición con la misma clave puede llegar tras el primer commit.
            current_op = get(conn, "operations", identifier, True)
            existing = conn.execute(
                "SELECT * FROM reservations WHERE operation_id=%s", (identifier,)
            ).fetchone()
            if not existing:
                if current_op["status"] != "PENDING" or hold["status"] != "HELD":
                    raise APIError(
                        "operation_conflict", "Operación sin retención vigente.", 409
                    )
                resource = get(conn, "resources", data["resource_id"], True)
                if (
                    resource["status"] != "AVAILABLE"
                    or resource["version"] != candidate["resource_version"]
                ):
                    raise APIError(
                        "stale_resource", "Recurso reservado o modificado.", 409
                    )
                if resource["expires_at"] <= datetime.now(timezone.utc) + timedelta(
                    minutes=route["travel_minutes"]
                ):
                    raise APIError(
                        "expired_resource",
                        "El límite capturado no permite el traslado estimado.",
                        409,
                    )
                row = insert(
                    conn,
                    "reservations",
                    dict(
                        id=str(uuid4()),
                        operation_id=identifier,
                        resource_id=resource["id"],
                        request_id=evaluation["request_id"],
                        recipient_id=evaluation["snapshot"]["recipient_id"],
                        origin_id=resource["tenant_id"],
                        destination_id=g.actor["tenant_id"],
                        region_id=g.actor["region_id"],
                        hold_id=hold["id"],
                        evaluation_id=data["evaluation_id"],
                        route_id=route["id"],
                        route_version=route["version"],
                    ),
                )
                update(
                    conn,
                    "resources",
                    data["resource_id"],
                    {"status": "RESERVED", "version": resource["version"] + 1},
                )
                insert(
                    conn,
                    "movements",
                    {
                        "id": str(uuid4()),
                        "resource_id": resource["id"],
                        "action": "RESERVED",
                        "actor_id": g.actor["id"],
                    },
                )
                emit(
                    conn,
                    "RESOURCE_RESERVED",
                    row["id"],
                    g.actor["tenant_id"],
                    targets=("auditoria", "alertas"),
                    metadata={
                        "origin_id": str(resource["tenant_id"]),
                        "destination_id": g.actor["tenant_id"],
                    },
                )
    except APIError as exc:
        with transaction() as conn:
            update(
                conn,
                "operations",
                identifier,
                {"status": "ROLLBACK_PENDING", "error": exc.code},
            )
        try:
            finalize(identifier)
        except APIError:
            return operation_result(identifier)
        raise
    try:
        return finalize(identifier)
    except APIError as exc:
        if exc.status == 503:
            return operation_result(identifier)
        raise


def register(app):
    @endpoint(
        app,
        "/api/v1/resources",
        "POST",
        model=ResourceCreate,
        roles=("OPERATOR",),
        status=201,
        summary="Registrar unidad u oferta separada, inicialmente en cuarentena",
    )
    def resource_create(data):
        from .locations import validate_location

        validate_location(data["location_id"])
        expires = utc_date(data["expires_at"])
        if expires <= datetime.now(timezone.utc):
            raise APIError(
                "validation", "Límite de conservación capturado debe ser futuro."
            )
        collected = utc_date(data["collected_at"]) if data["collected_at"] else None
        if collected and (
            collected > datetime.now(timezone.utc) or collected >= expires
        ):
            raise APIError(
                "validation", "Recolección futura o posterior al límite capturado."
            )
        if data["kind"] == "ORGAN" and data["component"] not in (
            "KIDNEY",
            "LIVER",
            "HEART",
        ):
            raise APIError("validation", "Tipo de órgano no soportado.")
        if data["donation_id"]:
            donation = call(
                "donantes", "GET", "/internal/v1/donations/" + data["donation_id"]
            )
            if donation["status"] != "PROCESSED" or any(
                donation[k] != data[k] for k in ("kind", "component", "blood_group")
            ):
                raise APIError(
                    "conflict", "Donación no procesada o distinta del recurso.", 409
                )

        def work(conn):
            row = insert(
                conn,
                "resources",
                dict(
                    data,
                    expires_at=expires,
                    collected_at=collected,
                    id=str(uuid4()),
                    tenant_id=g.actor["tenant_id"],
                    current_institution_id=g.actor["tenant_id"],
                    region_id=g.actor["region_id"],
                ),
            )
            insert(
                conn,
                "movements",
                {
                    "id": str(uuid4()),
                    "resource_id": row["id"],
                    "action": "CREATED",
                    "actor_id": g.actor["id"],
                },
            )
            emit(conn, "RESOURCE_CREATED", row["id"], row["tenant_id"])
            return row

        return atomic("resource_create", data, work)

    @endpoint(
        app,
        "/api/v1/resources/<identifier>/release",
        "POST",
        model=Release,
        roles=("MEDICAL",),
        summary="Liberación humana documentada",
    )
    def resource_release(identifier, data):
        def work(conn):
            row = get(conn, "resources", identifier, True)
            own(row["tenant_id"])
            if (
                row["version"] != data["version"]
                or row["status"] != "QUARANTINE"
                or row["expires_at"] <= datetime.now(timezone.utc)
            ):
                raise APIError("conflict", "Recurso obsoleto, liberado o vencido.", 409)
            insert(
                conn,
                "resource_reviews",
                dict(
                    id=str(uuid4()),
                    resource_id=identifier,
                    actor_id=g.actor["id"],
                    decision="RELEASED",
                    reason=data["reason"],
                ),
            )
            result = update(
                conn,
                "resources",
                identifier,
                {"status": "AVAILABLE", "version": row["version"] + 1},
            )
            insert(
                conn,
                "movements",
                {
                    "id": str(uuid4()),
                    "resource_id": identifier,
                    "action": "RELEASED",
                    "actor_id": g.actor["id"],
                },
            )
            emit(conn, "RESOURCE_RELEASED", identifier, row["tenant_id"])
            return result

        return atomic("resource_release:" + identifier, data, work)

    @endpoint(
        app,
        "/api/v1/resources",
        roles=("OPERATOR", "MEDICAL", "COORDINATOR"),
        paginated=True,
        query=("q", "kind", "status"),
        summary="Inventario propio; coordinador recibe disponibilidad regional mínima",
    )
    def resources_list():
        with transaction() as conn:
            filters = {
                "q": ("folio",),
                "kind": ("kind", ("BLOOD", "ORGAN")),
                "status": ("status", RESOURCE_FILTER),
            }
            visible = "" if request.args.get("status") else " AND status<>'WITHDRAWN'"
            if g.actor["role"] == "COORDINATOR":
                return listing(
                    conn,
                    "resources",
                    "region_id=%s" + visible,
                    (g.actor["region_id"],),
                    columns="id,folio,tenant_id,current_institution_id,kind,component,blood_group,status,expires_at,version",
                    filters=filters,
                )
            return listing(
                conn,
                "resources",
                "current_institution_id=%s" + visible,
                (g.actor["tenant_id"],),
                filters=filters,
            )

    @endpoint(
        app,
        "/api/v1/availability",
        roles=("MEDICAL", "OPERATOR", "COORDINATOR"),
        paginated=True,
        summary="Disponibilidad regional minimizada con caché autorizada",
    )
    def availability():
        from redhouse.api import pagination

        page, size, offset = pagination()
        # TTL breve: nunca se utiliza esta proyección para decidir una reserva.
        cache_key = key(
            f"cache:inventario:availability:{g.actor['region_id']}:{g.actor['tenant_id']}:{g.actor['role']}:{page}:{size}"
        )
        bypass = "no-cache" in request.headers.get("Cache-Control", "")
        cached = None if bypass else redis_call(lambda r: r.get(cache_key))
        if cached:
            g.cache_hit = True
            g.cache_status = "HIT"
            return json.loads(cached)
        g.cache_status = "BYPASS" if bypass else "MISS"
        with transaction() as conn:
            count = conn.execute(
                "SELECT count(*) AS n FROM resources WHERE region_id=%s AND status='AVAILABLE' AND expires_at>now()",
                (g.actor["region_id"],),
            ).fetchone()["n"]
            rows = conn.execute(
                "SELECT id,tenant_id,kind,component,blood_group,expires_at,status,version FROM resources "
                "WHERE region_id=%s AND status='AVAILABLE' AND expires_at>now() ORDER BY expires_at,id LIMIT %s OFFSET %s",
                (g.actor["region_id"], size, offset),
            ).fetchall()
        result = plain(
            {
                "items": rows,
                "page": page,
                "page_size": size,
                "total": count,
                "notice": "Disponibilidad orientativa; la reserva revalida PostgreSQL.",
            }
        )
        if not bypass:
            redis_call(
                lambda r: r.set(
                    cache_key, json.dumps(result), ex=app.config["CACHE_TTL"]
                )
            )
        return result

    @endpoint(
        app,
        "/internal/v1/available-resources",
        internal=("compatibilidad",),
        roles=("MEDICAL",),
        summary="Fuente autoritativa de candidatos; omite caché",
    )
    def resources_internal():
        with transaction() as conn:
            return {"items": available(conn)}

    @endpoint(
        app,
        "/api/v1/reservations",
        "POST",
        model=ReservationCreate,
        roles=("MEDICAL",),
        status=202,
        summary="Reservar con retención de capacidad y seguimiento de operación",
    )
    def reservation_create(data):
        try:
            return reserve(data)
        except APIError as exc:
            if exc.status != 503:
                with transaction() as conn:
                    conn.execute(
                        "UPDATE operations SET status='FAILED',error=%s WHERE user_id=%s AND key=%s "
                        "AND status='PENDING' AND hold_id IS NULL",
                        (
                            exc.code,
                            g.actor["id"],
                            request.headers.get("Idempotency-Key", ""),
                        ),
                    )
            raise

    @endpoint(
        app,
        "/api/v1/operations/<identifier>",
        roles=("MEDICAL",),
        summary="Consultar resultado tras pérdida de respuesta",
    )
    def operation_detail(identifier):
        with transaction() as conn:
            op = get(conn, "operations", identifier)
            own(op["tenant_id"])
            if str(op["user_id"]) != g.actor["id"]:
                raise APIError("forbidden", "Operación de otro usuario.", 403)
        return operation_result(identifier)

    @endpoint(
        app,
        "/api/v1/operations/<identifier>/resume",
        "POST",
        roles=("MEDICAL",),
        summary="Reanudar confirmación o compensación pendiente",
    )
    def operation_resume(identifier):
        operation_detail(identifier)
        return finalize(identifier)

    @endpoint(
        app,
        "/api/v1/reservations/<identifier>",
        roles=("MEDICAL", "OPERATOR", "COORDINATOR"),
        summary="Consultar asignación autorizada",
    )
    def reservation_detail(identifier):
        with transaction() as conn:
            row = get(conn, "reservations", identifier)
            reservation_access(row)
            row["expires_at"] = get(conn, "resources", str(row["resource_id"]))[
                "expires_at"
            ]
            row["decisions"] = history(conn, identifier)
            return row

    @endpoint(
        app,
        "/api/v1/reservations/<identifier>/cancel",
        "POST",
        model=Confirm,
        roles=("MEDICAL",),
        summary="Liberar reserva antes de programar un traslado",
    )
    def reservation_cancel(identifier, data):
        def work(conn):
            row = get(conn, "reservations", identifier, True)
            own(row["destination_id"])
            if row["status"] != "RESERVED" or row["shipment_id"] is not None:
                raise APIError(
                    "conflict",
                    "Reserva pendiente o con traslado; utiliza la cancelación logística autorizada.",
                    409,
                )
            resource = get(conn, "resources", str(row["resource_id"]), True)
            record(
                conn,
                identifier,
                row["destination_id"],
                "RESERVATION_CANCELLED",
                data["reason"],
            )
            result = update(conn, "reservations", identifier, {"status": "CANCELLED"})
            update(
                conn,
                "resources",
                str(resource["id"]),
                {"status": "AVAILABLE", "version": resource["version"] + 1},
            )
            insert(
                conn,
                "movements",
                {
                    "id": str(uuid4()),
                    "resource_id": resource["id"],
                    "action": "CANCELLED",
                    "actor_id": g.actor["id"],
                },
            )
            emit(
                conn,
                "RESERVATION_CANCELLED",
                identifier,
                row["destination_id"],
                targets=("auditoria", "receptores"),
                metadata={
                    "hold_id": str(row["hold_id"]),
                    "operation_id": str(row["operation_id"]),
                    "hold_action": "RELEASE",
                },
            )
            return result

        return atomic("reservation_cancel:" + identifier, data, work)

    @endpoint(
        app,
        "/internal/v1/reservations/<identifier>",
        internal=("transporte",),
        roles=("COORDINATOR",),
        summary="Datos mínimos para planear traslado",
    )
    def reservation_internal(identifier):
        return reservation_detail(identifier)

    @endpoint(
        app,
        "/internal/v1/reservations/<identifier>/claim",
        "POST",
        model=Claim,
        internal=("transporte",),
        delegate=False,
        summary="Vincular traslado durable antes de permitir recolección",
    )
    def reservation_claim(identifier, data):
        with transaction() as conn:
            row = get(conn, "reservations", identifier, True)
            if row["shipment_id"] is not None:
                if str(row["shipment_id"]) != data["shipment_id"]:
                    raise APIError("conflict", "Reserva con otro traslado.", 409)
                return row
            if row["status"] != "RESERVED":
                raise APIError("conflict", "Reserva no confirmada o cancelada.", 409)
            resource = get(conn, "resources", str(row["resource_id"]))
            if resource["expires_at"] <= datetime.now(timezone.utc):
                raise APIError(
                    "expired_resource",
                    "Recurso vencido antes de confirmar el plan.",
                    409,
                )
            return update(
                conn, "reservations", identifier, {"shipment_id": data["shipment_id"]}
            )

    from redhouse.event_model import Event

    @endpoint(
        app,
        "/internal/v1/events",
        "POST",
        model=Event,
        internal=("transporte",),
        delegate=False,
        summary="Aplicar hechos logísticos en orden y sin duplicación",
    )
    def inventory_events(data):
        if data["source"] != g.caller:
            raise APIError("forbidden", "Fuente de evento incorrecta.", 403)
        with transaction() as conn:
            if not consume(conn, data):
                return {"duplicate": True}
            metadata = data["metadata"]
            row = get(conn, "reservations", metadata["reservation_id"], True)
            if str(row["shipment_id"]) != data["resource_id"]:
                raise APIError("conflict", "Traslado no vinculado.", 409)
            sequence = metadata["sequence"]
            if sequence != row["shipment_sequence"] + 1:
                raise APIError(
                    "sequence_gap", "Falta un evento previo; se reintentará.", 409
                )
            resource = get(conn, "resources", str(row["resource_id"]), True)
            state = metadata["state"]
            updates = {"shipment_sequence": sequence}
            g.actor = {
                "id": data["actor_id"],
                "tenant_id": str(row["destination_id"]),
                "region_id": str(row["region_id"]),
            }
            if state == "COLLECTED":
                updates["status"] = "IN_TRANSIT"
                update(
                    conn,
                    "resources",
                    str(resource["id"]),
                    {"status": "IN_TRANSIT", "version": resource["version"] + 1},
                )
            elif state == "ACCEPTED":
                updates["status"] = "RECEIVED"
                update(
                    conn,
                    "resources",
                    str(resource["id"]),
                    {
                        "status": "RECEIVED",
                        "current_institution_id": row["destination_id"],
                        "location_id": metadata.get("destination_location_id"),
                        "version": resource["version"] + 1,
                    },
                )
                emit(
                    conn,
                    "RESERVATION_RECEIVED",
                    row["id"],
                    row["destination_id"],
                    targets=("auditoria", "receptores", "alertas"),
                    metadata={
                        "hold_id": str(row["hold_id"]),
                        "operation_id": str(row["operation_id"]),
                        "hold_action": "RECEIVE",
                    },
                )
            elif state == "CANCELLED":
                if row["status"] != "RESERVED":
                    raise APIError(
                        "conflict", "No puede liberarse un recurso recolectado.", 409
                    )
                updates["status"] = "CANCELLED"
                update(
                    conn,
                    "resources",
                    str(resource["id"]),
                    {"status": "AVAILABLE", "version": resource["version"] + 1},
                )
                emit(
                    conn,
                    "RESERVATION_CANCELLED",
                    row["id"],
                    row["destination_id"],
                    targets=("auditoria", "receptores"),
                    metadata={
                        "hold_id": str(row["hold_id"]),
                        "operation_id": str(row["operation_id"]),
                        "hold_action": "RELEASE",
                    },
                )
            if state in ("COLLECTED", "ACCEPTED", "CANCELLED"):
                insert(
                    conn,
                    "movements",
                    {
                        "id": str(uuid4()),
                        "resource_id": resource["id"],
                        "action": state,
                        "actor_id": data["actor_id"],
                    },
                )
            emit(
                conn,
                "INVENTORY_SHIPMENT_EVENT",
                row["id"],
                row["destination_id"],
                metadata={"status": state},
            )
            update(conn, "reservations", str(row["id"]), updates)
            return {"applied": True}
