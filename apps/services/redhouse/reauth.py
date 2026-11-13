"""Reto firmado y prueba ligados a una sola intención idempotente.

El replay idéntico recupera el ledger; no autoriza otra mutación. No se promete
atomicidad distribuida entre la sesión Redis y el commit PostgreSQL.
"""

import base64
import hashlib
import hmac
import json
import re
import secrets
import time

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives.serialization import (
    load_pem_private_key,
    load_pem_public_key,
)
from flask import current_app, g, request

from .db import get, transaction
from .errors import APIError
from .models import validate_id
from .security import authenticate, key, own, redis_call

PURPOSE = "redhouse-reauth-challenge-v1"
MAX_AGE = 120
SCOPES = {
    ("inventario", "resource_release"): ("resources", "tenant_id"),
    ("inventario", "resource_destination"): ("resources", "current_institution_id"),
    ("compatibilidad", "lab_result_review"): ("lab_results", "tenant_id"),
    ("compatibilidad", "evaluation_review"): ("evaluations", "tenant_id"),
    ("compatibilidad", "rule_transition"): ("lab_profiles", "tenant_id"),
    ("auditoria", "anomaly_resolve"): ("anomaly_reviews", "region_id"),
    ("identidad_acceso", "user_state"): ("users", "tenant_id"),
    ("identidad_acceso", "user_role"): ("users", "tenant_id"),
    ("inventario", "reservation_create"): (None, None),
}


def canonical(value):
    return json.dumps(
        value, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False
    ).encode()


def body_digest(data):
    secret = current_app.config.get("SERVICE_PRIVATE_KEY", "")
    if not secret:
        raise APIError(
            "reauthentication_unavailable", "Firma de desafío no configurada.", 503
        )
    derived = hashlib.sha256(("redhouse-reauth-body-v1:" + secret).encode()).digest()
    return hmac.new(derived, canonical(data), hashlib.sha256).hexdigest()


def _encode(value):
    return base64.urlsafe_b64encode(value).decode().rstrip("=")


def _decode(value):
    if not re.fullmatch(r"[A-Za-z0-9_-]+", value):
        raise ValueError("invalid encoding")
    decoded = base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
    if _encode(decoded) != value:
        raise ValueError("noncanonical encoding")
    return decoded


def authorize(operation, resource_id, data, conn=None, *, lock=False):
    scope = (current_app.config["SERVICE"], operation)
    if scope not in SCOPES:
        raise APIError(
            "reauthentication_unavailable",
            "Operación crítica sin autorización configurada.",
            503,
        )
    validate_id(resource_id)
    table, tenant_column = SCOPES[scope]
    if operation == "reservation_create":
        from .client import call

        evaluation = call(
            "compatibilidad", "GET", "/internal/v1/evaluations/" + data["evaluation_id"]
        )
        own(evaluation["tenant_id"])
        if not any(
            item["resource_id"] == resource_id for item in evaluation["candidates"]
        ):
            raise APIError("forbidden", "Recurso fuera de ámbito autorizado.", 403)
        return {"tenant_id": str(evaluation["tenant_id"])}
    if conn is None:
        with transaction() as local:
            return authorize(operation, resource_id, data, local, lock=lock)
    # Evaluations and laboratory profiles are append-only. Locking through
    # their access views requires privileges unavailable to service roles.
    immutable = operation in ("evaluation_review", "rule_transition")
    row = get(conn, table, resource_id, lock and not immutable)
    if operation == "anomaly_resolve":
        if str(row["region_id"]) != g.actor["region_id"]:
            raise APIError("forbidden", "Revisión fuera de ámbito.", 403)
    else:
        own(row[tenant_column])
    if operation == "evaluation_review" and not any(
        item["resource_id"] == data["resource_id"] for item in row["candidates"]
    ):
        raise APIError("forbidden", "Recurso fuera de ámbito autorizado.", 403)
    if (
        operation == "user_state"
        and resource_id == g.actor["id"]
        and not data["active"]
    ):
        raise APIError("conflict", "No puedes desactivar tu propia cuenta.", 409)
    if operation == "user_role" and (
        resource_id == g.actor["id"]
        or row["role"] in ("ADMIN", "AUDITOR", "COORDINATOR")
        or data["role"] in ("ADMIN", "AUDITOR", "COORDINATOR")
    ):
        raise APIError("forbidden", "Perfil fuera de ámbito autorizado.", 403)
    return {
        "tenant_id": str(
            row["tenant_id"] if operation == "anomaly_resolve" else row[tenant_column]
        )
    }


def binding(operation, resource_id, data):
    idem = request.headers.get("Idempotency-Key", "")
    if not re.fullmatch(r"[A-Za-z0-9_-]{8,100}", idem):
        raise APIError(
            "idempotency_required",
            "Idempotency-Key de 8–100 caracteres requerido.",
            400,
        )
    if request.query_string:
        raise APIError(
            "validation", "La operación crítica no admite parámetros de consulta.", 400
        )
    return {
        "purpose": PURPOSE,
        "service": current_app.config["SERVICE"],
        "operation": operation,
        "method": request.method,
        "path": request.path,
        "resource_id": resource_id,
        "user_id": g.actor["id"],
        "session_id": g.claims["sid"],
        "tenant_id": g.actor["tenant_id"],
        "version": g.actor["version"],
        "key": idem,
        "body_hash": body_digest(data),
    }


def challenge(bound):
    try:
        private = load_pem_private_key(
            current_app.config["SERVICE_PRIVATE_KEY"].encode(), password=None
        )
    except (ValueError, KeyError, TypeError):
        raise APIError(
            "reauthentication_unavailable", "Firma de desafío no configurada.", 503
        ) from None
    if not isinstance(private, Ed25519PrivateKey):
        raise APIError(
            "reauthentication_unavailable", "Firma de desafío no configurada.", 503
        )
    payload = dict(bound, issued_at=int(time.time()), nonce=secrets.token_urlsafe(24))
    message = canonical(payload)
    return (
        _encode(message)
        + "."
        + _encode(private.sign(PURPOSE.encode() + b"\0" + message))
    )


def verify_challenge(token):
    try:
        if not isinstance(token, str) or len(token) > 4096:
            raise ValueError()
        encoded, signature = token.split(".")
        message = _decode(encoded)
        value = json.loads(message)
        if (
            not isinstance(value, dict)
            or canonical(value) != message
            or value.get("purpose") != PURPOSE
        ):
            raise ValueError()
        issuer, operation = value["service"], value["operation"]
        if (issuer, operation) not in SCOPES:
            raise ValueError()
        public = load_pem_public_key(
            current_app.config["SERVICE_PUBLIC_KEYS"][issuer].encode()
        )
        if not isinstance(public, Ed25519PublicKey):
            raise ValueError()
        public.verify(_decode(signature), PURPOSE.encode() + b"\0" + message)
        now = int(time.time())
        if (
            type(value["issued_at"]) is not int
            or not now - MAX_AGE <= value["issued_at"] <= now
        ):
            raise ValueError()
        if any(
            value[k] != v
            for k, v in {
                "user_id": g.actor["id"],
                "session_id": g.claims["sid"],
                "tenant_id": g.actor["tenant_id"],
                "version": g.actor["version"],
            }.items()
        ):
            raise ValueError()
        return value
    except (ValueError, KeyError, TypeError, InvalidSignature, UnicodeError):
        raise APIError(
            "reauthentication_required",
            "Desafío inválido, vencido o de otro ámbito.",
            403,
        ) from None


def _existing_command(operation, resource_id, data, authorized, conn=None):
    if conn is None:
        with transaction() as local:
            return _existing_command(operation, resource_id, data, authorized, local)
    idem = request.headers.get("Idempotency-Key", "")
    if operation == "reservation_create":
        row = conn.execute(
            "SELECT tenant_id,fingerprint FROM operations WHERE user_id=%s AND key=%s",
            (g.actor["id"], idem),
        ).fetchone()
        expected = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
        if not row:
            return False
        if str(row["tenant_id"]) != authorized["tenant_id"]:
            raise APIError("forbidden", "Resultado fuera del ámbito vigente.", 403)
    else:
        name = operation + ":" + resource_id
        row = conn.execute(
            "SELECT fingerprint,result FROM idempotency WHERE user_id=%s AND key=%s",
            (g.actor["id"], idem),
        ).fetchone()
        expected = hashlib.sha256(
            json.dumps({"operation": name, "input": data}, sort_keys=True).encode()
        ).hexdigest()
        if not row:
            return False
        result = row["result"]
        tenant = result.get("tenant_id") if isinstance(result, dict) else None
        if tenant is None or str(tenant) != authorized["tenant_id"]:
            raise APIError("forbidden", "Resultado fuera del ámbito vigente.", 403)
    if not hmac.compare_digest(row["fingerprint"], expected):
        raise APIError(
            "idempotency_conflict",
            "Clave utilizada para otra operación o contenido.",
            409,
        )
    return True


def _check(operation, resource_id, data, *, conn=None, issue=False, lock=False):
    authorized = authorize(operation, resource_id, data, conn, lock=lock)
    expected = binding(operation, resource_id, data)
    proof = request.headers.get("X-Reauthentication-Proof", "")
    if not proof and _existing_command(operation, resource_id, data, authorized, conn):
        g.reauth_replay_only = True
        return authorized
    stored = None
    if 40 <= len(proof) <= 200:
        stored = redis_call(
            lambda r: r.get(
                key("reauth:v1:" + hashlib.sha256(proof.encode()).hexdigest())
            )
        )
    try:
        value = json.loads(stored) if stored else {}
    except (ValueError, TypeError):
        value = {}
    if not isinstance(value, dict) or not all(
        hmac.compare_digest(str(value.get(k, "")), str(v)) for k, v in expected.items()
    ):
        details = (
            [
                {
                    "field": "reauthentication",
                    "code": "challenge",
                    "challenge": challenge(expected),
                }
            ]
            if issue
            else []
        )
        raise APIError(
            "reauthentication_required",
            "Confirma tu identidad para esta operación.",
            403,
            details,
        )
    return authorized


def require(operation, resource_id, data, roles):
    _check(operation, resource_id, data, issue=True)
    g.reauth_context = (operation, resource_id, data, roles)


def recheck(conn, *, lock=False):
    context = getattr(g, "reauth_context", None)
    if not context:
        return None
    operation, resource_id, data, roles = context
    authenticate(roles)
    return _check(operation, resource_id, data, conn=conn, issue=True, lock=lock)
