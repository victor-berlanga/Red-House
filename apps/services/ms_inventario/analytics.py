"""Tendencias operativas y pronóstico empírico explícito; ninguna asignación."""

from datetime import datetime, timedelta, timezone
from math import ceil
from flask import g, request

from redhouse.api import endpoint
from redhouse.client import call
from redhouse.db import transaction
from redhouse.errors import APIError
from redhouse.extension_contracts import schema
from redhouse.models import Model, Text


class Demand(Model):
    kind: Text
    component: Text
    requested_units: int
    open_requested_units: int
    available: int
    gross_gap: int


class Trend(Model):
    day: Text
    used: int
    discarded: int


class Forecast(Model):
    kind: Text
    component: Text
    available: int
    expiring_in_seven_days: int
    observed_use: int
    observed_days: int
    empirical_daily_use: float | None
    estimated_surplus: int | None
    proposal: Text


class Analytics(Model):
    from_at: Text
    until_at: Text
    method: Text
    trends: list[Trend]
    products: list[Forecast]
    limitation: Text
    demand: list[Demand]
    demand_complete: bool
    discarded: int
    used: int


def install(app):
    @endpoint(
        app,
        "/api/v1/analytics/inventory",
        roles=("OPERATOR", "MEDICAL"),
        query=("days",),
        result=schema(Analytics),
    )
    def inventory_analytics():
        try:
            days = int(request.args.get("days", 30))
            if not 7 <= days <= 365:
                raise ValueError()
        except ValueError:
            raise APIError("validation", "Ventana entre 7 y 365 días.", 422) from None
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=days)
        with transaction() as conn:
            # Solo la última corrección del destino contribuye al consumo.
            events = conn.execute(
                "SELECT d.*,r.kind,r.component FROM resource_destinations d JOIN resources r ON r.id=d.resource_id "
                "WHERE d.tenant_id=%s AND d.occurred_at>=%s AND d.occurred_at<%s "
                "AND NOT EXISTS(SELECT 1 FROM resource_destinations newer WHERE newer.supersedes=d.id)",
                (g.actor["tenant_id"], start, end),
            ).fetchall()
            stocks = conn.execute(
                "SELECT kind,component,count(*) AS available,count(*) FILTER(WHERE expires_at<%s) AS expiring "
                "FROM resources WHERE current_institution_id=%s AND status='AVAILABLE' AND expires_at>%s GROUP BY kind,component ORDER BY kind,component",
                (end + timedelta(days=7), g.actor["tenant_id"], end),
            ).fetchall()
        trends = {}
        for row in events:
            day = row["occurred_at"].date().isoformat()
            trend = trends.setdefault(day, {"day": day, "used": 0, "discarded": 0})
            trend["used"] += row["destination"] in ("TRANSFUSED", "TRANSPLANTED")
            trend["discarded"] += row["destination"] == "DISCARDED"
        products = []
        for stock in stocks:
            used = [
                r
                for r in events
                if r["kind"] == stock["kind"]
                and r["component"] == stock["component"]
                and r["destination"] in ("TRANSFUSED", "TRANSPLANTED")
            ]
            observed = len({r["occurred_at"].date() for r in used})
            rate = len(used) / days if observed >= 7 else None
            surplus = (
                max(0, stock["expiring"] - ceil(7 * rate)) if rate is not None else None
            )
            products.append(
                {
                    "kind": stock["kind"],
                    "component": stock["component"],
                    "available": stock["available"],
                    "expiring_in_seven_days": stock["expiring"],
                    "observed_use": len(used),
                    "observed_days": observed,
                    "empirical_daily_use": rate,
                    "estimated_surplus": surplus,
                    "proposal": "INSUFFICIENT_HISTORY"
                    if rate is None
                    else "REVIEW_REDISTRIBUTION"
                    if surplus
                    else "MONITOR_DEMAND",
                }
            )
        demands, complete = {}, False
        for page in range(1, 11):
            result = call(
                "receptores", "GET", f"/api/v1/requests?page_size=100&page={page}"
            )
            for item in result["items"]:
                if (
                    start
                    <= datetime.fromisoformat(item["created_at"].replace("Z", "+00:00"))
                    < end
                ):
                    key = (item["kind"], item["component"])
                    demand = demands.setdefault(
                        key,
                        {
                            "kind": key[0],
                            "component": key[1],
                            "requested_units": 0,
                            "open_requested_units": 0,
                        },
                    )
                    demand["requested_units"] += item["quantity"]
                    if item["status"] in ("OPEN", "IN_PROGRESS"):
                        demand["open_requested_units"] += item["quantity"]
            if page * 100 >= result["total"]:
                complete = True
                break
        for key, demand in demands.items():
            demand["available"] = sum(
                s["available"] for s in stocks if (s["kind"], s["component"]) == key
            )
            demand["gross_gap"] = max(
                0, demand["open_requested_units"] - demand["available"]
            )
        return {
            "from_at": start.isoformat(),
            "until_at": end.isoformat(),
            "method": "EMPIRICAL-USE-1",
            "trends": [trends[k] for k in sorted(trends)],
            "products": products,
            "demand": list(demands.values()),
            "demand_complete": complete,
            "discarded": sum(t["discarded"] for t in trends.values()),
            "used": sum(t["used"] for t in trends.values()),
            "limitation": "Pronóstico: siete fechas de uso mínimo. Demanda: máximo 1000 solicitudes, brecha bruta sin descontar cobertura ni compatibilidad. Sin estacionalidad ni validación clínica.",
        }
