"""Instalación explícita; una repetición verifica la versión y conserva registros."""

import json
import sys
from pathlib import Path

import psycopg
import redis
from pymongo import MongoClient

sys.path.insert(0, "/app/apps/services")
from redhouse.config import SERVICES
from scripts.local import private_file
from scripts.provision import provision
from redhouse.shared_migrations import LATEST_VERSION


def main():
    directory = Path("/run/install")
    passwords = {
        name: (directory / (name + "-password")).read_text().strip()
        for name in ("postgres", "redis", "mongo")
    }
    admin = f"postgresql://rh_bootstrap:{passwords['postgres']}@postgres:5432/postgres"
    state_path = directory / "state.json"
    if state_path.exists():
        with psycopg.connect(admin.rsplit("/", 1)[0] + "/red_house") as conn:
            version = conn.execute(
                "SELECT max(version) FROM red_house.schema_migration"
            ).fetchone()[0]
            if version != LATEST_VERSION:
                raise RuntimeError(
                    "Requiere una migración explícita compatible; arranque cancelado."
                )
        from scripts.migrate_documents import migrate

        with MongoClient(
            f"mongodb://rh_bootstrap:{passwords['mongo']}@mongodb:27017/?authSource=admin"
        ) as client:
            migrate(client)
        from scripts.web_sessions import provision_web_storage, write_private

        state = json.loads(state_path.read_text())
        identity = json.loads((directory / "apps/identidad_acceso.json").read_text())
        cache = redis.Redis(host="redis", password=passwords["redis"], socket_timeout=2)
        storage = provision_web_storage(
            directory / "apps",
            admin,
            cache,
            "redis://redis:6379/0",
            identity["REDIS_PREFIX"],
        )
        cache.execute_command("ACL", "SAVE")
        web_path = directory / "web.json"
        web = json.loads(web_path.read_text())
        web.pop("WEB_SESSION_STORE", None)
        web.update(storage)
        write_private(web_path, json.dumps(web, indent=2) + "\n")
        web_path.chmod(0o644)
        state["web_sessions"] = storage
        write_private(state_path, json.dumps(state, indent=2) + "\n")
        print(
            f"Instalación existente v{LATEST_VERSION} verificada; datos y credenciales conservados."
        )
        return
    urls = {name: f"http://gateway:{port}" for name, port in SERVICES.items()}
    redisadmin = redis.Redis(
        host="redis", password=passwords["redis"], decode_responses=True
    )
    mongo = MongoClient(
        f"mongodb://rh_bootstrap:{passwords['mongo']}@mongodb:27017/?authSource=admin"
    )
    prepared = provision(
        directory / "apps",
        admin_url=admin,
        pg_host="postgres",
        pgport=5432,
        redisadmin=redisadmin,
        redis_host="redis",
        redisport=6379,
        mongo=mongo,
        mongo_host="mongodb",
        mongoport=27017,
        urls=urls,
        schema_path=Path("/app/data/database/schema.sql"),
    )
    redisadmin.execute_command("ACL", "SAVE")
    mongo.close()
    for name, config in prepared["configs"].items():
        config["PORT"] = 8080
        config["DATABASE_POOL_SIZE"] = 2
        config["WORKER_HEARTBEAT_FILE"] = "/tmp/worker-heartbeat"
        path = directory / "apps" / (name + ".json")
        path.write_text(json.dumps(config, indent=2) + "\n")
        path.chmod(
            0o644
        )  # Parent directory is private on the host; runtime is unprivileged.
    import secrets

    web = {
        "BACKEND_MODE": "monolith",
        "DOMAIN_CONFIGS": "/run/redhouse",
        "SERVICE_URLS": {
            name: f"http://127.0.0.1:{port}" for name, port in SERVICES.items()
        },
        **prepared["web_sessions"],
        "WORKER_HEARTBEAT_FILE": "/tmp/web-worker-heartbeat",
        "SECRET_KEY": secrets.token_hex(32),
        "JWT_SECRET_KEY": secrets.token_hex(32),
        "PRODUCTION": False,
        "SESSION_COOKIE_SECURE": False,
    }
    private_file(directory / "web.json", json.dumps(web, indent=2) + "\n")
    (directory / "web.json").chmod(0o644)
    (directory / "apps").chmod(0o755)
    state = {k: v for k, v in prepared.items() if k != "configs"}
    state.update(
        database_admin=admin,
        mongo_admin=f"mongodb://rh_bootstrap:{passwords['mongo']}@mongodb:27017/?authSource=admin",
        redis_admin=f"redis://:{passwords['redis']}@redis:6379/0",
    )
    private_file(state_path, json.dumps(state, indent=2) + "\n")
    print(
        "Base compartida, ACL, claves y 14 cuentas ficticias creadas; secretos en state.json privado."
    )


if __name__ == "__main__":
    main()
