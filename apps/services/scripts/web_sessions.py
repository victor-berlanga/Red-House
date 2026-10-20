"""Provisionar credenciales limitadas del portal sin modificar las sesiones de Identidad."""

import json
import os
import secrets
import tempfile
from pathlib import Path
from urllib.parse import urlsplit, unquote

import psycopg
from psycopg import sql
import redis


def write_private(path, value):
    """Publicar configuración privada completa mediante reemplazo atómico."""
    with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        try:
            stream.write(value)
            stream.flush()
            os.fsync(stream.fileno())
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)


def provision_web_storage(directory, admin_url, redisadmin, redis_url, prefix):
    directory = Path(directory)
    path = directory / "web-storage.json"
    previous = json.loads(path.read_text()) if path.exists() else None
    pg = urlsplit(admin_url)
    cache = urlsplit(redis_url)
    pg_password = (
        unquote(urlsplit(previous["WEB_DATABASE_URL"]).password)
        if previous
        else secrets.token_urlsafe(32)
    )
    redis_password = (
        unquote(urlsplit(previous["WEB_REDIS_URL"]).password)
        if previous
        else secrets.token_urlsafe(32)
    )
    owner_url = admin_url.split("?", 1)[0].rsplit("/", 1)[0] + "/red_house"
    with psycopg.connect(owner_url, connect_timeout=3) as conn:
        conn.execute("SET ROLE rh_shared_owner")
        conn.execute(
            (
                Path(__file__).resolve().parents[3] / "data/database/web_sessions.sql"
            ).read_text()
        )
        conn.execute("RESET ROLE")
        if not conn.execute(
            "SELECT 1 FROM pg_roles WHERE rolname='rh_web_sessions'"
        ).fetchone():
            conn.execute(
                "CREATE ROLE rh_web_sessions LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE"
            )
        conn.execute(
            sql.SQL("ALTER ROLE rh_web_sessions PASSWORD {}").format(
                sql.Literal(pg_password)
            )
        )
        conn.execute("GRANT CONNECT ON DATABASE red_house TO rh_web_sessions")
        conn.execute("GRANT USAGE ON SCHEMA web_runtime TO rh_web_sessions")
        conn.execute(
            "GRANT SELECT,INSERT,UPDATE,DELETE ON web_runtime.session_revocations TO rh_web_sessions"
        )
    web_prefix = prefix + "web:"
    redisadmin.execute_command(
        "ACL",
        "SETUSER",
        "web_sessions",
        "reset",
        "on",
        ">" + redis_password,
        "~" + web_prefix + "*",
        "-@all",
        "+ping",
        "+get",
        "+set",
        "+del",
        "+exists",
        "+eval",
        "+ttl",
    )
    config = {
        "WEB_REDIS_URL": f"redis://web_sessions:{redis_password}@{cache.hostname}:{cache.port or 6379}/0",
        "WEB_REDIS_PREFIX": web_prefix,
        "WEB_DATABASE_URL": f"postgresql://rh_web_sessions:{pg_password}@{pg.hostname}:{pg.port or 5432}/red_house",
    }
    write_private(path, json.dumps(config, indent=2) + "\n")
    return config


def upgrade_local(directory, state):
    """Repetible, conserva claves y datos; ejecutar con PostgreSQL y Redis disponibles."""
    directory = Path(directory)
    identity = json.loads((directory / "identidad_acceso.json").read_text())
    cache = redis.Redis.from_url(
        state["redis_admin"], socket_connect_timeout=2, socket_timeout=2
    )
    config = provision_web_storage(
        directory,
        state["database_admin"],
        cache,
        state["redis_admin"],
        identity["REDIS_PREFIX"],
    )
    cache.execute_command("ACL", "SAVE")
    state["web_sessions"] = config
    write_private(directory / "state.json", json.dumps(state, indent=2) + "\n")
    path = directory / "web-client.json"
    if path.exists():
        web = json.loads(path.read_text())
        web.pop("WEB_SESSION_STORE", None)
        web.update(config)
        write_private(path, json.dumps(web, indent=2) + "\n")
    return config
