"""Consultas y proyecciones públicas del servicio propietario."""

from flask import g
from redhouse.api import endpoint
from redhouse.db import get, transaction
from redhouse.decisions import history
from redhouse.security import own


def install(app):
    @endpoint(
        app,
        "/api/v1/donations/<identifier>",
        roles=("OPERATOR", "MEDICAL"),
        summary="Donación y pasos de procesamiento institucionales",
    )
    def donation_detail(identifier):
        with transaction() as conn:
            row = get(conn, "donations", identifier)
            own(row["tenant_id"])
            row["decisions"] = history(conn, identifier)
            row["steps"] = conn.execute(
                "SELECT id,state,reason,actor_id,created_at FROM donation_steps WHERE donation_id=%s ORDER BY created_at,id",
                (identifier,),
            ).fetchall()
            return row

    @endpoint(
        app,
        "/api/v1/summary",
        roles=("OPERATOR", "MEDICAL"),
        summary="Indicadores agregados autorizados; no expone expedientes",
    )
    def portal_summary():
        with transaction() as conn:
            where, values = "tenant_id=%s", (g.actor["tenant_id"],)
            counts = conn.execute(
                "SELECT status,count(*) AS value FROM donors WHERE "
                + where
                + " GROUP BY status ORDER BY status",
                values,
            ).fetchall()
            result = {"total": sum(row["value"] for row in counts), "statuses": counts}
            return result

    @endpoint(
        app,
        "/api/v1/campaigns/<identifier>",
        roles=("OPERATOR", "MEDICAL", "DONOR"),
        summary="Detalle de campaña institucional",
    )
    def campaign_detail(identifier):
        with transaction() as conn:
            row = get(conn, "campaigns", identifier)
            own(row["tenant_id"])
            if g.actor["role"] != "DONOR":
                row["decisions"] = history(conn, identifier)
            return row
