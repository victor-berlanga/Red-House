import hashlib
import hmac
import json
import re
import time
import base64
from uuid import uuid4

import jwt
import redis
from cryptography.hazmat.primitives.serialization import (
    load_pem_private_key,
    load_pem_public_key,
)
from cryptography.exceptions import InvalidSignature
from flask import current_app, g, request

from .errors import APIError


def redis_client():
    url = current_app.config["REDIS_URL"]
    clients = current_app.extensions.setdefault("redis_clients", {})
    if url not in clients:
        clients[url] = redis.Redis.from_url(
            url, socket_connect_timeout=1, socket_timeout=1, decode_responses=True
        )
    return clients[url]


def key(suffix):
    return current_app.config["REDIS_PREFIX"] + suffix


def redis_call(fn):
    try:
        return fn(redis_client())
    except redis.RedisError:
        raise APIError(
            "redis_unavailable", "No se puede verificar la sesión o autorización.", 503
        ) from None


def rate_limit(category="anonymous", identity=None):
    # No se confía en X-Forwarded-For sin un proxy explícitamente configurado.
    scope = hashlib.sha256(
        (identity or request.remote_addr or "unknown").encode()
    ).hexdigest()[:24]
    counter = key(
        f"limit:{current_app.config['SERVICE']}:{category}:{scope}:{int(time.time()) // 60}"
    )
    script = "local n=redis.call('INCR',KEYS[1]); if n==1 then redis.call('EXPIRE',KEYS[1],61) end; return n"
    n = redis_call(lambda r: r.eval(script, 1, counter))
    limit = (
        current_app.config.get("INTERNAL_RATE_LIMIT", 1800)
        if category == "service"
        else current_app.config["RATE_LIMIT"]
    )
    if n > limit:
        raise APIError("rate_limit", "Límite de consumo alcanzado.", 429)


# Distribución de perfiles por aplicación (requisito 19-nov-2026). Cada sesión
# nace en una aplicación declarada con la cabecera X-RedHouse-Client; el
# servidor la guarda en la sesión y en el JWT y exige que el perfil vigente siga
# permitido en ella. Los siete roles de Identidad no cambian.
CLIENT_HEADER = "X-RedHouse-Client"
CLIENT_ROLES = {
    "web": frozenset({"ADMIN", "OPERATOR", "MEDICAL", "COORDINATOR", "AUDITOR"}),
    "desktop": frozenset({"OPERATOR", "MEDICAL", "COORDINATOR"}),
    "mobile": frozenset({"DONOR", "TRANSPORT"}),
}
CLIENT_NAMES = {
    "web": "el portal web",
    "desktop": "la consola de escritorio",
    "mobile": "la aplicación móvil",
}


def allowed_apps(role):
    """Aplicaciones, en español, donde el perfil puede iniciar sesión."""
    names = [CLIENT_NAMES[c] for c in CLIENT_ROLES if role in CLIENT_ROLES[c]]
    return " o ".join(names) if names else "ninguna aplicación"


def ensure_client_allowed(role, client):
    """403 `client_not_allowed` si el perfil no corresponde a la aplicación."""
    if client not in CLIENT_ROLES or role not in CLIENT_ROLES[client]:
        raise APIError(
            "client_not_allowed",
            f"Tu perfil no puede iniciar sesión en {CLIENT_NAMES.get(client, 'esta aplicación')}. "
            f"Usa {allowed_apps(role)}.",
            403,
        )


def request_client():
    """Aplicación declarada en el login; falla cerrada si falta o es desconocida."""
    value = request.headers.get(CLIENT_HEADER, "")
    if value not in CLIENT_ROLES:
        raise APIError(
            "client_required",
            f"Declara la aplicación con la cabecera {CLIENT_HEADER}: web, desktop o mobile.",
            400,
        )
    return value


def authenticate(roles=()):
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        raise APIError("unauthorized", "JWT de acceso requerido.", 401)
    try:
        claims = jwt.decode(
            header[7:],
            current_app.config["JWT_PUBLIC_KEY"],
            algorithms=["RS256"],
            issuer=current_app.config["JWT_ISSUER"],
            audience=current_app.config["JWT_AUDIENCE"],
            options={
                "require": [
                    "sub",
                    "sid",
                    "jti",
                    "exp",
                    "iat",
                    "nbf",
                    "iss",
                    "aud",
                    "token_use",
                ]
            },
        )
        if claims["token_use"] != "access" or any(
            type(claims[k]) is not str for k in ("sub", "sid", "jti")
        ):
            raise ValueError()
        if any(type(claims[k]) is not int for k in ("exp", "iat", "nbf")):
            raise ValueError()
        from .models import validate_id

        for k in ("sub", "sid", "jti"):
            validate_id(claims[k])
    except (jwt.PyJWTError, ValueError, APIError):
        raise APIError("unauthorized", "JWT inválido o vencido.", 401) from None
    session, revoked, permission, permission_version = redis_call(
        lambda r: r.mget(
            key("session:" + claims["sid"]),
            key("revoked:" + claims["jti"]),
            key("permissions:" + claims["sub"]),
            key("permission_version:" + claims["sub"]),
        )
    )
    if not session or revoked or not permission:
        raise APIError("unauthorized", "Sesión revocada o permisos inexistentes.", 401)
    state, actor = json.loads(session), json.loads(permission)
    if (
        state.get("user_id") != claims["sub"]
        or not actor.get("active")
        or actor.get("id") != claims["sub"]
        or str(actor.get("version")) != permission_version
    ):
        raise APIError("unauthorized", "Sesión inactiva.", 401)
    client = state.get("client")
    if client not in CLIENT_ROLES or claims.get("client") != client:
        # Sesión emitida antes de la distribución por aplicación: falla cerrada.
        raise APIError(
            "unauthorized",
            "Tu sesión es anterior al acceso por aplicación; inicia sesión de nuevo.",
            401,
        )
    ensure_client_allowed(actor["role"], client)
    if roles and actor["role"] not in roles:
        raise APIError("forbidden", "Perfil sin permiso para esta operación.", 403)
    g.actor, g.claims = actor, claims
    return actor


def own(tenant):
    if str(tenant) != g.actor["tenant_id"]:
        raise APIError("forbidden", "Recurso de otra institución.", 403)


def regional():
    if g.actor["role"] not in ("COORDINATOR", "AUDITOR"):
        raise APIError("forbidden", "Permiso regional requerido.", 403)


def internal_signature(secret, method, path, timestamp, nonce, body):
    value = "\n".join(
        (method, path, timestamp, nonce, hashlib.sha256(body).hexdigest())
    )
    private = load_pem_private_key(secret.encode(), password=None)
    return base64.b64encode(private.sign(value.encode())).decode()


def internal_auth(allowed):
    service = request.headers.get("X-Service", "")
    public_key = current_app.config["SERVICE_PUBLIC_KEYS"].get(service)
    timestamp, nonce = (
        request.headers.get("X-Service-Time", ""),
        request.headers.get("X-Service-Nonce", ""),
    )
    try:
        if (
            service not in allowed
            or not public_key
            or abs(time.time() - int(timestamp)) > 30
        ):
            raise ValueError()
        if not re.fullmatch(r"[0-9a-f-]{36}", nonce):
            raise ValueError()
        value = "\n".join(
            (
                request.method,
                request.path,
                timestamp,
                nonce,
                hashlib.sha256(request.get_data()).hexdigest(),
            )
        )
        signature = base64.b64decode(
            request.headers.get("X-Service-Signature", ""), validate=True
        )
        load_pem_public_key(public_key.encode()).verify(signature, value.encode())
    except (ValueError, InvalidSignature):
        raise APIError(
            "unauthorized_service", "Identidad de servicio inválida.", 401
        ) from None
    if not redis_call(
        lambda r: r.set(
            key(f"nonce:{current_app.config['SERVICE']}:{service}:{nonce}"),
            "1",
            nx=True,
            ex=65,
        )
    ):
        raise APIError("replayed_service_request", "Petición interna repetida.", 401)
    g.caller = service


def access_token(user, sid, client):
    now = int(time.time())
    return jwt.encode(
        {
            "sub": str(user["id"]),
            "sid": sid,
            "jti": str(uuid4()),
            "iat": now,
            "nbf": now,
            "exp": now + current_app.config["ACCESS_TTL"],
            "token_use": "access",
            "client": client,
            "iss": current_app.config["JWT_ISSUER"],
            "aud": current_app.config["JWT_AUDIENCE"],
        },
        current_app.config["JWT_PRIVATE_KEY"],
        algorithm="RS256",
    )
