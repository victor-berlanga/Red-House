"""Comprobante efímero ligado a sesión, versión de permisos, operación y recurso."""

import hashlib
import json
from flask import g, request
from .errors import APIError
from .security import redis_call, key


def require(operation, resource_id):
    proof = request.headers.get("X-Reauthentication-Proof", "")
    if not 40 <= len(proof) <= 200:
        raise APIError(
            "reauthentication_required",
            "Confirma tu identidad para esta operación.",
            403,
        )
    stored = redis_call(
        lambda r: r.get(key("reauth:" + hashlib.sha256(proof.encode()).hexdigest()))
    )
    expected = {
        "user_id": g.actor["id"],
        "session_id": g.claims["sid"],
        "tenant_id": g.actor["tenant_id"],
        "version": g.actor["version"],
        "operation": operation,
        "resource_id": resource_id,
    }
    if not stored or json.loads(stored) != expected:
        raise APIError(
            "reauthentication_required",
            "Comprobante vencido o de otra operación, sesión o recurso.",
            403,
        )
