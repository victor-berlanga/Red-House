"""Bounded update of the existing Red House VM; staged local-storage activation."""

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
from urllib.request import Request, urlopen

ROOT = Path('/opt/redhouse')
INPUT = Path('/tmp/redhouse-continuidad-20261113')
BACKUP = ROOT / '.local/deploy-continuidad-20261113'
CFG = ROOT / '.local/compose'
TAG = 'continuidad-20261113'
PROJECT = 'redhouse-parcial2'
REHEARSAL = 'redhouse_rehearsal_20261113'
COMPATIBILITY_ANCHOR = {
    'files.py': {'base_sha256': 'a344518fcd63fee9b6c7bf115be5fbfbb3227ba7455d33c4af7a768b1ca00837',
                 'compat_sha256': '6ece3290b69b53fd5aeb83be7f3b17484b05599739c5fcd81d5f22055c2577fa'},
    'reports.py': {'base_sha256': '15a80f245f1afbfc0c5c492b3ab4d46462034cf700d57e73ee70b5960a737403',
                   'compat_sha256': '6b44c6c15af1521babaf908956bf61ae48071284a0618b7d8df14947eb3efcc9'},
}


def capture(args, data=None):
    result = subprocess.run(args, cwd=ROOT, input=data, text=True, capture_output=True, timeout=180)
    if result.returncode:
        # Commands never contain credentials. Do not print stderr from applications.
        raise RuntimeError(f'Command failed ({result.returncode}): {args[:4]}')
    return result.stdout.strip()


def run(args):
    subprocess.run(args, cwd=ROOT, check=True, timeout=900)


def save(name, value):
    (BACKUP / name).write_text(json.dumps(value, indent=2) + '\n')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compose():
    return ['docker', 'compose', '-f', str(ROOT / 'compose.yaml'),
            '-f', str(CFG / 'gcs.compose.yaml'), '-f', str(CFG / 'public.compose.yaml')]


def containers():
    ids = capture(['docker', 'ps', '-q', '--filter', f'label=com.docker.compose.project={PROJECT}']).split()
    assert ids, 'No running project containers'
    return {v['Config']['Labels']['com.docker.compose.service']:
            {'id': v['Id'], 'image': v['Image'], 'tag': v['Config']['Image'],
             'health': v['State'].get('Health', {}).get('Status'),
             'networks': {k: {'ip': n['IPAddress'], 'aliases': n.get('Aliases')}
                          for k, n in v['NetworkSettings']['Networks'].items()}}
            for v in json.loads(capture(['docker', 'inspect', *ids]))}


def manifest():
    return json.loads((BACKUP / 'manifest.json').read_text())


def targets(before):
    return [n for n in before if n.endswith(('-a', '-b'))] + ['web']


def owner(name):
    return name if name == 'web' else name[:-2]


def sql(statement, database='red_house'):
    assert database in ('red_house', REHEARSAL)
    pg = containers()['postgres']['id']
    command = 'export PGPASSWORD="$(cat /run/secrets/postgres_password)"; exec psql -X -v ON_ERROR_STOP=1 -U rh_bootstrap -d ' + database + ' -At'
    return capture(['docker', 'exec', '-i', pg, 'sh', '-c', command], statement)


def storage_fingerprint():
    # Includes object references, generations and hashes; only the aggregate escapes.
    return sql("SELECT json_build_object('version',(SELECT max(version) FROM red_house.schema_migration),"
               "'files',(SELECT count(*) FROM red_house.stored_file),"
               "'digest',(SELECT md5(coalesce(string_agg(to_jsonb(t)::text, '' ORDER BY id),'')) "
               "FROM (SELECT file_id AS id,object_path,sha256,generation FROM red_house.stored_file) t));")


def capacity():
    size = int(sql("SELECT pg_database_size('red_house');"))
    free = shutil.disk_usage(ROOT).free
    print(json.dumps({'postgres_bytes': size, 'disk_free_bytes': free,
                      'docker_space': capture(['docker', 'system', 'df', '--format', 'json'])}), flush=True)


def preflight():
    expected_metadata = {'instance/id': '2861822465669755197', 'instance/name': 'red-house',
                         'project/project-id': 'sistemas-integracion-01'}
    for name, expected_value in expected_metadata.items():
        request = Request('http://metadata.google.internal/computeMetadata/v1/' + name,
                          headers={'Metadata-Flavor': 'Google'})
        with urlopen(request, timeout=3) as response:
            assert response.read().decode() == expected_value, 'Wrong deployment target'
    expected = json.loads((INPUT / 'expected-before.json').read_text())
    actual = {n: digest(ROOT / n) if (ROOT / n).exists() else None for n in expected}
    state = containers()
    assert len(state) == 30 and all(v['health'] == 'healthy' for v in state.values())
    differences = {n: {'actual': actual[n], 'expected': value}
                   for n, value in expected.items() if actual[n] != value}
    (INPUT / 'source-differences.json').write_text(json.dumps(differences, indent=2) + '\n')
    assert not differences, 'Source differs from reviewed baseline; inspect source-differences.json'
    assert shutil.disk_usage(ROOT).free > 3_000_000_000
    assert capture(['systemctl', 'is-active', 'redhouse']) == 'active'
    assert sql('SELECT max(version) FROM red_house.schema_migration;') == '18'
    result = {'runtime': state, 'source_hashes': actual,
              'disk_free_bytes': shutil.disk_usage(ROOT).free,
              'storage': json.loads(storage_fingerprint())}
    (INPUT / 'preflight.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'healthy': len(state), 'source_matches': True, 'schema': 18,
                      'disk_free_bytes': result['disk_free_bytes']}), flush=True)


def prepare():
    previous = json.loads((INPUT / 'preflight.json').read_text())
    assert containers() == previous['runtime'], 'Runtime changed after preflight'
    files = json.loads((INPUT / 'manifest.json').read_text())
    assert files and all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in files)
    BACKUP.mkdir(mode=0o700, exist_ok=False)
    save('runtime-before.json', previous['runtime'])
    save('manifest.json', files)
    save('preflight.json', previous)
    shutil.copy2(INPUT / 'deploy.py', BACKUP / 'deploy.py')
    assert not any(p.is_symlink() for p in CFG.rglob('*')), 'Review configuration symlinks before backing up'
    shutil.copytree(CFG, BACKUP / 'configuration')
    for name in files:
        source = ROOT / name
        if source.exists():
            target = BACKUP / 'sources' / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    with tarfile.open(INPUT / 'payload.tar.gz') as archive:
        members = archive.getmembers()
        assert {m.name for m in members} == set(files) and len(members) == len(files)
        for member in members:
            assert member.isfile()
            content = archive.extractfile(member).read()
            assert hashlib.sha256(content).hexdigest() == files[member.name]
            path = BACKUP / 'payload' / member.name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
            path.chmod(0o644)
    builds = {}
    before = previous['runtime']
    for service in sorted({owner(n) for n in targets(before)}):
        sample = service if service == 'web' else service + '-a'
        base = before[sample]
        if service != 'web':
            assert base['image'] == before[service + '-b']['image']
        repository = base['tag'].split(':')[0]
        old_tag = repository + ':before-' + TAG
        new_tag = repository + ':' + TAG
        run(['docker', 'tag', base['image'], old_tag])
        module = 'servicio_monitoreo' if service == 'monitoreo' else 'ms_' + service.replace('-', '_')
        selected = [n for n in files if n.startswith('apps/') and (
            service == 'web' or n.startswith('apps/services/redhouse/')
            or n == 'apps/services/run.py' or n.startswith('apps/services/' + module + '/'))]
        build = BACKUP / 'build' / service
        for name in selected:
            destination = build / 'payload' / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(BACKUP / 'payload' / name, destination)
            for parent in destination.parents:
                if parent == build:
                    break
                parent.chmod(0o755)
        (build / 'Dockerfile').write_text(f'FROM {old_tag}\nCOPY payload/ /app/\n')
        print('BUILD ' + service, flush=True)
        run(['docker', 'build', '--network=none', '--pull=false', '-t', new_tag, str(build)])
        hashes = {n: files[n] for n in selected}
        check = ('import hashlib;from pathlib import Path;expected=' + repr(hashes) +
                 ';assert all(hashlib.sha256((Path("/app")/n).read_bytes()).hexdigest()==h for n,h in expected.items());'
                 '[compile((Path("/app")/n).read_text(),n,"exec") for n in expected if n.endswith(".py")];print("Payload verified")')
        run(['docker', 'run', '--rm', '--network=none', '--entrypoint', 'python', new_tag, '-c', check])
        image = json.loads(capture(['docker', 'image', 'inspect', new_tag]))[0]
        old = json.loads(capture(['docker', 'image', 'inspect', old_tag]))[0]
        assert all(image['Config'].get(k) == old['Config'].get(k)
                   for k in ('Env', 'Entrypoint', 'Cmd', 'User', 'WorkingDir'))
        builds[service] = {'tag': new_tag, 'id': image['Id'], 'base': base['image'], 'files': hashes}
    save('builds.json', builds)
    prepare_compatibility(before)
    print(json.dumps({'phase': 'prepared', 'images': len(builds), 'files': len(files)}), flush=True)


def prepare_compatibility(before):
    sources = INPUT / 'compatibility-sources'
    details = json.loads((sources / 'manifest.json').read_text())
    assert details['revision'] == '6d8b88d0c8e5de6e1c9267c68fac2a6a8a4cd837'
    assert details['files'] == COMPATIBILITY_ANCHOR and details['provider'] == 'gcs-only'
    preserved = BACKUP / 'compatibility-sources'
    if preserved.exists():
        assert all(digest(preserved / n) == value['compat_sha256'] for n, value in details['files'].items())
    else:
        shutil.copytree(sources, preserved)
    builds = {}
    for service in ('documentos', 'web'):
        original = before['web' if service == 'web' else 'documentos-a']
        base_hashes = {'apps/services/ms_documentos/' + n: v['base_sha256']
                       for n, v in details['files'].items()}
        verify = ('import hashlib;from pathlib import Path;expected=' + repr(base_hashes) +
                  ';assert all(hashlib.sha256((Path("/app")/n).read_bytes()).hexdigest()==h for n,h in expected.items())')
        run(['docker', 'run', '--rm', '--network=none', '--entrypoint', 'python', original['image'], '-c', verify])
        build = BACKUP / 'build' / (service + '-compatibility')
        payload = build / 'payload/apps/services/ms_documentos'
        payload.mkdir(parents=True, exist_ok=True)
        payload.chmod(0o755)
        for name, hashes in details['files'].items():
            assert digest(sources / name) == hashes['compat_sha256']
            shutil.copy2(sources / name, payload / name)
            (payload / name).chmod(0o644)
        for parent in payload.parents:
            if parent == build:
                break
            parent.chmod(0o755)
        tag = original['tag'].split(':')[0] + ':compatibility-' + TAG
        base_tag = original['tag'].split(':')[0] + ':before-' + TAG
        assert json.loads(capture(['docker', 'image', 'inspect', base_tag]))[0]['Id'] == original['image']
        (build / 'Dockerfile').write_text(f"FROM {base_tag}\nCOPY --chmod=755 payload/ /app/\n")
        run(['docker', 'build', '--network=none', '--pull=false', '-t', tag, str(build)])
        hashes = {'apps/services/ms_documentos/' + n: v['compat_sha256']
                  for n, v in details['files'].items()}
        verify = ('import hashlib;from pathlib import Path;expected=' + repr(hashes) +
                  ';assert all(hashlib.sha256((Path("/app")/n).read_bytes()).hexdigest()==h for n,h in expected.items())')
        run(['docker', 'run', '--rm', '--network=none', '--entrypoint', 'python', tag, '-c', verify])
        image = json.loads(capture(['docker', 'image', 'inspect', tag]))[0]
        base = json.loads(capture(['docker', 'image', 'inspect', original['image']]))[0]
        assert all(image['Config'].get(k) == base['Config'].get(k)
                   for k in ('Env', 'Entrypoint', 'Cmd', 'User', 'WorkingDir'))
        builds[service] = {'tag': tag, 'id': image['Id'], 'base': original['image'], 'files': hashes}
    save('compatibility-builds.json', builds)


def resume_compatibility_build():
    before = json.loads((BACKUP / 'runtime-before.json').read_text())
    assert containers() == before, 'Runtime changed during preparation'
    assert (BACKUP / 'builds.json').exists()
    prepare_compatibility(before)
    original = BACKUP / 'deploy-prepare-attempt1.py'
    if not original.exists():
        shutil.copy2(BACKUP / 'deploy.py', original)
    shutil.copy2(INPUT / 'deploy.py', BACKUP / 'deploy.py')
    print('Compatibility image preparation completed; running applications unchanged', flush=True)


def compatibility():
    assert (INPUT / 'compatibility-test-approved.json').exists(), 'Compatibility laboratory must pass first'
    assert (BACKUP / 'database-backup.json').exists()
    assert sql('SELECT max(version) FROM red_house.schema_migration;') == '18'
    before = json.loads((BACKUP / 'runtime-before.json').read_text())
    assert containers() == before
    builds = json.loads((BACKUP / 'compatibility-builds.json').read_text())
    override = json.loads((CFG / 'gcs.compose.yaml').read_text())
    for name in ('documentos-a', 'documentos-b', 'web'):
        override.setdefault('services', {}).setdefault(name, {})['image'] = builds[owner(name)]['tag']
    write_configuration(CFG / 'gcs.compose.yaml', override)
    run(compose() + ['config', '--quiet'])
    for name in ('documentos-a', 'documentos-b', 'web'):
        update_service(name)
    state = containers()
    assert all(state[n] == v for n, v in before.items() if n not in ('documentos-a', 'documentos-b', 'web'))
    assert all(v['health'] == 'healthy' for v in state.values())
    save('runtime-compatible.json', state)
    print('GCS-only compatibility images active; schema remains 18', flush=True)


def backup_database():
    pg = containers()['postgres']['id']
    path = BACKUP / 'postgres-before.dump'
    assert not path.exists()
    database_bytes = int(sql("SELECT pg_database_size('red_house');"))
    assert shutil.disk_usage(ROOT).free > database_bytes + 1_000_000_000, 'Insufficient backup and recovery headroom'
    command = 'export PGPASSWORD="$(cat /run/secrets/postgres_password)"; exec pg_dump -U rh_bootstrap -d red_house -Fc'
    with path.open('xb') as stream:
        result = subprocess.run(['docker', 'exec', pg, 'sh', '-c', command],
                                stdout=stream, stderr=subprocess.PIPE, timeout=900)
    assert result.returncode == 0, 'PostgreSQL backup failed; application untouched'
    with path.open('rb') as stream:
        result = subprocess.run(['docker', 'exec', '-i', pg, 'pg_restore', '--list'],
                                stdin=stream, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
    assert result.returncode == 0 and b'TABLE DATA' in result.stdout
    save('database-backup.json', {'bytes': path.stat().st_size, 'sha256': digest(path),
         'catalogue_verified': True, 'restore_tested': False,
         'scope': 'PostgreSQL red_house live logical snapshot; not coordinated multi-store backup'})


MIGRATE = '''import json,sys
from pathlib import Path
sys.path.insert(0,'/app/apps/services')
import psycopg
from redhouse.shared_migrations import upgrade
database='red_house'
dsn=psycopg.conninfo.make_conninfo(host='postgres',port=5432,dbname=database,
 user='rh_bootstrap',password=Path('/run/install/postgres-password').read_text().strip(),connect_timeout=5)
def fingerprint(conn,table):
 return conn.execute("SELECT count(*),md5(coalesce(string_agg((to_jsonb(t)-'storage_provider')::text,'' ORDER BY (to_jsonb(t)->>'file_id'),(to_jsonb(t)->>'id')),'')) FROM red_house."+table+" t").fetchone()
with psycopg.connect(dsn) as conn:
 conn.execute("SET LOCAL lock_timeout='10s'")
 conn.execute("SET LOCAL statement_timeout='120s'")
 conn.execute('SET LOCAL ROLE rh_shared_owner')
 assert conn.execute('SELECT max(version) FROM red_house.schema_migration').fetchone()[0]==18
 conn.execute('LOCK TABLE red_house.stored_file,red_house.export_jobs IN SHARE ROW EXCLUSIVE MODE')
 before={t:fingerprint(conn,t) for t in ('stored_file','export_jobs')}
 assert upgrade(conn)==19
 assert all(fingerprint(conn,t)==v for t,v in before.items())
 assert all(conn.execute('SELECT count(*) FROM red_house.'+t+" WHERE storage_provider<>'gcs'").fetchone()[0]==0 for t in before)
 assert conn.execute("SELECT bool_and(pg_get_userbyid(proowner)='rh_shared_owner') FROM pg_proc WHERE pronamespace='red_house'::regnamespace AND proname IN ('file_storage_immutable','export_storage_immutable')").fetchone()[0] is True
 print(json.dumps({'version':19,'historical_rows_preserved':True,'historical_provider':'gcs','counts':{t:v[0] for t,v in before.items()}}))
'''


def migrate():
    assert (BACKUP / 'database-backup.json').exists()
    assert (BACKUP / 'rehearsal.json').exists(), 'Restored-copy migration must pass first'
    assert (BACKUP / 'rehearsal-cleanup.json').exists(), 'Private rehearsal database must be cleaned up first'
    assert containers() == json.loads((BACKUP / 'runtime-compatible.json').read_text())
    builds = json.loads((BACKUP / 'builds.json').read_text())
    result = capture(['docker', 'run', '--rm', '--user', '0:0', '--read-only',
                      '--network', PROJECT + '_data', '--mount',
                      f'type=bind,src={CFG},dst=/run/install,readonly',
                      '--entrypoint', 'python', builds['web']['tag'], '-c', MIGRATE])
    save('migration.json', json.loads(result))
    print(result, flush=True)


def rehearse():
    """Restore into a separate private database; never overwrite red_house."""
    assert (BACKUP / 'database-backup.json').exists()
    metadata = json.loads((BACKUP / 'database-backup.json').read_text())
    assert digest(BACKUP / 'postgres-before.dump') == metadata['sha256']
    assert sql("SELECT count(*) FROM pg_database WHERE datname='" + REHEARSAL + "';") == '0'
    assert sql('SELECT max(version) FROM red_house.schema_migration;') == '18'
    size = int(sql("SELECT pg_database_size('red_house');"))
    assert shutil.disk_usage(ROOT).free > size * 2 + 1_000_000_000
    before = containers()
    started = time.monotonic()
    sql('CREATE DATABASE ' + REHEARSAL + ' OWNER rh_shared_owner TEMPLATE template0;')
    sql('REVOKE CONNECT ON DATABASE ' + REHEARSAL + ' FROM PUBLIC;')
    restored = False
    try:
        command = 'export PGPASSWORD="$(cat /run/secrets/postgres_password)"; exec pg_restore --exit-on-error -U rh_bootstrap -d ' + REHEARSAL
        with (BACKUP / 'postgres-before.dump').open('rb') as stream:
            result = subprocess.run(['docker', 'exec', '-i', before['postgres']['id'], 'sh', '-c', command],
                                    stdin=stream, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=900)
        assert result.returncode == 0, 'Private restoration failed; preserve database for inspection'
        # Database ACLs are not restored without --create. Verify this boundary
        # explicitly before opening the copy through the migration connection.
        assert sql("SELECT count(*) FROM pg_roles WHERE rolcanlogin AND NOT rolsuper "
                   "AND has_database_privilege(rolname,'" + REHEARSAL + "','CONNECT');") == '0'
        assert sql('SELECT max(version) FROM red_house.schema_migration;', REHEARSAL) == '18'
        builds = json.loads((BACKUP / 'builds.json').read_text())
        assert MIGRATE.count("database='red_house'") == 1
        program = MIGRATE.replace("database='red_house'", f"database='{REHEARSAL}'")
        assert program != MIGRATE
        migrated = capture(['docker', 'run', '--rm', '--user', '0:0', '--read-only',
                            '--network', PROJECT + '_data', '--mount',
                            f'type=bind,src={CFG},dst=/run/install,readonly',
                            '--entrypoint', 'python', builds['web']['tag'], '-c', program])
        assert sql('SELECT max(version) FROM red_house.schema_migration;', REHEARSAL) == '19'
        assert sql('SELECT max(version) FROM red_house.schema_migration;') == '18'
        assert containers() == before, 'Runtime changed during private rehearsal'
        save('rehearsal.json', {'database': REHEARSAL, 'restored_from_schema': 18,
             'migration': json.loads(migrated), 'elapsed_seconds': time.monotonic() - started,
             'production_schema': 18, 'runtime_unchanged': True,
             'scope': 'Private database restore and schema migration, not application RTO or platform failover'})
        restored = True
    finally:
        if restored:
            sql('DROP DATABASE ' + REHEARSAL + ';')
            save('rehearsal-cleanup.json', {'dropped_only_private_database': REHEARSAL})
    print((BACKUP / 'rehearsal.json').read_text(), flush=True)


def write_configuration(path, value):
    # Preserve mounted file inode and existing permissions for Docker bind mounts.
    path.write_text(json.dumps(value, indent=2) + '\n')


def update_service(name, *, force=False):
    print('ROLLOUT ' + name, flush=True)
    run(compose() + ['up', '-d', '--no-deps', '--no-build', '--wait', '--wait-timeout', '240']
        + (['--force-recreate'] if force else []) + [name])


def check_effective_mounts():
    merged = json.loads(capture(compose() + ['config', '--format', 'json']))
    mounts = [v for v in merged['services']['gateway']['volumes']
              if v['target'] == '/etc/nginx/nginx.conf']
    assert len(mounts) == 1 and mounts[0]['source'] == str(CFG / 'public.nginx.conf')
    assert mounts[0]['read_only'] is True
    for name in ('documentos-a', 'documentos-b', 'web'):
        volumes = [v for v in merged['services'][name]['volumes']
                   if v['target'] == '/var/lib/redhouse-private']
        assert len(volumes) == 1 and volumes[0]['source'] == 'private-files'
    save('effective-mounts.json', {'gateway_uses_preserved_public_config': True,
                                  'private_volume_shared_by_consumers': True})


def resolve_peers(state):
    gateway = state['gateway']
    network = PROJECT + '_data'
    address = gateway['networks'][network]['ip']
    assert address and 'gateway-private' in gateway['networks'][network]['aliases']
    script = ("import json,socket;print(json.dumps(sorted({x[4][0] for x in "
              "socket.getaddrinfo('gateway-private',None,type=socket.SOCK_STREAM)})))")
    for name in targets(state):
        actual = json.loads(capture(['docker', 'exec', state[name]['id'], 'python', '-c', script]))
        assert actual == [address], 'Gateway peer ambiguous in ' + name
        assert name + '-private' in state[name]['networks'][network]['aliases']
    return address


def rollout():
    assert (BACKUP / 'migration.json').exists()
    before = json.loads((BACKUP / 'runtime-before.json').read_text())
    assert containers() == json.loads((BACKUP / 'runtime-compatible.json').read_text()), 'Runtime changed before rollout'
    expected = json.loads((BACKUP / 'preflight.json').read_text())['source_hashes']
    assert all((digest(ROOT / n) if (ROOT / n).exists() else None) == value
               for n, value in expected.items()), 'Host sources changed before rollout'
    builds = json.loads((BACKUP / 'builds.json').read_text())
    for name in manifest():
        target = ROOT / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(BACKUP / 'payload' / name, target)
    old_nginx = (CFG / 'public.nginx.conf').read_bytes()
    spec = importlib.util.spec_from_file_location('redhouse_public', ROOT / 'deployment/gcp/configure_public.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.configure(CFG, '34.18.186.116')
    desired_nginx = (CFG / 'public.nginx.conf').read_bytes()
    (BACKUP / 'desired.nginx.conf').write_bytes(desired_nginx)
    (CFG / 'public.nginx.conf').write_bytes(old_nginx)
    # Publish provider-aware code first. No local objects exist during this gate.
    document_path = CFG / 'apps/documentos.json'
    document = json.loads(document_path.read_text())
    document.update(STORAGE_PROVIDER='gcs', STORAGE_LOCAL_ROOT='/var/lib/redhouse-private')
    write_configuration(document_path, document)
    override = json.loads((CFG / 'gcs.compose.yaml').read_text())
    for name in targets(before):
        override.setdefault('services', {}).setdefault(name, {})['image'] = builds[owner(name)]['tag']
    override['services']['storage-init'] = {'image': builds['documentos']['tag']}
    write_configuration(CFG / 'gcs.compose.yaml', override)
    run(compose() + ['config', '--quiet'])
    check_effective_mounts()
    # The installed Compose `run` has no --no-build flag. The prepared image is
    # pinned above; --pull never prevents an unexpected image fetch.
    run(compose() + ['run', '--rm', '--no-deps', '--pull', 'never', 'storage-init'])
    update_service('gateway')
    for name in targets(before):
        update_service(name)
    state = containers()
    assert len(state) == 30 and all(v['health'] == 'healthy' for v in state.values())
    address = resolve_peers(state)
    for name in ('postgres', 'mongodb', 'redis', 'clamav'):
        assert state[name] == before[name], 'Unrelated dependency changed'
    assert all(state[n]['image'] == builds[owner(n)]['id'] for n in targets(before))
    (CFG / 'public.nginx.conf').write_bytes(desired_nginx)
    run(['docker', 'exec', state['gateway']['id'], 'nginx', '-t'])
    run(['docker', 'exec', state['gateway']['id'], 'nginx', '-s', 'reload'])
    save('runtime-staged.json', state)
    save('staged.json', {'healthy': 30, 'schema': 19, 'gateway_private_ip': address,
                         'write_provider': 'gcs', 'ready_for_public_smoke': True})
    print((BACKUP / 'staged.json').read_text(), flush=True)


def enable_local():
    assert (BACKUP / 'public-smoke-approved.json').exists(), 'Public smoke must pass first'
    before = containers()
    assert before == json.loads((BACKUP / 'runtime-staged.json').read_text())
    for path in (CFG / 'apps/documentos.json', CFG / 'web.json'):
        value = json.loads(path.read_text())
        value.update(STORAGE_PROVIDER='local', STORAGE_LOCAL_ROOT='/var/lib/redhouse-private',
                     STORAGE_PUBLIC_BASE_URL='https://34.18.186.116')
        write_configuration(path, value)
    # From this point old GCS-only images must not be restored without reconciliation.
    save('local-activation-started.json', {'retain_provider_adapter_and_volume': True})
    for name in ('documentos-a', 'documentos-b', 'web'):
        # Bind-mounted JSON contents do not change Compose's service hash.
        update_service(name, force=True)
    state = containers()
    assert all(v['health'] == 'healthy' for v in state.values())
    assert state['gateway'] == before['gateway']
    resolve_peers(state)
    save('runtime-local.json', state)
    print(json.dumps({'phase': 'local_enabled', 'healthy': len(state), 'verification_pending': True}), flush=True)


def rollback_before_local():
    assert not (BACKUP / 'local-activation-started.json').exists(), 'Keep provider-compatible images after local activation'
    assert sql("SELECT count(*) FROM red_house.stored_file WHERE storage_provider='local';") == '0'
    assert sql("SELECT count(*) FROM red_house.export_jobs WHERE storage_provider='local';") == '0'
    for name in manifest():
        old = BACKUP / 'sources' / name
        if old.exists():
            shutil.copy2(old, ROOT / name)
        # New source files are harmless with pinned old images; preserve evidence.
    for name in ('gcs.compose.yaml', 'public.compose.yaml', 'public.nginx.conf', 'web.json', 'public.json'):
        old = BACKUP / 'configuration' / name
        if old.exists():
            shutil.copy2(old, CFG / name)
    for old in (BACKUP / 'configuration/apps').glob('*.json'):
        shutil.copy2(old, CFG / 'apps' / old.name)
    builds = json.loads((BACKUP / 'compatibility-builds.json').read_text())
    override = json.loads((CFG / 'gcs.compose.yaml').read_text())
    for name in ('documentos-a', 'documentos-b', 'web'):
        override.setdefault('services', {}).setdefault(name, {})['image'] = builds[owner(name)]['tag']
    write_configuration(CFG / 'gcs.compose.yaml', override)
    run(compose() + ['config', '--quiet'])
    before = json.loads((BACKUP / 'runtime-before.json').read_text())
    update_service('gateway')
    for name in targets(before):
        update_service(name)
    state = containers()
    assert all(state[n]['image'] == (builds[owner(n)]['id'] if n in ('documentos-a', 'documentos-b', 'web') else before[n]['image']) and state[n]['health'] == 'healthy'
               for n in targets(before) + ['gateway'])
    save('rollback-result.json', {'prior_business_images_with_gcs_compatibility': True, 'additive_schema19_retained': True})


def recover_gcs_writes():
    """Keep both-provider readers and local data; only change future writes.

    This is not a repair for lost local files and not a database restoration.
    Existing local rows remain local and unavailable objects must be restored
    from their own coordinated backup, never silently substituted from GCS.
    """
    assert (BACKUP / 'local-activation-started.json').exists()
    assert sql('SELECT max(version) FROM red_house.schema_migration;') == '19'
    builds = json.loads((BACKUP / 'builds.json').read_text())
    before = containers()
    names = ('documentos-a', 'documentos-b', 'web')
    assert all(before[name]['image'] == builds[owner(name)]['id'] for name in names)
    # Capture the exact configuration once, without exposing it in output.
    for relative in ('apps/documentos.json', 'web.json'):
        path = CFG / relative
        saved = BACKUP / 'before-gcs-write-recovery' / relative
        if not saved.exists():
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, saved)
        value = json.loads(path.read_text())
        value['STORAGE_PROVIDER'] = 'gcs'
        write_configuration(path, value)
    save('gcs-write-recovery-started.json', {'retain_provider_adapter_and_volume': True})
    for name in names:
        update_service(name, force=True)
    state = containers()
    assert state['gateway'] == before['gateway']
    assert all(value['health'] == 'healthy' for value in state.values())
    resolve_peers(state)
    save('gcs-write-recovery-result.json', {'write_provider': 'gcs',
         'schema19_and_local_volume_retained': True, 'public_verification_pending': True})


if __name__ == '__main__':
    os.umask(0o077)
    assert os.geteuid() == 0 and ROOT.exists()
    {'preflight': preflight, 'capacity': capacity, 'prepare': prepare,
     'resume-compatibility-build': resume_compatibility_build,
     'backup': backup_database, 'compatibility': compatibility,
     'rehearse': rehearse, 'migrate': migrate, 'rollout': rollout, 'enable-local': enable_local,
     'rollback-before-local': rollback_before_local,
     'recover-gcs-writes': recover_gcs_writes}[sys.argv[1]]()
