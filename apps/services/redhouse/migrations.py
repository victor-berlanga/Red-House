"""Migraciones aditivas por propietario; nunca se ejecutan al atender HTTP."""

from pathlib import Path

from .schema import service_path


COMMON_V2 = """
CREATE TABLE decisions(id uuid PRIMARY KEY, resource_id uuid NOT NULL, tenant_id uuid NOT NULL,
 actor_id uuid NOT NULL, action text NOT NULL, reason text NOT NULL,
 changes jsonb NOT NULL DEFAULT '{}', created_at timestamptz NOT NULL DEFAULT now());
CREATE INDEX decisions_resource ON decisions(resource_id,created_at);
CREATE TRIGGER decisions_immutable BEFORE UPDATE OR DELETE ON decisions FOR EACH ROW EXECUTE FUNCTION reject_history_mutation();
CREATE TABLE worker_health(id integer PRIMARY KEY CHECK(id=1), checked_at timestamptz NOT NULL,
 last_success timestamptz, last_error text);
"""


def migrate(conn, service):
    """Requiere credencial de propietario, search_path api y transacción externa."""
    conn.execute("SELECT pg_advisory_xact_lock(72182026)")
    installed = {
        row[0] for row in conn.execute("SELECT version FROM schema_version").fetchall()
    }
    scripts = {2: COMMON_V2}
    for path in sorted((service_path(service) / "migrations").glob("*.sql")):
        version = int(path.stem)
        if version > 1:
            scripts[version] = scripts.get(version, "") + "\n" + path.read_text()
    for version, sql in sorted(scripts.items()):
        if version not in installed:
            conn.execute(sql)
            conn.execute("INSERT INTO schema_version(version) VALUES(%s)", (version,))
