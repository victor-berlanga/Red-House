"""Configuración operativa institucional y publicación explícita minimizada."""

from typing import Annotated, Literal
from flask import g
from pydantic import Field
from redhouse.api import endpoint, atomic
from redhouse.db import transaction, get, insert, update
from redhouse.decisions import record
from redhouse.events import emit
from redhouse.errors import APIError
from redhouse.extension_contracts import schema
from redhouse.models import Model, Confirm, ID, Text, utc_date
from redhouse.security import own


class Presentation(Model):
    id: ID
    version: int
    published: bool
    description: Annotated[str, Field(max_length=1000)]
    latitude: float | None
    longitude: float | None
    coordinate_source: str | None
    coordinate_recorded_at: str | None
    synthetic: bool


class PresentationChange(Confirm):
    version: Annotated[int, Field(ge=0)]
    published: bool
    description: Annotated[str, Field(max_length=1000)] = ""
    latitude: Annotated[float, Field(ge=-90, le=90)] | None = None
    longitude: Annotated[float, Field(ge=-180, le=180)] | None = None
    coordinate_source: Text | None = None
    coordinate_recorded_at: Text | None = None
    synthetic: bool


class Policy(Model):
    id: ID
    version: int
    timezone: Literal[
        "America/Monterrey", "America/Mexico_City", "America/Tijuana", "UTC"
    ]
    tracking_interval_seconds: Annotated[int, Field(ge=1, le=300)]
    tracking_stale_seconds: Annotated[int, Field(ge=5, le=3600)]
    reference: Text


class PolicyChange(Confirm):
    version: Annotated[int, Field(ge=0)]
    timezone: Literal[
        "America/Monterrey", "America/Mexico_City", "America/Tijuana", "UTC"
    ]
    tracking_interval_seconds: Annotated[int, Field(ge=1, le=300)]
    tracking_stale_seconds: Annotated[int, Field(ge=5, le=3600)]
    reference: Text


def save(conn, table, identifier, data, action):
    get(conn, "institutions", identifier, True)
    old = conn.execute(
        f"SELECT * FROM {table} WHERE id=%s FOR UPDATE", (identifier,)
    ).fetchone()
    if data["version"] != (old["version"] if old else 0):
        raise APIError(
            "stale_version",
            "Configuración modificada; consulta la versión vigente.",
            412,
        )
    values = {
        k: v
        for k, v in data.items()
        if k not in ("reason", "human_confirmation", "version")
    }
    values["version"] = data["version"] + 1
    row = (
        update(conn, table, identifier, values)
        if old
        else insert(conn, table, dict(values, id=identifier))
    )
    record(conn, identifier, identifier, action, data["reason"], values)
    emit(conn, action, identifier, identifier)
    return row


def install(app):
    @endpoint(
        app,
        "/api/v1/public/institutions",
        public=True,
        result={
            "type": "object",
            "required": ["items"],
            "properties": {
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["name", "description"],
                        "additionalProperties": False,
                        "properties": {
                            "name": {"type": "string"},
                            "description": {"type": "string"},
                        },
                    },
                }
            },
        },
    )
    def public_institutions():
        with transaction() as conn:
            return {
                "items": conn.execute(
                    "SELECT i.name,p.description FROM institutions i JOIN institution_presentations p ON p.id=i.id WHERE i.active AND p.published ORDER BY i.name,i.id"
                ).fetchall()
            }

    @endpoint(
        app,
        "/api/v1/institutions/<identifier>/presentation",
        roles=("ADMIN", "OPERATOR", "MEDICAL", "COORDINATOR", "TRANSPORT"),
        result=schema(Presentation),
    )
    def institution_presentation(identifier):
        with transaction() as conn:
            institution = get(conn, "institutions", identifier)
            if str(institution["region_id"]) != g.actor["region_id"]:
                raise APIError("forbidden", "Institución fuera de ámbito.", 403)
            if g.actor["role"] == "ADMIN":
                own(identifier)
            row = conn.execute(
                "SELECT * FROM institution_presentations WHERE id=%s", (identifier,)
            ).fetchone()
            return row or dict(
                id=identifier,
                version=0,
                published=False,
                description="",
                latitude=None,
                longitude=None,
                coordinate_source=None,
                coordinate_recorded_at=None,
                synthetic=True,
            )

    @endpoint(
        app,
        "/api/v1/institutions/<identifier>/presentation",
        "POST",
        roles=("ADMIN",),
        model=PresentationChange,
        result=schema(Presentation),
    )
    def institution_presentation_change(identifier, data):
        own(identifier)
        if (data["latitude"] is None) != (data["longitude"] is None):
            raise APIError(
                "validation", "Captura ambas coordenadas o deja ambas pendientes.", 422
            )
        if data["latitude"] is not None and not (
            data["coordinate_source"] and data["coordinate_recorded_at"]
        ):
            raise APIError(
                "validation", "Coordenadas requieren fuente y fecha de consulta.", 422
            )
        if data["coordinate_recorded_at"]:
            data["coordinate_recorded_at"] = utc_date(
                data["coordinate_recorded_at"]
            ).isoformat()
        return atomic(
            "institution_presentation:" + identifier,
            data,
            lambda conn: save(
                conn,
                "institution_presentations",
                identifier,
                data,
                "INSTITUTION_PRESENTATION_CHANGED",
            ),
        )

    @endpoint(
        app,
        "/api/v1/portal-policy",
        roles=(
            "ADMIN",
            "OPERATOR",
            "MEDICAL",
            "COORDINATOR",
            "TRANSPORT",
            "DONOR",
            "AUDITOR",
        ),
        result=schema(Policy),
    )
    def portal_policy():
        with transaction() as conn:
            row = conn.execute(
                "SELECT * FROM portal_policies WHERE id=%s", (g.actor["tenant_id"],)
            ).fetchone()
            return row or dict(
                id=g.actor["tenant_id"],
                version=0,
                timezone="America/Monterrey",
                tracking_interval_seconds=10,
                tracking_stale_seconds=30,
                reference="Valor operativo inicial: tres intervalos esperados sin observación; pendiente de revisión institucional",
            )

    @endpoint(
        app,
        "/api/v1/portal-policy",
        "POST",
        roles=("ADMIN",),
        model=PolicyChange,
        result=schema(Policy),
    )
    def portal_policy_change(data):
        if data["tracking_stale_seconds"] < data["tracking_interval_seconds"]:
            raise APIError(
                "validation",
                "Antigüedad debe cubrir al menos un intervalo de envío.",
                422,
            )
        return atomic(
            "portal_policy",
            data,
            lambda conn: save(
                conn,
                "portal_policies",
                g.actor["tenant_id"],
                data,
                "PORTAL_POLICY_CHANGED",
            ),
        )
