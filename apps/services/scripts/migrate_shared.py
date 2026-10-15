"""Traslada las once bases al esquema compartido con respaldo y comparación de filas.

Requiere procesos API/web/worker detenidos; mantiene infraestructura y bases de origen.
No borra bases antiguas. Publica conexiones solo después de verificar la copia completa.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from redhouse.config import SERVICES
from redhouse.shared import COMMON_TABLES, service_schema
from scripts.local import pid_matches


def atomic_json(path, data):
    temporary = path.with_suffix(path.suffix + ".new")
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as f:
        json.dump(data, f, indent=2)
    os.replace(temporary, path)


def fingerprint(rows):
    encoded = [
        json.dumps(r, sort_keys=True, default=str, separators=(",", ":")) for r in rows
    ]
    return hashlib.sha256("\n".join(sorted(encoded)).encode()).hexdigest()


def migrate_shared(directory, target="red_house", verify_only=False):
    directory = Path(directory).resolve()
    state = json.loads((directory / "state.json").read_text())
    if Path(state["directory"]).resolve() != directory:
        raise RuntimeError("Directorio de entorno incorrecto")
    if state.get("database_layout") == "shared-v6":
        print("El entorno ya utiliza la base compartida.")
        return
    for group in ("web_pids", "worker_pids", "service_pids"):
        if any(pid_matches(pid, directory) for pid in state.get(group, {}).values()):
            raise RuntimeError(
                "Detén primero APIs, workers y portal; conserva PostgreSQL iniciado."
            )
    if verify_only:
        print("Procesos detenidos; entorno apto para preparar la migración.")
        return
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    backup = directory / "backups" / ("shared-" + stamp)
    backup.mkdir(parents=True, mode=0o700)
    originals = {
        name: json.loads((directory / (name + ".json")).read_text())
        for name in SERVICES
    }
    for name, cfg in originals.items():
        atomic_json(backup / (name + ".json"), cfg)
    atomic_json(backup / "state.json", state)
    binary = shutil.which("pg_dump") or str(
        Path(state["infrastructure_commands"]["postgres"][0]).with_name("pg_dump")
    )
    for name in SERVICES:
        params = conninfo_to_dict(state["database_owners"][name])
        dump = backup / (name + ".dump")
        result = subprocess.run(
            [
                binary,
                "--host",
                params["host"],
                "--port",
                params["port"],
                "--username",
                params["user"],
                "--dbname",
                params["dbname"],
                "--format=custom",
                "--file",
                str(dump),
            ],
            env=dict(os.environ, PGPASSWORD=params["password"]),
            capture_output=True,
        )
        if result.returncode:
            raise RuntimeError(
                "No se pudo respaldar " + name + "; no se cambian conexiones."
            )
        dump.chmod(0o600)
    params = conninfo_to_dict(state["database_admin"])
    target_dsn = make_conninfo(**dict(params, dbname=target))
    with psycopg.connect(state["database_admin"], autocommit=True) as admin:
        if admin.execute(
            "SELECT 1 FROM pg_database WHERE datname=%s", (target,)
        ).fetchone():
            raise RuntimeError(
                "La base destino ya existe; no se sobrescribe. Conserva/revisa ese intento antes de repetir."
            )
        if not admin.execute(
            "SELECT 1 FROM pg_roles WHERE rolname='rh_shared_owner'"
        ).fetchone():
            admin.execute("CREATE ROLE rh_shared_owner NOLOGIN")
        admin.execute(
            sql.SQL("CREATE DATABASE {} OWNER rh_shared_owner").format(
                sql.Identifier(target)
            )
        )
        admin.execute(
            sql.SQL("REVOKE ALL ON DATABASE {} FROM PUBLIC").format(
                sql.Identifier(target)
            )
        )
    with psycopg.connect(target_dsn) as conn:
        conn.execute("SET ROLE rh_shared_owner")
        conn.execute((ROOT.parents[1] / "data/database/schema.sql").read_text())
        conn.execute("REVOKE ALL ON SCHEMA public FROM PUBLIC")
        conn.execute("REVOKE ALL ON SCHEMA red_house FROM PUBLIC")
        # Foreign keys still enforce integrity at commit, while import order may
        # contain cycles such as institutions.created_by -> users -> institutions.
        for table, constraint in conn.execute(
            "SELECT conrelid::regclass::text,conname FROM pg_constraint WHERE contype='f' AND connamespace='red_house'::regnamespace"
        ).fetchall():
            conn.execute(
                sql.SQL(
                    "ALTER TABLE {} ALTER CONSTRAINT {} DEFERRABLE INITIALLY IMMEDIATE"
                ).format(sql.Identifier(*table.split(".")), sql.Identifier(constraint))
            )
    comparison = {}
    source_rows = {}
    with psycopg.connect(target_dsn, row_factory=dict_row) as destination:
        destination.execute("SET CONSTRAINTS ALL DEFERRED")
        destination.execute("DELETE FROM red_house.cache_revision")
        for service in SERVICES:
            access = service_schema(service)
            with psycopg.connect(
                state["database_owners"][service],
                row_factory=dict_row,
                options="-c search_path=api,pg_catalog",
            ) as source:
                tables = [
                    r["tablename"]
                    for r in source.execute(
                        "SELECT tablename FROM pg_tables WHERE schemaname='api' ORDER BY tablename"
                    )
                ]
                for table in tables:
                    rows = source.execute(
                        sql.SQL("SELECT * FROM {}").format(sql.Identifier(table))
                    ).fetchall()
                    if table == "schema_version":
                        installed = [r["version"] for r in rows]
                        expected = [
                            r["version"]
                            for r in destination.execute(
                                sql.SQL("SELECT version FROM {}.schema_version").format(
                                    sql.Identifier(access)
                                )
                            )
                        ]
                        if set(installed) != set(expected):
                            raise RuntimeError(
                                "Actualiza las migraciones de origen antes de consolidar "
                                + service
                            )
                        destination.execute(
                            "DELETE FROM red_house.service_schema_version WHERE service=%s",
                            (service,),
                        )
                    if rows:
                        names = list(rows[0])
                        query = sql.SQL("INSERT INTO {}.{} ({}) VALUES ({})").format(
                            sql.Identifier(access),
                            sql.Identifier(table),
                            sql.SQL(",").join(map(sql.Identifier, names)),
                            sql.SQL(",").join(sql.Placeholder() for _ in names),
                        )
                        with destination.cursor() as cursor:
                            cursor.executemany(
                                query,
                                [
                                    [
                                        Jsonb(v) if isinstance(v, (dict, list)) else v
                                        for v in row.values()
                                    ]
                                    for row in rows
                                ],
                            )
                    source_rows[(service, table)] = rows
        # Cached revision may have advanced during import triggers; keep the source
        # revision so the exact copy can be verified before runtime resumes.
        source_cache = [
            row
            for (service, table), rows in source_rows.items()
            if table == "cache_revision"
            for row in rows
        ]
        for row in source_cache:
            destination.execute(
                "UPDATE red_house.cache_revision SET revision=%s WHERE name=%s",
                (row["revision"], row["name"]),
            )
        destination.execute("SET CONSTRAINTS ALL IMMEDIATE")
        for (service, table), expected in source_rows.items():
            actual = destination.execute(
                sql.SQL("SELECT * FROM {}.{}").format(
                    sql.Identifier(service_schema(service)), sql.Identifier(table)
                )
            ).fetchall()
            if fingerprint(actual) != fingerprint(expected):
                raise RuntimeError(
                    "La copia difiere en "
                    + service
                    + "."
                    + table
                    + "; no se cambian conexiones."
                )
            comparison[service + "." + table] = {
                "rows": len(actual),
                "sha256": fingerprint(actual),
            }
    # New runtime roles keep their existing passwords; only the database changes.
    new_configs = {}
    new_state = dict(state)
    new_state["database_owners"] = {}
    with psycopg.connect(target_dsn) as conn:
        for service in SERVICES:
            access = service_schema(service)
            role = "rh_" + service
            conn.execute(
                sql.SQL(
                    "ALTER ROLE {} IN DATABASE {} SET search_path={},pg_catalog"
                ).format(
                    sql.Identifier(role), sql.Identifier(target), sql.Identifier(access)
                )
            )
            conn.execute(
                sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(
                    sql.Identifier(target), sql.Identifier(role)
                )
            )
            conn.execute(
                sql.SQL("REVOKE ALL ON SCHEMA {} FROM PUBLIC").format(
                    sql.Identifier(access)
                )
            )
            conn.execute(
                sql.SQL("GRANT USAGE ON SCHEMA {} TO {}").format(
                    sql.Identifier(access), sql.Identifier(role)
                )
            )
            conn.execute(
                sql.SQL(
                    "GRANT SELECT,INSERT,UPDATE,DELETE ON ALL TABLES IN SCHEMA {} TO {}"
                ).format(sql.Identifier(access), sql.Identifier(role))
            )
            for table in (
                "activity_events",
                "schema_version",
                "inbox",
                "idempotency",
                "decisions",
                "donor_reviews",
                "donation_steps",
                "resource_reviews",
                "movements",
                "reviews",
                "evaluations",
                "rankings",
                "proposals",
                "transitions",
                "telemetry",
                "custody_events",
                "audit_events",
                "checks",
            ):
                if conn.execute(
                    "SELECT to_regclass(%s)", (access + "." + table,)
                ).fetchone()[0]:
                    conn.execute(
                        sql.SQL("REVOKE UPDATE,DELETE ON {}.{} FROM {}").format(
                            sql.Identifier(access),
                            sql.Identifier(table),
                            sql.Identifier(role),
                        )
                    )
            conn.execute(
                sql.SQL(
                    "REVOKE INSERT,UPDATE,DELETE ON {}.schema_version FROM {}"
                ).format(sql.Identifier(access), sql.Identifier(role))
            )
            cfg = dict(originals[service])
            runtime = conninfo_to_dict(cfg["DATABASE_URL"])
            cfg["DATABASE_URL"] = make_conninfo(
                **dict(
                    runtime,
                    dbname=target,
                    options="-csearch_path=" + access + ",pg_catalog",
                )
            )
            new_configs[service] = cfg
            new_state["database_owners"][service] = make_conninfo(
                **dict(
                    params,
                    dbname=target,
                    options="-csearch_path=" + access + ",pg_catalog",
                )
            )
    new_state["database_layout"] = "shared-v6"
    new_state["shared_migration_backup"] = str(backup)
    atomic_json(backup / "comparison.json", comparison)
    # Roll back configuration files if publication fails; source databases stay intact.
    try:
        for service, cfg in new_configs.items():
            atomic_json(directory / (service + ".json"), cfg)
        atomic_json(directory / "state.json", new_state)
    except BaseException:
        for service, cfg in originals.items():
            atomic_json(directory / (service + ".json"), cfg)
        atomic_json(directory / "state.json", state)
        raise
    print("Base compartida preparada y conexiones actualizadas:", target)
    print(
        "Tablas verificadas:",
        len(comparison),
        "Filas:",
        sum(x["rows"] for x in comparison.values()),
    )
    print("Respaldo privado y comparación:", backup)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--target", default="red_house")
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    try:
        migrate_shared(args.directory, args.target, args.verify_only)
    except psycopg.Error as exc:
        raise SystemExit(
            "La migración se detuvo por "
            + type(exc).__name__
            + ". No se publican detalles de filas ni credenciales; revisa el respaldo privado y conserva las bases de origen."
        ) from None
