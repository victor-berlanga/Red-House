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
BASE = '1f02c0cc7e3e13c9d7593e659fbd407165ef9823'


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def allowed(name):
    return (
        name.startswith('apps/services/')
        and '/tests/' not in name
        and not name.rsplit('/', 1)[-1].startswith('requirements')
    ) or name.startswith('apps/web/src/') or name == 'deployment/gcp/configure_public.py'


if __name__ == '__main__':
    target = git('rev-parse', '--verify', sys.argv[1] + '^{commit}').decode().strip()
    deleted = git('diff', '--name-only', '--diff-filter=D', BASE, target).decode().splitlines()
    assert not any(allowed(name) for name in deleted), 'Deletion requires a separate deployment review'
    names = [name for name in git('diff', '--name-only', BASE, target).decode().splitlines() if allowed(name)]
    reviewed_prefixes = ('apps/services/ms_donantes/', 'apps/services/ms_compatibilidad/', 'apps/web/src/')
    assert all(name.startswith(reviewed_prefixes) or name == 'apps/services/redhouse/audit_catalog.py' for name in names), 'Unexpected runtime module; review deployment scope'
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
