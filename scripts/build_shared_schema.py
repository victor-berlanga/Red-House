"""Construye el esquema compartido desde main fijado y verifica su restauración."""

import argparse
import difflib
import json
import re
from pathlib import Path
import shutil
import sys
import tempfile

from export_schemas import ROOT, normalize, run

sys.path.insert(0, str(ROOT / "apps/services"))
import psycopg
from psycopg import sql
from redhouse.shared_schema import extend
from redhouse.shared_migrations import upgrade, LATEST_VERSION

BASE_COMMIT = "44eeaf90c445b4d9564c2f0ab2dd3167f0296418"
SOURCES = [
    "data/database/schema.sql",
    "data/database/migrations/002_regional.sql",
    "data/database/migrations/003_recipient_urgency_history.sql",
    "data/database/migrations/004_organs.sql",
]
CATALOGUES = {
    "role": ["role_code", "role_name", "is_enabled"],
    "capability": ["capability_code", "capability_name"],
    "blood_status_transition": ["previous_status", "new_status", "is_illustrative"],
    "cache_revision": ["name", "revision"],
    "schema_migration": ["version", "description"],
    "service_schema_version": ["service", "version"],
}


def canonical_dump(text):
    # PostgreSQL 14 desplaza casts de ARRAY varchar a sus elementos al restaurar.
    # Solo normalizar listas literales de varchar; conservar toda otra expresión.
    def array_cast(match):
        items = re.findall(r"'(?:[^']|'')*'::character varying", match.group(1))
        if ", ".join(items) != match.group(1):
            return match.group(0)
        return "ARRAY[" + ", ".join("(" + item + ")::text" for item in items) + "]"

    return re.sub(r"\(ARRAY\[([^\]]+)\]\)::text\[\]", array_cast, normalize(text))


def inventory(conn):
    return {
        table: [
            r[0]
            for r in conn.execute(
                "SELECT column_name FROM information_schema.columns WHERE table_schema='red_house' AND table_name=%s ORDER BY ordinal_position",
                (table,),
            )
        ]
        for (table,) in conn.execute(
            "SELECT tablename FROM pg_tables WHERE schemaname='red_house' ORDER BY tablename"
        ).fetchall()
    }


def rejected(conn, statement, exception):
    try:
        with conn.transaction():
            conn.execute(statement)
    except exception:
        return
    raise AssertionError("La base aceptó un registro que debía rechazar: " + statement)


def build(check, binaries):
    sources = [
        run(["git", "-C", str(ROOT), "show", f"{BASE_COMMIT}:{p}"]) for p in SOURCES
    ]
    extension = (ROOT / "data/database/shared/005_services.sql").read_text()
    with tempfile.TemporaryDirectory(prefix="rh-shared-", dir="/tmp") as directory:
        base = Path(directory)
        cluster = base / "pg"
        socket = base / "socket"
        socket.mkdir(mode=0o700)
        run(
            [
                str(binaries / "initdb"),
                "-D",
                str(cluster),
                "-U",
                "schema_builder",
                "--auth=trust",
                "--encoding=UTF8",
                "--locale=C",
            ]
        )
        with (cluster / "postgresql.conf").open("a") as f:
            f.write(f"\nlisten_addresses=''\nunix_socket_directories='{socket}'\n")
        run(
            [
                str(binaries / "pg_ctl"),
                "-D",
                str(cluster),
                "-l",
                str(base / "pg.log"),
                "-w",
                "start",
            ]
        )
        try:
            params = {"host": str(socket), "user": "schema_builder"}
            with psycopg.connect(dbname="postgres", autocommit=True, **params) as admin:
                for name in ("shared", "restored"):
                    admin.execute(
                        sql.SQL("CREATE DATABASE {} TEMPLATE template0").format(
                            sql.Identifier(name)
                        )
                    )
            with psycopg.connect(dbname="shared", **params) as conn:
                for source in sources:
                    conn.execute(source)
                before = inventory(conn)
                conn.execute(extension)
                extend(conn)
                upgrade(conn)
                after = inventory(conn)
                assert set(before) <= set(after)
                for table, columns in before.items():
                    assert {
                        ("is_illustrative" if c == "is_demo" else c) for c in columns
                    } <= set(after[table])
                seeds = []
                for table, columns in CATALOGUES.items():
                    fields = sql.SQL(",").join(map(sql.Identifier, columns))
                    rows = conn.execute(
                        sql.SQL("SELECT {} FROM red_house.{} ORDER BY 1,2").format(
                            fields, sql.Identifier(table)
                        )
                    ).fetchall()
                    for row in rows:
                        seeds.append(
                            sql.SQL("INSERT INTO red_house.{} ({}) VALUES ({});")
                            .format(
                                sql.Identifier(table),
                                fields,
                                sql.SQL(",").join(map(sql.Literal, row)),
                            )
                            .as_string(conn)
                        )
            dump_command = [
                str(binaries / "pg_dump"),
                "--host",
                str(socket),
                "--username",
                "schema_builder",
                "--schema-only",
                "--schema=red_house",
                "--schema=access_*",
                "--no-owner",
                "--no-privileges",
                "--dbname",
            ]
            dump = canonical_dump(run(dump_command + ["shared"]))
            output = (
                f"-- Red House: base única compartida; PostgreSQL 14+.\n-- Base: main {BASE_COMMIT}, esquema inicial y migraciones 002–004.\n"
                "-- Generado con scripts/build_shared_schema.py, shared/005_services.sql y redhouse/shared_schema.py.\n"
                "-- Instalación estructural en una base VACÍA. No migra datos de las once bases actuales.\n"
                "-- Incluye catálogos, no cuentas, credenciales ni datos clínicos.\nBEGIN;\n"
                + dump
                + "\n"
                + "\n".join(seeds)
                + "\nCOMMIT;\n"
            )
            candidate = base / "schema.sql"
            candidate.write_text(output)
            run(
                [
                    str(binaries / "psql"),
                    "--host",
                    str(socket),
                    "--username",
                    "schema_builder",
                    "--dbname",
                    "restored",
                    "--no-psqlrc",
                    "--set",
                    "ON_ERROR_STOP=1",
                    "--file",
                    str(candidate),
                ]
            )
            restored_dump = canonical_dump(run(dump_command + ["restored"]))
            if restored_dump != dump:
                raise AssertionError(
                    "\n".join(
                        difflib.unified_diff(
                            dump.splitlines(), restored_dump.splitlines()
                        )
                    )
                )
            with psycopg.connect(dbname="restored", **params) as conn:
                conn.execute("SET search_path=red_house,pg_catalog")
                assert inventory(conn) == after
                assert (
                    conn.execute("SELECT count(*) FROM schema_migration").fetchone()[0]
                    == LATEST_VERSION
                )
                assert (
                    conn.execute(
                        "SELECT count(*) FROM role WHERE is_enabled"
                    ).fetchone()[0]
                    == 7
                )
                # Validate shared-domain references with API-facing projections.
                rejected(
                    conn,
                    "INSERT INTO access_donantes.appointments(id,tenant_id,donor_id,campaign_id) VALUES(gen_random_uuid(),gen_random_uuid(),gen_random_uuid(),gen_random_uuid())",
                    psycopg.errors.ForeignKeyViolation,
                )
                conn.execute(
                    "INSERT INTO access_monitoreo.checks(id,service,state,elapsed_ms) VALUES(gen_random_uuid(),'inventario','up',1)"
                )
                rejected(
                    conn,
                    "UPDATE red_house.service_health_check SET state='down'",
                    psycopg.errors.CheckViolation,
                )
                conn.execute(
                    "INSERT INTO access_identidad_acceso.institutions(id,name,region_id) VALUES(gen_random_uuid(),'Test',gen_random_uuid())"
                )
                assert (
                    conn.execute(
                        "SELECT revision FROM cache_revision WHERE name='catalogues'"
                    ).fetchone()[0]
                    == 1
                )
            assert "DEMO" not in output.upper()
            report = {
                "base_commit": BASE_COMMIT,
                "baseline_tables": len(before),
                "shared_tables": len(after),
                "added_tables": sorted(set(after) - set(before)),
                "changed_columns": {
                    t: sorted(set(after[t]) - set(before[t]))
                    for t in before
                    if before[t] != after[t]
                },
                "checks": [
                    "all baseline tables retained",
                    "baseline columns retained except two explicit renames",
                    "restore structure identical",
                    "migration catalogue and seven roles",
                    "orphan FK rejected",
                    "immutable history enforced",
                    "cache revision trigger",
                    "no redundant labels",
                ],
            }
            target = ROOT / "data/database/schema.sql"
            if check:
                assert target.read_text() == output, (
                    "Regenerar data/database/schema.sql"
                )
            else:
                target.write_text(output)
            print(json.dumps(report, indent=2, ensure_ascii=False))
        finally:
            run(
                [
                    str(binaries / "pg_ctl"),
                    "-D",
                    str(cluster),
                    "-m",
                    "fast",
                    "-w",
                    "stop",
                ]
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--pg-bin", type=Path)
    args = parser.parse_args()
    executable = shutil.which("initdb")
    if not args.pg_bin and not executable:
        parser.error("Faltan herramientas PostgreSQL; indica --pg-bin")
    build(args.check, args.pg_bin or Path(executable).resolve().parent)
