"""Contratos de frames distintos de OpenAPI; generación sin credenciales reales."""

import json

from ms_transporte.tracking_contracts import (
    Position,
    StoredPosition,
    Message,
    Event,
    encode,
)
from redhouse.codec import request_xsd
from redhouse.examples import EXAMPLE_ID


def generate(folder):
    folder.mkdir(parents=True, exist_ok=True)
    for name, model in (
        ("position", Position),
        ("stored-position", StoredPosition),
        ("message", Message),
        ("event", Event),
    ):
        (folder / (name + ".schema.json")).write_text(
            json.dumps(model.model_json_schema(), indent=2, ensure_ascii=False) + "\n"
        )
        (folder / (name + ".xsd")).write_bytes(request_xsd(model))
    position = {
        "schema_version": 1,
        "event_id": EXAMPLE_ID,
        "shipment_id": EXAMPLE_ID,
        "device_id": EXAMPLE_ID,
        "source": "SIMULATOR",
        "sequence": 1,
        "captured_at": "2026-10-28T12:00:00+00:00",
        "fix_valid": True,
        "latitude": 25.6866,
        "longitude": -100.3161,
        "accuracy_m": 8.0,
    }
    stored = dict(position, cursor=1, received_at="2026-10-28T12:00:01+00:00")
    messages = {
        "authenticate": {
            "type": "authenticate",
            "credential_kind": "user",
            "credential": "REEMPLAZAR_POR_CREDENCIAL_PRIVADA_NO_PUBLICAR_0000000000000000000000",
        },
        "subscribe": {"type": "subscribe", "shipment_id": EXAMPLE_ID, "cursor": 0},
        "unsubscribe": {"type": "unsubscribe", "shipment_id": EXAMPLE_ID},
        "position-publish": {"type": "position.publish", "position": position},
        "heartbeat": {"type": "heartbeat"},
    }
    events = {
        "authenticated": {"type": "authenticated"},
        "subscribed": {
            "type": "subscribed",
            "shipment_id": EXAMPLE_ID,
            "cursor": 1,
            "position": stored,
            "state": "LIVE",
        },
        "unsubscribed": {"type": "unsubscribed", "shipment_id": EXAMPLE_ID},
        "position-updated": {
            "type": "position.updated",
            "shipment_id": EXAMPLE_ID,
            "position": stored,
            "cursor": 1,
        },
        "position-ack": {
            "type": "position.ack",
            "shipment_id": EXAMPLE_ID,
            "event_id": EXAMPLE_ID,
            "cursor": 1,
            "state": "PERSISTED_SQL",
        },
        "tracking-status": {
            "type": "tracking.status",
            "shipment_id": EXAMPLE_ID,
            "cursor": 1,
            "state": "STALE",
        },
        "resync-required": {
            "type": "resync.required",
            "shipment_id": EXAMPLE_ID,
            "code": "resync_required",
        },
        "error": {
            "type": "error",
            "code": "forbidden",
            "message": "Traslado fuera del ámbito autorizado.",
        },
    }
    for prefix, values, model in (
        ("client", messages, Message),
        ("server", events, Event),
    ):
        for name, value in values.items():
            for fmt in ("json", "xml"):
                (folder / f"{prefix}-{name}.{fmt}").write_text(
                    encode(value, fmt, model) + "\n"
                )
