"""Genera y verifica esquemas PostgreSQL desde migraciones en un clúster temporal."""

import argparse
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps/services"))

import psycopg
from psycopg import sql

from redhouse.config import SERVICES
from redhouse.migrations import migrate
from redhouse.schema import COMMON, SCHEMAS


def run(command):
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result.stdout


def normalize(dump):
    # pg_dump versions and session guard tokens are not part of the schema.
    dump = re.sub(r"^-- Dumped (?:from|by).*$\n?", "", dump, flags=re.M)
    dump = re.sub(r"^\\(?:un)?restrict .*\n?", "", dump, flags=re.M)
    return dump.strip() + "\n"


def export(directory, binaries, check):
    generated = {}
    with tempfile.TemporaryDirectory(prefix="rh-schema-", dir="/tmp") as temporary:
        base = Path(temporary)
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
        # Private Unix socket only; no TCP listener and no runtime credentials.
        with (cluster / "postgresql.conf").open("a") as config:
            config.write(
                f"\nlisten_addresses = ''\nunix_socket_directories = '{socket}'\n"
            )
        started = False
        try:
            run(
                [
                    str(binaries / "pg_ctl"),
                    "-D",
                    str(cluster),
                    "-l",
                    str(base / "postgres.log"),
                    "-w",
                    "start",
                ]
            )
            started = True
            params = {"host": str(socket), "user": "schema_builder"}
            with psycopg.connect(dbname="postgres", autocommit=True, **params) as admin:
                for service in SERVICES:
                    database = "rh_" + service
                    restored = database + "_restored"
                    for name in (database, restored):
                        admin.execute(
                            sql.SQL("CREATE DATABASE {} TEMPLATE template0").format(
                                sql.Identifier(name)
                            )
                        )
                    with psycopg.connect(dbname=database, **params) as connection:
                        connection.execute("CREATE SCHEMA api")
                        connection.execute("SET search_path=api,pg_catalog")
                        connection.execute(COMMON + SCHEMAS[service])
                        connection.execute(
                            "INSERT INTO schema_version(version) VALUES(1)"
                        )
                        migrate(connection, service)
                        versions = [
                            row[0]
                            for row in connection.execute(
                                "SELECT version FROM schema_version ORDER BY version"
                            )
                        ]
                        tables = connection.execute(
                            "SELECT count(*) FROM pg_tables WHERE schemaname='api'"
                        ).fetchone()[0]
                    command = [
                        str(binaries / "pg_dump"),
                        "--host",
                        str(socket),
                        "--username",
                        "schema_builder",
                        "--schema-only",
                        "--schema=api",
                        "--no-owner",
                        "--no-privileges",
                        "--dbname",
                    ]
                    dump = normalize(run(command + [database]))
                    snapshot = base / "schema.sql"
                    snapshot.write_text(dump)
                    run(
                        [
                            str(binaries / "psql"),
                            "--host",
                            str(socket),
                            "--username",
                            "schema_builder",
                            "--dbname",
                            restored,
                            "--no-psqlrc",
                            "--set",
                            "ON_ERROR_STOP=1",
                            "--single-transaction",
                            "--file",
                            str(snapshot),
                        ]
                    )
                    if normalize(run(command + [restored])) != dump:
                        raise RuntimeError(
                            f"La restauración de {service} difiere del esquema original"
                        )
                    header = (
                        f"-- Red House: {service}; base de referencia: {database}.\n"
                        f"-- Migraciones aplicadas: {', '.join(map(str, versions))}.\n"
                        "-- Generado por scripts/export_schemas.py; no editar manualmente.\n"
                        "-- Solo estructura; sin registros, roles, permisos ni marcas de migración.\n"
                        "-- Para consulta/restauración estructural en una base vacía, no para actualizar el entorno.\n\n"
                    )
                    generated[service + ".sql"] = header + dump
                    print(
                        f"{service}: {tables} tablas; migraciones {versions}; restauración verificada"
                    )
        finally:
            if started:
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
    if check:
        differences = [
            name
            for name, content in generated.items()
            if not (directory / name).exists()
            or (directory / name).read_text() != content
        ]
        extras = {p.name for p in directory.glob("*.sql")} - generated.keys()
        if differences or extras:
            raise RuntimeError(
                f"Esquemas desactualizados: {sorted(set(differences) | extras)}"
            )
        print("Los once esquemas coinciden con las migraciones actuales.")
    else:
        directory.mkdir(parents=True, exist_ok=True)
        for name, content in generated.items():
            (directory / name).write_text(content)
        print(f"Esquemas escritos en {directory}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pg-bin",
        type=Path,
        help="Directorio de initdb, pg_ctl, pg_dump y psql de la misma versión",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verifica sin modificar los SQL versionados",
    )
    args = parser.parse_args()
    binary = shutil.which("initdb")
    binaries = args.pg_bin or (Path(binary).resolve().parent if binary else None)
    if not binaries or any(
        not os.access(binaries / name, os.X_OK)
        for name in ("initdb", "pg_ctl", "pg_dump", "psql")
    ):
        parser.error("Instala las herramientas PostgreSQL o indica --pg-bin")
    export(ROOT / "data/database/postgresql", binaries, args.check)


if __name__ == "__main__":
    main()
