"""Migración explícita Compose; requiere respaldo externo verificado y APIs detenidas.

Ejecutar con la imagen bootstrap correctiva y /run/install montado como en Compose.
No arranca servicios, no envía avisos y no crea infraestructura.
"""

import argparse
import json
from pathlib import Path
from urllib.parse import quote, urlsplit, urlunsplit

import psycopg
from psycopg import sql
from redhouse.shared_migrations import upgrade
from scripts.web_sessions import write_private
from scripts.upgrade_documents import provision_documents
from scripts.upgrade_final_acl import upgrade_acl


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backup", type=Path, required=True)
    parser.add_argument("--directory", type=Path, default=Path("/run/install"))
    args = parser.parse_args()
    if not args.backup.is_file() or args.backup.stat().st_size == 0:
        raise RuntimeError("Respaldo privado requerido antes de migrar.")
    directory = args.directory.resolve()
    state = json.loads((directory / "state.json").read_text())
    dsn = next(iter(state["database_owners"].values()))
    with psycopg.connect(dsn) as conn:
        # Las instalaciones antiguas no conceden CREATE en la base al dueño del
        # esquema. La extracción crea un esquema nuevo: permiso transaccional,
        # retirado antes del commit y revertido si cualquier migración falla.
        database, had_create = conn.execute(
            "SELECT current_database(), "
            "has_database_privilege('rh_shared_owner', current_database(), 'CREATE')"
        ).fetchone()
        if not had_create:
            conn.execute(
                sql.SQL("GRANT CREATE ON DATABASE {} TO rh_shared_owner").format(
                    sql.Identifier(database)
                )
            )
        conn.execute("SET LOCAL ROLE rh_shared_owner")
        version = upgrade(conn)
        conn.execute("RESET ROLE")
        if not had_create:
            conn.execute(
                sql.SQL("REVOKE CREATE ON DATABASE {} FROM rh_shared_owner").format(
                    sql.Identifier(database)
                )
            )
    # El instalador v7 conservaba la contraseña administrativa en un archivo
    # separado, sin redis_admin en state.json. No rotar esa credencial.
    if "redis_admin" not in state:
        config = json.loads((directory / "apps/donantes.json").read_text())
        location = urlsplit(config["REDIS_URL"])
        password = quote((directory / "redis-password").read_text().strip(), safe="")
        state["redis_admin"] = urlunsplit(
            location._replace(
                netloc=f":{password}@{location.hostname}:{location.port or 6379}"
            )
        )
    provision_documents(directory / "apps", state)
    upgrade_acl(directory / "apps", state)
    # El directorio host es privado; los secretos montados son legibles por UID 10001.
    for path in (directory / "apps").glob("*.json"):
        path.chmod(0o644)
    web_path = directory / "web.json"
    web = json.loads(web_path.read_text())
    web["SERVICE_URLS"]["documentos"] = "http://127.0.0.1:5112"
    write_private(web_path, json.dumps(web, indent=2) + "\n")
    web_path.chmod(0o644)
    write_private(directory / "state.json", json.dumps(state, indent=2) + "\n")
    (directory / "apps/state.json").unlink(missing_ok=True)
    print(
        f"Migración compartida {version} y propietario Documentos preparados; reiniciar versión compatible."
    )


if __name__ == "__main__":
    main()
