"""Presentación de resultados según contratos; nunca reenvía una escritura."""

import hashlib
import json

from ..access import BusinessError
from .client import call


def reservation_status(data, command_key):
    fingerprint = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
    try:
        return call(
            "inventario",
            "/api/v1/operations/by-key/" + command_key,
            params={"fingerprint": fingerprint},
        )
    except BusinessError as exc:
        if exc.status == 404:
            return None
        raise


def notice(path, result):
    if isinstance(result, dict) and "operation_id" in result:
        state = result.get("status")
        if state == "COMPLETED":
            return "Operación finalizada y confirmada.", "success", False
        if state == "FAILED":
            return (
                "La operación no se completó. Revisa su seguimiento antes de iniciar otra.",
                "error",
                True,
            )
        return (
            "Operación pendiente de confirmación. Consulta su seguimiento; no inicies otra reserva.",
            "warning",
            True,
        )
    if isinstance(result, dict) and result.get("inventory_pending"):
        return (
            "Plan registrado, pendiente de confirmación del inventario. Consulta el traslado antes de continuar.",
            "warning",
            True,
        )
    if path.startswith("/api/v1/export-jobs"):
        return (
            "Exportación solicitada. La descarga estará disponible cuando termine la generación y el análisis.",
            "info",
            True,
        )
    return "Cambio registrado.", "success", False
