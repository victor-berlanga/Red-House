"""Reviewed scope: configure ClamAV readiness on the existing verified VM only."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import time

sys.path.insert(0, '/opt/redhouse/.local/deploy-scanner20-20261113')
import release_base as base

ROOT, CFG = base.ROOT, base.CFG
INPUT = Path('/tmp/redhouse-scanner-health-20261113')
BACKUP = ROOT / '.local/deploy-scanner-health-20261113'
FILES = ('deployment/gcp/configure_scanner.py', 'deployment/gcp/clamav_readiness.sh', 'deployment/backup.py')
HELPER = CFG / 'clamav-readiness.sh'
OVERRIDE = CFG / 'gcs.compose.yaml'
DOC = CFG / 'apps/documentos.json'
TARGET = '/opt/redhouse/clamav-readiness.sh'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(name):
    return json.loads((BACKUP / name).read_text())


def save(name, value, directory=BACKUP):
    path = directory / name
    temporary = path.with_suffix(path.suffix + '.tmp')
    with temporary.open('w') as out:
        json.dump(value, out, indent=2)
        out.write('\n')
        out.flush()
        os.fsync(out.fileno())
    os.replace(temporary, path)


def payload():
    manifest = json.loads((INPUT / 'manifest.json').read_text())
    assert set(manifest) == set(FILES)
    for name in FILES:
        assert base.digest(INPUT / 'payload' / name) == manifest[name]['new']
    return manifest


def runtime_other(before, after):
    assert set(before) == set(after) and len(after) == 30
    for name in before:
        if name != 'clamav':
            assert after[name] == before[name], 'Unexpected change outside ClamAV'
    assert after['clamav']['image'] == before['clamav']['image']
    assert after['clamav']['running']


def safe_destinations():
    assert not ROOT.is_symlink(), 'Installation root is a symlink'
    for path in [ROOT / name for name in FILES] + [HELPER, OVERRIDE, DOC]:
        parent = ROOT
        assert path.is_relative_to(ROOT)
        for part in path.relative_to(ROOT).parts:
            parent = parent / part
            assert not parent.is_symlink(), 'Symlink in deployment path'
        assert path.resolve().is_relative_to(ROOT.resolve()), 'Destination escapes installation'


def preflight():
    base.target()
    safe_destinations()
    assert not HELPER.exists()
    manifest = payload()
    if (BACKUP / 'preflight.json').exists():
        saved = read('preflight.json')
        assert saved['sources'] == manifest
        print(json.dumps({'preflight_reused': True}))
        return
    assert not BACKUP.exists(), 'Unrecognized backup; preserve it'
    assert all(base.digest(ROOT / name) == manifest[name]['old'] for name in FILES)
    assert not any(p.is_symlink() for p in CFG.rglob('*'))
    state = base.containers()
    assert len(state) == 30 and all(v['running'] and v['health'] == 'healthy' for v in state.values())
    document = json.loads(DOC.read_text())
    assert document['STORAGE_PROVIDER'] == 'local'
    assert document['CLAMD_SIGNATURE_MAX_AGE_SECONDS'] == 172800
    assert document['CLAMD_VERSION_TIMEZONE'] == 'UTC'
    assert shutil.disk_usage(ROOT).free > 1_000_000_000
    before_override = json.loads(OVERRIDE.read_text())
    assert before_override['services']['clamav']['environment']['FRESHCLAM_CHECKS'] == '12'
    assert before_override['services']['clamav']['environment']['CLAMD_CONF_ConcurrentDatabaseReload'] == 'no'
    clamav_details = json.loads(base.capture(['docker', 'inspect', state['clamav']['id']]))[0]
    signature_mount = next(m for m in clamav_details['Mounts'] if m['Destination'] == '/var/lib/clamav')
    staging = BACKUP.with_name(BACKUP.name + '-staging')
    staging.mkdir(mode=0o700, exist_ok=True)
    for name in FILES:
        source = ROOT / name
        if source.exists():
            dest = staging / 'sources' / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            if dest.exists():
                assert base.digest(dest) == base.digest(source), 'Unrecognized backup file'
            shutil.copy2(source, dest)
    saved_override = staging / 'override-before.json'
    if saved_override.exists():
        assert base.digest(saved_override) == base.digest(OVERRIDE)
    shutil.copy2(OVERRIDE, saved_override)
    save('preflight.json', {'runtime': state, 'document_sha256': base.digest(DOC),
         'override_sha256': base.digest(OVERRIDE), 'sources': manifest,
         'signature_mount': signature_mount}, staging)
    os.replace(staging, BACKUP)
    print(json.dumps({'healthy': 30, 'payload_files': 3, 'storage_provider': 'local'}))


def prepare():
    base.target()
    before = read('preflight.json')
    assert base.containers() == before['runtime'] and base.digest(DOC) == before['document_sha256']
    assert base.digest(OVERRIDE) == before['override_sha256']
    assert all(base.digest(ROOT / n) == before['sources'][n]['old'] for n in FILES)
    final_candidate = BACKUP / 'candidate'
    candidate = final_candidate
    if not final_candidate.exists():
        candidate = Path(tempfile.mkdtemp(prefix='candidate-staging-', dir=BACKUP))
        (candidate / 'apps').mkdir(mode=0o700)
        shutil.copy2(OVERRIDE, candidate / 'gcs.compose.yaml')
        shutil.copy2(DOC, candidate / 'apps/documentos.json')
        spec = importlib.util.spec_from_file_location('candidate_scanner', INPUT / 'payload/deployment/gcp/configure_scanner.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.configure(candidate)
    assert json.loads((candidate / 'apps/documentos.json').read_text()) == json.loads(DOC.read_text())
    assert (candidate / 'clamav-readiness.sh').stat().st_mode & 0o777 == 0o444
    assert base.digest(candidate / 'clamav-readiness.sh') == before['sources'][FILES[1]]['new']
    old = json.loads((BACKUP / 'override-before.json').read_text())
    new = json.loads((candidate / 'gcs.compose.yaml').read_text())
    old_clam, new_clam = old['services'].pop('clamav'), new['services'].pop('clamav')
    assert old == new, 'Configuration outside ClamAV changed'
    expected = dict(old_clam)
    assert isinstance(old_clam.get('labels', {}), dict)
    expected['labels'] = dict(old_clam.get('labels', {}), **{'org.redhouse.clamav-readiness.sha256': before['sources'][FILES[1]]['new']})
    expected['environment'] = dict(old_clam['environment'], CLAMD_SIGNATURE_MAX_AGE_SECONDS='172800')
    expected['volumes'] = old_clam['volumes'] + [{'type': 'bind', 'source': '${REDHOUSE_COMPOSE_DIR:-./.local/compose}/clamav-readiness.sh', 'target': TARGET, 'read_only': True}]
    expected['healthcheck'] = {'test': ['CMD', '/bin/sh', TARGET], 'interval': '30s', 'timeout': '15s', 'start_period': '240s', 'retries': 3}
    assert new_clam == expected, 'Unexpected ClamAV change'
    before_effective = base.effective_config()
    command = base.compose()
    command[command.index(str(OVERRIDE))] = str(candidate / 'gcs.compose.yaml')
    after_effective = json.loads(base.capture(command + ['config', '--format', 'json']))
    before_clam = before_effective['services'].pop('clamav')
    after_clam = after_effective['services'].pop('clamav')
    assert before_clam['image'] == after_clam['image'] and before_clam.get('mem_limit') == after_clam.get('mem_limit')
    expected_labels = dict(before_clam.get('labels', {}), **{'org.redhouse.clamav-readiness.sha256': before['sources'][FILES[1]]['new']})
    assert after_clam.get('labels') == expected_labels
    bind = [v for v in after_clam['volumes'] if v['target'] == TARGET]
    assert len(bind) == 1 and bind[0]['type'] == 'bind' and bind[0]['read_only'] is True
    assert Path(bind[0]['source']).resolve() == HELPER.resolve()
    assert before_effective == after_effective, 'Effective configuration outside ClamAV changed'
    if candidate != final_candidate:
        os.replace(candidate, final_candidate)
        candidate = final_candidate
    save('prepared.json', {'candidate_sha256': base.digest(candidate / 'gcs.compose.yaml'),
         'helper_sha256': before['sources'][FILES[1]]['new']})
    print(json.dumps({'candidate_reviewed': True}))


def safe_source(name, before):
    current = base.digest(ROOT / name)
    assert current in (before['sources'][name]['old'], before['sources'][name]['new'])


def atomic_install(destination, content, mode):
    temporary = destination.with_name(destination.name + '.health-new')
    if temporary.exists():
        assert content.startswith(temporary.read_bytes()), 'Unknown temporary file'
    with temporary.open('wb') as out:
        out.write(content)
        out.flush()
        os.fsync(out.fileno())
    temporary.chmod(mode)
    os.replace(temporary, destination)


def write_preserve_inode(path, content, alternatives):
    existing = path.read_bytes()
    assert any(existing == value or value.startswith(existing) for value in alternatives), 'Unknown interrupted write'
    with path.open('wb') as out:
        out.write(content)
        out.truncate()
        out.flush()
        os.fsync(out.fileno())


def publish():
    base.target()
    safe_destinations()
    before, prepared = read('preflight.json'), read('prepared.json')
    assert payload() == before['sources'], 'Payload changed after preflight'
    assert base.digest(DOC) == before['document_sha256']
    candidate = BACKUP / 'candidate/gcs.compose.yaml'
    assert base.digest(candidate) == prepared['candidate_sha256']
    for name in FILES:
        safe_source(name, before)
    if HELPER.exists():
        assert base.digest(HELPER) == prepared['helper_sha256']
    if not (BACKUP / 'write-intent.json').exists():
        assert base.containers() == before['runtime'], 'Runtime changed since preflight'
    save('write-intent.json', {'scope': 'clamav-only'})
    try:
        for name in FILES:
            destination = ROOT / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            atomic_install(destination, (INPUT / 'payload' / name).read_bytes(), 0o644)
        if not HELPER.exists():
            atomic_install(HELPER, (INPUT / 'payload' / FILES[1]).read_bytes(), 0o444)
        old_bytes = (BACKUP / 'override-before.json').read_bytes()
        new_bytes = candidate.read_bytes()
        write_preserve_inode(OVERRIDE, new_bytes, (old_bytes, new_bytes))
        base.capture(base.compose() + ['config', '--quiet'])
        base.run(base.compose() + ['up', '-d', '--no-deps', '--no-build', '--wait', '--wait-timeout', '300', 'clamav'])
        runtime_other(before['runtime'], base.containers())
        save('published.json', {'candidate_sha256': prepared['candidate_sha256'], 'validation_pending': True})
        print(json.dumps({'published': True, 'validation_pending': True}))
    except Exception:
        rollback()
        raise


def rollback():
    base.target()
    safe_destinations()
    before, prepared = read('preflight.json'), read('prepared.json')
    assert base.digest(DOC) == before['document_sha256']
    assert base.digest(BACKUP / 'override-before.json') == before['override_sha256']
    for name in FILES:
        old = before['sources'][name]['old']
        if old is not None:
            assert base.digest(BACKUP / 'sources' / name) == old, 'Backup source mismatch'
    assert base.digest(BACKUP / 'candidate/gcs.compose.yaml') == prepared['candidate_sha256']
    old_bytes = (BACKUP / 'override-before.json').read_bytes()
    new_bytes = (BACKUP / 'candidate/gcs.compose.yaml').read_bytes()
    for name in FILES:
        safe_source(name, before)
    if HELPER.exists():
        assert base.digest(HELPER) == prepared['helper_sha256']
    write_preserve_inode(OVERRIDE, old_bytes, (old_bytes, new_bytes))
    for name in FILES:
        old = before['sources'][name]['old']
        if old is None:
            if (ROOT / name).exists():
                (ROOT / name).unlink()
        else:
            prior = BACKUP / 'sources' / name
            atomic_install(ROOT / name, prior.read_bytes(), prior.stat().st_mode & 0o777)
    base.capture(base.compose() + ['config', '--quiet'])
    base.run(base.compose() + ['up', '-d', '--no-deps', '--no-build', '--wait', '--wait-timeout', '300', 'clamav'])
    runtime_other(before['runtime'], base.containers())
    if HELPER.exists():
        assert base.digest(HELPER) == prepared['helper_sha256']
        HELPER.unlink()
    save('rollback.json', {'old_override_restored': True, 'signature_volume_untouched': True})
    print(json.dumps({'rollback': True}))


SCANNER = r'''
import json,sys
from pathlib import Path
sys.path.insert(0,'/app/apps/services')
from flask import Flask
from redhouse.malware import scan
config=json.loads(Path('/run/secrets/config').read_text())
app=Flask('scanner-health-check')
app.config.update({k:config[k] for k in ('CLAMD_HOST','CLAMD_PORT','CLAMD_VERSION_TIMEZONE','CLAMD_SIGNATURE_MAX_AGE_SECONDS')})
assert app.config['CLAMD_VERSION_TIMEZONE']=='UTC' and app.config['CLAMD_SIGNATURE_MAX_AGE_SECONDS']==172800
with app.app_context():
 clean=scan(b'Red House synthetic scanner health check\n')
 infected=scan(br'X5O!P%@AP[4\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*')
 assert clean=='CLEAN' and infected=='INFECTED' and clean.metadata==infected.metadata
 print(json.dumps({'clean':'CLEAN','eicar':'INFECTED','in_memory_only':True}))
'''


def validate():
    base.target()
    before, prepared = read('preflight.json'), read('prepared.json')
    assert read('published.json')['candidate_sha256'] == prepared['candidate_sha256']
    assert base.digest(DOC) == before['document_sha256']
    assert base.digest(OVERRIDE) == prepared['candidate_sha256']
    assert base.digest(HELPER) == prepared['helper_sha256']
    deadline = time.monotonic() + 110
    while True:
        current = base.containers()
        runtime_other(before['runtime'], current)
        details = json.loads(base.capture(['docker', 'inspect', current['clamav']['id']]))[0]
        health = details['State']['Health']
        successes = [entry for entry in health['Log'] if entry['ExitCode'] == 0 and entry['Output'].strip() == 'healthy: signatures current']
        if health['Status'] == 'healthy' and len({e['Start'] for e in successes}) >= 2:
            break
        assert time.monotonic() < deadline, 'Two readiness checks not observed'
        time.sleep(5)
    mounts = {m['Destination']: m for m in details['Mounts']}
    assert mounts['/var/lib/clamav'] == before['signature_mount']
    assert mounts[TARGET]['RW'] is False
    actual_hash = base.capture(['docker', 'exec', current['clamav']['id'], 'sha256sum', TARGET]).split()[0]
    assert actual_hash == prepared['helper_sha256']
    result = json.loads(base.capture(['docker', 'exec', '-i', current['documentos-a']['id'], 'python', '-c', SCANNER]))
    assert result == {'clean': 'CLEAN', 'eicar': 'INFECTED', 'in_memory_only': True}
    runtime_other(before['runtime'], base.containers())
    save('validation.json', {'two_periodic_healthchecks': True, 'helper_sha256': actual_hash,
         'mount_read_only': True, 'signature_volume_unchanged': True, 'other_containers_unchanged': 29,
         'scanner': result, 'storage_provider': 'local', 'database_modified': False})
    print(json.dumps({'validation': 'passed'}))


def release():
    publish()
    try:
        validate()
    except Exception:
        rollback()
        raise


if __name__ == '__main__':
    os.umask(0o077)
    assert os.geteuid() == 0
    {'preflight': preflight, 'prepare': prepare, 'publish': publish, 'rollback': rollback, 'validate': validate, 'release': release}[sys.argv[1]]()
