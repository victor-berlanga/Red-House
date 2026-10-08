import hashlib
import json

from flask import g

from redhouse.api import endpoint
from redhouse.client import call
from redhouse.db import get, insert, transaction, update
from redhouse.errors import APIError
from redhouse.event_model import Event
from redhouse.events import consume, queue


def register(app):
    @endpoint(
        app,
        "/internal/v1/events",
        "POST",
        model=Event,
        internal=("transporte",),
        delegate=False,
        summary="Custodia secuencial, deduplicada e inmutable",
    )
    def custody_ingest(data):
        if data["source"] != g.caller or not data["region_id"]:
            raise APIError("forbidden", "Fuente o región de evento incorrectas.", 403)
        meta = data["metadata"]
        required = {
            "sequence",
            "origin_id",
            "destination_id",
            "state",
            "reservation_id",
        }
        if (
            not required <= meta.keys()
            or type(meta["sequence"]) is not int
            or meta["sequence"] < 1
        ):
            raise APIError("validation", "Evento de custodia incompleto.", 422)
        with transaction() as conn:
            if not consume(conn, data):
                return {"duplicate": True}
            conn.execute(
                "INSERT INTO chains(id,region_id,origin_id,destination_id) VALUES(%s,%s,%s,%s) ON CONFLICT DO NOTHING",
                (
                    data["resource_id"],
                    data["region_id"],
                    meta["origin_id"],
                    meta["destination_id"],
                ),
            )
            chain = get(conn, "chains", data["resource_id"], True)
            if meta["sequence"] != chain["last_sequence"] + 1:
                raise APIError(
                    "sequence_gap",
                    "Evento anterior pendiente; no se altera la secuencia.",
                    409,
                )
            serialized = json.dumps(data, sort_keys=True, separators=(",", ":"))
            digest = hashlib.sha256(
                (chain["last_hash"] + serialized).encode()
            ).hexdigest()
            row = insert(
                conn,
                "custody_events",
                dict(
                    id=data["event_id"],
                    shipment_id=data["resource_id"],
                    sequence=meta["sequence"],
                    event=data,
                    previous_hash=chain["last_hash"],
                    hash=digest,
                ),
            )
            update(
                conn,
                "chains",
                data["resource_id"],
                {"last_sequence": meta["sequence"], "last_hash": digest},
            )
            queue(
                conn,
                dict(
                    data,
                    metadata=dict(meta, previous_hash=chain["last_hash"], hash=digest),
                ),
                "mongodb",
            )
            return {"stored": True, "sequence": row["sequence"], "hash": digest}

    @endpoint(
        app,
        "/api/v1/chains/<identifier>",
        roles=("TRANSPORT", "COORDINATOR", "OPERATOR", "MEDICAL", "AUDITOR"),
        summary="Consultar cadena; hash detecta alteraciones, no certifica veracidad física",
    )
    def chain_detail(identifier):
        with transaction() as conn:
            chain = get(conn, "chains", identifier)
            if str(chain["region_id"]) != g.actor["region_id"]:
                raise APIError("forbidden", "Custodia fuera de la región.", 403)
        if g.actor["role"] != "AUDITOR":
            call(
                "transporte", "GET", "/internal/v1/shipments/" + identifier + "/access"
            )
        with transaction() as conn:
            rows = conn.execute(
                "SELECT * FROM custody_events WHERE shipment_id=%s ORDER BY sequence",
                (identifier,),
            ).fetchall()
        return {
            "chain": chain,
            "events": rows,
            "notice": "Recepción no significa transfusión ni trasplante. Evidencia inmutable bajo credenciales de aplicación; no impide intervención del propietario de base.",
        }
