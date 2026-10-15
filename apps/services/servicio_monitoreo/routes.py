from time import perf_counter
from uuid import uuid4
from datetime import datetime, timedelta, timezone

import requests
from flask import current_app, g

from redhouse.api import endpoint, listing
from redhouse.config import SERVICES
from redhouse.db import insert, transaction
from redhouse.events import queue, deliver_mongo, mongodb
from redhouse.errors import APIError
from pymongo.errors import PyMongoError


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
        identifier = str(uuid4())
        observed_at = datetime.now(timezone.utc)
        event = {
            "event_id": identifier,
            "source": "monitoreo",
            "service": service,
            "state": state,
            "elapsed_ms": elapsed,
            "dependency": dependency,
            "error": error,
            "version": version,
            "checked_at": observed_at.isoformat(),
        }
        # Persist before touching the database being monitored. MongoDB is an
        # independent dependency; a PostgreSQL outage cannot discard this sample.
        mongo_saved = False
        try:
            deliver_mongo(event)
            mongo_saved = True
        except APIError:
            current_app.logger.warning(
                "monitor_document_store_unavailable service=%s", service
            )
        row = dict(
            id=identifier,
            service=service,
            state=state,
            elapsed_ms=elapsed,
            dependency=dependency,
            last_error=error,
            version=version,
            created_at=observed_at,
        )
        try:
            with transaction() as conn:
                row = insert(conn, "checks", row)
                if not mongo_saved:
                    queue(conn, event, "mongodb")
        except APIError as exc:
            if exc.code != "database_unavailable":
                raise
            if not mongo_saved:
                # Technical observation only; no secrets, clinical data or tokens.
                current_app.logger.error(
                    "monitor_sample_unpersisted service=%s state=%s dependency=%s",
                    service,
                    state,
                    dependency,
                )
        checked.append(row)
    return {"items": checked}


def documentary_status():
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    try:
        with mongodb() as client:
            collection = client[current_app.config["MONGODB_DATABASE"]].events
            pipeline = [
                {"$match": {"source": "monitoreo", "checked_at": {"$exists": True}}},
                {"$sort": {"checked_at": -1}},
                {"$group": {"_id": "$service", "sample": {"$first": "$$ROOT"}}},
            ]
            latest = []
            for item in collection.aggregate(pipeline):
                e = item["sample"]
                latest.append(
                    dict(
                        id=e["event_id"],
                        service=e["service"],
                        state=e["state"],
                        elapsed_ms=e["elapsed_ms"],
                        dependency=e.get("dependency"),
                        last_error=e.get("error"),
                        version=e.get("version"),
                        created_at=datetime.fromisoformat(e["checked_at"]),
                    )
                )
            totals = []
            for item in collection.aggregate(
                [
                    {"$match": {"source": "monitoreo", "checked_at": {"$gte": cutoff}}},
                    {
                        "$group": {
                            "_id": "$service",
                            "checks": {"$sum": 1},
                            "errors": {
                                "$sum": {"$cond": [{"$eq": ["$state", "up"]}, 0, 1]}
                            },
                            "average_ms": {"$avg": "$elapsed_ms"},
                        }
                    },
                ]
            ):
                item["service"] = item.pop("_id")
                item["availability_percent"] = (
                    100 * (item["checks"] - item["errors"]) / item["checks"]
                )
                totals.append(item)
            return sorted(latest, key=lambda x: x["service"]), sorted(
                totals, key=lambda x: x["service"]
            )
    except PyMongoError:
        raise APIError(
            "monitor_storage_unavailable",
            "Los almacenes de monitoreo no están disponibles.",
            503,
        ) from None


def register(app):
    @endpoint(
        app,
        "/api/v1/status",
        roles=("ADMIN", "COORDINATOR", "AUDITOR"),
        summary="Estado, promedio, último error, versión e historial resumido",
    )
    def status():
        try:
            with transaction() as conn:
                latest = conn.execute(
                    "SELECT DISTINCT ON (service) * FROM checks ORDER BY service,created_at DESC,id"
                ).fetchall()
                totals = conn.execute(
                    "SELECT service,count(*) AS checks,count(*) FILTER(WHERE state<>'up') AS errors,"
                    "avg(elapsed_ms) AS average_ms,100.0*count(*) FILTER(WHERE state='up')/count(*) AS availability_percent "
                    "FROM checks WHERE created_at>now()-interval '24 hours' GROUP BY service"
                ).fetchall()
        except APIError as exc:
            if exc.code != "database_unavailable":
                raise
            latest, totals = documentary_status()
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
