"""Consultas y proyecciones públicas del servicio propietario."""

from flask import g
from redhouse.api import endpoint
from redhouse.db import transaction


def install(app):
    @endpoint(
        app,
        "/api/v1/summary",
        roles=("OPERATOR", "MEDICAL", "COORDINATOR", "TRANSPORT"),
        summary="Indicadores agregados autorizados; no expone expedientes",
    )
    def portal_summary():
        with transaction() as conn:
            if g.actor["role"] == "COORDINATOR":
                where, values = "region_id=%s", (g.actor["region_id"],)
            elif g.actor["role"] == "TRANSPORT":
                where, values = "transport_user_id=%s", (g.actor["id"],)
            else:
                where, values = (
                    "(origin_id=%s OR destination_id=%s)",
                    (g.actor["tenant_id"], g.actor["tenant_id"]),
                )
            counts = conn.execute(
                "SELECT status,count(*) AS value FROM shipments WHERE "
                + where
                + " GROUP BY status ORDER BY status",
                values,
            ).fetchall()
            result = {"total": sum(row["value"] for row in counts), "statuses": counts}
            return result
