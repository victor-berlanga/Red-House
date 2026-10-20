"""Vista documental mutable del último paso logístico; eventos originales inmutables."""

from flask import current_app, g
from pymongo.errors import DuplicateKeyError, PyMongoError

from redhouse.api import endpoint
from redhouse.db import get, transaction
from redhouse.errors import APIError
from redhouse.events import mongodb


def project(database, event):
    metadata = event.get("metadata", {})
    if event.get("source") != "transporte" or "sequence" not in metadata:
        return
    identifier, version = event["resource_id"], metadata["sequence"]
    snapshot = {
        "shipment_id": identifier,
        "schema_version": 1,
        "version": version,
        "region_id": event["region_id"],
        "origin_id": metadata["origin_id"],
        "destination_id": metadata["destination_id"],
        "transport_user_id": metadata["transport_user_id"],
        "reservation_id": metadata["reservation_id"],
        "last_state": metadata["state"],
        "last_event_id": event["event_id"],
        "occurred_at": event["occurred_at"],
        "owner": "transporte",
    }
    collection = database.shipment_tracking
    try:
        collection.update_one(
            {"_id": identifier, "version": {"$lt": version}},
            {"$set": snapshot},
            upsert=True,
        )
    except DuplicateKeyError:
        # A duplicate delivery or an older sequence cannot rewind the projection.
        stored = collection.find_one({"_id": identifier})
        if (
            stored
            and stored["version"] == version
            and stored["last_event_id"] != event["event_id"]
        ):
            raise APIError(
                "projection_conflict", "Secuencia documental contradictoria.", 409
            ) from None
        if stored is None or stored["version"] < version:
            collection.update_one(
                {"_id": identifier, "version": {"$lt": version}}, {"$set": snapshot}
            )


def rebuild(database):
    """Reaplica eventos completos; el administrador prepara la colección vacía."""
    count = 0
    for event in database.events.find(
        {"source": "transporte", "metadata.sequence": {"$exists": True}}
    ).sort([("resource_id", 1), ("metadata.sequence", 1)]):
        project(database, event)
        count += 1
    return count


def install(app, access):
    app.extensions["project_event"] = project

    @endpoint(
        app,
        "/api/v1/shipments/<identifier>/tracking",
        roles=("TRANSPORT", "COORDINATOR", "OPERATOR", "MEDICAL"),
        summary="Último paso documental con versión y referencia a PostgreSQL",
    )
    def shipment_tracking(identifier):
        with transaction() as conn:
            shipment = get(conn, "shipments", identifier)
            access(shipment)
        try:
            with mongodb() as client:
                row = client[
                    current_app.config["MONGODB_DATABASE"]
                ].shipment_tracking.find_one({"_id": identifier}, {"_id": 0})
            if row is None:
                raise APIError(
                    "projection_pending",
                    "Seguimiento pendiente de sincronización.",
                    404,
                )
            return dict(row, pending=row["version"] < shipment["sequence"])
        except PyMongoError:
            raise APIError(
                "mongodb_unavailable",
                "Seguimiento documental temporalmente inaccesible.",
                503,
            ) from None

    @endpoint(
        app,
        "/api/v1/shipment-statistics",
        roles=("COORDINATOR",),
        summary="Agregación regional del último paso documental de cada traslado",
    )
    def shipment_statistics():
        try:
            with mongodb() as client:
                rows = list(
                    client[
                        current_app.config["MONGODB_DATABASE"]
                    ].shipment_tracking.aggregate(
                        [
                            {"$match": {"region_id": g.actor["region_id"]}},
                            {"$group": {"_id": "$last_state", "count": {"$sum": 1}}},
                            {"$sort": {"_id": 1}},
                            {"$project": {"_id": 0, "last_state": "$_id", "count": 1}},
                        ]
                    )
                )
            return {"items": rows, "schema_version": 1}
        except PyMongoError:
            raise APIError(
                "mongodb_unavailable", "Estadísticas documentales inaccesibles.", 503
            ) from None
