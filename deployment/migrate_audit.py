"""Respaldo y migración aditiva de auditoría 6→7 en una instalación Compose existente."""

import argparse
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args()
    directory = args.directory.resolve()
    if not (directory / "installation.json").is_file():
        raise RuntimeError("Selecciona una instalación Docker existente con marcador.")
    os.umask(0o077)
    environment = dict(os.environ, REDHOUSE_COMPOSE_DIR=str(directory))
    compose = ["docker", "compose", "-f", str(ROOT / "compose.yaml")]
    prefix = compose + ["exec", "-T", "postgres"]
    psql = prefix + [
        "psql",
        "-U",
        "rh_bootstrap",
        "-d",
        "red_house",
        "-qAt",
        "-v",
        "ON_ERROR_STOP=1",
    ]

    def run(command, data=None, output=None):
        result = subprocess.run(
            command,
            input=data,
            stdout=output or subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=environment,
            check=False,
        )
        if result.returncode:
            raise RuntimeError(
                "Falló el respaldo o la migración de PostgreSQL; no se exponen credenciales. Revisa el estado antes de reiniciar aplicaciones."
            )
        return result.stdout

    before = int(
        run(psql + ["-c", "SELECT max(version) FROM red_house.schema_migration"])
    )
    if before == 7:
        print("El esquema ya tiene la versión 7; no se modificó.")
        return
    if before != 6:
        raise RuntimeError("Esta migración requiere la versión compartida 6.")
    destination = (
        directory
        / "backups"
        / ("audit-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
    )
    destination.mkdir(parents=True, mode=0o700)
    with (destination / "red_house.dump").open("wb") as stream:
        run(
            prefix + ["pg_dump", "-U", "rh_bootstrap", "-d", "red_house", "-Fc"],
            output=stream,
        )
    with (destination / "roles.sql").open("wb") as stream:
        run(
            prefix + ["pg_dumpall", "-U", "rh_bootstrap", "--globals-only"],
            output=stream,
        )
    migration = (ROOT / "apps/services/redhouse/shared_migrations/007.sql").read_text()
    guard = """BEGIN;
SELECT pg_advisory_xact_lock(72182027);
DO $$ BEGIN
 IF (SELECT max(version) FROM red_house.schema_migration) <> 6 THEN
  RAISE EXCEPTION 'Version changed before migration';
 END IF;
END $$;
SET ROLE rh_shared_owner;
"""
    run(psql, (guard + migration + "\nCOMMIT;\n").encode())
    after = int(
        run(psql + ["-c", "SELECT max(version) FROM red_house.schema_migration"])
    )
    (destination / "report.json").write_text(
        json.dumps(
            {"before": before, "after": after, "backup": "red_house.dump"}, indent=2
        )
        + "\n"
    )
    print(f"Esquema actualizado a {after}. Respaldo privado: {destination}")


if __name__ == "__main__":
    main()
