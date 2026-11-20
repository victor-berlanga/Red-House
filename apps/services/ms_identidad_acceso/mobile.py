"""Registro del teléfono propio: nunca permite elegir usuario, tenant o credencial autónoma.

Solo DONOR y TRANSPORT (perfiles de la aplicación móvil); sus sesiones nacen con
X-RedHouse-Client: mobile y el resto de perfiles no puede iniciar sesión allí."""

from datetime import datetime, timezone, timedelta
from typing import Literal
from flask import g
from redhouse.api import endpoint, atomic
from redhouse.db import transaction, get, insert, update
from redhouse.errors import APIError
from redhouse.events import emit
from redhouse.extension_contracts import schema, version
from redhouse.models import Model, ID, Text
from redhouse.security import redis_call, key
from .devices import Device, DeviceChange, public


class MobileDevice(Model):
    id: ID
    source: Literal["ANDROID", "IOS"]
    label: Text


def install(app):
    @endpoint(
        app,
        "/api/v1/mobile/devices",
        "POST",
        model=MobileDevice,
        roles=("DONOR", "TRANSPORT"),
        result=schema(Device),
        summary="Registrar teléfono propio, sin credencial de emisor autónomo",
    )
    def mobile_device_register(data):
        def work(conn):
            conn.execute(
                "SELECT pg_advisory_xact_lock(hashtextextended(%s,91))",
                (g.actor["id"],),
            )
            old = conn.execute(
                "SELECT * FROM devices WHERE id=%s FOR UPDATE", (data["id"],)
            ).fetchone()
            if old:
                if (
                    str(old["user_id"]) != g.actor["id"]
                    or str(old["tenant_id"]) != g.actor["tenant_id"]
                ):
                    raise APIError("forbidden", "Dispositivo de otra identidad.", 403)
                if (
                    not old["active"]
                    or old["expires_at"] <= datetime.now(timezone.utc)
                    or old["source"] != data["source"]
                ):
                    raise APIError(
                        "device_revoked",
                        "Dispositivo revocado, vencido o de otra plataforma.",
                        403,
                    )
                return public(old)
            count = conn.execute(
                "SELECT count(*) AS n FROM devices WHERE user_id=%s AND active AND expires_at>now()",
                (g.actor["id"],),
            ).fetchone()["n"]
            if count >= 10:
                raise APIError(
                    "device_limit",
                    "Revoca un dispositivo anterior antes de registrar otro.",
                    409,
                )
            row = insert(
                conn,
                "devices",
                dict(
                    data,
                    user_id=g.actor["id"],
                    tenant_id=g.actor["tenant_id"],
                    token_hash="UNISSUED",
                    expires_at=datetime.now(timezone.utc) + timedelta(days=30),
                ),
            )
            emit(conn, "DEVICE_REGISTERED", row["id"], row["tenant_id"])
            return public(row)

        with transaction() as conn:
            return work(conn)

    @endpoint(
        app,
        "/api/v1/mobile/devices/<identifier>/revoke",
        "POST",
        model=DeviceChange,
        roles=("DONOR", "TRANSPORT"),
        result=schema(Device),
    )
    def mobile_device_revoke(identifier, data):
        with transaction() as conn:
            row = get(conn, "devices", identifier, True)
            if (
                str(row["user_id"]) != g.actor["id"]
                or str(row["tenant_id"]) != g.actor["tenant_id"]
            ):
                raise APIError("forbidden", "Dispositivo ajeno.", 403)
            version(row, data["version"])
            redis_call(lambda r: r.delete(key("device:" + identifier)))
            row = update(
                conn,
                "devices",
                identifier,
                {"active": False, "version": row["version"] + 1},
            )
            emit(conn, "DEVICE_REVOKED", identifier, row["tenant_id"])
            return public(row)
