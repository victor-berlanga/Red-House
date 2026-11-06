"""Historia por referencia sin revelar identidades de donantes o receptores."""

from flask import g

from redhouse.api import endpoint
from redhouse.client import call
from redhouse.db import get, transaction
from redhouse.errors import APIError
from redhouse.extension_contracts import schema
from redhouse.models import Model, ID, Text
from redhouse.security import own


from redhouse.trace_contract import TraceEvent


class Trace(Model):
    resource_id: ID
    donation_id: ID | None
    parent_ids: list[ID]
    child_ids: list[ID]
    shipment_ids: list[ID]
    events: list[TraceEvent]
    restricted_or_unavailable_sources: list[Text]
    final_destination_recorded: bool
    notice: Text


def install(app):
    @endpoint(
        app,
        "/api/v1/resources/<identifier>/trace",
        roles=("MEDICAL",),
        result=schema(Trace),
    )
    def resource_trace(identifier):
        with transaction() as conn:
            row = get(conn, "resources", identifier)
            own(row["current_institution_id"])
            links = conn.execute(
                "SELECT parent_id,child_id FROM resource_lineage WHERE parent_id=%s OR child_id=%s",
                (identifier, identifier),
            ).fetchall()
            events = conn.execute(
                "SELECT id,event->>'source' AS source,event->>'action' AS action,event->>'occurred_at' AS occurred_at "
                "FROM activity_events WHERE event->>'resource_id'=%s ORDER BY created_at,id LIMIT 2000",
                (identifier,),
            ).fetchall()
            allocations = conn.execute(
                "SELECT id,shipment_id FROM reservations WHERE resource_id=%s AND (origin_id=%s OR destination_id=%s)",
                (identifier, g.actor["tenant_id"], g.actor["tenant_id"]),
            ).fetchall()
            final = bool(
                conn.execute(
                    "SELECT 1 FROM resource_destinations WHERE resource_id=%s",
                    (identifier,),
                ).fetchone()
            )
        restricted = []
        sources = [
            (
                "compatibilidad",
                "/api/v1/laboratory/resources/" + identifier + "/history",
            )
        ]
        if row["donation_id"]:
            sources.append(
                ("donantes", f"/api/v1/donations/{row['donation_id']}/history")
            )
        for service, path in sources:
            try:
                events.extend(call(service, "GET", path)["events"])
            except APIError as exc:
                if exc.status in (403, 404, 503):
                    restricted.append(service)
                else:
                    raise
        shipment_ids = [str(a["shipment_id"]) for a in allocations if a["shipment_id"]]
        for shipment_id in shipment_ids:
            try:
                chain = call("custodia", "GET", "/api/v1/chains/" + shipment_id)
                events.extend(
                    {
                        "id": str(e["id"]),
                        "source": "custodia",
                        "action": e["event"]["action"],
                        "occurred_at": e["event"]["occurred_at"],
                    }
                    for e in chain["events"]
                )
            except APIError as exc:
                if exc.status in (403, 404, 503):
                    restricted.append("custodia")
                else:
                    raise
        events.sort(key=lambda e: (str(e["occurred_at"]), str(e["id"])))
        return {
            "resource_id": identifier,
            "donation_id": row["donation_id"],
            "events": events,
            "parent_ids": [
                str(l["parent_id"]) for l in links if str(l["child_id"]) == identifier
            ],
            "child_ids": [
                str(l["child_id"]) for l in links if str(l["parent_id"]) == identifier
            ],
            "shipment_ids": shipment_ids,
            "restricted_or_unavailable_sources": sorted(set(restricted)),
            "final_destination_recorded": final,
            "notice": "Recepción logística y uso clínico son hechos distintos. Referencias no conceden acceso a expedientes de otra institución.",
        }
