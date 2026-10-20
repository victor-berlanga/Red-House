"""Restaura el respaldo en un Compose nuevo y compara datos antes de abrir la web."""

import argparse
import json
import os
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "deployment"))
from backup import MONGO_STATE, MONGO_TOOL, command, sql_state
from configure import configure


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("--directory", type=Path, default=ROOT / ".local/compose")
    parser.add_argument("--project", default="sistemas-integracion-01")
    parser.add_argument(
        "--bucket", default="red-house-evidencias-sistemas-integracion-01"
    )
    args = parser.parse_args()
    os.umask(0o077)
    snapshot, directory = args.snapshot.resolve(), args.directory.resolve()
    if directory.exists():
        raise RuntimeError("El destino ya existe; no se sobrescribe una instalación.")
    os.environ["REDHOUSE_COMPOSE_DIR"] = str(directory)
    compose = ["docker", "compose", "-f", str(ROOT / "compose.yaml")]
    existing = command(compose + ["ps", "-a", "--quiet"]).strip()
    if existing:
        raise RuntimeError(
            "El proyecto Docker ya contiene contenedores; revisar destino."
        )
    project = json.loads((ROOT / "compose.yaml").read_text())["name"]
    volumes = command(
        [
            "docker",
            "volume",
            "ls",
            "-q",
            "--filter",
            "label=com.docker.compose.project=" + project,
        ]
    ).strip()
    if volumes:
        raise RuntimeError(
            "El proyecto Docker ya contiene volúmenes; no se reemplazan datos."
        )
    shutil.copytree(snapshot / "configuration", directory)
    directory.chmod(0o700)
    configure(directory, args.project, args.bucket)
    command(compose + ["up", "-d", "--wait", "postgres", "mongodb"])
    pg = compose + ["exec", "-T", "postgres"]
    mongo = compose + ["exec", "-T", "mongodb"]
    # Esperar los procesos definitivos, no las bases temporales de inicialización.
    deadline = time.monotonic() + 60
    while True:
        try:
            for prefix, process in ((pg, "postgres"), (mongo, "mongod")):
                command(
                    prefix + ["sh", "-c", 'test "$(cat /proc/1/comm)" = ' + process]
                )
            command(mongo + ["python3", "-c", MONGO_STATE])
            break
        except RuntimeError:
            if time.monotonic() >= deadline:
                raise
            time.sleep(1)
    roles = (
        (snapshot / "roles.sql").read_text().replace("CREATE ROLE rh_bootstrap;", "")
    )
    command(
        pg + ["psql", "-U", "rh_bootstrap", "-v", "ON_ERROR_STOP=1"],
        data=roles.encode(),
    )
    command(pg + ["createdb", "-U", "rh_bootstrap", "red_house"])
    command(
        pg + ["pg_restore", "-U", "rh_bootstrap", "-d", "red_house", "--exit-on-error"],
        data=(snapshot / "postgres.dump").read_bytes(),
    )
    for namespace in ("admin.*", "rh_*.*"):
        command(
            mongo + ["python3", "-c", MONGO_TOOL, "mongorestore", namespace],
            data=(snapshot / "mongo.archive.gz").read_bytes(),
        )

    expected = json.loads((snapshot / "expected.json").read_text())
    actual = {
        "postgres": sql_state(pg),
        "mongo": json.loads(command(mongo + ["python3", "-c", MONGO_STATE])),
    }
    if expected != actual:
        raise RuntimeError("Los conteos o hashes SQL/MongoDB difieren del respaldo.")

    # Cargar el RDB una vez y generar AOF antes de usar la configuración habitual.
    command(
        compose
        + [
            "run",
            "--rm",
            "--no-deps",
            "--user",
            "0",
            "--entrypoint",
            "sh",
            "-v",
            str(snapshot) + ":/backup:ro",
            "redis",
            "-c",
            (
                "set -eu; test ! -e /data/appendonlydir; "
                "cp /backup/dump.rdb /data/dump.rdb; "
                "cp /run/secrets/redis_acl /data/users.acl; "
                "chown redis:redis /data/dump.rdb /data/users.acl"
            ),
        ]
    )
    name = "redhouse-redis-import"
    command(
        compose
        + [
            "run",
            "-d",
            "--no-deps",
            "--name",
            name,
            "--entrypoint",
            "redis-server",
            "redis",
            "/run/secrets/redis_config",
            "--appendonly",
            "no",
        ]
    )
    password = (directory / "redis-password").read_text().strip()

    def redis_request(text, prefix=None):
        return command(
            (prefix or ["docker", "exec", "-i", name]) + ["redis-cli", "--raw"],
            data=("AUTH " + password + "\n" + text + "\n").encode(),
        ).decode()

    try:
        deadline = time.monotonic() + 30
        while True:
            try:
                if redis_request("PING").splitlines() == ["OK", "PONG"]:
                    break
            except RuntimeError:
                pass
            if time.monotonic() >= deadline:
                raise RuntimeError("Redis no terminó de cargar el respaldo.")
            time.sleep(1)
        if redis_request("CONFIG SET appendonly yes").splitlines() != ["OK", "OK"]:
            raise RuntimeError("No se pudo habilitar la persistencia AOF.")
        deadline = time.monotonic() + 30
        while True:
            info = redis_request("INFO persistence")
            if (
                "aof_rewrite_in_progress:0" in info
                and "aof_last_bgrewrite_status:ok" in info
            ):
                break
            if time.monotonic() >= deadline:
                raise RuntimeError("Redis no terminó de generar su AOF.")
            time.sleep(1)
    finally:
        command(["docker", "stop", name])
        command(["docker", "rm", name])
    command(compose + ["up", "-d", "--wait", "redis"])
    prefix = compose + ["exec", "-T", "redis"]
    if redis_request("PING", prefix).splitlines() != ["OK", "PONG"]:
        raise RuntimeError("Redis restaurado no acepta la credencial conservada.")
    keys = redis_request("KEYS backup-proof:*", prefix).splitlines()[1:]
    probes = [
        redis_request("GET " + key, prefix).splitlines()[-1] for key in keys if key
    ]
    if "restored" not in probes:
        raise RuntimeError(
            "La clave temporal del respaldo no está vigente; revisar evidencia Redis."
        )
    permissions = json.loads(
        command(
            pg
            + [
                "psql",
                "-U",
                "rh_bootstrap",
                "-d",
                "red_house",
                "-qAt",
                "-c",
                (
                    "SELECT json_build_object('technical_table',has_table_privilege('rh_web_sessions','web_runtime.session_revocations','SELECT,INSERT,UPDATE,DELETE'),"
                    "'domain_schema',has_schema_privilege('rh_web_sessions','red_house','USAGE'))"
                ),
            ]
        )
    )
    if permissions != {"technical_table": True, "domain_schema": False}:
        raise RuntimeError("Permisos del portal distintos a los esperados.")
    result = {
        "result": "passed",
        "postgres_tables": len(actual["postgres"]),
        "postgres_rows": sum(x["rows"] for x in actual["postgres"]),
        "mongo_documents": sum(
            x["rows"] for k, x in actual["mongo"].items() if not k.startswith("admin.")
        ),
        "sql_mongo_counts_and_hashes_match": True,
        "redis_restored": True,
        "web_permissions": permissions,
        "personal_adc_used": False,
    }
    (directory / "gcp-restoration.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
