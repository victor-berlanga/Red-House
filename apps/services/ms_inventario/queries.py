"""Consultas y proyecciones públicas del servicio propietario."""

from flask import g
from redhouse.api import endpoint, listing
from redhouse.db import get, transaction
from redhouse.decisions import history
from redhouse.errors import APIError
from redhouse.security import own
from .states import RESERVATION_FILTER


def install(app):
    @endpoint(
        app,
        "/api/v1/resources/<identifier>",
        roles=("OPERATOR", "MEDICAL", "COORDINATOR"),
        summary="Recurso y movimientos; sin identidad del donante",
    )
    def resource_detail(identifier):
        with transaction() as conn:
            row = get(conn, "resources", identifier)
            if g.actor["role"] == "COORDINATOR":
                if str(row["region_id"]) != g.actor["region_id"]:
                    raise APIError("forbidden", "Recurso fuera de la región.", 403)
                return {
                    k: row[k]
                    for k in (
                        "id",
                        "folio",
                        "tenant_id",
                        "current_institution_id",
                        "kind",
                        "component",
                        "blood_group",
                        "expires_at",
                        "status",
                        "version",
                    )
                }
            own(row["current_institution_id"])
            row["decisions"] = history(conn, identifier)
            row["movements"] = conn.execute(
                "SELECT id,action,created_at FROM movements WHERE resource_id=%s ORDER BY created_at,id",
                (identifier,),
            ).fetchall()
            row["reviews"] = conn.execute(
                "SELECT id,decision,reason,actor_id,created_at FROM resource_reviews WHERE resource_id=%s ORDER BY created_at,id",
                (identifier,),
            ).fetchall()
            return row

    @endpoint(
        app,
        "/api/v1/reservations",
        roles=("OPERATOR", "MEDICAL", "COORDINATOR"),
        paginated=True,
        query=("status", "request_id", "q", "unplanned"),
        summary="Reservas institucionales o regionales para coordinación",
    )
    def reservation_list():
        with transaction() as conn:
            where, values = (
                ("region_id=%s", (g.actor["region_id"],))
                if g.actor["role"] == "COORDINATOR"
                else (
                    "origin_id=%s OR destination_id=%s",
                    (g.actor["tenant_id"], g.actor["tenant_id"]),
                )
            )
            return listing(
                conn,
                "reservations",
                where,
                values,
                filters={
                    "status": ("status", RESERVATION_FILTER),
                    "request_id": ("request_id", ()),
                    "q": ("id::text",),
                    "unplanned": (
                        "(shipment_id IS NULL)",
                        {"true": True, "false": False},
                    ),
                },
            )

    @endpoint(
        app,
        "/api/v1/summary",
        roles=("OPERATOR", "MEDICAL", "COORDINATOR"),
        summary="Indicadores agregados autorizados; no expone expedientes",
    )
    def portal_summary():
        with transaction() as conn:
            if g.actor["role"] == "COORDINATOR":
                where, values = "region_id=%s", (g.actor["region_id"],)
            else:
                where, values = "current_institution_id=%s", (g.actor["tenant_id"],)
            counts = conn.execute(
                "SELECT status,count(*) AS value FROM resources WHERE "
                + where
                + " GROUP BY status ORDER BY status",
                values,
            ).fetchall()
            result = {"total": sum(row["value"] for row in counts), "statuses": counts}
            result["groups"] = conn.execute(
                "SELECT blood_group AS label,count(*) AS value FROM resources WHERE "
                + where
                + " AND kind='BLOOD' AND status='AVAILABLE' AND expires_at>now() GROUP BY blood_group ORDER BY blood_group",
                values,
            ).fetchall()
            result["institutions"] = conn.execute(
                "SELECT current_institution_id AS institution_id,count(*) AS value FROM resources WHERE "
                + where
                + " GROUP BY current_institution_id ORDER BY current_institution_id",
                values,
            ).fetchall()
            result["expiring"] = conn.execute(
                "SELECT count(*) AS value FROM resources WHERE "
                + where
                + " AND status='AVAILABLE' AND expires_at BETWEEN now() AND now()+interval '48 hours'",
                values,
            ).fetchone()["value"]
            result["expired"] = conn.execute(
                "SELECT count(*) AS value FROM resources WHERE "
                + where
                + " AND status='AVAILABLE' AND expires_at<=now()",
                values,
            ).fetchone()["value"]
            return result
