"""Catálogos administrativos institucionales; no contienen reglas clínicas."""

from datetime import time
from typing import Annotated
from uuid import uuid4

from flask import g
from pydantic import Field, create_model
from redhouse.api import atomic, endpoint, listing
from redhouse.cache import cached_read
from redhouse.db import get, insert, transaction, update
from redhouse.decisions import history, record
from redhouse.errors import APIError
from redhouse.events import emit
from redhouse.models import ID, Confirm, Model, Text
from redhouse.security import own
from redhouse.validation import invalid


class AppointmentSiteLabelsQuery(Model):
    ids: Annotated[list[ID], Field(min_length=1, max_length=100)]


class AppointmentSiteLabel(Model):
    id: ID
    name: Text


class AppointmentSiteLabels(Model):
    items: list[AppointmentSiteLabel]


class Site(Model):
    name: Text
    municipality: Text
    address: Text


class Contact(Model):
    name: Text
    value: Text
    operational: bool = False


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


class Responsible(Model):
    name: Text
    parent_id: ID
    user_id: ID
    function: Text
    authorization_reference: Text


class InstitutionalService(Model):
    name: Text
    parent_id: ID
    description: Text
    capability_reference: Text


MODELS = {
    "sites": Site,
    "contacts": Contact,
    "schedules": Schedule,
    "capacities": Capacity,
    "locations": Location,
    "responsibles": Responsible,
    "services": InstitutionalService,
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
    if kind == "responsibles":
        responsible = get(conn, "users", data["user_id"])
        own(responsible["tenant_id"])
        if not responsible["active"]:
            raise APIError("conflict", "Responsable institucional inactivo.", 409)
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
    from redhouse.extension_contracts import schema

    @endpoint(
        app,
        "/internal/v1/appointment-site-labels",
        "POST",
        model=AppointmentSiteLabelsQuery,
        internal=("donantes",),
        roles=("DONOR", "OPERATOR"),
        result=schema(AppointmentSiteLabels),
        summary="Nombres de sedes propias para una página de horarios autorizados",
    )
    def appointment_site_labels(data):
        from redhouse.events import audit_read

        audit_read("appointment-site-labels")
        with transaction() as conn:
            rows = conn.execute(
                "SELECT id,name FROM catalogue WHERE tenant_id=%s AND kind='sites' "
                "AND id=ANY(%s::uuid[]) ORDER BY id",
                (g.actor["tenant_id"], data["ids"]),
            ).fetchall()
            return {"items": rows}

    @endpoint(
        app,
        "/internal/v1/institutions/<identifier>/operational-contacts",
        internal=("transporte",),
        roles=("TRANSPORT", "OPERATOR", "COORDINATOR"),
        summary="Contactos explícitamente operativos; solo proyección de tarea por Transporte",
        result={
            "type": "object",
            "required": ["id", "name", "contacts", "operators"],
            "properties": {
                "id": {"type": "string", "format": "uuid"},
                "name": {"type": "string"},
                "contacts": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["id", "name", "value", "version"],
                        "properties": {
                            "id": {"type": "string"},
                            "name": {"type": "string"},
                            "value": {"type": "string"},
                            "version": {"type": "integer"},
                        },
                    },
                },
                "operators": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["id", "name"],
                        "properties": {
                            "id": {"type": "string"},
                            "name": {"type": "string"},
                        },
                    },
                },
            },
        },
    )
    def operational_contacts(identifier):
        with transaction() as conn:
            institution = get(conn, "institutions", identifier)
            if (
                str(institution["region_id"]) != g.actor["region_id"]
                or not institution["active"]
            ):
                raise APIError("forbidden", "Institución operativa no disponible.", 403)
            contacts = conn.execute(
                "SELECT id,name,details->>'value' AS value,version FROM catalogue WHERE tenant_id=%s AND kind='contacts' AND active AND details->'operational'='true'::jsonb ORDER BY name,id",
                (identifier,),
            ).fetchall()
            # A task needs a handover identity, never general user/contact/clinical data.
            operators = conn.execute(
                "SELECT id,username AS name FROM users WHERE tenant_id=%s AND role='OPERATOR' AND active ORDER BY username,id",
                (identifier,),
            ).fetchall()
            emit(conn, "OPERATIONAL_CONTACTS_READ", identifier, identifier)
            return dict(
                id=identifier,
                name=institution["name"],
                contacts=contacts,
                operators=operators,
            )

    @endpoint(
        app,
        "/api/v1/appointment-sites",
        roles=("DONOR", "OPERATOR"),
        paginated=True,
        query=("q",),
        result={
            "type": "object",
            "required": ["items", "page", "page_size", "total"],
            "properties": {
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["id", "name"],
                        "properties": {
                            "id": {"type": "string", "format": "uuid"},
                            "name": {"type": "string"},
                        },
                    },
                },
                "page": {"type": "integer"},
                "page_size": {"type": "integer"},
                "total": {"type": "integer"},
            },
        },
    )
    def appointment_sites():
        # Agenda necesita etiquetas propias, nunca contactos o capacidades privadas.
        with transaction() as conn:
            result = listing(
                conn,
                "catalogue",
                "tenant_id=%s AND kind='sites' AND active",
                (g.actor["tenant_id"],),
                filters={"q": ("name",)},
                order="name,id",
            )
            result["items"] = [
                {"id": r["id"], "name": r["name"]} for r in result["items"]
            ]
            return result

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
        output, paged = None, None
        if kind in ("responsibles", "services"):
            from typing import Any

            from redhouse.extension_contracts import page_schema, schema

            output_model = create_model(
                "Institutional" + kind,
                __base__=model,
                id=(ID, ...),
                tenant_id=(ID, ...),
                kind=(Text, ...),
                parent_id=(ID | None, None),
                active=(bool, ...),
                version=(int, ...),
                created_at=(Text, ...),
                details=(dict[str, Any], ...),
                decisions=(list[dict[str, Any]], []),
            )
            output, paged = schema(output_model), page_schema(output_model)
        base = "/api/v1/catalogues/" + kind
        endpoint(
            app,
            base,
            roles=("ADMIN", "OPERATOR", "MEDICAL"),
            paginated=True,
            result=paged,
            query=("q", "active"),
            summary="Consultar " + kind,
        )(list_rows)
        endpoint(
            app,
            base + "/<identifier>",
            roles=("ADMIN", "OPERATOR", "MEDICAL"),
            result=output,
            summary="Detalle de " + kind,
        )(detail)
        endpoint(
            app,
            base,
            "POST",
            model=model,
            roles=("ADMIN",),
            result=output,
            status=201,
            summary="Registrar " + kind,
        )(create)
        endpoint(
            app,
            base + "/<identifier>",
            "PATCH",
            model=edit_model,
            roles=("ADMIN",),
            result=output,
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
