"""Referencia HTTP a ubicaciones; nunca consulta tablas de Identidad."""

from redhouse.client import call
from redhouse.errors import APIError


def validate_location(identifier):
    if identifier:
        row = call("identidad_acceso", "GET", "/internal/v1/locations/" + identifier)
        if not row["active"]:
            raise APIError("conflict", "Ubicación inactiva.", 409)
