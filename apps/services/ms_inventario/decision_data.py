"""Authoritative, institution-scoped extraction for analytical review."""

from datetime import datetime, timedelta, timezone

from flask import g, request
from redhouse.api import endpoint
from redhouse.db import transaction
from redhouse.errors import APIError


def bounded(conn, query, args):
    rows = conn.execute(query + " LIMIT 10001", args).fetchall()
    if len(rows) > 10000:
        raise APIError(
            "volume_limit", "Extracción supera 10000 hechos; reduce ventana.", 422
        )
    return rows


def install(app):
    @endpoint(
        app,
        "/api/v1/decision-data",
        roles=("MEDICAL",),
        query=("days", "component"),
        result={"type": "object"},
    )
    def inventory_decision_data():
        try:
            days = int(request.args.get("days", "30"))
            if not 6 <= days <= 365:
                raise ValueError()
        except ValueError:
            raise APIError("validation", "Ventana entre 6 y 365 días.", 422) from None
        component = request.args.get("component", "RBC")
        end = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        start = end - timedelta(days=days)
        with transaction() as conn:
            tenant = g.actor["tenant_id"]
            resources = bounded(
                conn,
                "SELECT id,folio,donation_id,kind,component,status,version,expires_at,current_institution_id,tenant_id FROM resources WHERE current_institution_id=%s ORDER BY id",
                (tenant,),
            )
            reservations = bounded(
                conn,
                "SELECT id,resource_id,request_id,status,shipment_sequence FROM reservations WHERE origin_id=%s OR destination_id=%s ORDER BY id",
                (tenant, tenant),
            )
            lineage = bounded(
                conn,
                "SELECT * FROM resource_lineage WHERE tenant_id=%s ORDER BY id",
                (tenant,),
            )
            readings = bounded(
                conn,
                "SELECT r.*,p.minimum_c,p.maximum_c,p.max_gap_seconds FROM cold_readings r JOIN cold_profiles p ON p.id=r.profile_id WHERE r.tenant_id=%s AND r.captured_at>=%s ORDER BY r.resource_id,r.captured_at,r.id",
                (tenant, start),
            )
            uses = bounded(
                conn,
                "SELECT d.id,d.resource_id,d.version,d.occurred_at,d.destination FROM resource_destinations d JOIN resources r ON r.id=d.resource_id WHERE d.tenant_id=%s AND r.component=%s AND d.occurred_at>=%s AND d.occurred_at<%s AND NOT EXISTS(SELECT 1 FROM resource_destinations n WHERE n.supersedes=d.id) ORDER BY d.occurred_at,d.id",
                (tenant, component, start, end),
            )
        observations = []
        for i in range(days):
            a = start + timedelta(days=i)
            b = a + timedelta(days=1)
            selected = [
                u
                for u in uses
                if a <= u["occurred_at"] < b
                and u["destination"] in ("TRANSFUSED", "TRANSPLANTED")
            ]
            observations.append(
                {
                    "start_at": a.isoformat(),
                    "end_at": b.isoformat(),
                    "value": len(selected),
                    "event_ids": [str(u["id"]) for u in selected],
                    "source": "inventario:resource_destinations",
                    "quality": "RECORDED_EVENTS" if selected else "NO_EVENTS_RECORDED",
                }
            )
        lots = [
            {"identifier": str(r["id"]), "quantity": 1, "expires_at": r["expires_at"]}
            for r in resources
            if r["component"] == component and r["status"] == "AVAILABLE"
        ]
        return {
            "source": "inventario",
            "tenant_id": tenant,
            "from_at": start,
            "history_until": end,
            "as_of": datetime.now(timezone.utc),
            "observed_at": datetime.now(timezone.utc),
            "component": component,
            "observations": observations,
            "lots": lots,
            "resources": resources,
            "reservations": reservations,
            "lineage": lineage,
            "readings": readings,
            "quality_policy": "RECORDED-DAILY-1: sin evento registrado cuenta cero; no acredita ausencia física de consumo",
        }
