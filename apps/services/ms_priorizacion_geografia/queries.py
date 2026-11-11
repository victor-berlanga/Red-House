"""Consultas y proyecciones públicas del servicio propietario."""

from flask import g
from redhouse.api import endpoint, listing
from redhouse.db import get, transaction
from redhouse.errors import APIError
from redhouse.client import call


def proposal_scope():
    """Ámbito operativo regional confirmado por Identidad, sin leer tablas ajenas."""
    if g.actor["role"] != "COORDINATOR":
        return [g.actor["tenant_id"]]
    identifiers = []
    for page in range(1, 51):
        result = call("identidad_acceso", "GET", f"/api/v1/institutions?page={page}&page_size=100")
        identifiers.extend(row["id"] for row in result["items"])
        if len(identifiers) >= result["total"]:
            return identifiers
    raise APIError("volume_limit", "Ámbito institucional supera el límite de consulta.", 422)


def install(app):

    @endpoint(
        app,
        "/api/v1/allocation-proposals",
        roles=("MEDICAL", "COORDINATOR"),
        paginated=True,
        summary="Historial institucional de propuestas de cobertura, sin reservas automáticas",
        query=("q", "from_at", "until_at", "date_field", "sort"),
    )
    def proposal_list():
        scope = proposal_scope()
        with transaction() as conn:
            return listing(
                conn,
                "proposals",
                "tenant_id=ANY(%s::uuid[])",
                (scope,),
                columns="id,tenant_id,algorithm_version,elapsed_ms,slot_count,matched_count,created_at",
            )

    @endpoint(
        app,
        "/api/v1/rankings",
        roles=("MEDICAL",),
        paginated=True,
        query=("evaluation_id", "q", "from_at", "until_at", "date_field", "sort"),
        summary="Historial propio de rankings operativos",
    )
    def ranking_list():
        with transaction() as conn:
            return listing(
                conn,
                "rankings",
                "tenant_id=%s",
                (g.actor["tenant_id"],),
                filters={"evaluation_id": ("evaluation_id", ())},
            )

    @endpoint(
        app,
        "/api/v1/routes/<identifier>",
        roles=("COORDINATOR", "MEDICAL"),
        summary="Consultar una ruta regional por identificador",
    )
    def route_detail(identifier):
        with transaction() as conn:
            row = get(conn, "routes", identifier)
            if str(row["region_id"]) != g.actor["region_id"]:
                raise APIError("forbidden", "Ruta de otra región.", 403)
            return row
