"""Cookie opaca; credenciales cifradas en Redis y cierres durables en PostgreSQL."""

import base64
import hashlib
import json
import math
import re
import secrets
import time
from contextlib import contextmanager

import psycopg
import redis
from cryptography.fernet import Fernet, InvalidToken
from flask import current_app, g

from ..access import BusinessError
from .client import call

SESSION_TTL = 86400


def cipher():
    return Fernet(
        base64.urlsafe_b64encode(
            hashlib.sha256(
                ("web-session:" + current_app.config["SECRET_KEY"]).encode()
            ).digest()
        )
    )


def redis_client():
    url = current_app.config["WEB_REDIS_URL"]
    clients = current_app.extensions.setdefault("web_redis_clients", {})
    if url not in clients:
        clients[url] = redis.Redis.from_url(
            url, socket_connect_timeout=1, socket_timeout=1, decode_responses=False
        )
    return clients[url]


def redis_call(fn):
    try:
        return fn(redis_client())
    except redis.RedisError:
        raise BusinessError(
            "No se puede consultar la sesión web. Reintenta más tarde.", 503
        ) from None


@contextmanager
def database():
    try:
        with psycopg.connect(
            current_app.config["WEB_DATABASE_URL"],
            connect_timeout=2,
            options="-c statement_timeout=2000 -c lock_timeout=1000",
        ) as conn:
            yield conn
    except psycopg.Error:
        raise BusinessError(
            "No se puede verificar el cierre de sesión. Reintenta más tarde.", 503
        ) from None


def key(sid):
    return hashlib.sha256(sid.encode()).hexdigest()


def redis_key(area, identifier):
    return current_app.config["WEB_REDIS_PREFIX"] + area + ":" + identifier


def valid_sid(sid):
    return isinstance(sid, str) and re.fullmatch(r"[A-Za-z0-9_-]{43}", sid)


def closed(identifier):
    with database() as conn:
        return (
            conn.execute(
                "SELECT 1 FROM web_runtime.session_revocations WHERE id=%s AND expires>now()",
                (identifier,),
            ).fetchone()
            is not None
        )


def decode(payload, *, strict=False):
    if payload is None:
        return None
    try:
        value = json.loads(cipher().decrypt(bytes(payload)))
        return value if value["session_expires"] > time.time() else None
    except (InvalidToken, ValueError, TypeError, KeyError):
        if strict:
            raise BusinessError(
                "No se pudo descifrar la revocación pendiente.", 503
            ) from None
        return None


def load(sid):
    if not valid_sid(sid) or closed(key(sid)):
        return None
    payload = redis_call(lambda r: r.get(redis_key("session", key(sid))))
    return decode(payload)


def save(sid, value):
    ttl = math.ceil(value["session_expires"] - time.time())
    if ttl <= 0:
        raise BusinessError("La sesión terminó. Inicia sesión nuevamente.", 401)
    redis_call(
        lambda r: r.set(
            redis_key("session", key(sid)),
            cipher().encrypt(json.dumps(value).encode()),
            ex=ttl,
        )
    )


def login(username, password):
    # Comprobar ambos almacenes antes de emitir nuevas credenciales.
    with database() as conn:
        conn.execute("SELECT 1 FROM web_runtime.session_revocations LIMIT 1")
    redis_call(lambda r: r.ping())
    value = call(
        "identidad_acceso",
        "/api/v1/auth/login",
        "POST",
        {"username": username, "password": password},
    )
    value.update(
        expires_at=time.time() + value["expires_in"],
        session_expires=time.time() + SESSION_TTL,
    )
    sid = secrets.token_urlsafe(32)
    save(sid, value)
    return sid


def authenticate(sid):
    value = load(sid)
    if not value or value["expires_at"] <= time.time():
        return None
    g.access_token = value["access_token"]
    # JWT, sesión, revocación y permisos se verifican en Identidad/Redis cada petición web protegida.
    user = call("identidad_acceso", "/api/v1/auth/me")
    g.web_session = value
    return user


def renew(sid):
    value = load(sid)
    if not value:
        raise BusinessError("La sesión terminó. Inicia sesión nuevamente.", 401)
    owner = secrets.token_hex(16)
    session_key, lock_key = (
        redis_key(area, key(sid)) for area in ("session", "renewal")
    )
    if not redis_call(lambda r: r.set(lock_key, owner, nx=True, ex=60)):
        raise BusinessError(
            "Esta sesión se está renovando. Vuelve a consultar su estado.", 409
        )
    try:
        # Leer de nuevo bajo la concesión: otra pestaña pudo renovar antes de adquirirla.
        value = load(sid)
        if not value:
            raise BusinessError("La sesión terminó. Inicia sesión nuevamente.", 401)
        result = call(
            "identidad_acceso",
            "/api/v1/auth/refresh",
            "POST",
            {"refresh_token": value["refresh_token"]},
            token="",
        )
        value.update(result, expires_at=time.time() + result["expires_in"])
        if closed(key(sid)):
            raise BusinessError("La sesión terminó durante la renovación.", 401)
        # Comparar dueño y existencia de la sesión en una sola operación: no resucitar un logout.
        script = """
        if redis.call('GET',KEYS[2])~=ARGV[1] or redis.call('EXISTS',KEYS[1])==0 then return 0 end
        redis.call('SET',KEYS[1],ARGV[2],'EX',ARGV[3]); return 1
        """
        ttl = math.ceil(value["session_expires"] - time.time())
        if ttl <= 0 or not redis_call(
            lambda r: r.eval(
                script,
                2,
                session_key,
                lock_key,
                owner,
                cipher().encrypt(json.dumps(value).encode()),
                ttl,
            )
        ):
            raise BusinessError("La sesión terminó durante la renovación.", 401)
        return {"expires_at": value["expires_at"], "server_time": time.time()}
    finally:
        try:
            redis_call(
                lambda r: r.eval(
                    "if redis.call('GET',KEYS[1])==ARGV[1] then return redis.call('DEL',KEYS[1]) end return 0",
                    1,
                    lock_key,
                    owner,
                )
            )
        except BusinessError:
            current_app.logger.warning("web_session_renewal_release_unavailable")


def finish_revocation(identifier):
    # Serializar workers por fila; conservar el payload antes de borrar Redis.
    with database() as conn:
        row = conn.execute(
            "SELECT payload,confirmed FROM web_runtime.session_revocations WHERE id=%s AND expires>now() FOR UPDATE",
            (identifier,),
        ).fetchone()
        if not row or row[1]:
            return False
        payload = row[0]
        if payload is None:
            payload = redis_call(lambda r: r.get(redis_key("session", identifier)))
            if payload is not None:
                conn.execute(
                    "UPDATE web_runtime.session_revocations SET payload=%s WHERE id=%s",
                    (payload, identifier),
                )
    redis_call(
        lambda r: r.delete(
            redis_key("session", identifier), redis_key("renewal", identifier)
        )
    )
    value = decode(payload, strict=True)
    if value:
        revoke(value)
    with database() as conn:
        # Conservar la marca hasta expirar: una copia antigua de Redis no reactiva la cookie.
        conn.execute(
            "UPDATE web_runtime.session_revocations SET confirmed=true,payload=NULL WHERE id=%s",
            (identifier,),
        )
    return True


def logout(sid):
    if not valid_sid(sid):
        return
    identifier = key(sid)
    # El navegador pierde sus credenciales incluso si Identidad no está disponible.
    # La marca durable se escribe aun cuando Redis esté caído, usando solo el hash de cookie.
    with database() as conn:
        conn.execute(
            "INSERT INTO web_runtime.session_revocations(id,expires) VALUES(%s,now()+interval '24 hours') ON CONFLICT(id) DO NOTHING",
            (identifier,),
        )
    try:
        finish_revocation(identifier)
    except BusinessError as exc:
        current_app.logger.warning("remote_logout_unconfirmed status=%s", exc.status)
        return False
    return True


def revoke(value):
    try:
        call(
            "identidad_acceso",
            "/api/v1/auth/revoke",
            "POST",
            {"refresh_token": value["refresh_token"]},
            token="",
        )
    except BusinessError as exc:
        if exc.status != 404:
            raise
        # Compatibilidad con Identidad v1 anterior durante despliegue gradual.
        call(
            "identidad_acceso",
            "/api/v1/auth/logout",
            "POST",
            token=value["access_token"],
        )


def retry_revocations(limit=10):
    """Reintento desde worker/CLI; nunca restaura una sesión cerrada."""
    with database() as conn:
        conn.execute("DELETE FROM web_runtime.session_revocations WHERE expires<=now()")
        pending = conn.execute(
            "SELECT id FROM web_runtime.session_revocations WHERE NOT confirmed ORDER BY expires LIMIT %s",
            (limit,),
        ).fetchall()
    delivered = 0
    for (identifier,) in pending:
        try:
            delivered += bool(finish_revocation(identifier))
        except BusinessError:
            continue
    return delivered
