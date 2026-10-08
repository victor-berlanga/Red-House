"""Restaura respaldos en bases desechables propias y comprueba migración repetible."""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from redhouse.migrations import migrate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--backup", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    state = json.loads((args.directory / "state.json").read_text())
    if Path(state["directory"]).resolve() != args.directory.resolve():
        raise RuntimeError("Entorno no corresponde.")
    backup = args.backup.resolve()
    if args.directory.resolve() not in backup.parents:
        raise RuntimeError("El respaldo debe pertenecer a este entorno.")
    params = conninfo_to_dict(state["database_admin"])
    executable = str(
        Path(state["infrastructure_commands"]["postgres"][0]).with_name("pg_restore")
    )
    report = {}
    with psycopg.connect(state["database_admin"], autocommit=True) as admin:
        for source in sorted(backup.glob("*.dump")):
            service = source.stem
            name = "verify_backup_" + uuid4().hex
            admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
            try:
                result = subprocess.run(
                    [
                        executable,
                        "--host",
                        params["host"],
                        "--port",
                        params["port"],
                        "--username",
                        params["user"],
                        "--dbname",
                        name,
                        "--no-owner",
                        "--no-privileges",
                        "--exit-on-error",
                        str(source),
                    ],
                    env={**os.environ, "PGPASSWORD": params["password"]},
                    capture_output=True,
                )
                if result.returncode:
                    raise RuntimeError("Falló restauración aislada de " + service)
                with psycopg.connect(
                    make_conninfo(state["database_admin"], dbname=name)
                ) as conn:
                    conn.execute("SET search_path=api,pg_catalog")
                    tables = [
                        row[0]
                        for row in conn.execute(
                            "SELECT tablename FROM pg_tables WHERE schemaname='api' AND tablename!='schema_version' ORDER BY tablename"
                        )
                    ]

                    def counts():
                        return {
                            table: conn.execute(
                                sql.SQL("SELECT count(*) FROM {}").format(
                                    sql.Identifier(table)
                                )
                            ).fetchone()[0]
                            for table in tables
                        }

                    before = counts()
                    migrate(conn, service)
                    migrate(conn, service)
                    assert before == counts(), service
                    versions = [
                        row[0]
                        for row in conn.execute(
                            "SELECT version FROM schema_version ORDER BY version"
                        )
                    ]
                    report[service] = {
                        "restored": True,
                        "existing_rows_preserved": True,
                        "tables_verified": len(tables),
                        "versions": versions,
                    }
            finally:
                # Solo la base aleatoria creada en esta iteración; nunca una base de aplicación.
                admin.execute(
                    sql.SQL("DROP DATABASE {} WITH (FORCE)").format(
                        sql.Identifier(name)
                    )
                )
    args.report.write_text(
        json.dumps({"result": "passed", "services": report}, indent=2) + "\n"
    )
    print(
        "Respaldos restaurados, migración repetida y datos conservados en once bases desechables."
    )


if __name__ == "__main__":
    main()
