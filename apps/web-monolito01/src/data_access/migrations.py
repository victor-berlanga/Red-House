"""Migraciones aditivas versionadas, atómicas y sin reinicialización."""
import hashlib
from pathlib import Path


MIGRATIONS = Path(__file__).resolve().parents[4] / 'data/database/migrations'


def migrate(conn):
    conn.execute("SELECT pg_advisory_xact_lock(hashtextextended('red-house-schema-migrations',0))")
    conn.execute('''CREATE TABLE IF NOT EXISTS schema_migration (
        version varchar(80) PRIMARY KEY, sha256 char(64) NOT NULL,
        applied_at timestamptz NOT NULL DEFAULT now())''')
    applied = []
    for path in sorted(MIGRATIONS.glob('*.sql')):
        source = path.read_bytes()
        digest = hashlib.sha256(source).hexdigest()
        row = conn.execute('SELECT sha256 FROM schema_migration WHERE version=%s', (path.name,)).fetchone()
        if row:
            if row['sha256'] != digest:
                raise RuntimeError('Una migración aplicada fue modificada. Requiere revisión; no se confirma ningún cambio.')
            continue
        conn.execute(source.decode('utf-8'))
        conn.execute('INSERT INTO schema_migration(version,sha256) VALUES (%s,%s)', (path.name,digest))
        applied.append(path.name)
    return applied
