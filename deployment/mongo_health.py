"""MongoDB process readiness; application probes also validate their credentials."""

from pymongo import MongoClient

with MongoClient(
    "mongodb://127.0.0.1:27017",
    serverSelectionTimeoutMS=1500,
    connectTimeoutMS=1500,
    socketTimeoutMS=1500,
) as client:
    if client.admin.command("ping").get("ok") != 1:
        raise SystemExit(1)
