"""Respalda y aplica migraciones aditivas; admite actualizar un único servicio."""

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from redhouse.config import SERVICES
from redhouse.migrations import migrate


def upgrade(directory, services):
    directory = Path(directory).resolve()
    state = json.loads((directory / "state.json").read_text())
    if Path(state["directory"]).resolve() != directory:
        raise RuntimeError("El directorio no coincide con el entorno.")
    if state.get("database_layout") == "shared-v6":
        from redhouse.shared_migrations import upgrade as upgrade_shared, LATEST_VERSION

        dsn = next(iter(state["database_owners"].values()))
        with psycopg.connect(dsn) as conn:
            version = conn.execute(
                "SELECT max(version) FROM red_house.schema_migration"
            ).fetchone()[0]
        if version not in (6, LATEST_VERSION):
            raise RuntimeError(
                "Versión compartida inesperada; requiere una migración global revisada."
            )
        backup = None
        if version < LATEST_VERSION:
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
            backup = directory / "backups" / ("audit-" + stamp)
            backup.mkdir(parents=True, mode=0o700)
            params = conninfo_to_dict(dsn)
            binary = shutil.which("pg_dump") or str(
                Path(state["infrastructure_commands"]["postgres"][0]).with_name(
                    "pg_dump"
                )
            )
            dump = backup / "red_house.dump"
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
                    "Falló el respaldo; no se aplicó la migración compartida."
                )
            dump.chmod(0o600)
        with psycopg.connect(dsn) as conn:
            conn.execute("SET ROLE rh_shared_owner")
            current = upgrade_shared(conn)
        report = {
            "before": version,
            "shared_version": current,
            "backup": str(backup) if backup else None,
        }
        if backup:
            (backup / "report.json").write_text(json.dumps(report, indent=2) + "\n")
        print(
            f"Esquema compartido versión {current} verificado; registros conservados."
        )
        return report
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    backup = directory / "backups" / stamp
    backup.mkdir(parents=True, mode=0o700)
    binary = shutil.which("pg_dump") or str(
        Path(state["infrastructure_commands"]["postgres"][0]).with_name("pg_dump")
    )
    results = {}
    for service in services:
        dsn = state["database_owners"][service]
        params = conninfo_to_dict(dsn)
        dump = backup / (service + ".dump")
        environment = dict(os.environ, PGPASSWORD=params["password"])
        command = [
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
        ]
        result = subprocess.run(command, env=environment, capture_output=True)
        if result.returncode:
            raise RuntimeError(
                "Falló el respaldo de " + service + "; no se aplicaron sus migraciones."
            )
        os.chmod(dump, 0o600)
        with psycopg.connect(dsn) as conn:
            conn.execute("SET search_path=api,pg_catalog")
            conn.execute(
                sql.SQL("SET ROLE {}").format(
                    sql.Identifier("rh_" + service + "_owner")
                )
            )
            before = [
                r[0]
                for r in conn.execute(
                    "SELECT version FROM schema_version ORDER BY version"
                )
            ]
            migrate(conn, service)
            runtime = "rh_" + service
            for table in (
                "decisions",
                "worker_health",
                "catalogue",
                "cache_revision",
                "audit_findings",
                "audit_finding_links",
                "audit_finding_actions",
            ):
                if conn.execute("SELECT to_regclass(%s)", ("api." + table,)).fetchone()[
                    0
                ]:
                    conn.execute(
                        sql.SQL("GRANT SELECT,INSERT,UPDATE,DELETE ON {} TO {}").format(
                            sql.Identifier(table), sql.Identifier(runtime)
                        )
                    )
            conn.execute(
                sql.SQL("REVOKE UPDATE,DELETE ON decisions FROM {}").format(
                    sql.Identifier(runtime)
                )
            )
            if service == "auditoria":
                conn.execute(
                    sql.SQL("REVOKE DELETE ON audit_findings FROM {}").format(
                        sql.Identifier(runtime)
                    )
                )
                conn.execute(
                    sql.SQL(
                        "REVOKE UPDATE,DELETE ON audit_finding_links,audit_finding_actions FROM {}"
                    ).format(sql.Identifier(runtime))
                )
                conn.execute(
                    sql.SQL("GRANT EXECUTE ON FUNCTION event_time(text) TO {}").format(
                        sql.Identifier(runtime)
                    )
                )
            after = [
                r[0]
                for r in conn.execute(
                    "SELECT version FROM schema_version ORDER BY version"
                )
            ]
        config_path = directory / (service + ".json")
        config = json.loads(config_path.read_text())
        config["WORKER_REQUIRED"] = True
        config_path.write_text(json.dumps(config, indent=2))
        os.chmod(config_path, 0o600)
        results[service] = {"before": before, "after": after, "backup": dump.name}
    (backup / "report.json").write_text(json.dumps(results, indent=2) + "\n")
    print("Migraciones verificadas:", ", ".join(results))
    print("Respaldo privado:", backup)
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--service", choices=SERVICES)
    args = parser.parse_args()
    upgrade(args.directory, [args.service] if args.service else list(SERVICES))


if __name__ == "__main__":
    main()
