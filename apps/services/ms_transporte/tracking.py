"""Ingreso durable, autorización vigente y recuperación acotada del rastreo."""

import hashlib
import hmac
import json
import secrets
from datetime import datetime, timezone, timedelta
from typing import Annotated
from uuid import uuid4

from flask import current_app, g, request
from pydantic import Field

from redhouse.api import endpoint, atomic, listing
from redhouse.codec import plain
from redhouse.db import transaction, get, insert, update
from redhouse.errors import APIError
from redhouse.events import emit, queue
from redhouse.extension_contracts import schema, version
from redhouse.models import ID, Confirm, Model, Text, utc_date, validate_id
from redhouse.security import authenticate, key, redis_call
from .routes import shipment_access
from .tracking_contracts import Position, StoredPosition

ROLES = ("COORDINATOR", "TRANSPORT", "OPERATOR", "MEDICAL")
ACTIVE = ("PREPARED", "COLLECTED", "IN_TRANSIT", "INCIDENT", "DELIVERED")


class AssignmentCreate(Confirm):
    device_id: ID
    starts_at: Text
    ends_at: Text
    version: Annotated[int, Field(ge=1)]


class AssignmentChange(Confirm):
    version: Annotated[int, Field(ge=1)]


class Assignment(Model):
    id: ID
    shipment_id: ID
    device_id: ID
    responsible_id: ID
    starts_at: Text
    ends_at: Text
    active: bool
    version: int
    actor_id: ID
    created_at: Text


def authorize(credential_kind, credential):
    g.tracking_scope = None
    if credential_kind == "browser":
        digest = hashlib.sha256(credential.encode()).hexdigest()
        raw = redis_call(lambda r: r.get(key("tracking:ticket:" + digest)))
        if not raw:
            raise APIError("unauthorized", "Acceso de rastreo vencido.", 401)
        ticket = json.loads(raw)
        g.tracking_scope = ticket["shipment_id"]
        request.environ["HTTP_AUTHORIZATION"] = "Bearer " + ticket["token"]
        return authenticate(ROLES)
    if credential_kind == "user":
        request.environ["HTTP_AUTHORIZATION"] = "Bearer " + credential
        # Flask Headers reads the same request environ; never write the token to logs.
        return authenticate(ROLES)
    try:
        identifier = validate_id(credential.split(".")[0])
    except (APIError, AttributeError):
        raise APIError(
            "unauthorized", "Credencial de dispositivo inválida.", 401
        ) from None
    digest = hashlib.sha256(credential.encode()).hexdigest()
    permitted = redis_call(lambda r: r.get(key("device:" + identifier)))
    with transaction() as conn:
        device = conn.execute(
            "SELECT * FROM tracking_devices WHERE id=%s", (identifier,)
        ).fetchone()
        if not device:
            raise APIError("unauthorized", "Credencial de dispositivo inválida.", 401)
        if (
            not permitted
            or not hmac.compare_digest(permitted, digest)
            or not hmac.compare_digest(device["token_hash"], digest)
            or not device["active"]
            or not device["user_active"]
            or not device["institution_active"]
            or device["user_role"] != "TRANSPORT"
            or device["expires_at"] <= datetime.now(timezone.utc)
        ):
            raise APIError("unauthorized", "Dispositivo revocado o vencido.", 401)
    return plain(device)


def access(conn, shipment_id, *, live=False, lock=False):
    if getattr(g, "tracking_scope", None) not in (None, shipment_id):
        raise APIError("forbidden", "Acceso limitado al traslado autorizado.", 403)
    row = get(conn, "shipments", shipment_id, lock)
    shipment_access(row)
    if live and row["status"] not in ACTIVE:
        raise APIError("tracking_closed", "El traslado no admite rastreo activo.", 403)
    if (
        live
        and not conn.execute(
            "SELECT 1 FROM tracking_assignments a JOIN tracking_devices d ON d.id=a.device_id "
            "WHERE a.shipment_id=%s AND a.responsible_id=%s AND a.active AND a.starts_at<=now() AND a.ends_at>now() "
            "AND d.active AND d.user_active AND d.institution_active AND d.user_role='TRANSPORT' AND d.expires_at>now()",
            (shipment_id, row["transport_user_id"]),
        ).fetchone()
    ):
        raise APIError(
            "tracking_closed",
            "El traslado ya no tiene asignación de rastreo vigente.",
            403,
        )
    return row


def publish(data, credential_kind, credential):
    if credential_kind == "browser":
        raise APIError("forbidden", "El acceso del mapa es de solo lectura.", 403)
    data = Position.model_validate(data).model_dump()
    # Mantener la huella histórica para emisores que no envían el campo opcional.
    if not data["simulated"]:
        data.pop("simulated")
    actor = authorize(credential_kind, credential)
    now = datetime.now(timezone.utc)
    captured = utc_date(data["captured_at"], "captured_at")
    if captured > now + timedelta(seconds=10) or captured < now - timedelta(days=7):
        raise APIError(
            "capture_time",
            "Captura fuera de la ventana de siete días o en el futuro.",
            422,
        )
    fingerprint = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
    with transaction() as conn:
        # Serializa cursores por traslado hasta el commit; no hay huecos de commit entre réplicas.
        shipment = get(conn, "shipments", data["shipment_id"], True)
        device = get(conn, "tracking_devices", data["device_id"])
        if credential_kind == "device":
            if actor["id"] != data["device_id"]:
                raise APIError("forbidden", "Emisor ajeno.", 403)
            g.actor = {
                "id": actor["user_id"],
                "tenant_id": actor["tenant_id"],
                "region_id": str(shipment["region_id"]),
                "role": "TRANSPORT",
            }
        elif g.actor["role"] != "TRANSPORT" or str(device["user_id"]) != actor["id"]:
            raise APIError(
                "forbidden", "Solo el transportista vinculado puede publicar.", 403
            )
        shipment_access(shipment)
        assignment = conn.execute(
            "SELECT * FROM tracking_assignments WHERE device_id=%s AND shipment_id=%s AND active "
            "AND starts_at<=now() AND ends_at>now()",
            (data["device_id"], data["shipment_id"]),
        ).fetchone()
        if (
            not assignment
            or shipment["status"] not in ACTIVE
            or not device["active"]
            or not device["user_active"]
            or not device["institution_active"]
            or device["user_role"] != "TRANSPORT"
            or device["expires_at"] <= now
            or device["source"] != data["source"]
            or str(assignment["responsible_id"]) != str(shipment["transport_user_id"])
            or str(device["user_id"]) != str(assignment["responsible_id"])
            or not assignment["starts_at"] <= captured < assignment["ends_at"]
        ):
            raise APIError(
                "unassigned_device",
                "No existe asignación vigente para esta captura.",
                403,
            )
        old = conn.execute(
            "SELECT * FROM tracking_points WHERE id=%s OR (assignment_id=%s AND sequence=%s)",
            (data["event_id"], assignment["id"], data["sequence"]),
        ).fetchone()
        if old:
            if old["fingerprint"] != fingerprint:
                raise APIError(
                    "event_conflict",
                    "Evento o secuencia reutilizados con otro contenido.",
                    409,
                )
            return stored(old)
        cursor = conn.execute(
            "SELECT coalesce(max(cursor),0)+1 AS n FROM tracking_points WHERE shipment_id=%s",
            (shipment["id"],),
        ).fetchone()["n"]
        row = insert(
            conn,
            "tracking_points",
            {
                "id": data["event_id"],
                "shipment_id": data["shipment_id"],
                "assignment_id": assignment["id"],
                "device_id": data["device_id"],
                "cursor": cursor,
                "sequence": data["sequence"],
                "captured_at": captured,
                "fingerprint": fingerprint,
                "position": data,
            },
        )
        event = emit(
            conn, "TRACKING_POSITION_PERSISTED", shipment["id"], shipment["origin_id"]
        )
        # Solo la proyección de Transporte contiene geometría; auditoría general conserva IDs.
        projection = dict(
            event, event_id=str(uuid4()), metadata={"position": stored(row)}
        )
        queue(conn, projection, "mongodb")
    result = stored(row)
    # El ACK se emite después del commit SQL. Redis puede reconstruirse del historial.
    cache_latest(data["shipment_id"])
    redis_call(
        lambda r: r.publish(key("tracking:channel:" + data["shipment_id"]), str(cursor))
    )
    return result


def stored(row):
    return dict(
        row["position"],
        cursor=row["cursor"],
        received_at=row["received_at"].isoformat(),
    )


def cache_latest(shipment_id):
    with transaction() as conn:
        row = conn.execute(
            "SELECT * FROM tracking_points WHERE shipment_id=%s "
            "ORDER BY captured_at DESC,cursor DESC LIMIT 1",
            (shipment_id,),
        ).fetchone()
    if row:
        # CAS por fecha/cursor: un escritor lento nunca hace retroceder el caché.
        script = """local old=redis.call('GET',KEYS[1]);
        if old then local v=cjson.decode(old); if v.time>tonumber(ARGV[1]) or
          (v.time==tonumber(ARGV[1]) and v.cursor>tonumber(ARGV[2])) then return 0 end end
        redis.call('SET',KEYS[1],ARGV[3],'EX',300); return 1"""
        redis_call(
            lambda r: r.eval(
                script,
                1,
                key("tracking:last:" + shipment_id),
                row["captured_at"].timestamp(),
                row["cursor"],
                json.dumps(
                    {
                        "time": row["captured_at"].timestamp(),
                        "cursor": row["cursor"],
                        "position": stored(row),
                    }
                ),
            )
        )


def snapshot(shipment_id, cursor=None, live=False):
    with transaction() as conn:
        # Read committed bajo bloqueo comparte corte con publish, incluso entre réplicas.
        shipment = access(conn, shipment_id, live=live, lock=True)
        last = conn.execute(
            "SELECT * FROM tracking_points WHERE shipment_id=%s ORDER BY captured_at DESC,cursor DESC LIMIT 1",
            (shipment_id,),
        ).fetchone()
        head = conn.execute(
            "SELECT coalesce(max(cursor),0) AS n FROM tracking_points WHERE shipment_id=%s",
            (shipment_id,),
        ).fetchone()["n"]
        minimum = max(0, head - current_app.config.get("TRACKING_REPLAY_WINDOW", 10000))
        if cursor is not None and (cursor < minimum or cursor > head):
            raise APIError(
                "resync_required",
                "Cursor fuera de ventana; solicita una instantánea nueva.",
                409,
            )
        rows = (
            []
            if cursor is None or cursor == head
            else conn.execute(
                "SELECT * FROM tracking_points WHERE shipment_id=%s AND cursor>%s AND cursor<=%s ORDER BY cursor LIMIT 100",
                (shipment_id, cursor, head),
            ).fetchall()
        )
    age = (
        (datetime.now(timezone.utc) - last["captured_at"]).total_seconds()
        if last
        else None
    )
    state = (
        "FINALIZED"
        if shipment["status"] not in ACTIVE
        else (
            "NO_DATA"
            if last is None
            else "NO_FIX"
            if not last["position"]["fix_valid"]
            else "STALE"
            if age > current_app.config.get("TRACKING_STALE_SECONDS", 30)
            else "LIVE"
        )
    )
    return {
        "shipment_id": shipment_id,
        "cursor": rows[-1]["cursor"] if rows else (head if cursor is None else cursor),
        "head": head,
        "position": stored(last) if last else None,
        "events": [stored(r) for r in rows],
        "state": state,
    }


class Snapshot(Model):
    shipment_id: ID
    cursor: int
    head: int
    position: StoredPosition | None
    events: list[StoredPosition]
    state: str


class TrackingMetrics(Model):
    shipment_id: ID
    persisted_points: int
    received_last_minute: int
    last_received_at: Text | None
    capture_to_receive_p95_ms: float | None
    mongo_pending_events: int
    active_connections_global: int


class BrowserTicket(Model):
    credential: Text
    expires_in: int


def install(app):
    @endpoint(app, "/api/v1/shipments/<identifier>/tracking/devices", roles=("COORDINATOR",), result={
        "type": "object", "required": ["items"], "properties": {"items": {"type": "array", "items": {
            "type": "object", "required": ["id", "label", "source"], "additionalProperties": False,
            "properties": {"id": {"type": "string", "format": "uuid"}, "label": {"type": "string"}, "source": {"type": "string"}}}}}})
    def tracking_devices_for_shipment(identifier):
        with transaction() as conn:
            shipment = access(conn, identifier)
            return {"items": conn.execute("SELECT id,label,source FROM tracking_devices WHERE user_id=%s AND tenant_id=%s AND active AND user_active AND institution_active AND user_role='TRANSPORT' AND expires_at>now() ORDER BY label,id",
                (shipment["transport_user_id"], shipment["origin_id"])).fetchall()}

    @endpoint(
        app,
        "/api/v1/shipments/<identifier>/tracking/ticket",
        "POST",
        roles=ROLES,
        result=schema(BrowserTicket),
    )
    def tracking_ticket(identifier):
        with transaction() as conn:
            access(conn, identifier, live=True)
        credential = secrets.token_urlsafe(48)
        digest = hashlib.sha256(credential.encode()).hexdigest()
        token = request.headers.get("Authorization", "").removeprefix("Bearer ")
        redis_call(
            lambda r: r.set(
                key("tracking:ticket:" + digest),
                json.dumps(
                    {
                        "token": token,
                        "shipment_id": identifier,
                    }
                ),
                ex=90,
            )
        )
        return {"credential": credential, "expires_in": 90}

    @endpoint(
        app,
        "/api/v1/shipments/<identifier>/tracking/metrics",
        roles=ROLES,
        result=schema(TrackingMetrics),
    )
    def tracking_metrics(identifier):
        with transaction() as conn:
            access(conn, identifier)
            metrics = conn.execute(
                "SELECT count(*) AS persisted_points,count(*) FILTER(WHERE received_at>now()-interval '1 minute') AS received_last_minute,"
                "max(received_at) AS last_received_at,percentile_cont(0.95) WITHIN GROUP(ORDER BY extract(epoch FROM received_at-captured_at)*1000) AS capture_to_receive_p95_ms "
                "FROM tracking_points WHERE shipment_id=%s",
                (identifier,),
            ).fetchone()
            metrics["mongo_pending_events"] = conn.execute(
                "SELECT count(*) AS n FROM outbox WHERE target='mongodb' AND delivered_at IS NULL AND event->'metadata'->'position'->>'shipment_id'=%s",
                (identifier,),
            ).fetchone()["n"]
        metrics["active_connections_global"] = redis_call(
            lambda r: r.zcard(key("tracking:connections:global"))
        )
        return dict(metrics, shipment_id=identifier)

    @endpoint(
        app,
        "/api/v1/shipments/<identifier>/tracking/assignments",
        "POST",
        model=AssignmentCreate,
        roles=("COORDINATOR",),
        result=schema(Assignment),
        status=201,
    )
    def tracking_assign(identifier, data):
        def work(conn):
            shipment = access(conn, identifier, lock=True)
            version(shipment, data["version"])
            device = get(conn, "tracking_devices", data["device_id"])
            starts, ends = utc_date(data["starts_at"]), utc_date(data["ends_at"])
            if (
                shipment["status"] not in ("PLANNED", *ACTIVE)
                or not device["active"]
                or not device["user_active"]
                or not device["institution_active"]
                or device["user_role"] != "TRANSPORT"
                or str(device["user_id"]) != str(shipment["transport_user_id"])
                or str(device["tenant_id"]) != str(shipment["origin_id"])
                or not starts < ends <= device["expires_at"]
                or ends <= datetime.now(timezone.utc)
                or ends - starts > timedelta(days=7)
            ):
                raise APIError(
                    "invalid_assignment",
                    "Dispositivo, responsable o vigencia incompatibles.",
                    409,
                )
            row = insert(
                conn,
                "tracking_assignments",
                {
                    "id": str(uuid4()),
                    "shipment_id": identifier,
                    "device_id": data["device_id"],
                    "responsible_id": shipment["transport_user_id"],
                    "starts_at": starts,
                    "ends_at": ends,
                    "actor_id": g.actor["id"],
                },
            )
            emit(conn, "TRACKING_ASSIGNED", identifier, shipment["origin_id"])
            return row

        return atomic("tracking_assign:" + identifier, data, work)

    @endpoint(
        app,
        "/api/v1/shipments/<identifier>/tracking/assignments",
        roles=ROLES,
        paginated=True,
        result={
            "type": "object",
            "properties": {
                "items": {"type": "array", "items": schema(Assignment)},
                "page": {"type": "integer"},
                "page_size": {"type": "integer"},
                "total": {"type": "integer"},
            },
        },
        query=("q", "from_at", "until_at", "date_field", "sort"),
    )
    def tracking_assignments(identifier):
        with transaction() as conn:
            access(conn, identifier)
            return listing(
                conn, "tracking_assignments", "shipment_id=%s", (identifier,)
            )

    @endpoint(
        app,
        "/api/v1/tracking/assignments/<identifier>/revoke",
        "POST",
        model=AssignmentChange,
        roles=("COORDINATOR",),
        result=schema(Assignment),
    )
    def tracking_revoke(identifier, data):
        def work(conn):
            assignment = get(conn, "tracking_assignments", identifier)
            shipment = access(conn, str(assignment["shipment_id"]), lock=True)
            assignment = get(conn, "tracking_assignments", identifier, True)
            version(assignment, data["version"])
            row = update(
                conn,
                "tracking_assignments",
                identifier,
                {"active": False, "version": assignment["version"] + 1},
            )
            emit(
                conn,
                "TRACKING_ASSIGNMENT_REVOKED",
                shipment["id"],
                shipment["origin_id"],
            )
            return row

        return atomic("tracking_revoke:" + identifier, data, work)

    @endpoint(
        app,
        "/api/v1/shipments/<identifier>/tracking/snapshot",
        roles=ROLES,
        result=schema(Snapshot),
        query=("cursor",),
    )
    def tracking_snapshot(identifier):
        if set(request.args) - {"cursor"} or len(request.args.getlist("cursor")) > 1:
            raise APIError("validation", "Consulta inválida.", 422)
        try:
            cursor = int(request.args["cursor"]) if "cursor" in request.args else None
            if cursor is not None and cursor < 0:
                raise ValueError()
        except ValueError:
            raise APIError("validation", "Cursor inválido.", 422) from None
        return snapshot(identifier, cursor)

    @endpoint(
        app,
        "/api/v1/shipments/<identifier>/tracking/history",
        roles=ROLES,
        query=("cursor", "through", "limit"),
        result={
            "type": "object",
            "required": ["items", "cursor", "through", "has_more"],
            "properties": {
                "items": {"type": "array", "items": schema(StoredPosition)},
                "cursor": {"type": "integer"},
                "through": {"type": "integer"},
                "has_more": {"type": "boolean"},
            },
        },
    )
    def tracking_history(identifier):
        if set(request.args) - {"cursor", "through", "limit"} or any(
            len(request.args.getlist(k)) != 1 for k in request.args
        ):
            raise APIError("validation", "Consulta histórica inválida.", 422)
        try:
            cursor = int(request.args.get("cursor", "0"))
            limit = int(request.args.get("limit", "100"))
            through = (
                int(request.args["through"]) if "through" in request.args else None
            )
            if (
                cursor < 0
                or not 1 <= limit <= 100
                or (through is not None and through < cursor)
            ):
                raise ValueError()
        except ValueError:
            raise APIError("validation", "Cursor o límite inválidos.", 422) from None
        with transaction() as conn:
            access(conn, identifier, lock=True)
            head = conn.execute(
                "SELECT coalesce(max(cursor),0) AS n FROM tracking_points WHERE shipment_id=%s",
                (identifier,),
            ).fetchone()["n"]
            through = head if through is None else through
            if through > head or cursor > head:
                raise APIError("validation", "Cursor futuro.", 422)
            rows = conn.execute(
                "SELECT * FROM tracking_points WHERE shipment_id=%s AND cursor>%s AND cursor<=%s ORDER BY cursor LIMIT %s",
                (identifier, cursor, through, limit),
            ).fetchall()
            next_cursor = rows[-1]["cursor"] if rows else cursor
            return {
                "items": [stored(r) for r in rows],
                "cursor": next_cursor,
                "through": through,
                "has_more": next_cursor < through,
            }

    from .tracking_socket import install as sockets

    sockets(app)
