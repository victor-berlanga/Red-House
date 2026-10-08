"""Consultas y proyecciones públicas del servicio propietario."""

from flask import g
from redhouse.api import endpoint, listing
from redhouse.db import get, transaction
from redhouse.errors import APIError


def install(app):

    @endpoint(
        app,
        "/api/v1/allocation-proposals",
        roles=("MEDICAL",),
        paginated=True,
        summary="Historial institucional de propuestas de cobertura, sin reservas automáticas",
    )
    def proposal_list():
        with transaction() as conn:
            return listing(
                conn,
                "proposals",
                "tenant_id=%s",
                (g.actor["tenant_id"],),
                columns="id,tenant_id,algorithm_version,elapsed_ms,slot_count,matched_count,created_at",
            )

    @endpoint(
        app,
        "/api/v1/rankings",
        roles=("MEDICAL",),
        paginated=True,
        query=("evaluation_id",),
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
