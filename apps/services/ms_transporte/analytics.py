"""Tiempos observados de traslados visibles; fechas de servidor, nunca ETA clínica."""

from datetime import datetime, timedelta, timezone
from flask import g, request
from redhouse.api import endpoint
from redhouse.db import transaction
from redhouse.errors import APIError
from redhouse.extension_contracts import schema
from redhouse.models import Model, Text


class Durations(Model):
    from_at: Text
    until_at: Text
    completed: int
    mean_seconds: float | None
    p95_seconds: float | None
    interpretation: Text


def install(app):
    @endpoint(
        app,
        "/api/v1/analytics/transport",
        roles=("MEDICAL", "OPERATOR", "COORDINATOR"),
        query=("days",),
        result=schema(Durations),
    )
    def transport_analytics():
        try:
            days = int(request.args.get("days", 30))
            if not 7 <= days <= 365:
                raise ValueError()
        except ValueError:
            raise APIError("validation", "Ventana entre 7 y 365 días.", 422) from None
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=days)
        where, values = (
            ("s.region_id=%s", (g.actor["region_id"],))
            if g.actor["role"] == "COORDINATOR"
            else (
                "(s.origin_id=%s OR s.destination_id=%s)",
                (g.actor["tenant_id"], g.actor["tenant_id"]),
            )
        )
        with transaction() as conn:
            result = conn.execute(
                "SELECT count(*) AS completed,avg(seconds)::float AS mean_seconds,"
                "percentile_cont(0.95) WITHIN GROUP(ORDER BY seconds) AS p95_seconds FROM ("
                "SELECT extract(epoch FROM a.created_at-c.created_at) AS seconds FROM shipments s "
                "JOIN transitions a ON a.shipment_id=s.id AND a.state='ACCEPTED' "
                "JOIN transitions c ON c.shipment_id=s.id AND c.state='COLLECTED' WHERE "
                + where
                + " AND a.created_at>=%s AND a.created_at<%s) observed",
                (*values, start, end),
            ).fetchone()
        return dict(
            result,
            from_at=start.isoformat(),
            until_at=end.isoformat(),
            interpretation="Tiempo entre registros de recolección y recepción. Excluye traslados abiertos; no mide viabilidad clínica ni tiempo de conducción puro.",
        )
