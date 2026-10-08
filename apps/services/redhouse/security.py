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


def access_token(user, sid):
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
            "iss": current_app.config["JWT_ISSUER"],
            "aud": current_app.config["JWT_AUDIENCE"],
        },
        current_app.config["JWT_PRIVATE_KEY"],
        algorithm="RS256",
    )
