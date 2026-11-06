"""Provisiona solo el propietario extraído; conserva claves y sesiones existentes.

Ejecutar durante mantenimiento, después del respaldo y migración global 013.
Un archivo privado de preparación permite retomar tras un fallo sin rotar claves.
"""

import json
import secrets
from urllib.parse import urlsplit, urlunsplit

import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo
import redis
from cryptography.hazmat.primitives.asymmetric import ed25519

from redhouse.shared_migrations import upgrade
from scripts.local import pem, private_file
from scripts.web_sessions import write_private


def provision_documents(directory, state):
    existing = directory / "documentos.json"
    staged = directory / "documentos.pending.json"
    base = json.loads((directory / "donantes.json").read_text())
    transport = json.loads((directory / "transporte.json").read_text())
    if existing.exists():
        config = json.loads(existing.read_text())
    elif staged.exists():
        config = json.loads(staged.read_text())
    else:
        private, public = pem(ed25519.Ed25519PrivateKey.generate())
        params = conninfo_to_dict(base["DATABASE_URL"])
        params.update(
            user="rh_documentos",
            password=secrets.token_urlsafe(32),
            options="-csearch_path=access_documentos,pg_catalog",
        )
        location = urlsplit(base["REDIS_URL"])
        config = dict(
            base,
            SERVICE="documentos",
            PORT=8080 if base.get("PORT") == 8080 else 5112,
            DATABASE_URL=make_conninfo(**params),
            SERVICE_PRIVATE_KEY=private,
            SERVICE_PUBLIC_KEYS={**base["SERVICE_PUBLIC_KEYS"], "documentos": public},
            REDIS_URL=urlunsplit(
                location._replace(
                    netloc="documentos:"
                    + secrets.token_urlsafe(32)
                    + "@"
                    + location.netloc.split("@")[-1]
                )
            ),
        )
        for key in ("MONGODB_URL", "MONGODB_DATABASE"):
            config.pop(key, None)
        for key in (
            "GCS_BUCKET",
            "GCS_PROJECT",
            "GCS_SIGNER",
            "CLAMD_HOST",
            "CLAMD_PORT",
        ):
            if key in transport:
                config[key] = transport[key]
        private_file(staged, json.dumps(config, indent=2))
    params = conninfo_to_dict(config["DATABASE_URL"])
    owner = next(iter(state["database_owners"].values()))
    with psycopg.connect(owner) as conn:
        if not conn.execute(
            "SELECT 1 FROM pg_roles WHERE rolname='rh_documentos'"
        ).fetchone():
            conn.execute(
                sql.SQL(
                    "CREATE ROLE rh_documentos LOGIN PASSWORD {} NOSUPERUSER NOCREATEDB NOCREATEROLE"
                ).format(sql.Literal(params["password"]))
            )
        conn.execute("GRANT CONNECT ON DATABASE red_house TO rh_documentos")
        conn.execute("REVOKE ALL ON SCHEMA access_documentos FROM PUBLIC")
        conn.execute("GRANT USAGE ON SCHEMA access_documentos TO rh_documentos")
        conn.execute(
            "GRANT SELECT,INSERT,UPDATE,DELETE ON ALL TABLES IN SCHEMA access_documentos TO rh_documentos"
        )
        conn.execute(
            "REVOKE UPDATE,DELETE ON access_documentos.activity_events,access_documentos.inbox,access_documentos.idempotency,access_documentos.decisions FROM rh_documentos"
        )
        conn.execute(
            "REVOKE INSERT,UPDATE,DELETE ON access_documentos.schema_version FROM rh_documentos"
        )
        conn.execute(
            "ALTER ROLE rh_documentos IN DATABASE red_house SET search_path=access_documentos,pg_catalog"
        )
        upgrade(conn)
    location = urlsplit(config["REDIS_URL"])
    prefix = config["REDIS_PREFIX"]
    with redis.Redis.from_url(state["redis_admin"], socket_timeout=3) as admin:
        admin.execute_command(
            "ACL",
            "SETUSER",
            "documentos",
            "on",
            ">" + location.password,
            "resetkeys",
            "-@all",
            *[
                f"%R~{prefix}{area}:*"
                for area in (
                    "session",
                    "permissions",
                    "permission_version",
                    "revoked",
                    "reauth",
                )
            ],
            *[f"~{prefix}{area}:documentos:*" for area in ("limit", "nonce", "cache")],
            *[
                "+" + command
                for command in (
                    "ping",
                    "get",
                    "mget",
                    "exists",
                    "set",
                    "del",
                    "incr",
                    "expire",
                    "ttl",
                    "eval",
                    "multi",
                    "exec",
                )
            ],
        )
        admin.execute_command("ACL", "SAVE")
    location = urlsplit(base["SERVICE_URLS"]["donantes"])
    url = urlunsplit(location._replace(netloc=f"{location.hostname}:5112"))
    public = config["SERVICE_PUBLIC_KEYS"]["documentos"]
    for path in directory.glob("*.json"):
        current = json.loads(path.read_text())
        if "SERVICE_PUBLIC_KEYS" in current and path != staged:
            current["SERVICE_PUBLIC_KEYS"]["documentos"] = public
            current["SERVICE_URLS"]["documentos"] = url
            write_private(path, json.dumps(current, indent=2))
    config["SERVICE_URLS"]["documentos"] = url
    write_private(existing, json.dumps(config, indent=2))
    owner_params = conninfo_to_dict(owner)
    owner_params["options"] = "-csearch_path=access_documentos,pg_catalog"
    state["database_owners"]["documentos"] = make_conninfo(**owner_params)
    state.setdefault("urls", {})["documentos"] = url
    write_private(directory / "state.json", json.dumps(state, indent=2))
    staged.unlink(missing_ok=True)
