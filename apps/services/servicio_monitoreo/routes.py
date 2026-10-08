from time import perf_counter
from uuid import uuid4
from datetime import datetime, timedelta, timezone

import requests
from flask import current_app, g

from redhouse.api import endpoint, listing
from redhouse.config import SERVICES
from redhouse.db import insert, transaction
from redhouse.events import queue


def poll():
    checked = []
    for service in SERVICES:
        url = current_app.config["SERVICE_URLS"].get(service)
        start = perf_counter()
        state, dependency, error, version = "down", None, "unconfigured", None
        if url:
            try:
                response = requests.get(
                    url.rstrip("/") + "/health/ready",
                    timeout=(1, 3),
                    allow_redirects=False,
                )
                data = response.json()["data"]
                if response.status_code not in (200, 503) or data["state"] not in (
                    "up",
                    "degraded",
                ):
                    raise ValueError()
                state, version = data["state"], data["version"]
                dependencies = [
                    name
                    for name, value in data["dependencies"].items()
                    if value["state"] in ("down", "degraded")
                ]
                dependency = ",".join(dependencies) or None
                error = "dependency_unavailable" if dependencies else None
            except (requests.RequestException, ValueError, KeyError, TypeError):
                state, error = "down", "unreachable_or_invalid_response"
        elapsed = round((perf_counter() - start) * 1000, 3)
        with transaction() as conn:
            row = insert(
                conn,
                "checks",
                dict(
                    id=str(uuid4()),
                    service=service,
                    state=state,
                    elapsed_ms=elapsed,
                    dependency=dependency,
                    last_error=error,
                    version=version,
                ),
            )
            event = {
                "event_id": str(row["id"]),
                "source": "monitoreo",
                "service": service,
                "state": state,
                "elapsed_ms": elapsed,
                "dependency": dependency,
                "error": error,
                "version": version,
            }
            queue(conn, event, "mongodb")
        checked.append(row)
    return {"items": checked}


def register(app):
    @endpoint(
        app,
        "/api/v1/status",
        roles=("ADMIN", "COORDINATOR", "AUDITOR"),
        summary="Estado, promedio, último error, versión e historial resumido",
    )
    def status():
        with transaction() as conn:
            latest = conn.execute(
                "SELECT DISTINCT ON (service) * FROM checks ORDER BY service,created_at DESC,id"
            ).fetchall()
            totals = conn.execute(
                "SELECT service,count(*) AS checks,count(*) FILTER(WHERE state<>'up') AS errors,"
                "avg(elapsed_ms) AS average_ms,100.0*count(*) FILTER(WHERE state='up')/count(*) AS availability_percent "
                "FROM checks WHERE created_at>now()-interval '24 hours' GROUP BY service"
            ).fetchall()
        for row in latest:
            row["stale"] = row["created_at"] < datetime.now(timezone.utc) - timedelta(
                seconds=120
            )
            if row["stale"]:
                row["observed_state"] = row["state"]
                row.update(
                    state="degraded", dependency="monitoreo", last_error="stale_check"
                )
        return {
            "latest": latest,
            "statistics": totals,
            "window_hours": 24,
            "notice": "Estado técnico global, sin datos clínicos. Estadísticas de las últimas 24 horas; un sondeo vencido no acredita disponibilidad actual.",
        }

    @endpoint(
        app,
        "/api/v1/checks",
        roles=("ADMIN", "COORDINATOR", "AUDITOR"),
        paginated=True,
        summary="Historial persistente de verificaciones",
    )
    def checks_list():
        with transaction() as conn:
            return listing(conn, "checks", "true", ())
