"""Edición personal mínima; no modifica identidad de cuenta ni datos clínicos."""

from typing import Annotated

from pydantic import Field

from redhouse.api import atomic, endpoint
from redhouse.db import get, transaction, update
from redhouse.decisions import record
from redhouse.errors import APIError
from redhouse.events import emit
from redhouse.models import ID, Model, Text
from redhouse.extension_contracts import schema
from redhouse.security import authenticate

from .routes import donor_access
from .withdrawal import require_active


class DonorPersonalEdit(Model):
    display_name: Text
    version: Annotated[int, Field(ge=1)]


class DonorPersonalResult(DonorPersonalEdit):
    id: ID


def authorized(conn, identifier, *, lock=False):
    # Revalidar también al recuperar una respuesta idempotente. No basta con
    # haber sido propietario cuando se registró el comando original.
    authenticate(("DONOR",))
    row = get(conn, "donors", identifier, lock)
    donor_access(row)
    require_active(row)
    return row


def install(app):
    @endpoint(
        app,
        "/api/v1/donors/<identifier>/personal",
        "PATCH",
        model=DonorPersonalEdit,
        roles=("DONOR",),
        result=schema(DonorPersonalResult),
        summary="Actualizar el nombre mostrado del expediente propio sin cambiar datos clínicos",
    )
    def donor_personal_edit(identifier, data):
        with transaction() as conn:
            authorized(conn, identifier)

        def work(conn):
            row = authorized(conn, identifier, lock=True)
            if row["version"] != data["version"]:
                raise APIError(
                    "stale_version",
                    "Tu expediente cambió. Vuelve a abrirlo antes de guardar.",
                    409,
                )
            fields = {
                "display_name": data["display_name"],
                "version": row["version"] + 1,
            }
            record(
                conn,
                identifier,
                row["tenant_id"],
                "DONOR_PERSONAL_UPDATED",
                "Actualización personal del nombre mostrado.",
                {**fields, "previous_display_name": row["display_name"]},
            )
            result = update(conn, "donors", identifier, fields)
            emit(conn, "DONOR_PERSONAL_UPDATED", identifier, row["tenant_id"])
            return {key: result[key] for key in ("id", "display_name", "version")}

        result = atomic("donor_personal_edit:" + identifier, data, work)
        with transaction() as conn:
            authorized(conn, identifier)
        return result
