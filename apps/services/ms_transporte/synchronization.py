"""Comandos offline no clínicos; resultado durable con autorización actual."""

import hashlib
import json
from datetime import datetime, timezone, timedelta
from typing import Annotated, Literal

from flask import g, request
from pydantic import Field

from redhouse.api import endpoint
from redhouse.db import transaction, get, insert
from redhouse.errors import APIError
from redhouse.events import emit
from redhouse.extension_contracts import schema, version
from redhouse.models import ID, Model, Reason, Text, utc_date
from .routes import shipment_access


class Observation(Model):
    command: Literal["TRANSPORT_OBSERVATION"]
    reason: Reason


class Command(Model):
    id: ID
    shipment_id: ID
    device_id: ID
    expected_version: Annotated[int, Field(ge=1)]
    captured_at: Text
    body: Observation


class Result(Model):
    command_id: ID
    shipment_id: ID
    cursor: int
    status: Literal["RECORDED"]
    shipment_version: int


class Changes(Model):
    items: list[Result]
    cursor: int
    has_more: bool


class ShipmentChange(Model):
    id: ID
    cursor: int
    state: Text
    received_at: Text


class ShipmentChanges(Model):
    items: list[ShipmentChange]
    cursor: int
    version: int
    active: bool
    has_more: bool


def authorized(conn, shipment_id, device_id):
    row = get(conn, "shipments", shipment_id, True)
    shipment_access(row)
    device = get(conn, "tracking_devices", device_id)
    if (
        str(device["user_id"]) != g.actor["id"]
        or str(device["tenant_id"]) != g.actor["tenant_id"]
        or not device["active"]
        or not device["user_active"]
        or not device["institution_active"]
        or device["expires_at"] <= datetime.now(timezone.utc)
    ):
        raise APIError(
            "forbidden", "Dispositivo no autorizado para esta identidad.", 403
        )
    return row


def install(app):
    @endpoint(
        app,
        "/api/v1/sync/shipments/<identifier>/changes",
        roles=("TRANSPORT", "OPERATOR", "MEDICAL", "COORDINATOR"),
        query=("cursor",),
        result=schema(ShipmentChanges),
    )
    def sync_shipment_changes(identifier):
        try:
            cursor = int(request.args.get("cursor", 0))
            if cursor < 0:
                raise ValueError()
        except ValueError:
            raise APIError("validation", "Cursor inválido.", 422) from None
        with transaction() as conn:
            row = get(conn, "shipments", identifier, True)
            shipment_access(row)
            if cursor > row["sequence"]:
                raise APIError(
                    "resync_required",
                    "Cursor posterior al historial; consulta el estado actual.",
                    409,
                )
            changes = conn.execute(
                "SELECT id,sequence AS cursor,state,created_at AS received_at FROM transitions "
                "WHERE shipment_id=%s AND sequence>%s ORDER BY sequence LIMIT 101",
                (identifier, cursor),
            ).fetchall()
            return {
                "items": changes[:100],
                "cursor": changes[99]["cursor"]
                if len(changes) > 100
                else row["sequence"],
                "has_more": len(changes) > 100,
                "version": row["version"],
                "active": row["status"] not in ("ACCEPTED", "CANCELLED", "REJECTED"),
            }

    @endpoint(
        app,
        "/api/v1/sync/commands",
        "POST",
        model=Command,
        roles=("TRANSPORT",),
        result=schema(Result),
        status=201,
    )
    def sync_command(data):
        fingerprint = hashlib.sha256(
            json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        with transaction() as conn:
            conn.execute(
                "SELECT pg_advisory_xact_lock(hashtextextended(%s, 72))",
                (g.actor["id"],),
            )
            shipment = authorized(conn, data["shipment_id"], data["device_id"])
            old = conn.execute(
                "SELECT * FROM sync_commands WHERE id=%s", (data["id"],)
            ).fetchone()
            if old:
                if (
                    str(old["user_id"]) != g.actor["id"]
                    or str(old["tenant_id"]) != g.actor["tenant_id"]
                ):
                    raise APIError("forbidden", "Comando de otra identidad.", 403)
                if old["fingerprint"] != fingerprint:
                    raise APIError(
                        "idempotency_conflict",
                        "Identificador repetido con otro contenido.",
                        409,
                    )
                return old["result"]
            version(shipment, data["expected_version"])
            captured = utc_date(data["captured_at"])
            if (
                not datetime.now(timezone.utc) - timedelta(days=7)
                <= captured
                <= datetime.now(timezone.utc)
            ):
                raise APIError(
                    "validation",
                    "Captura fuera de la ventana offline de siete días.",
                    422,
                )
            if shipment["status"] not in (
                "PREPARED",
                "COLLECTED",
                "IN_TRANSIT",
                "DELIVERED",
            ):
                raise APIError(
                    "conflict", "Traslado fuera del periodo de captura.", 409
                )
            cursor = conn.execute(
                "SELECT coalesce(max(cursor),0)+1 AS n FROM sync_commands WHERE user_id=%s",
                (g.actor["id"],),
            ).fetchone()["n"]
            result = {
                "command_id": data["id"],
                "shipment_id": data["shipment_id"],
                "cursor": cursor,
                "status": "RECORDED",
                "shipment_version": shipment["version"],
            }
            insert(
                conn,
                "sync_commands",
                dict(
                    data,
                    tenant_id=g.actor["tenant_id"],
                    user_id=g.actor["id"],
                    cursor=cursor,
                    fingerprint=fingerprint,
                    result=result,
                    captured_at=captured,
                ),
            )
            emit(
                conn,
                "TRANSPORT_OBSERVATION_RECORDED",
                shipment["id"],
                shipment["origin_id"],
                metadata={"command_id": data["id"]},
            )
            return result

    @endpoint(
        app,
        "/api/v1/sync/commands/<identifier>",
        roles=("TRANSPORT",),
        result=schema(Result),
    )
    def sync_result(identifier):
        with transaction() as conn:
            row = get(conn, "sync_commands", identifier)
            if (
                str(row["user_id"]) != g.actor["id"]
                or str(row["tenant_id"]) != g.actor["tenant_id"]
            ):
                raise APIError("forbidden", "Comando de otra identidad.", 403)
            authorized(conn, str(row["shipment_id"]), str(row["device_id"]))
            return row["result"]

    @endpoint(
        app,
        "/api/v1/sync/changes",
        roles=("TRANSPORT",),
        query=("cursor",),
        result=schema(Changes),
    )
    def sync_changes():
        try:
            cursor = int(request.args.get("cursor", 0))
            if cursor < 0:
                raise ValueError()
        except ValueError:
            raise APIError("validation", "Cursor inválido.", 422) from None
        with transaction() as conn:
            # Se filtra antes de paginar. Un cambio de asignación o baja de dispositivo
            # retira el acceso a resultados anteriores, incluso con un cursor válido.
            rows = conn.execute(
                "SELECT c.* FROM sync_commands c JOIN shipments s ON s.id=c.shipment_id "
                "JOIN tracking_devices d ON d.id=c.device_id WHERE c.user_id=%s AND c.tenant_id=%s "
                "AND s.transport_user_id=%s AND d.user_id=%s AND d.active AND d.user_active AND d.institution_active "
                "AND d.expires_at>now() AND c.cursor>%s ORDER BY c.cursor LIMIT 101",
                (
                    g.actor["id"],
                    g.actor["tenant_id"],
                    g.actor["id"],
                    g.actor["id"],
                    cursor,
                ),
            ).fetchall()
            return {
                "items": [r["result"] for r in rows[:100]],
                "cursor": rows[min(len(rows), 100) - 1]["cursor"] if rows else cursor,
                "has_more": len(rows) > 100,
            }
