"""Consultas y proyecciones públicas del servicio propietario."""

from flask import g
from redhouse.api import endpoint, listing
from redhouse.db import transaction


def install(app):

    @endpoint(
        app,
        "/api/v1/evaluations",
        roles=("MEDICAL",),
        paginated=True,
        query=("request_id",),
        summary="Historial institucional de evaluaciones y versiones",
    )
    def evaluation_list():
        with transaction() as conn:
            return listing(
                conn,
                "evaluations",
                "tenant_id=%s",
                (g.actor["tenant_id"],),
                columns="id,tenant_id,request_id,kind,algorithm_version,elapsed_ms,created_at",
                filters={"request_id": ("request_id", ())},
            )
