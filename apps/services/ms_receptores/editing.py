"""Correcciones institucionales con control de versión e historia."""

from typing import Annotated
from pydantic import Field
from redhouse.api import atomic, endpoint
from redhouse.db import get, update
from redhouse.decisions import record
from redhouse.errors import APIError
from redhouse.validation import invalid
from redhouse.events import emit
from redhouse.models import Confirm, Text
from redhouse.security import own
from .routes import RecipientCreate


class RecipientEdit(RecipientCreate, Confirm):
    version: Annotated[int, Field(ge=1)]


class RequestEdit(Confirm):
    component: Text
    quantity: Annotated[int, Field(ge=1, le=100)]
    urgency: Annotated[int, Field(ge=1, le=3)]
    version: Annotated[int, Field(ge=1)]


def install(app):
    @endpoint(
        app,
        "/api/v1/recipients/<identifier>",
        "PATCH",
        model=RecipientEdit,
        roles=("MEDICAL",),
        summary="Corregir receptor antes de registrar solicitudes",
    )
    def recipient_edit(identifier, data):
        if (data["kind"] == "ORGAN") != (data["organ_type"] is not None):
            raise invalid(
                "Selecciona un órgano si el recurso es Órgano; para Sangre deja el órgano vacío.",
                "kind",
                "organ_type",
                code="organ_kind",
            )

        def work(conn):
            row = get(conn, "recipients", identifier, True)
            own(row["tenant_id"])
            if (
                row["version"] != data["version"]
                or conn.execute(
                    "SELECT 1 FROM requests WHERE recipient_id=%s LIMIT 1",
                    (identifier,),
                ).fetchone()
            ):
                raise APIError(
                    "conflict",
                    "Expediente obsoleto o con solicitudes; no se reescribe historia clínica.",
                    409,
                )
            fields = {
                k: data[k]
                for k in (
                    "folio",
                    "display_name",
                    "kind",
                    "blood_group",
                    "organ_type",
                    "studies",
                    "restrictions",
                    "requirement",
                    "status",
                )
            }
            fields["version"] = row["version"] + 1
            record(
                conn,
                identifier,
                row["tenant_id"],
                "RECIPIENT_UPDATED",
                data["reason"],
                fields,
            )
            result = update(conn, "recipients", identifier, fields)
            emit(conn, "RECIPIENT_UPDATED", identifier, row["tenant_id"])
            return result

        return atomic("recipient_edit:" + identifier, data, work)

    @endpoint(
        app,
        "/api/v1/requests/<identifier>",
        "PATCH",
        model=RequestEdit,
        roles=("MEDICAL",),
        summary="Editar solicitud abierta sin retenciones, invalidando evaluaciones anteriores",
    )
    def request_edit(identifier, data):
        def work(conn):
            row = get(conn, "requests", identifier, True)
            own(row["tenant_id"])
            if (
                row["version"] != data["version"]
                or row["status"] != "OPEN"
                or conn.execute(
                    "SELECT 1 FROM holds WHERE request_id=%s LIMIT 1", (identifier,)
                ).fetchone()
            ):
                raise APIError(
                    "conflict", "Solicitud obsoleta o con historia de asignación.", 409
                )
            person = get(conn, "recipients", str(row["recipient_id"]), True)
            if row["kind"] == "ORGAN" and (
                data["quantity"] != 1 or data["component"] != person["organ_type"]
            ):
                raise APIError(
                    "validation", "Órgano y cantidad deben corresponder al expediente."
                )
            fields = {k: data[k] for k in ("component", "quantity", "urgency")}
            fields["version"] = row["version"] + 1
            record(
                conn,
                identifier,
                row["tenant_id"],
                "REQUEST_UPDATED",
                data["reason"],
                fields,
            )
            result = update(conn, "requests", identifier, fields)
            emit(conn, "REQUEST_UPDATED", identifier, row["tenant_id"])
            return result

        return atomic("request_edit:" + identifier, data, work)
