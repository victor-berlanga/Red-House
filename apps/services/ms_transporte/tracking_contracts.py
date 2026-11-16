"""Contrato WGS84 v1, independiente de la marca y del transporte del GPS."""

import json
from typing import Annotated, Literal

from lxml import etree as E
from pydantic import Field, ValidationError, model_validator

from redhouse.codec import XML_SCHEMA_COMPILE_LOCK, request_xsd, _decode, _pairs
from redhouse.errors import APIError
from redhouse.examples import request_xml
from redhouse.models import ID, Model, Text


class Position(Model):
    schema_version: Literal[1] = 1
    event_id: ID
    shipment_id: ID
    device_id: ID
    source: Literal["SIMULATOR", "GPS_BRIDGE", "ANDROID", "IOS"]
    simulated: bool = False
    sequence: Annotated[int, Field(ge=0, le=9007199254740991)]
    captured_at: Text
    latitude: Annotated[float, Field(ge=-90, le=90)] | None = None
    longitude: Annotated[float, Field(ge=-180, le=180)] | None = None
    fix_valid: bool
    accuracy_m: Annotated[float, Field(ge=0, le=100000)] | None = None
    speed_m_s: Annotated[float, Field(ge=0, le=1000)] | None = None
    heading_deg: Annotated[float, Field(ge=0, lt=360)] | None = None
    altitude_m: Annotated[float, Field(ge=-12000, le=100000)] | None = None
    battery_percent: Annotated[float, Field(ge=0, le=100)] | None = None

    @model_validator(mode="after")
    def coordinates(self):
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("Par de coordenadas incompleto.")
        if self.fix_valid and self.latitude is None:
            raise ValueError("Fijación válida requiere coordenadas.")
        return self


class StoredPosition(Position):
    cursor: int
    received_at: Text


class Message(Model):
    schema_version: Literal[1] = 1
    type: Literal[
        "authenticate", "subscribe", "unsubscribe", "position.publish", "heartbeat"
    ]
    credential_kind: Literal["user", "device", "browser"] | None = None
    credential: Annotated[str, Field(min_length=40, max_length=8192)] | None = None
    shipment_id: ID | None = None
    cursor: Annotated[int, Field(ge=0, le=9007199254740991)] | None = None
    position: Position | None = None

    @model_validator(mode="after")
    def fields_for_type(self):
        supplied = {
            k
            for k in (
                "credential_kind",
                "credential",
                "shipment_id",
                "cursor",
                "position",
            )
            if getattr(self, k) is not None
        }
        allowed = {
            "authenticate": {"credential_kind", "credential"},
            "subscribe": {"shipment_id", "cursor"},
            "unsubscribe": {"shipment_id"},
            "position.publish": {"position"},
            "heartbeat": set(),
        }[self.type]
        required = allowed - ({"cursor"} if self.type == "subscribe" else set())
        if not required <= supplied <= allowed:
            raise ValueError("Campos incompatibles con el mensaje.")
        return self


class Event(Model):
    schema_version: Literal[1] = 1
    type: Literal[
        "authenticated",
        "subscribed",
        "unsubscribed",
        "position.updated",
        "position.ack",
        "tracking.status",
        "resync.required",
        "error",
        "heartbeat",
    ]
    shipment_id: ID | None = None
    event_id: ID | None = None
    cursor: int | None = None
    position: StoredPosition | None = None
    state: Text | None = None
    code: Text | None = None
    message: Text | None = None


def decode(raw, model=Message, representation="json"):
    if not isinstance(raw, str) or len(raw.encode()) > 16384:
        raise APIError("invalid_message", "Mensaje excesivo o binario.", 400)
    try:
        if representation == "json":
            value = json.loads(
                raw,
                object_pairs_hook=_pairs,
                parse_constant=lambda _: (_ for _ in ()).throw(ValueError()),
            )
        else:
            tree = E.fromstring(
                raw.encode(),
                E.XMLParser(resolve_entities=False, load_dtd=False, no_network=True),
            )
            if tree.getroottree().docinfo.doctype:
                raise ValueError()
            with XML_SCHEMA_COMPILE_LOCK:
                parser = E.XMLParser(
                    resolve_entities=False, load_dtd=False, no_network=True, huge_tree=False
                )
                validator = E.XMLSchema(E.fromstring(request_xsd(model), parser))
            validator.assertValid(tree)
            definition = model.model_json_schema()
            value = _decode(tree, definition, definition)
        return model.model_validate(value).model_dump()
    except (
        ValueError,
        TypeError,
        KeyError,
        ValidationError,
        E.XMLSyntaxError,
        E.DocumentInvalid,
    ):
        raise APIError(
            "invalid_message", "Mensaje contrario al contrato v1.", 400
        ) from None


def encode(value, representation="json", model=Event):
    value = model.model_validate(value).model_dump(exclude_none=True)
    return (
        request_xml(value)
        if representation == "xml"
        else json.dumps(value, allow_nan=False)
    )
