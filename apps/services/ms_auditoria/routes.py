from flask import g

from redhouse.api import endpoint, listing
from redhouse.config import SERVICES
from redhouse.db import insert, transaction
from redhouse.errors import APIError
from redhouse.event_model import Event
from redhouse.events import consume, mongodb, queue


def register(app):
    @endpoint(
        app,
        "/internal/v1/events",
        "POST",
        model=Event,
        internal=tuple(SERVICES),
        delegate=False,
        summary="Recibir registro minimizado y conservarlo de forma inmutable",
    )
    def audit_ingest(data):
        if data["source"] != g.caller or not data["region_id"]:
            raise APIError("forbidden", "Fuente o región de evento incorrectas.", 403)
        with transaction() as conn:
            if not consume(conn, data):
                return {"duplicate": True}
            insert(
                conn,
                "audit_events",
                dict(
                    id=data["event_id"],
                    tenant_id=data["tenant_id"],
                    region_id=data["region_id"],
                    source=data["source"],
                    action=data["action"],
                    actor_id=data["actor_id"],
                    event=data,
                ),
            )
            queue(conn, data, "mongodb")
        return {"stored": True}

    @endpoint(
        app,
        "/api/v1/events",
        roles=("AUDITOR",),
        paginated=True,
        summary="Bitácora regional de solo lectura; sin credenciales ni contenido clínico",
    )
    def audit_list():
        with transaction() as conn:
            return listing(
                conn, "audit_events", "region_id=%s", (g.actor["region_id"],)
            )

    @endpoint(
        app,
        "/api/v1/events/<identifier>",
        roles=("AUDITOR",),
        summary="Evento auditable y correlación",
    )
    def audit_detail(identifier):
        from redhouse.db import get

        with transaction() as conn:
            row = get(conn, "audit_events", identifier)
            if str(row["region_id"]) != g.actor["region_id"]:
                raise APIError("forbidden", "Evento fuera de la región.", 403)
            return row

    @endpoint(
        app,
        "/api/v1/documentary-events",
        roles=("AUDITOR",),
        paginated=True,
        summary="Proyección documental MongoDB; puede estar pendiente de sincronización",
    )
    def documentary_events():
        from redhouse.api import pagination
        from pymongo.errors import PyMongoError

        page, size, offset = pagination()
        try:
            with mongodb() as client:
                collection = client[app.config["MONGODB_DATABASE"]].events
                query = {"region_id": g.actor["region_id"]}
                rows = list(
                    collection.find(query, {"_id": 0})
                    .sort("_id", 1)
                    .skip(offset)
                    .limit(size)
                )
                return {
                    "items": rows,
                    "page": page,
                    "page_size": size,
                    "total": collection.count_documents(query),
                }
        except PyMongoError:
            raise APIError(
                "mongodb_unavailable",
                "Proyección documental temporalmente inaccesible.",
                503,
            ) from None
