"""Freeze a reviewed Git delta; excludes clients, tests, credentials and evidence."""
import hashlib
import io
import json
import subprocess
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = Path(__file__).resolve().parent
BASE = '9648bf4c0cb857498566e2f3a68c253887deb13f'


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


RUNTIME_FILES = {
    'apps/services/ms_documentos/files.py',
    'apps/services/ms_documentos/reports.py',
    'apps/services/ms_identidad_acceso/devices.py',
    'apps/services/ms_identidad_acceso/routes.py',
    'apps/services/ms_identidad_acceso/contracts/openapi.json',
    'apps/services/ms_identidad_acceso/contracts/user_creation_receipt.response.json',
    'apps/services/redhouse/config.py',
    'apps/services/redhouse/evidence.py',
    'apps/services/redhouse/malware.py',
    'apps/services/redhouse/openapi.py',
    'apps/services/redhouse/shared_migrations.py',
    'apps/services/redhouse/shared_migrations/020.sql',
    'deployment/gcp/configure_scanner.py',
}


def allowed(name):
    return name in RUNTIME_FILES


if __name__ == '__main__':
    target = git('rev-parse', '--verify', sys.argv[1] + '^{commit}').decode().strip()
    deleted = git('diff', '--name-only', '--diff-filter=D', BASE, target).decode().splitlines()
    assert not any(allowed(name) for name in deleted), 'Deletion requires a separate deployment review'
    names = [name for name in git('diff', '--name-only', BASE, target).decode().splitlines() if allowed(name)]
    assert set(names) == RUNTIME_FILES, 'Unexpected runtime scope'
    assert names and all(Path(name).suffix in ('.py', '.json', '.xml', '.xsd', '.sql', '.html', '.css', '.js') for name in names)
    before = {}
    after = {}
    baseline_names = set(git('ls-tree', '-r', '--name-only', BASE).decode().splitlines())
    with tarfile.open(OUTPUT / 'payload.tar.gz', 'w:gz') as archive:
        for name in names:
            content = git('show', target + ':' + name)
            after[name] = hashlib.sha256(content).hexdigest()
            before[name] = hashlib.sha256(git('show', BASE + ':' + name)).hexdigest() if name in baseline_names else None
            entry = tarfile.TarInfo(name)
            entry.size = len(content)
            entry.mode = 0o644
            archive.addfile(entry, io.BytesIO(content))
    for name, value in [('manifest.json', after), ('expected-before.json', before), ('source.json', {'base': BASE, 'commit': target})]:
        (OUTPUT / name).write_text(json.dumps(value, indent=2) + '\n')
    print(json.dumps({'commit': target, 'files': len(names), 'payload_sha256': hashlib.sha256((OUTPUT / 'payload.tar.gz').read_bytes()).hexdigest()}))
