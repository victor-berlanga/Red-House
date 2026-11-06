"""Outbox-fed potential anomalies. Only an authorized human resolves a review."""

from typing import Annotated, Literal
from uuid import uuid4

from flask import g
from pydantic import Field
from redhouse.api import atomic, endpoint, listing
from redhouse.db import get, insert, transaction, update
from redhouse.errors import APIError
from redhouse.events import emit
from redhouse.extension_contracts import page_schema, schema
from redhouse.models import ID, Confirm, Model, Text


class Action(Model):
    id: ID
    review_id: ID
    tenant_id: ID
    author_id: ID
    state: Literal["CONFIRMED", "DISMISSED"]
    reason: Text
    created_at: Text


class Review(Model):
    id: ID
    tenant_id: ID
    region_id: ID
    source: Literal["priorizacion_geografia"]
    source_run_id: ID
    deduplication_key: Text
    evidence: dict
    correlation_id: Text
    responsible_id: ID
    state: Literal["OPEN", "CONFIRMED", "DISMISSED"]
    version: int
    created_at: Text


class ReviewDetail(Review):
    history: list[Action]


def ingest(conn, event):
    if event["action"] != "ANOMALY_REVIEW_REQUESTED":
        return
    if event["source"] != "priorizacion_geografia":
        raise APIError("forbidden", "Propietario de análisis no autorizado.", 403)
    meta = event["metadata"]
    key = meta["deduplication_key"]
    conn.execute(
        "SELECT pg_advisory_xact_lock(hashtextextended(%s,0))", ("anomaly:" + key,)
    )
    if conn.execute(
        "SELECT 1 FROM anomaly_reviews WHERE deduplication_key=%s", (key,)
    ).fetchone():
        return
    insert(
        conn,
        "anomaly_reviews",
        {
            "id": str(uuid4()),
            "tenant_id": event["tenant_id"],
            "region_id": event["region_id"],
            "source": event["source"],
            "source_run_id": event["resource_id"],
            "deduplication_key": key,
            "evidence": {
                "finding": meta["finding"],
                "algorithm_version": meta["algorithm_version"],
            },
            "correlation_id": event["correlation_id"],
            "responsible_id": meta["responsible_id"],
        },
    )


class Resolution(Confirm):
    version: Annotated[int, Field(ge=1)]
    state: Literal["CONFIRMED", "DISMISSED"]


def authorized(row):
    if (
        str(row["region_id"]) != g.actor["region_id"]
        or g.actor["role"] != "AUDITOR"
        and str(row["tenant_id"]) != g.actor["tenant_id"]
    ):
        raise APIError("forbidden", "Revisión fuera de ámbito.", 403)


def install(app):
    @endpoint(
        app,
        "/api/v1/anomaly-reviews",
        roles=("MEDICAL", "COORDINATOR", "AUDITOR"),
        paginated=True,
        result=page_schema(Review),
    )
    def anomaly_list():
        with transaction() as conn:
            where, args = (
                ("region_id=%s", (g.actor["region_id"],))
                if g.actor["role"] == "AUDITOR"
                else ("tenant_id=%s", (g.actor["tenant_id"],))
            )
            return listing(conn, "anomaly_reviews", where, args)

    @endpoint(
        app,
        "/api/v1/anomaly-reviews/<identifier>",
        roles=("MEDICAL", "COORDINATOR", "AUDITOR"),
        result=schema(ReviewDetail),
    )
    def anomaly_detail(identifier):
        with transaction() as conn:
            row = get(conn, "anomaly_reviews", identifier)
            authorized(row)
            row["history"] = conn.execute(
                "SELECT * FROM anomaly_actions WHERE review_id=%s ORDER BY created_at,id",
                (identifier,),
            ).fetchall()
            return row

    @endpoint(
        app,
        "/api/v1/anomaly-reviews/<identifier>/resolve",
        "POST",
        model=Resolution,
        roles=("AUDITOR",),
        result=schema(Review),
    )
    def anomaly_resolve(identifier, data):
        def work(conn):
            row = get(conn, "anomaly_reviews", identifier, True)
            authorized(row)
            if row["version"] != data["version"] or row["state"] != "OPEN":
                raise APIError(
                    "stale_version", "Revisión ya resuelta o versión obsoleta.", 412
                )
            insert(
                conn,
                "anomaly_actions",
                {
                    "id": str(uuid4()),
                    "review_id": identifier,
                    "tenant_id": row["tenant_id"],
                    "author_id": g.actor["id"],
                    "state": data["state"],
                    "reason": data["reason"],
                },
            )
            row = update(
                conn,
                "anomaly_reviews",
                identifier,
                {"state": data["state"], "version": row["version"] + 1},
            )
            emit(conn, "ANOMALY_REVIEW_RESOLVED", identifier, row["tenant_id"])
            return row

        return atomic("anomaly_resolve:" + identifier, data, work)
