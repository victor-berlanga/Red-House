"""Read-only oracle for the two objects already produced by Chrome."""
import hashlib
import json
import os
from pathlib import Path
import socket
import stat
import subprocess
import time

import psycopg
from psycopg.conninfo import conninfo_to_dict

os.umask(0o077)
folder = Path('/private/tmp/red-house-ms-tests-33vyo8a9')
out = Path('.local/artifacts/portal-documentos-20261114/intento-02').resolve()
assert folder.resolve() == folder and folder.stat().st_uid == os.getuid()
state_file = folder / 'state.json'
assert stat.S_IMODE(state_file.stat().st_mode) == 0o600
state = json.loads(state_file.read_text())
assert Path(state['directory']).resolve() == folder
command = state['infrastructure_commands']['postgres']
assert Path(command[0]).name == 'postgres'
assert Path(command[command.index('-D') + 1]).resolve() == folder / 'pg'
assert not (folder / 'pg/postmaster.pid').exists()
dsn = state['database_owners']['documentos']
settings = conninfo_to_dict(dsn)
assert settings['host'] == '127.0.0.1'
port = int(settings['port'])
assert int(command[command.index('-p') + 1]) == port
with socket.socket() as guard:
    guard.bind(('127.0.0.1', port))
report = json.loads((out / 'browser.json').read_text())
assert report['passed']
ids = report['documents']
assert len(ids) == len(set(ids)) == 2
summary = dict(passed=False, source_attempt=2, browser_repeated=False)
process = None
try:
    with (out / 'oraculo-postgres.private.log').open('w') as log:
        process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
        for _ in range(100):
            assert process.poll() is None
            try:
                connection = psycopg.connect(dsn, connect_timeout=1)
                break
            except psycopg.OperationalError:
                time.sleep(0.1)
        else:
            raise RuntimeError('owned_postgres_not_ready')
        with connection as conn:
            conn.execute('SET TRANSACTION READ ONLY')
            rows = conn.execute(
                'SELECT id::text,version,supersedes::text FROM document_metadata '
                'WHERE id = ANY(%s::uuid[]) ORDER BY version', (ids,),
            ).fetchall()
            assert rows == [(ids[0], 1, None), (ids[1], 2, ids[0])]
            for index, identifier in enumerate(ids, 1):
                content = (out / f'descarga-v{index}.png').read_bytes()
                digest = hashlib.sha256(content).hexdigest()
                row = conn.execute(
                    'SELECT status,size,sha256,mime_type,generation FROM files WHERE id=%s',
                    (identifier,),
                ).fetchone()
                assert row[:4] == ('VERIFIED', len(content), digest, 'image/png')
                assert row[4]
                clean = conn.execute(
                    'SELECT status FROM file_scans WHERE file_id=%s AND generation=%s '
                    'AND sha256=%s ORDER BY created_at DESC,id DESC LIMIT 1',
                    (identifier, row[4], digest),
                ).fetchone()
                assert clean == ('CLEAN',)
                for action in ('DOCUMENT_PREPARED', 'FILE_VERIFIED'):
                    count = conn.execute(
                        "SELECT count(*) FROM activity_events WHERE event->>'resource_id'=%s "
                        "AND event->>'action'=%s", (identifier, action),
                    ).fetchone()[0]
                    assert count == 1
            assert (out / 'descarga-v1.png').read_bytes() == (out / 'descarga-v1-conservada.png').read_bytes()
            summary.update(passed=True, versions=2, verified=2, clean_same_generation=2,
                           document_prepared_events=2, file_verified_events=2,
                           download_bytes_match=True, old_version_preserved=True,
                           read_only_transaction=True)
finally:
    if process is not None and process.poll() is None:
        process.terminate()
        process.wait(timeout=15)
    summary['owned_postgres_stopped'] = process is None or process.poll() is not None
    (out / 'oraculo-corregido.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary))
