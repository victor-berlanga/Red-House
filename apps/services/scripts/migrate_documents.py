"""Migración documental explícita, aditiva e idempotente; no altera eventos."""

import argparse
import json
import sys
from pathlib import Path

from pymongo import MongoClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def migrate(client):
    database = client.rh_transporte
    if "shipment_tracking" not in database.list_collection_names():
        database.create_collection("shipment_tracking")
    database.shipment_tracking.create_index(
        [("region_id", 1), ("last_state", 1)], name="regional_state"
    )
    database.events.create_index(
        [("resource_id", 1), ("metadata.sequence", 1)], name="shipment_sequence"
    )
    database.command(
        "updateRole",
        "journal_writer",
        privileges=[
            {
                "resource": {"db": "rh_transporte", "collection": "events"},
                "actions": ["find", "insert"],
            },
            {
                "resource": {"db": "rh_transporte", "collection": "shipment_tracking"},
                "actions": ["find", "insert", "update"],
            },
        ],
        roles=[],
    )
    client.rh_monitoreo.events.create_index(
        [("source", 1), ("checked_at", -1), ("service", 1)], name="monitor_window"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args()
    state = json.loads((args.directory / "state.json").read_text())
    with MongoClient(state["mongo_admin"]) as client:
        migrate(client)
    print(
        "Proyección, permisos mínimos e índices documentales preparados; eventos conservados."
    )
