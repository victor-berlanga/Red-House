"""Sesiones propias de la web: cookie opaca y tokens cifrados en almacenamiento privado."""

import base64
import hashlib
import json
import os
import re
import secrets
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path

from cryptography.fernet import Fernet
from flask import current_app, g

from ..access import BusinessError
from .client import call


def cipher():
    return Fernet(
        base64.urlsafe_b64encode(
            hashlib.sha256(
                ("web-session:" + current_app.config["SECRET_KEY"]).encode()
            ).digest()
        )
    )


@contextmanager
def database():
    path = Path(current_app.config["WEB_SESSION_STORE"])
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.close(descriptor)
    except FileExistsError:
        pass
    os.chmod(path, 0o600)
    conn = sqlite3.connect(path, timeout=12)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS sessions(id TEXT PRIMARY KEY,payload BLOB NOT NULL,expires REAL NOT NULL)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS renewals(id TEXT PRIMARY KEY,owner TEXT NOT NULL,expires REAL NOT NULL)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS revocations(id TEXT PRIMARY KEY,payload BLOB NOT NULL,expires REAL NOT NULL)"
    )
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def key(sid):
    return hashlib.sha256(sid.encode()).hexdigest()


def load(sid, conn=None):
    if not sid or not re.fullmatch(r"[A-Za-z0-9_-]{43}", sid):
        return None
    if conn is None:
        with database() as connection:
            return load(sid, connection)
    row = conn.execute(
        "SELECT payload,expires FROM sessions WHERE id=?", (key(sid),)
    ).fetchone()
    if not row or row[1] <= time.time():
        return None
    try:
        return json.loads(cipher().decrypt(row[0]))
    except Exception:
        return None


def save(conn, sid, value):
    conn.execute(
        "INSERT OR REPLACE INTO sessions VALUES(?,?,?)",
        (
            key(sid),
            cipher().encrypt(json.dumps(value).encode()),
            value["session_expires"],
        ),
    )


def login(username, password):
    value = call(
        "identidad_acceso",
        "/api/v1/auth/login",
        "POST",
        {"username": username, "password": password},
    )
    value.update(
        expires_at=time.time() + value["expires_in"],
        session_expires=time.time() + 86400,
    )
    sid = secrets.token_urlsafe(32)
    with database() as conn:
        conn.execute("DELETE FROM sessions WHERE expires<=?", (time.time(),))
        save(conn, sid, value)
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
    owner = secrets.token_hex(16)
    with database() as conn:
        conn.execute("BEGIN IMMEDIATE")
        value = load(sid, conn)
        if not value:
            raise BusinessError("La sesión terminó. Inicia sesión nuevamente.", 401)
        conn.execute("DELETE FROM renewals WHERE expires<=?", (time.time(),))
        claimed = conn.execute(
            "INSERT OR IGNORE INTO renewals VALUES(?,?,?)",
            (key(sid), owner, time.time() + 60),
        )
        if not claimed.rowcount:
            raise BusinessError(
                "Esta sesión se está renovando. Vuelve a consultar su estado.", 409
            )
    try:
        # La espera HTTP no mantiene un bloqueo global del archivo SQLite.
        result = call(
            "identidad_acceso",
            "/api/v1/auth/refresh",
            "POST",
            {"refresh_token": value["refresh_token"]},
            token="",
        )
        value.update(result, expires_at=time.time() + result["expires_in"])
        with database() as conn:
            conn.execute("BEGIN IMMEDIATE")
            current = conn.execute(
                "SELECT owner FROM renewals WHERE id=?", (key(sid),)
            ).fetchone()
            if not current or current[0] != owner or not load(sid, conn):
                raise BusinessError("La sesión terminó durante la renovación.", 401)
            save(conn, sid, value)
        return {"expires_at": value["expires_at"], "server_time": time.time()}
    finally:
        with database() as conn:
            conn.execute(
                "DELETE FROM renewals WHERE id=? AND owner=?", (key(sid), owner)
            )


def logout(sid):
    value = load(sid)
    if not value:
        return
    with database() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO revocations VALUES(?,?,?)",
            (
                key(sid),
                cipher().encrypt(json.dumps(value).encode()),
                value["session_expires"],
            ),
        )
        conn.execute("DELETE FROM sessions WHERE id=?", (key(sid),))
        conn.execute("DELETE FROM renewals WHERE id=?", (key(sid),))
    # El navegador pierde sus credenciales incluso si Identidad no está disponible.
    try:
        revoke(value)
    except BusinessError as exc:
        current_app.logger.warning("remote_logout_unconfirmed status=%s", exc.status)
        return False
    with database() as conn:
        conn.execute("DELETE FROM revocations WHERE id=?", (key(sid),))
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
    """Reintento explícito desde CLI; nunca restaura una sesión cerrada."""
    with database() as conn:
        conn.execute("DELETE FROM revocations WHERE expires<=?", (time.time(),))
        pending = conn.execute(
            "SELECT id,payload FROM revocations ORDER BY expires LIMIT ?", (limit,)
        ).fetchall()
    delivered = 0
    for identifier, payload in pending:
        try:
            revoke(json.loads(cipher().decrypt(payload)))
        except BusinessError:
            continue
        with database() as conn:
            conn.execute("DELETE FROM revocations WHERE id=?", (identifier,))
        delivered += 1
    return delivered
