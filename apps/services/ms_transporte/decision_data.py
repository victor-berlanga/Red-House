"""Owner compares durable transitions with its MongoDB projection."""

from flask import current_app, g
from redhouse.api import endpoint
from redhouse.db import transaction
from redhouse.errors import APIError
from redhouse.events import mongodb


def install(app):
    @endpoint(
        app, "/api/v1/decision-data", roles=("MEDICAL",), result={"type": "object"}
    )
    def transport_decision_data():
        with transaction() as conn:
            rows = conn.execute(
                "SELECT id,sequence FROM shipments WHERE origin_id=%s OR destination_id=%s ORDER BY id LIMIT 1001",
                (g.actor["tenant_id"], g.actor["tenant_id"]),
            ).fetchall()
            if len(rows) > 1000:
                raise APIError("volume_limit", "Más de 1000 traslados.", 422)
            with mongodb() as mongo:
                collection = mongo[
                    current_app.config["MONGODB_DATABASE"]
                ].shipment_tracking
                for row in rows:
                    transitions = conn.execute(
                        "SELECT sequence FROM transitions WHERE shipment_id=%s ORDER BY sequence",
                        (row["id"],),
                    ).fetchall()
                    row["sequences"] = [t["sequence"] for t in transitions]
                    projected = collection.find_one({"_id": str(row["id"])})
                    row["projection_version"] = (
                        projected["version"] if projected else None
                    )
        return {"source": "transporte", "shipments": rows}
