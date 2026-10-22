"""Instantánea minimizada al ejecutar la operación; nunca reconstruye identidad histórica."""

from uuid import UUID

from flask import g
from psycopg import sql

from .audit_catalog import describe
from .codec import plain

TABLES = {
    "DONOR": "donors",
    "DONATION": "donations",
    "CAMPAIGN": "campaigns",
    "APPOINTMENT": "appointments",
    "RECIPIENT": "recipients",
    "REQUEST": "requests",
    "CAPACITY": "requests",
    "RESOURCE": "resources",
    "RESERVATION": "reservations",
    "EVALUATION": "evaluations",
    "ROUTE": "routes",
    "SHIPMENT": "shipments",
    "FILE": "files",
    "TELEMETRY": "shipments",
    "RANKING": "rankings",
    "ALLOCATION": "proposals",
    "CATALOGUE": "catalogue",
}
RELATED = (
    "request_id",
    "resource_id",
    "reservation_id",
    "shipment_id",
    "evaluation_id",
    "donation_id",
    "donor_id",
    "hold_id",
    "operation_id",
)


def snapshot(conn, action, resource_id, metadata):
    actor = getattr(g, "actor", {})
    result = {
        "actor_name": actor.get("username"),
        "actor_role": actor.get("role"),
        "actor_institution_id": actor.get("tenant_id"),
        "result": describe(action)[2],
    }
    if action == "LOGIN_FAILED":
        result.update(actor_name=None, actor_role=None, actor_institution_id=None)
    context = getattr(g, "audit_changes", {}).get(str(resource_id), {})
    result.update(context)
    if getattr(g, "validated_reason", None):
        result["reason"] = g.validated_reason
    related = {str(resource_id)}
    table = (
        "reservations"
        if action == "RESOURCE_RESERVED"
        else TABLES.get(action.split("_", 1)[0])
    )
    try:
        UUID(str(resource_id))
    except (ValueError, TypeError):
        table = None
    if table:
        row = conn.execute(
            sql.SQL("SELECT * FROM {} WHERE id=%s").format(sql.Identifier(table)),
            (resource_id,),
        ).fetchone()
        if row:
            if row.get("folio"):
                result["resource_folio"] = row["folio"]
            related.update(str(row[k]) for k in RELATED if row.get(k))
    related.update(str(metadata[k]) for k in RELATED if metadata.get(k))
    result["related_resources"] = sorted(related)
    return plain(result)
