"""Incrementos globales aditivos para una base compartida instalada; uso administrativo."""

from pathlib import Path

from psycopg import sql

LATEST_VERSION = 7


def upgrade(conn):
    conn.execute("SELECT pg_advisory_xact_lock(72182027)")
    installed = {
        row[0] for row in conn.execute("SELECT version FROM red_house.schema_migration")
    }
    if 6 not in installed or max(installed) > LATEST_VERSION:
        raise RuntimeError("Versión compartida no compatible.")
    if 7 not in installed:
        path = Path(__file__).resolve().parent / "shared_migrations/007.sql"
        conn.execute(path.read_text())
    # También se aplica después de crear las credenciales en instalaciones nuevas.
    if conn.execute("SELECT 1 FROM pg_roles WHERE rolname='rh_auditoria'").fetchone():
        for table in ("audit_findings", "audit_finding_links", "audit_finding_actions"):
            conn.execute(
                sql.SQL(
                    "GRANT SELECT,INSERT ON access_auditoria.{} TO rh_auditoria"
                ).format(sql.Identifier(table))
            )
            conn.execute(
                sql.SQL(
                    "REVOKE UPDATE,DELETE ON access_auditoria.{} FROM rh_auditoria"
                ).format(sql.Identifier(table))
            )
        conn.execute("GRANT UPDATE ON access_auditoria.audit_findings TO rh_auditoria")
        conn.execute(
            "GRANT EXECUTE ON FUNCTION access_auditoria.event_time(text) TO rh_auditoria"
        )
    return LATEST_VERSION
