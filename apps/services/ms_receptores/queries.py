"""Consultas y proyecciones públicas del servicio propietario."""

from flask import g
from redhouse.api import endpoint
from redhouse.db import transaction


def install(app):
    @endpoint(
        app,
        "/api/v1/summary",
        roles=("OPERATOR", "MEDICAL", "COORDINATOR"),
        summary="Indicadores agregados autorizados; no expone expedientes",
    )
    def portal_summary():
        with transaction() as conn:
            where, values = "tenant_id=%s", (g.actor["tenant_id"],)
            counts = conn.execute(
                "SELECT status,count(*) AS value FROM requests WHERE "
                + where
                + " GROUP BY status ORDER BY status",
                values,
            ).fetchall()
            result = {"total": sum(row["value"] for row in counts), "statuses": counts}
            result["urgencies"] = conn.execute(
                "SELECT urgency AS label,count(*) AS value FROM requests WHERE "
                + where
                + " AND status IN ('OPEN','IN_PROGRESS') GROUP BY urgency ORDER BY urgency",
                values,
            ).fetchall()
            result["trend"] = conn.execute(
                "SELECT created_at::date AS label,count(*) AS value FROM requests WHERE "
                + where
                + " AND created_at>now()-interval '7 days' GROUP BY created_at::date ORDER BY created_at::date",
                values,
            ).fetchall()
            return result
