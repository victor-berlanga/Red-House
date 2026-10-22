"""Catálogos administrativos institucionales; no contienen reglas clínicas."""

from datetime import time
from typing import Annotated
from uuid import uuid4

from flask import g
from pydantic import Field, create_model

from redhouse.api import atomic, endpoint, listing
from redhouse.db import get, insert, transaction, update
from redhouse.decisions import record, history
from redhouse.errors import APIError
from redhouse.events import emit
from redhouse.models import Confirm, ID, Model, Text
from redhouse.security import own
from redhouse.cache import cached_read
from redhouse.validation import invalid


class Site(Model):
    name: Text
    municipality: Text
    address: Text


class Contact(Model):
    name: Text
    value: Text


class Schedule(Model):
    name: Text
    parent_id: ID
    weekday: Annotated[int, Field(ge=0, le=6)]
    opens_at: Annotated[str, Field(pattern=r"^[0-2][0-9]:[0-5][0-9]$")]
    closes_at: Annotated[str, Field(pattern=r"^[0-2][0-9]:[0-5][0-9]$")]


class Capacity(Model):
    name: Text
    parent_id: ID
    component: Text
    quantity: Annotated[int, Field(ge=0, le=100000)]


class Location(Model):
    name: Text
    parent_id: ID
    description: Text


MODELS = {
    "sites": Site,
    "contacts": Contact,
    "schedules": Schedule,
    "capacities": Capacity,
    "locations": Location,
}


def public(row):
    return dict(row, **row["details"])


def authorized(conn, identifier, kind=None, lock=False):
    row = get(conn, "catalogue", identifier, lock)
    own(row["tenant_id"])
    if kind is not None and row["kind"] != kind:
        raise APIError("not_found", "Registro no disponible en este catálogo.", 404)
    return row


def values(conn, kind, data):
    if data.get("parent_id"):
        site = authorized(conn, data["parent_id"], "sites", True)
        if not site["active"]:
            raise APIError("conflict", "Sede inactiva.", 409)
    if kind == "schedules":
        hours = {}
        for name in ("opens_at", "closes_at"):
            try:
                hours[name] = time.fromisoformat(data[name])
            except ValueError:
                raise invalid(
                    "Escribe una hora válida entre 00:00 y 23:59.", name
                ) from None
        if hours["opens_at"] >= hours["closes_at"]:
            raise invalid(
                "El cierre debe ser posterior a la apertura del mismo día.",
                "opens_at",
                "closes_at",
                code="time_order",
            )
    detail = {
        k: v
        for k, v in data.items()
        if k
        not in (
            "name",
            "parent_id",
            "active",
            "version",
            "reason",
            "human_confirmation",
        )
    }
    return dict(name=data["name"], parent_id=data.get("parent_id"), details=detail)


def install(app):
    def register_kind(kind, model):
        edit_model = create_model(
            model.__name__ + "Edit",
            __base__=(model, Confirm),
            active=(bool, ...),
            version=(Annotated[int, Field(ge=1)], ...),
        )

        @cached_read("catalogues", ttl=30)
        def list_rows():
            with transaction() as conn:
                result = listing(
                    conn,
                    "catalogue",
                    "tenant_id=%s AND kind=%s",
                    (g.actor["tenant_id"], kind),
                    order="name,id",
                    filters={
                        "q": ("name",),
                        "active": ("active", {"true": True, "false": False}),
                    },
                )
                result["items"] = [public(r) for r in result["items"]]
                return result

        def detail(identifier):
            with transaction() as conn:
                row = public(authorized(conn, identifier, kind))
                row["decisions"] = history(conn, identifier)
                return row

        def create(data):
            def work(conn):
                row = insert(
                    conn,
                    "catalogue",
                    dict(
                        id=str(uuid4()),
                        tenant_id=g.actor["tenant_id"],
                        kind=kind,
                        **values(conn, kind, data),
                    ),
                )
                emit(
                    conn,
                    "CATALOGUE_CREATED",
                    row["id"],
                    row["tenant_id"],
                    metadata={"kind": kind},
                )
                return public(row)

            return atomic(kind + "_create", data, work)

        def edit(identifier, data):
            def work(conn):
                row = authorized(conn, identifier, kind, True)
                if row["version"] != data["version"]:
                    raise APIError(
                        "stale_version",
                        "Registro modificado; vuelve a consultarlo.",
                        409,
                    )
                if str(row["parent_id"] or "") != str(data.get("parent_id") or ""):
                    raise APIError(
                        "conflict",
                        "No se reasocia un registro a otra sede; crea uno nuevo.",
                        409,
                    )
                if (
                    kind == "sites"
                    and not data["active"]
                    and conn.execute(
                        "SELECT 1 FROM catalogue WHERE parent_id=%s AND active LIMIT 1",
                        (identifier,),
                    ).fetchone()
                ):
                    raise APIError(
                        "conflict",
                        "Desactiva primero los registros dependientes de la sede.",
                        409,
                    )
                fields = dict(
                    values(conn, kind, data),
                    active=data["active"],
                    version=row["version"] + 1,
                )
                record(
                    conn,
                    identifier,
                    row["tenant_id"],
                    "CATALOGUE_UPDATED",
                    data["reason"],
                    fields,
                )
                result = update(conn, "catalogue", identifier, fields)
                emit(
                    conn,
                    "CATALOGUE_UPDATED",
                    identifier,
                    row["tenant_id"],
                    metadata={"kind": kind},
                )
                return public(result)

            return atomic(kind + "_edit:" + identifier, data, work)

        for fn in (list_rows, detail, create, edit):
            fn.__name__ = kind + "_" + fn.__name__
        base = "/api/v1/catalogues/" + kind
        endpoint(
            app,
            base,
            roles=("ADMIN", "OPERATOR", "MEDICAL"),
            paginated=True,
            query=("q", "active"),
            summary="Consultar " + kind,
        )(list_rows)
        endpoint(
            app,
            base + "/<identifier>",
            roles=("ADMIN", "OPERATOR", "MEDICAL"),
            summary="Detalle de " + kind,
        )(detail)
        endpoint(
            app,
            base,
            "POST",
            model=model,
            roles=("ADMIN",),
            status=201,
            summary="Registrar " + kind,
        )(create)
        endpoint(
            app,
            base + "/<identifier>",
            "PATCH",
            model=edit_model,
            roles=("ADMIN",),
            summary="Editar o desactivar " + kind,
        )(edit)

    for kind, model in MODELS.items():
        register_kind(kind, model)

    @endpoint(
        app,
        "/internal/v1/locations/<identifier>",
        internal=("inventario", "transporte"),
        roles=("OPERATOR", "MEDICAL"),
        summary="Validar ubicación y sede de la institución del usuario",
    )
    def location_internal(identifier):
        with transaction() as conn:
            row = authorized(conn, identifier, "locations")
            site = authorized(conn, str(row["parent_id"]), "sites")
            return {
                "id": row["id"],
                "tenant_id": row["tenant_id"],
                "active": row["active"] and site["active"],
            }
