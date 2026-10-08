"""Carga contratos públicos explícitos del servicio, nunca inspecciona tablas."""

import json
from functools import lru_cache
from .schema import service_path


def object_schema(properties, required=None):
    return {
        "type": "object",
        "properties": properties,
        "required": list(properties) if required is None else required,
    }


@lru_cache(maxsize=32)
def outputs(service):
    return json.loads((service_path(service) / "outputs.json").read_text())


def result_schema(service, name):
    return outputs(service).get(name, {"type": "object", "additionalProperties": True})
