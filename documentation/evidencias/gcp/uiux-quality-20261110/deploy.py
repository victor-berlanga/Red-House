"""Publish the reviewed presentation delta over the current web image only."""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

ROOT = Path('/opt/redhouse')
INPUT = Path('/tmp/redhouse-uiux-quality-20261110')
BACKUP = ROOT / '.local/deploy-uiux-quality-20261110'
CFG = ROOT / '.local/compose'
TAG = 'redhouse/web:uiux-quality-20261110'
OLD_TAG = 'redhouse/web:uiux-quality-before-20261110'
WEB = 'redhouse-parcial2-web-1'

def run(args):
    subprocess.run(args, cwd=ROOT, check=True)

def capture(args):
    return subprocess.check_output(args, cwd=ROOT, text=True).strip()

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(name, data):
    (BACKUP / name).write_text(json.dumps(data, indent=2) + '\n')

def compose():
    return ['docker', 'compose', '-f', str(ROOT/'compose.yaml'), '-f', str(CFG/'gcs.compose.yaml'), '-f', str(CFG/'public.compose.yaml')]

def containers():
    ids = capture(['docker', 'ps', '-aq', '--filter', 'label=com.docker.compose.project=redhouse-parcial2']).split()
    return {v['Name'].lstrip('/'): {'id': v['Id'], 'image': v['Image'], 'health': v['State'].get('Health', {}).get('Status'), 'running': v['State']['Running']} for v in json.loads(capture(['docker', 'inspect', *ids]))}

def main():
    assert os.geteuid() == 0
    manifest = json.loads((INPUT/'manifest.json').read_text())
    expected = json.loads((INPUT/'expected-before.json').read_text())
    preflight = json.loads((INPUT/'preflight.json').read_text())
    assert len(manifest) == 20 and set(manifest) == set(expected)
    for name, sha in expected.items():
        assert name.startswith('apps/web/src/presentation/') and '..' not in Path(name).parts
        assert Path(name).suffix in {'.html', '.css', '.js', '.svg'}
        assert (digest(ROOT/name) if (ROOT/name).exists() else None) == sha, 'Changed remote source: ' + name
    before = containers()
    assert before == preflight['containers'], 'Runtime changed after preflight'
    assert sum(v['running'] for v in before.values()) == 30
    assert all(v['health'] == 'healthy' for v in before.values() if v['running'])
    BACKUP.mkdir(mode=0o700, exist_ok=False)
    save('runtime-before.json', before)
    save('manifest.json', manifest)
    save('expected-before.json', expected)
    for name, sha in expected.items():
        if sha is not None:
            destination = BACKUP/'sources'/name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT/name, destination)
    shutil.copy2(CFG/'gcs.compose.yaml', BACKUP/'gcs.compose.yaml')
    shutil.copy2(INPUT/'rollback.py', BACKUP/'rollback.py')
    old = before[WEB]['image']
    run(['docker', 'tag', old, OLD_TAG])
    build = BACKUP/'build'
    build.mkdir()
    with tarfile.open(INPUT/'presentation.tar.gz') as archive:
        members = archive.getmembers()
        assert len(members) == len(manifest) and {m.name for m in members} == set(manifest)
        for member in members:
            assert member.isfile()
            data = archive.extractfile(member).read()
            assert hashlib.sha256(data).hexdigest() == manifest[member.name]
            destination = build/'payload'/member.name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
            destination.chmod(0o644)
    (build/'Dockerfile').write_text(f'FROM {OLD_TAG}\nCOPY payload/ /app/\n')
    run(['docker', 'build', '--network=none', '-t', TAG, str(build)])
    check = 'import hashlib;from pathlib import Path;from jinja2 import Environment;expected=' + repr(manifest) + ';assert all(hashlib.sha256((Path("/app")/n).read_bytes()).hexdigest()==h for n,h in expected.items());env=Environment();[env.parse(p.read_text()) for p in Path("/app/apps/web/src/presentation/templates").rglob("*.html")];print("Image hashes and Jinja syntax verified")'
    run(['docker', 'run', '--rm', '--network=none', '--entrypoint', 'python', TAG, '-c', check])
    original = json.loads((CFG/'gcs.compose.yaml').read_text())
    updated = json.loads(json.dumps(original))
    updated['services']['web']['image'] = TAG
    try:
        for name in manifest:
            (ROOT/name).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(build/'payload'/name, ROOT/name)
        (CFG/'gcs.compose.yaml').write_text(json.dumps(updated, indent=2) + '\n')
        run(compose() + ['config', '--quiet'])
        run(compose() + ['up', '-d', '--no-deps', '--no-build', '--wait', '--wait-timeout', '180', 'web'])
        after = containers()
        assert set(after) == set(before)
        assert all(after[n] == v for n, v in before.items() if n != WEB), 'Another container changed'
        assert all(v['health'] == 'healthy' for v in after.values() if v['running'])
        assert all(digest(ROOT/n) == sha for n, sha in manifest.items())
        save('runtime-after.json', after)
        result = {'tag': TAG, 'files': len(manifest), 'new_files': sum(v is None for v in expected.values()), 'running_containers': sum(v['running'] for v in after.values()), 'unchanged_other_running_containers': 29, 'healthy': True, 'database_migrations': False, 'backup': str(BACKUP), 'old_image': old, 'new_image': after[WEB]['image']}
        save('result.json', result)
        print(json.dumps(result, indent=2))
    except BaseException:
        run(['python3', str(BACKUP/'rollback.py')])
        raise

if __name__ == '__main__':
    main()
