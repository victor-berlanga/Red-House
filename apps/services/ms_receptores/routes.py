from typing import Annotated, Literal
from uuid import uuid4

from flask import g
from pydantic import Field

from redhouse.api import atomic, endpoint, listing
from redhouse.db import get, insert, transaction, update
from redhouse.errors import APIError
from redhouse.validation import invalid
from redhouse.decisions import record, history
from redhouse.events import consume, emit
from redhouse.models import Confirm, Group, ID, Kind, Model, Organ, Reason, Text
from redhouse.security import own


class RecipientCreate(Model):
    restrictions: Reason | None = None
    requirement: Reason | None = None
    status: Literal["ACTIVE", "INACTIVE"] = "ACTIVE"
    folio: Annotated[
        str, Field(min_length=6, max_length=30, pattern=r"^[A-Za-z0-9_-]+$")
    ]
    display_name: Text
    kind: Kind
    blood_group: Group
    organ_type: Organ | None = None
    studies: Reason


class RequestCreate(Model):
    recipient_id: ID
    component: Text
    quantity: Annotated[int, Field(ge=1, le=100)]
    urgency: Annotated[int, Field(ge=1, le=3)]


class HoldCreate(Model):
    operation_id: ID
    request_id: ID
    resource_id: ID
    request_version: Annotated[int, Field(ge=1)]
    recipient_version: Annotated[int, Field(ge=1)]


class Cancel(Confirm):
    version: Annotated[int, Field(ge=1)]


class HoldAction(Model):
    operation_id: ID
    action: str


def apply_hold(conn, identifier, data):
    if data["action"] not in ("CONFIRM", "RELEASE", "RECEIVE"):
        raise APIError("validation", "Acción de retención inválida.")
    initial = get(conn, "holds", identifier)
    req = get(conn, "requests", str(initial["request_id"]), True)
    person = get(conn, "recipients", str(req["recipient_id"]), True)
    hold = get(conn, "holds", identifier, True)
    if str(hold["operation_id"]) != data["operation_id"]:
        raise APIError("operation_conflict", "Operación no coincide.", 409)
    target = {"CONFIRM": "CONFIRMED", "RELEASE": "RELEASED", "RECEIVE": "RECEIVED"}[
        data["action"]
    ]
    if hold["status"] == target:
        return hold
    allowed = {
        "CONFIRMED": ("HELD",),
        "RELEASED": ("HELD", "CONFIRMED"),
        "RECEIVED": ("CONFIRMED",),
    }
    if hold["status"] not in allowed[target]:
        raise APIError("conflict", "Transición de retención inválida.", 409)
    row = update(conn, "holds", identifier, {"status": target})
    g.actor = {
        "id": None,
        "tenant_id": str(req["tenant_id"]),
        "region_id": str(hold["region_id"]),
    }
    emit(conn, "CAPACITY_" + target, req["id"], req["tenant_id"])
    received = conn.execute(
        "SELECT count(*) AS n FROM holds WHERE request_id=%s AND status='RECEIVED'",
        (req["id"],),
    ).fetchone()["n"]
    state = "CLOSED" if received == req["quantity"] else "IN_PROGRESS"
    if target == "RELEASED":
        active = conn.execute(
            "SELECT 1 FROM holds WHERE request_id=%s AND status<>'RELEASED'",
            (req["id"],),
        ).fetchone()
        state = "IN_PROGRESS" if active else "OPEN"
    if state != req["status"]:
        update(
            conn,
            "requests",
            str(req["id"]),
            {"status": state, "version": req["version"] + 1},
        )
        emit(
            conn,
            "REQUEST_" + state,
            req["id"],
            req["tenant_id"],
            targets=("auditoria", "alertas") if state == "CLOSED" else ("auditoria",),
        )
        if state == "CLOSED" and req["kind"] == "ORGAN":
            update(
                conn,
                "recipients",
                str(person["id"]),
                {"status": "CLOSED", "version": person["version"] + 1},
            )
    return row


def snapshot(conn, identifier):
    row = get(conn, "requests", identifier)
    own(row["tenant_id"])
    person = get(conn, "recipients", str(row["recipient_id"]))
    row["recipient"] = {
        k: person[k]
        for k in ("id", "kind", "blood_group", "organ_type", "status", "version")
    }
    return row


def register(app):
    @endpoint(
        app,
        "/api/v1/recipients",
        "POST",
        model=RecipientCreate,
        roles=("MEDICAL",),
        status=201,
        summary="Expediente diferenciado de sangre u órgano",
    )
    def recipient_create(data):
        if (data["kind"] == "BLOOD" and data["organ_type"] is not None) or (
            data["kind"] == "ORGAN" and data["organ_type"] is None
        ):
            raise invalid(
                "Selecciona un órgano si el recurso es Órgano; para Sangre deja el órgano vacío.",
                "kind",
                "organ_type",
                code="organ_kind",
            )

        def work(conn):
            row = insert(
                conn,
                "recipients",
                dict(id=str(uuid4()), tenant_id=g.actor["tenant_id"], **data),
            )
            emit(conn, "RECIPIENT_CREATED", row["id"], row["tenant_id"])
            return row

        return atomic("recipient_create", data, work)

    @endpoint(
        app,
        "/api/v1/recipients",
        roles=("MEDICAL", "OPERATOR"),
        paginated=True,
        query=("q", "kind"),
        summary="Expedientes de la propia institución",
    )
    def recipients():
        with transaction() as conn:
            columns = (
                "recipients.*, NOT EXISTS(SELECT 1 FROM requests r WHERE r.recipient_id=recipients.id) AS can_edit"
                if g.actor["role"] == "MEDICAL"
                else "id,tenant_id,folio,kind,status,version"
            )
            return listing(
                conn,
                "recipients",
                "tenant_id=%s",
                (g.actor["tenant_id"],),
                order="folio,id",
                columns=columns,
                filters={
                    "q": ("folio", "display_name")
                    if g.actor["role"] == "MEDICAL"
                    else ("folio",),
                    "kind": ("kind", ("BLOOD", "ORGAN")),
                },
            )

    @endpoint(
        app,
        "/api/v1/recipients/<identifier>",
        roles=("MEDICAL",),
        summary="Consultar expediente clínico autorizado",
    )
    def recipient_detail(identifier):
        with transaction() as conn:
            row = get(conn, "recipients", identifier)
            own(row["tenant_id"])
            row["can_edit"] = not conn.execute(
                "SELECT 1 FROM requests WHERE recipient_id=%s LIMIT 1", (identifier,)
            ).fetchone()
            row["decisions"] = history(conn, identifier)
            return row

    @endpoint(
        app,
        "/api/v1/requests",
        "POST",
        model=RequestCreate,
        roles=("MEDICAL",),
        status=201,
        summary="Solicitud humana de recursos",
    )
    def request_create(data):
        def work(conn):
            person = get(conn, "recipients", data["recipient_id"], True)
            own(person["tenant_id"])
            if person["status"] != "ACTIVE":
                raise APIError("conflict", "Receptor inactivo.", 409)
            if person["kind"] == "ORGAN":
                if data["quantity"] != 1:
                    raise invalid(
                        "Una solicitud de órgano debe indicar una unidad.", "quantity"
                    )
                if data["component"] != person["organ_type"]:
                    raise invalid(
                        "Selecciona el mismo órgano registrado en el expediente del receptor.",
                        "component",
                    )
            row = insert(
                conn,
                "requests",
                dict(
                    id=str(uuid4()),
                    tenant_id=g.actor["tenant_id"],
                    kind=person["kind"],
                    **data,
                ),
            )
            emit(
                conn,
                "REQUEST_CREATED",
                row["id"],
                row["tenant_id"],
                targets=("auditoria", "alertas"),
            )
            return row

        return atomic("request_create", data, work)

    @endpoint(
        app,
        "/api/v1/requests",
        roles=("MEDICAL", "OPERATOR"),
        paginated=True,
        query=("kind", "status"),
        summary="Solicitudes institucionales y cobertura",
    )
    def requests_list():
        with transaction() as conn:
            return listing(
                conn,
                "requests",
                "tenant_id=%s",
                (g.actor["tenant_id"],),
                columns="requests.*, (status='OPEN' AND NOT EXISTS(SELECT 1 FROM holds h WHERE h.request_id=requests.id)) AS can_edit",
                filters={
                    "kind": ("kind", ("BLOOD", "ORGAN")),
                    "status": (
                        "status",
                        ("OPEN", "IN_PROGRESS", "CLOSED", "CANCELLED"),
                    ),
                },
            )

    @endpoint(
        app,
        "/api/v1/requests/<identifier>",
        roles=("MEDICAL", "OPERATOR"),
        summary="Solicitud y reservas pendientes/confirmadas",
    )
    def request_detail(identifier):
        with transaction() as conn:
            row = snapshot(conn, identifier)
            row["can_edit"] = (
                row["status"] == "OPEN"
                and not conn.execute(
                    "SELECT 1 FROM holds WHERE request_id=%s LIMIT 1", (identifier,)
                ).fetchone()
            )
            row["decisions"] = history(conn, identifier)
            row["coverage"] = conn.execute(
                "SELECT status,count(*) AS quantity FROM holds WHERE request_id=%s GROUP BY status",
                (identifier,),
            ).fetchall()
            return row

    @endpoint(
        app,
        "/api/v1/requests/<identifier>/cancel",
        "POST",
        model=Cancel,
        roles=("MEDICAL",),
        summary="Cancelar únicamente sin reservas pendientes o físicas",
    )
    def request_cancel(identifier, data):
        def work(conn):
            req = get(conn, "requests", identifier, True)
            own(req["tenant_id"])
            if req["version"] != data["version"] or req["status"] not in (
                "OPEN",
                "IN_PROGRESS",
            ):
                raise APIError("conflict", "Solicitud obsoleta o cerrada.", 409)
            active = conn.execute(
                "SELECT 1 FROM holds WHERE request_id=%s AND status<>'RELEASED'",
                (identifier,),
            ).fetchone()
            if active:
                raise APIError(
                    "pending_reservations",
                    "Cancela primero las reservas que puedan liberarse; hay coordinación pendiente o recepción.",
                    409,
                )
            row = update(
                conn,
                "requests",
                identifier,
                {"status": "CANCELLED", "version": req["version"] + 1},
            )
            record(
                conn, identifier, req["tenant_id"], "REQUEST_CANCELLED", data["reason"]
            )
            emit(conn, "REQUEST_CANCELLED", identifier, req["tenant_id"])
            return row

        return atomic("request_cancel:" + identifier, data, work)

    @endpoint(
        app,
        "/internal/v1/requests/<identifier>",
        internal=("compatibilidad", "inventario"),
        roles=("MEDICAL",),
        summary="Instantánea mínima para compatibilidad y reserva",
    )
    def request_internal(identifier):
        with transaction() as conn:
            return snapshot(conn, identifier)

    @endpoint(
        app,
        "/internal/v1/holds",
        "POST",
        model=HoldCreate,
        internal=("inventario",),
        roles=("MEDICAL",),
        summary="Retener capacidad; serializar solicitud y receptor",
    )
    def hold_create(data):
        with transaction() as conn:
            req = get(conn, "requests", data["request_id"], True)
            own(req["tenant_id"])
            person = get(conn, "recipients", str(req["recipient_id"]), True)
            old = conn.execute(
                "SELECT * FROM holds WHERE operation_id=%s", (data["operation_id"],)
            ).fetchone()
            if old:
                if (
                    str(old["resource_id"]) != data["resource_id"]
                    or str(old["request_id"]) != data["request_id"]
                ):
                    raise APIError(
                        "operation_conflict", "Operación vinculada a otra reserva.", 409
                    )
                return old
            count = conn.execute(
                "SELECT count(*) AS n FROM holds WHERE request_id=%s AND status<>'RELEASED'",
                (req["id"],),
            ).fetchone()["n"]
            if (
                req["status"] not in ("OPEN", "IN_PROGRESS")
                or person["status"] != "ACTIVE"
                or count >= req["quantity"]
            ):
                raise APIError(
                    "request_covered",
                    "Solicitud cerrada, receptor inactivo o cantidad cubierta.",
                    409,
                )
            if (
                req["version"] != data["request_version"]
                or person["version"] != data["recipient_version"]
            ):
                raise APIError("stale_version", "Solicitud o receptor cambiaron.", 409)
            row = insert(
                conn,
                "holds",
                dict(
                    id=str(uuid4()),
                    request_id=req["id"],
                    recipient_id=person["id"],
                    operation_id=data["operation_id"],
                    resource_id=data["resource_id"],
                    kind=req["kind"],
                    request_version=req["version"],
                    region_id=g.actor["region_id"],
                ),
            )
            emit(conn, "CAPACITY_HELD", req["id"], req["tenant_id"])
            return row

    @endpoint(
        app,
        "/internal/v1/holds/<identifier>",
        "POST",
        model=HoldAction,
        internal=("inventario",),
        delegate=False,
        summary="Confirmar, liberar o recibir retención de forma idempotente",
    )
    def hold_action(identifier, data):
        with transaction() as conn:
            return apply_hold(conn, identifier, data)

    @endpoint(
        app,
        "/internal/v1/holds-by-operation/<identifier>",
        internal=("inventario",),
        delegate=False,
        summary="Localizar retención tras perder una respuesta",
    )
    def hold_lookup(identifier):
        from redhouse.models import validate_id

        validate_id(identifier)
        with transaction() as conn:
            return {
                "hold": conn.execute(
                    "SELECT * FROM holds WHERE operation_id=%s", (identifier,)
                ).fetchone()
            }

    from redhouse.event_model import Event

    @endpoint(
        app,
        "/internal/v1/events",
        "POST",
        model=Event,
        internal=("inventario",),
        delegate=False,
        summary="Recibir recepción o liberación sin duplicados",
    )
    def recipient_events(data):
        if data["source"] != g.caller:
            raise APIError("forbidden", "Fuente de evento incorrecta.", 403)
        with transaction() as conn:
            if not consume(conn, data):
                return {"duplicate": True}
            metadata = data["metadata"]
            return apply_hold(
                conn,
                metadata["hold_id"],
                {
                    "operation_id": metadata["operation_id"],
                    "action": metadata["hold_action"],
                },
            )
