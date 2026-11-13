"""Identidad revocable de emisores; Transporte es dueño de sus asignaciones."""

import hashlib
import secrets
from datetime import datetime, timezone, timedelta
from typing import Annotated, Literal

from flask import g
from pydantic import Field

from redhouse.api import endpoint, atomic, listing
from redhouse.db import transaction, get, insert, update
from redhouse.errors import APIError
from redhouse.events import emit
from redhouse.extension_contracts import schema, version
from redhouse.models import ID, Model, Text, Confirm, utc_date
from redhouse.security import own, redis_call, key


class DeviceCreate(Model):
    id: ID
    user_id: ID
    source: Literal["SIMULATOR", "GPS_BRIDGE", "ANDROID", "IOS"]
    label: Text
    expires_at: Text


class DeviceChange(Confirm):
    version: Annotated[int, Field(ge=1)]


class Device(Model):
    id: ID
    tenant_id: ID
    user_id: ID
    source: Literal["SIMULATOR", "GPS_BRIDGE", "ANDROID", "IOS"]
    label: Text
    expires_at: Text
    active: bool
    version: int
    created_at: Text


class Credential(Model):
    device_id: ID
    credential: str
    version: int


def public(row):
    return {k: v for k, v in row.items() if k != "token_hash"}


def install(app):
    from .mobile import install as mobile

    mobile(app)

    @endpoint(
        app,
        "/api/v1/devices",
        "POST",
        model=DeviceCreate,
        roles=("ADMIN",),
        result=schema(Device),
        status=201,
    )
    def device_create(data):
        expires = utc_date(data["expires_at"], "expires_at")
        if (
            not datetime.now(timezone.utc)
            < expires
            <= datetime.now(timezone.utc) + timedelta(days=30)
        ):
            raise APIError(
                "validation", "Vigencia debe estar entre ahora y 30 días.", 422
            )

        def work(conn):
            user = get(conn, "users", data["user_id"])
            own(user["tenant_id"])
            if not user["active"] or user["role"] != "TRANSPORT":
                raise APIError("forbidden", "Se requiere un transportista activo.", 403)
            row = insert(
                conn,
                "devices",
                dict(
                    data,
                    tenant_id=g.actor["tenant_id"],
                    token_hash="UNISSUED",
                    expires_at=expires,
                ),
            )
            emit(conn, "DEVICE_REGISTERED", row["id"], row["tenant_id"])
            return public(row)

        return atomic("device_create", data, work)

    @endpoint(
        app,
        "/api/v1/devices",
        roles=("ADMIN",),
        paginated=True,
        result={
            "type": "object",
            "properties": {
                "items": {"type": "array", "items": schema(Device)},
                "page": {"type": "integer"},
                "page_size": {"type": "integer"},
                "total": {"type": "integer"},
            },
        },
        query=("q", "from_at", "until_at", "date_field", "sort"),
    )
    def device_list():
        with transaction() as conn:
            result = listing(conn, "devices", "tenant_id=%s", (g.actor["tenant_id"],))
            result["items"] = [public(r) for r in result["items"]]
            return result

    @endpoint(
        app, "/api/v1/devices/<identifier>", roles=("ADMIN",), result=schema(Device)
    )
    def device_detail(identifier):
        with transaction() as conn:
            row = get(conn, "devices", identifier)
            own(row["tenant_id"])
            return public(row)

    @endpoint(
        app,
        "/api/v1/devices/<identifier>/credentials",
        "POST",
        model=DeviceChange,
        roles=("ADMIN",),
        result=schema(Credential),
    )
    def device_credentials(identifier, data):
        # Se entrega una sola vez. Ante respuesta perdida se rota usando la nueva versión.
        secret = identifier + "." + secrets.token_urlsafe(32)
        digest = hashlib.sha256(secret.encode()).hexdigest()
        with transaction() as conn:
            row = get(conn, "devices", identifier, True)
            own(row["tenant_id"])
            version(row, data["version"])
            if not row["active"] or row["expires_at"] <= datetime.now(timezone.utc):
                raise APIError("conflict", "Dispositivo revocado o vencido.", 409)
            # Redis primero: si SQL revierte, la comparación con ambos almacenes falla cerrada.
            redis_call(
                lambda r: r.set(
                    key("device:" + identifier),
                    digest,
                    ex=max(
                        1,
                        int(
                            (
                                row["expires_at"] - datetime.now(timezone.utc)
                            ).total_seconds()
                        ),
                    ),
                )
            )
            update(
                conn,
                "devices",
                identifier,
                {"token_hash": digest, "version": row["version"] + 1},
            )
            emit(conn, "DEVICE_CREDENTIAL_ROTATED", identifier, row["tenant_id"])
        return {
            "device_id": identifier,
            "credential": secret,
            "version": row["version"] + 1,
        }

    @endpoint(
        app,
        "/api/v1/devices/<identifier>/revoke",
        "POST",
        model=DeviceChange,
        roles=("ADMIN",),
        result=schema(Device),
    )
    def device_revoke(identifier, data):
        with transaction() as conn:
            row = get(conn, "devices", identifier, True)
            own(row["tenant_id"])
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
