"""Publish reviewed donor and HLA changes to the existing Red House VM."""
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tarfile
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path('/opt/redhouse')
INPUT = Path('/tmp/redhouse-scanner20-20261113')
BACKUP = ROOT / '.local/deploy-scanner20-20261113'
CFG = ROOT / '.local/compose'
PROJECT = 'redhouse-parcial2'
TAG = 'scanner20-20261113'


def capture(args, data=None):
    result = subprocess.run(args, cwd=ROOT, input=data, text=True, capture_output=True, timeout=180)
    if result.returncode:
        raise RuntimeError(f'Command failed ({result.returncode}): {args[:3]}')
    return result.stdout.strip()


def run(args):
    subprocess.run(args, cwd=ROOT, check=True, timeout=900)


def save(name, value):
    (BACKUP / name).write_text(json.dumps(value, indent=2) + '\n')


def read(name):
    return json.loads((BACKUP / name).read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def config_hashes():
    assert not any(p.is_symlink() for p in CFG.rglob('*'))
    return {str(p.relative_to(CFG)): digest(p) for p in CFG.rglob('*') if p.is_file()}


def effective_config():
    return json.loads(capture(compose() + ['config', '--format', 'json']))


def validate_nginx(content):
    gateway = containers()['gateway']['id']
    capture(['docker', 'exec', '-i', gateway, 'sh', '-c',
             'set -eu\numask 077\ncat > /tmp/redhouse-clients-candidate.conf\nnginx -t -c /tmp/redhouse-clients-candidate.conf'], content)


def install_nginx(content):
    # The target is a bind-mounted file. Preserve its inode, validate before
    # writing, fsync, then reload. If interrupted, recover-nginx reapplies the
    # previously validated gated candidate before allowing writes again.
    validate_nginx(content)
    save('nginx-write-intent.json', {'sha256': hashlib.sha256(content.encode()).hexdigest()})
    with (CFG / 'public.nginx.conf').open('w') as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())
    gateway = containers()['gateway']['id']
    run(['docker', 'exec', gateway, 'nginx', '-t'])
    run(['docker', 'exec', gateway, 'nginx', '-s', 'reload'])
    if 'X-RedHouse-Maintenance' in content:
        save('gate-state.json', {'sha256': digest(CFG / 'public.nginx.conf'),
             'mtime_ns': (CFG / 'public.nginx.conf').stat().st_mtime_ns,
             'gateway': containers()['gateway']})


def gated(content):
    anchor = '    listen 8443 ssl;'
    assert content.count(anchor) == 1
    return content.replace(anchor, anchor + '\n    add_header X-RedHouse-Maintenance "scanner20-20261113" always;\n    if ($request_method !~ ^(GET|HEAD|OPTIONS)$) { return 503; }', 1)


def check_gate():
    state = read('gate-state.json')
    assert digest(CFG / 'public.nginx.conf') == state['sha256']
    assert (CFG / 'public.nginx.conf').stat().st_mtime_ns == state['mtime_ns']
    assert containers()['gateway'] == state['gateway'], 'Gateway changed; repeat closure and expiry wait'
    request = Request('https://34.18.186.116/services/identidad-acceso/api/v1/auth/reauthenticate',
                      data=b'{}', headers={'Content-Type': 'application/json'}, method='POST')
    try:
        urlopen(request, timeout=10)
        raise AssertionError('Public HTTP write gate is not active')
    except HTTPError as response:
        assert response.code == 503 and response.headers.get('X-RedHouse-Maintenance') == 'scanner20-20261113'


def target():
    expected = {'instance/id': '2861822465669755197', 'instance/name': 'red-house',
                'project/project-id': 'sistemas-integracion-01'}
    for name, value in expected.items():
        request = Request('http://metadata.google.internal/computeMetadata/v1/' + name,
                          headers={'Metadata-Flavor': 'Google'})
        with urlopen(request, timeout=3) as response:
            assert response.read().decode() == value, 'Wrong deployment target'


def compose():
    return ['docker', 'compose', '-f', str(ROOT / 'compose.yaml'),
            '-f', str(CFG / 'gcs.compose.yaml'), '-f', str(CFG / 'public.compose.yaml')]


def containers():
    ids = capture(['docker', 'ps', '-q', '--filter', f'label=com.docker.compose.project={PROJECT}']).split()
    state = json.loads(capture(['docker', 'inspect', *ids]))
    expected = set(effective_config()['services']) - {'bootstrap', 'storage-init'}
    selected = [v for v in state
                if v['Config']['Labels'].get('com.docker.compose.oneoff', '').lower() != 'true'
                and v['Config']['Labels'].get('com.docker.compose.service') in expected]
    # Historical restore containers remain stopped and preserved. Exact set
    # equality below still rejects a missing/stopped current runtime service.
    names = [v['Config']['Labels']['com.docker.compose.service'] for v in selected]
    assert len(names) == len(set(names)), 'Ambiguous runtime service containers'
    assert set(names) == expected, 'Missing runtime service container'
    return {v['Config']['Labels']['com.docker.compose.service']:
            {'id': v['Id'], 'image': v['Image'], 'tag': v['Config']['Image'],
             'running': v['State']['Running'], 'started_at': v['State']['StartedAt'],
             'health': v['State'].get('Health', {}).get('Status')}
            for v in selected}


def sql(statement):
    pg = containers()['postgres']['id']
    command = 'export PGPASSWORD="$(cat /run/secrets/postgres_password)"; exec psql -X -v ON_ERROR_STOP=1 -U rh_bootstrap -d red_house -At'
    return capture(['docker', 'exec', '-i', pg, 'sh', '-c', command], statement)


def storage():
    return json.loads(sql("SELECT json_build_object('schema',(SELECT max(version) FROM red_house.schema_migration),'files',count(*),'digest',md5(coalesce(string_agg(to_jsonb(t)::text,'' ORDER BY id),''))) FROM (SELECT file_id AS id,object_path,sha256,generation,storage_provider FROM red_house.stored_file) t;"))


def targets(state):
    names = ['auditoria-a', 'auditoria-b', 'compatibilidad-a', 'compatibilidad-b', 'donantes-a', 'donantes-b', 'web']
    assert set(names) <= set(state)
    return names


def owner(name):
    return name if name == 'web' else name[:-2]


def preflight():
    target()
    expected = json.loads((INPUT / 'expected-before.json').read_text())
    actual = {name: digest(ROOT / name) for name in expected}
    assert actual == expected, 'Host source differs from reviewed baseline'
    state = containers()
    assert len(state) == 30 and all(v['running'] and v['health'] == 'healthy' for v in state.values())
    assert storage()['schema'] == 19
    assert capture(['systemctl', 'is-active', 'redhouse']) == 'active'
    assert shutil.disk_usage(ROOT).free > 1_500_000_000
    for relative in ('apps/documentos.json', 'web.json'):
        config = json.loads((CFG / relative).read_text())
        assert config['STORAGE_PROVIDER'] == 'local'
    report = {'runtime': state, 'source_hashes': actual, 'storage': storage(),
              'disk_free_bytes': shutil.disk_usage(ROOT).free, 'configuration': config_hashes()}
    (INPUT / 'preflight.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'healthy': len(state), 'source_matches': len(actual), 'schema': 19}))


def prepare():
    target()
    previous = json.loads((INPUT / 'preflight.json').read_text())
    assert containers() == previous['runtime'], 'Runtime changed after preflight'
    assert config_hashes() == previous['configuration'], 'Configuration changed after preflight'
    assert all(digest(ROOT / n) == value for n, value in previous['source_hashes'].items())
    files = json.loads((INPUT / 'manifest.json').read_text())
    assert files and all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in files)
    if not BACKUP.exists():
        staging = Path(str(BACKUP) + '-preparation')
        staging.mkdir(mode=0o700, exist_ok=True)
        (staging / 'preflight.json').write_text(json.dumps(previous, indent=2) + '\n')
        (staging / 'manifest.json').write_text(json.dumps(files, indent=2) + '\n')
        shutil.copy2(INPUT / 'source.json', staging / 'source.json')
        shutil.copytree(CFG, staging / 'configuration', dirs_exist_ok=True)
        for name in files:
            if (ROOT / name).exists():
                destination = staging / 'sources' / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / name, destination)
        assert all(digest(staging / 'configuration' / name) == value for name, value in previous['configuration'].items())
        assert all(digest(staging / 'sources' / name) == value for name, value in previous['source_hashes'].items())
        assert config_hashes() == previous['configuration']
        (staging / 'backup-complete.json').write_text(json.dumps({'configuration_and_source_hashes_verified': True}) + '\n')
        (staging / 'compose-before.private.json').write_text(json.dumps(effective_config(), indent=2) + '\n')
        staging.rename(BACKUP)
    else:
        assert read('manifest.json') == files and read('preflight.json') == previous
        assert read('backup-complete.json')['configuration_and_source_hashes_verified']
    shutil.copy2(INPUT / 'deploy.py', BACKUP / 'deploy.py')
    with tarfile.open(INPUT / 'payload.tar.gz') as archive:
        members = archive.getmembers()
        assert {m.name for m in members} == set(files) and len(members) == len(files)
        for member in members:
            assert member.isfile()
            content = archive.extractfile(member).read()
            assert hashlib.sha256(content).hexdigest() == files[member.name]
            destination = BACKUP / 'payload' / member.name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(content)
    builds = read('builds.json') if (BACKUP / 'builds.json').exists() else {}
    for service in sorted({owner(n) for n in targets(previous['runtime'])}):
        sample = service if service == 'web' else service + '-a'
        base = previous['runtime'][sample]
        if service != 'web':
            assert base['image'] == previous['runtime'][service + '-b']['image']
        repository = base['tag'].split(':')[0]
        old_tag, new_tag = repository + ':before-' + TAG, repository + ':' + TAG
        module = 'servicio_monitoreo' if service == 'monitoreo' else 'ms_' + service.replace('-', '_')
        names = [n for n in files if n.startswith('apps/') and (
            service == 'web' or n.startswith('apps/services/redhouse/') or n.startswith('apps/services/' + module + '/'))]
        if service not in builds:
            run(['docker', 'tag', base['image'], old_tag])
            directory = BACKUP / 'build' / service
            for name in names:
                destination = directory / 'payload' / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(BACKUP / 'payload' / name, destination)
            (directory / 'Dockerfile').write_text(f'FROM {old_tag}\nCOPY --chmod=755 payload/ /app/\n')
            run(['docker', 'build', '--network=none', '--pull=false', '-t', new_tag, str(directory)])
            image = json.loads(capture(['docker', 'image', 'inspect', new_tag]))[0]
            old = json.loads(capture(['docker', 'image', 'inspect', old_tag]))[0]
            assert all(image['Config'].get(k) == old['Config'].get(k) for k in ('Env', 'Entrypoint', 'Cmd', 'User', 'WorkingDir'))
            builds[service] = {'tag': new_tag, 'id': image['Id'], 'base': base['image'], 'files': {n: files[n] for n in names}}
            save('builds.json', builds)
        checks = builds[service]['files']
        program = ('import hashlib;from pathlib import Path;expected=' + repr(checks) +
                   ';assert all(hashlib.sha256((Path("/app")/n).read_bytes()).hexdigest()==h for n,h in expected.items());'
                   '[compile((Path("/app")/n).read_text(),n,"exec") for n in expected if n.endswith(".py")];print("Payload verified")')
        run(['docker', 'run', '--rm', '--network=none', '--entrypoint', 'python', builds[service]['id'], '-c', program])
    save('prepared.json', {'images': len(builds), 'files': len(files)})
    print(json.dumps(read('prepared.json')))


def backup_database():
    target()
    assert (BACKUP / 'prepared.json').exists()
    assert not (BACKUP / 'database.dump').exists(), 'Preserve existing backup'
    pg = containers()['postgres']['id']
    temporary = BACKUP / 'database.partial'
    command = 'export PGPASSWORD="$(cat /run/secrets/postgres_password)"; exec pg_dump -U rh_bootstrap -d red_house -Fc'
    with temporary.open('wb') as stream:
        subprocess.run(['docker', 'exec', pg, 'sh', '-c', command], stdout=stream, check=True, timeout=600)
    with temporary.open('rb') as stream:
        subprocess.run(['docker', 'exec', '-i', pg, 'pg_restore', '--list'], stdin=stream, stdout=subprocess.DEVNULL, check=True, timeout=120)
    temporary.rename(BACKUP / 'database.dump')
    save('database-backup.json', {'bytes': (BACKUP / 'database.dump').stat().st_size,
         'sha256': digest(BACKUP / 'database.dump'), 'catalogue_valid': True, 'restore_tested': False})
    print(json.dumps(read('database-backup.json')))


def close_writes():
    target()
    assert (BACKUP / 'database-backup.json').exists()
    assert digest(BACKUP / 'database.dump') == read('database-backup.json')['sha256']
    old = (BACKUP / 'configuration/public.nginx.conf').read_text()
    candidate = gated(old)
    (BACKUP / 'maintenance.nginx.conf').write_text(candidate)
    install_nginx(candidate)
    check_gate()
    # Return immediately; the operator can verify public 503 and communicate
    # while the 125-second HTTP grace interval elapses (workers/WSS are not stopped).
    save('writes-closed.json', {'at': time.time(), 'minimum_wait_seconds': 125})
    print(json.dumps({'writes_closed': True, 'wait_before_publish_seconds': 125}))


def recover_nginx():
    target()
    candidate = BACKUP / 'desired-gated.nginx.conf'
    if not candidate.exists():
        candidate = BACKUP / 'maintenance.nginx.conf'
    install_nginx(candidate.read_text())
    check_gate()
    save('writes-closed.json', {'at': time.time(), 'minimum_wait_seconds': 125})
    print(json.dumps({'gated_configuration_restored': True}))


def publish():
    target()
    assert (BACKUP / 'database-backup.json').exists()
    assert digest(BACKUP / 'database.dump') == read('database-backup.json')['sha256']
    assert time.time() - read('writes-closed.json')['at'] >= 125, 'HTTP grace interval has not elapsed'
    check_gate()
    previous = read('preflight.json')
    files = read('manifest.json')
    assert all(digest(ROOT / n) in (previous['source_hashes'][n], value) for n, value in files.items())
    assert storage()['schema'] == 19
    save('publication-started.json', {'forward_recovery': True, 'keeps_schema_and_provider': True})
    for name in files:
        destination = ROOT / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(BACKUP / 'payload' / name, destination)
        destination.chmod(0o644)
    # No migration or business-state write. Retain the deployed security grant.
    assert sql("SELECT has_table_privilege('rh_inventario','access_inventario.operations','DELETE');") == 'f'
    desired_nginx = (BACKUP / 'configuration/public.nginx.conf').read_text()
    validate_nginx(desired_nginx)
    (BACKUP / 'desired.nginx.conf').write_text(desired_nginx)
    (BACKUP / 'desired-gated.nginx.conf').write_text(gated(desired_nginx))
    install_nginx(gated(desired_nginx))
    builds = read('builds.json')
    override = json.loads((CFG / 'gcs.compose.yaml').read_text())
    for name in targets(previous['runtime']):
        override.setdefault('services', {}).setdefault(name, {})['image'] = builds[owner(name)]['tag']
    (CFG / 'gcs.compose.yaml').write_text(json.dumps(override, indent=2) + '\n')
    run(compose() + ['config', '--quiet'])
    effective = effective_config()
    expected = read('compose-before.private.json')
    for name in targets(previous['runtime']):
        expected['services'][name]['image'] = builds[owner(name)]['tag']
    assert effective == expected, 'Effective configuration differs beyond reviewed images'
    names = targets(previous['runtime'])
    ordered = [n for n in names if n != 'web'] + ['web']
    for name in ordered:
        check_gate()
        print('ROLLOUT ' + name, flush=True)
        run(compose() + ['up', '-d', '--no-deps', '--no-build', '--wait', '--wait-timeout', '240', name])
    state = containers()
    assert len(state) == 30 and all(v['running'] and v['health'] == 'healthy' for v in state.values())
    assert all(state[n]['image'] == builds[owner(n)]['id'] for n in names)
    assert all(state[n] == previous['runtime'][n] for n in previous['runtime'] if n not in names)
    assert all(digest(ROOT / name) == value for name, value in files.items())
    current_config = config_hashes()
    assert all(current_config[n] == value for n, value in previous['configuration'].items()
               if n not in ('public.nginx.conf', 'gcs.compose.yaml'))
    assert storage()['schema'] == 19
    check_gate()
    save('runtime-final.json', state)
    save('publication.json', {'healthy': 30, 'schema': 19, 'files': len(files), 'storage_before': previous['storage'],
                            'storage_after': storage(), 'public_validation_pending': True, 'writes_closed': True})
    print(json.dumps(read('publication.json')))


def open_writes():
    target()
    assert read('validation-approved.json')['approved'] is True
    check_gate()
    state = containers()
    assert state == read('runtime-final.json')
    assert all(v['health'] == 'healthy' for v in state.values())
    install_nginx((BACKUP / 'desired.nginx.conf').read_text())
    save('writes-opened.json', {'at': time.time(), 'validation_checked': True})
    (BACKUP / 'writes-closed.json').unlink()
    (BACKUP / 'gate-state.json').unlink()
    print(json.dumps({'writes_open': True, 'public_smoke_required': True}))


if __name__ == '__main__':
    os.umask(0o077)
    assert os.geteuid() == 0 and ROOT.exists()
    {'preflight': preflight, 'prepare': prepare, 'backup': backup_database,
     'close-writes': close_writes, 'recover-nginx': recover_nginx,
     'publish': publish, 'open-writes': open_writes}[sys.argv[1]]()
