"""Extrae solo catálogo SQL de un fixture privado; no inicia ni detiene motores."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]


def capture(directory):
    import psycopg
    from psycopg.conninfo import conninfo_to_dict, make_conninfo
    from psycopg.rows import dict_row

    sys.path.insert(0, str(ROOT / "apps/services"))
    from redhouse.config import SERVICES

    if directory.is_symlink():
        raise ValueError("El fixture no puede ser un enlace simbólico")
    directory = directory.resolve(strict=True)
    state_path = directory / "state.json"
    info = state_path.stat()
    if state_path.is_symlink() or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise ValueError("Se requiere state.json privado del usuario actual")
    state = json.loads(state_path.read_text())
    if Path(state["directory"]).resolve() != directory:
        raise ValueError("El estado no corresponde al fixture indicado")
    if any(os.environ.get(key) for key in ("PGHOSTADDR", "PGSERVICE", "PGOPTIONS")):
        raise ValueError("Retirar variables PostgreSQL ajenas al fixture")
    options = conninfo_to_dict(state["database_admin"])
    if (
        options.get("host") != "127.0.0.1"
        or not options.get("port", "").isdigit()
        or any(options.get(key) for key in ("hostaddr", "service", "options"))
        or set(state["database_owners"]) != set(SERVICES)
    ):
        raise ValueError("El fixture exige loopback y doce propietarios conocidos")
    dsn = make_conninfo(state["database_admin"], dbname="red_house")
    with psycopg.connect(dsn, connect_timeout=3, row_factory=dict_row) as conn:
        conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
        conn.execute("SET LOCAL statement_timeout='10s'")
        conn.execute("SET LOCAL lock_timeout='1s'")
        if (
            Path(
                conn.execute("SHOW data_directory").fetchone()["data_directory"]
            ).resolve()
            != directory / "pg"
        ):
            raise ValueError("PostgreSQL no pertenece al fixture indicado")
        version = conn.execute(
            "SELECT max(version) AS version FROM red_house.schema_migration"
        ).fetchone()["version"]
        if version != 20:
            raise ValueError("El catálogo final requiere esquema 20")
        tables = conn.execute("""
            SELECT n.nspname AS schema,c.relname AS name,c.oid
            FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
            WHERE n.nspname IN ('red_house','web_runtime') AND c.relkind IN ('r','p')
            ORDER BY n.nspname,c.relname
        """).fetchall()
        for table in tables:
            oid = table.pop("oid")
            table["columns"] = conn.execute(
                """
                SELECT column_name,ordinal_position,column_default,is_nullable,data_type,
                    character_maximum_length,udt_name
                FROM information_schema.columns
                WHERE table_schema=%s AND table_name=%s ORDER BY ordinal_position
            """,
                (table["schema"], table["name"]),
            ).fetchall()
            table["constraints"] = conn.execute(
                """
                SELECT c.conname AS name,c.contype AS type,
                    pg_catalog.pg_get_constraintdef(c.oid,true) AS definition,
                    CASE WHEN c.confrelid<>0 THEN tn.nspname||'.'||t.relname END AS target
                FROM pg_catalog.pg_constraint c
                LEFT JOIN pg_catalog.pg_class t ON t.oid=c.confrelid
                LEFT JOIN pg_catalog.pg_namespace tn ON tn.oid=t.relnamespace
                WHERE c.conrelid=%s ORDER BY c.conname
            """,
                (oid,),
            ).fetchall()
            table["triggers"] = conn.execute(
                """
                SELECT tgname AS name,pg_catalog.pg_get_triggerdef(oid,true) AS definition
                FROM pg_catalog.pg_trigger WHERE tgrelid=%s AND NOT tgisinternal ORDER BY tgname
            """,
                (oid,),
            ).fetchall()
        indexes = conn.execute("""
            SELECT schemaname,tablename,indexname,indexdef FROM pg_catalog.pg_indexes
            WHERE schemaname IN ('red_house','web_runtime')
            ORDER BY schemaname,tablename,indexname
        """).fetchall()
        views = conn.execute("""
            SELECT substring(n.nspname FROM 8) AS owner,v.relname AS name,
                coalesce(array_agg(DISTINCT tn.nspname||'.'||t.relname
                    ORDER BY tn.nspname||'.'||t.relname)
                    FILTER (WHERE tn.nspname IN ('red_house','web_runtime')
                        AND t.relkind IN ('r','p')),ARRAY[]::text[]) AS tables
            FROM pg_catalog.pg_class v JOIN pg_catalog.pg_namespace n ON n.oid=v.relnamespace
            LEFT JOIN pg_catalog.pg_rewrite r ON r.ev_class=v.oid
            LEFT JOIN pg_catalog.pg_depend d ON d.classid='pg_rewrite'::regclass
                AND d.objid=r.oid AND d.refclassid='pg_class'::regclass
            LEFT JOIN pg_catalog.pg_class t ON t.oid=d.refobjid
            LEFT JOIN pg_catalog.pg_namespace tn ON tn.oid=t.relnamespace
            WHERE left(n.nspname,7)='access_' AND v.relkind='v'
            GROUP BY n.nspname,v.relname ORDER BY n.nspname,v.relname
        """).fetchall()
        readonly = (
            conn.execute("SHOW transaction_read_only").fetchone()[
                "transaction_read_only"
            ]
            == "on"
        )
        server = conn.execute("SHOW server_version").fetchone()["server_version"]
    return {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "schema_version": version,
        "transaction_read_only": readonly,
        "server_version": server,
        "scope": "pg_catalog/information_schema y versión técnica de migración; sin filas de negocio, roles personales, DSN o secretos",
        "service_names": sorted(SERVICES),
        "tables": tables,
        "indexes": indexes,
        "views": views,
        "migration_sources": {
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(
                (ROOT / "apps/services/redhouse/shared_migrations").glob("*.sql")
            )
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    destination = args.output.resolve()
    allowed = ROOT / "documentation/evidencias/entrega-final"
    if not destination.is_relative_to(allowed) or destination.exists():
        parser.error(
            "Usar un archivo nuevo dentro de documentation/evidencias/entrega-final"
        )
    try:
        metadata = capture(args.fixture)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("x") as stream:
            json.dump(metadata, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
    except Exception as exc:
        # Los errores del controlador pueden incluir detalles de conexión.
        print(
            "Extracción no completada; tipo de error: " + type(exc).__name__,
            file=sys.stderr,
        )
        return 1
    print(
        json.dumps(
            {
                "tables": len(metadata["tables"]),
                "indexes": len(metadata["indexes"]),
                "services": len(metadata["service_names"]),
                "schema_version": metadata["schema_version"],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
