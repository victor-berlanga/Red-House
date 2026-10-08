"""Corrección y baja lógica del inventario; no modifica asignaciones históricas."""

from datetime import datetime, timezone
from typing import Annotated
from pydantic import Field
from flask import g
from redhouse.api import atomic, endpoint
from redhouse.db import get, update, insert
from redhouse.decisions import record
from redhouse.errors import APIError
from redhouse.events import emit
from redhouse.models import Confirm, utc_date
from redhouse.security import own
from .routes import ResourceCreate
from uuid import uuid4


class ResourceEdit(ResourceCreate, Confirm):
    version: Annotated[int, Field(ge=1)]


class Withdraw(Confirm):
    version: Annotated[int, Field(ge=1)]


def install(app):
    @endpoint(
        app,
        "/api/v1/resources/<identifier>",
        "PATCH",
        model=ResourceEdit,
        roles=("OPERATOR",),
        summary="Corregir unidad antes de liberación clínica",
    )
    def resource_edit(identifier, data):
        from .locations import validate_location

        validate_location(data["location_id"])
        expires = utc_date(data["expires_at"])
        if expires <= datetime.now(timezone.utc) or (
            data["kind"] == "ORGAN"
            and data["component"] not in ("KIDNEY", "LIVER", "HEART")
        ):
            raise APIError("validation", "Componente o caducidad inválidos.")
        collected = utc_date(data["collected_at"]) if data["collected_at"] else None
        if collected and (
            collected > datetime.now(timezone.utc) or collected >= expires
        ):
            raise APIError(
                "validation", "Recolección futura o posterior al límite capturado."
            )

        def work(conn):
            row = get(conn, "resources", identifier, True)
            own(row["tenant_id"])
            if row["version"] != data["version"] or row["status"] != "QUARANTINE":
                raise APIError("conflict", "Recurso obsoleto o ya liberado.", 409)
            if str(row["donation_id"] or "") != str(data["donation_id"] or "") or (
                row["donation_id"]
                and any(row[k] != data[k] for k in ("kind", "component", "blood_group"))
            ):
                raise APIError(
                    "conflict",
                    "No se puede alterar la procedencia ni su clasificación.",
                    409,
                )
            fields = {
                k: data[k]
                for k in ("folio", "kind", "component", "blood_group", "location_id")
            }
            fields.update(
                expires_at=expires, collected_at=collected, version=row["version"] + 1
            )
            record(
                conn,
                identifier,
                row["tenant_id"],
                "RESOURCE_UPDATED",
                data["reason"],
                {"folio": data["folio"], "expires_at": expires.isoformat()},
            )
            result = update(conn, "resources", identifier, fields)
            emit(conn, "RESOURCE_UPDATED", identifier, row["tenant_id"])
            return result

        return atomic("resource_edit:" + identifier, data, work)

    @endpoint(
        app,
        "/api/v1/resources/<identifier>/withdraw",
        "POST",
        model=Withdraw,
        roles=("OPERATOR",),
        summary="Baja lógica sin reservas ni traslado; conserva historial",
    )
    def resource_withdraw(identifier, data):
        def work(conn):
            row = get(conn, "resources", identifier, True)
            own(row["tenant_id"])
            if (
                row["version"] != data["version"]
                or row["status"] not in ("QUARANTINE", "AVAILABLE")
                or conn.execute(
                    "SELECT 1 FROM reservations WHERE resource_id=%s LIMIT 1",
                    (identifier,),
                ).fetchone()
            ):
                raise APIError(
                    "conflict", "Recurso obsoleto o con historia de asignación.", 409
                )
            record(
                conn, identifier, row["tenant_id"], "RESOURCE_WITHDRAWN", data["reason"]
            )
            result = update(
                conn,
                "resources",
                identifier,
                {"status": "WITHDRAWN", "version": row["version"] + 1},
            )
            insert(
                conn,
                "movements",
                {
                    "id": str(uuid4()),
                    "resource_id": identifier,
                    "action": "WITHDRAWN",
                    "actor_id": g.actor["id"],
                },
            )
            emit(conn, "RESOURCE_WITHDRAWN", identifier, row["tenant_id"])
            return result

        return atomic("resource_withdraw:" + identifier, data, work)
