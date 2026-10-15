import hashlib
import json
import atexit
from contextlib import contextmanager
from threading import Lock
from uuid import uuid4

from flask import current_app, g
from psycopg.types.json import Jsonb
from pymongo import MongoClient
from pymongo.errors import PyMongoError

from .client import call
from .codec import plain
from .db import insert, transaction
from .errors import APIError


def emit(
    conn, action, resource_id, tenant_id, *, targets=("auditoria",), metadata=None
):
    actor = getattr(g, "actor", {})
    event = {
        "event_id": str(uuid4()),
        "source": current_app.config["SERVICE"],
        "action": action,
        "resource_id": str(resource_id),
        "tenant_id": str(tenant_id),
        "region_id": actor.get("region_id"),
        "actor_id": actor.get("id"),
        "correlation_id": getattr(g, "correlation_id", str(uuid4())),
        "metadata": metadata or {},
        "occurred_at": conn.execute("SELECT clock_timestamp() AS time")
        .fetchone()["time"]
        .isoformat(),
    }
    insert(
        conn,
        "activity_events",
        {"id": event["event_id"], "tenant_id": tenant_id, "event": event},
    )
    for target in targets:
        queue(conn, event, target)
    return event


def queue(conn, event, target):
    insert(
        conn,
        "outbox",
        {
            "id": str(uuid4()),
            "event_id": event["event_id"],
            "target": target,
            "event": event,
        },
    )


def audit_read(resource="collection"):
    actor = getattr(g, "actor", None)
    if actor:
        with transaction() as conn:
            emit(conn, "READ", resource, actor["tenant_id"])


_mongo_lock = Lock()


@contextmanager
def mongodb():
    cfg = current_app.config
    if not cfg["MONGODB_URL"]:
        raise APIError("mongodb_unconfigured", "MongoDB no configurado.", 503)
    with _mongo_lock:
        clients = current_app.extensions.setdefault("mongo_clients", {})
        if cfg["MONGODB_URL"] not in clients:
            client = MongoClient(
                cfg["MONGODB_URL"],
                serverSelectionTimeoutMS=1000,
                connectTimeoutMS=1000,
                socketTimeoutMS=1500,
                maxPoolSize=8,
            )
            clients[cfg["MONGODB_URL"]] = client
            atexit.register(client.close)
        client = clients[cfg["MONGODB_URL"]]
    yield client


def deliver_mongo(event):
    try:
        with mongodb() as client:
            collection = client[current_app.config["MONGODB_DATABASE"]].events
            # La clave natural impide duplicados tras un timeout de escritura.
            document = dict(event, _id=event["event_id"])
            from pymongo.errors import DuplicateKeyError

            try:
                collection.insert_one(document)
            except DuplicateKeyError:
                stored = collection.find_one({"_id": document["_id"]})
                if stored != document:
                    raise APIError(
                        "event_conflict", "Evento repetido con contenido distinto.", 409
                    )
    except PyMongoError:
        raise APIError(
            "mongodb_unavailable", "MongoDB temporalmente inaccesible.", 503
        ) from None


def dispatch(limit=100):
    """Entrega como mínimo una vez; consumidores deduplican. Sin secretos en errores."""
    done, failed = 0, 0
    blocked = set()
    for _ in range(limit):
        with transaction() as conn:
            row = conn.execute(
                "SELECT * FROM outbox WHERE delivered_at IS NULL AND next_attempt<=now() "
                "AND NOT(target=ANY(%s)) ORDER BY created_at,id FOR UPDATE SKIP LOCKED LIMIT 1",
                (list(blocked),),
            ).fetchone()
            if not row:
                break
            try:
                if row["target"] == "mongodb":
                    deliver_mongo(row["event"])
                else:
                    call(
                        row["target"],
                        "POST",
                        "/internal/v1/events",
                        row["event"],
                        delegate=False,
                    )
                conn.execute(
                    "UPDATE outbox SET delivered_at=now(),attempts=attempts+1,last_error=NULL WHERE id=%s",
                    (row["id"],),
                )
                done += 1
            except APIError as exc:
                conn.execute(
                    "UPDATE outbox SET attempts=attempts+1,last_error=%s,next_attempt=now()+interval '2 seconds' WHERE id=%s",
                    (exc.code, row["id"]),
                )
                failed += 1
                if exc.status == 503:
                    blocked.add(row["target"])
    return {"delivered": done, "failed": failed}


def consume(conn, event):
    serialized = json.dumps(event, sort_keys=True, separators=(",", ":"))
    fingerprint = hashlib.sha256(serialized.encode()).hexdigest()
    conn.execute(
        "SELECT pg_advisory_xact_lock(hashtextextended(%s, 51))", (event["event_id"],)
    )
    old = conn.execute(
        "SELECT fingerprint FROM inbox WHERE event_id=%s", (event["event_id"],)
    ).fetchone()
    if old is None:
        conn.execute(
            "INSERT INTO inbox(event_id,fingerprint) VALUES(%s,%s)",
            (event["event_id"], fingerprint),
        )
        return True
    if old["fingerprint"] != fingerprint:
        raise APIError("event_conflict", "Evento repetido con contenido distinto.", 409)
    return False
