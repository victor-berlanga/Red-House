"""Bounded schema-20 release on the existing, verified Red House VM."""
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import release_base as base
from release_base import (
    ROOT, INPUT, BACKUP, CFG, PROJECT, capture, run, save, read, digest,
    config_hashes, effective_config, containers, storage, target, compose,
    check_gate, gated, install_nginx, validate_nginx, owner, sql,
)

REHEARSAL = 'rh_scanner20_20261113'


def targets(state):
    names = sorted(n for n in state if n.endswith(('-a', '-b')))
    assert len(names) == 24
    return names + ['web']


base.targets = targets


def sql_database(statement, database):
    assert database in ('red_house', REHEARSAL)
    pg = containers()['postgres']['id']
    command = ('export PGPASSWORD="$(cat /run/secrets/postgres_password)"; '
               'exec psql -X -v ON_ERROR_STOP=1 -U rh_bootstrap -d ' + database + ' -At')
    return capture(['docker', 'exec', '-i', pg, 'sh', '-c', command], statement)


MIGRATE = r'''
import json,sys
from pathlib import Path
sys.path.insert(0,'/app/apps/services')
import psycopg
from redhouse.shared_migrations import upgrade
database='red_house'
dsn=psycopg.conninfo.make_conninfo(host='postgres',port=5432,dbname=database,
 user='rh_bootstrap',password=Path('/run/install/postgres-password').read_text().strip(),connect_timeout=5)
def fingerprint(conn,table):
 return conn.execute("SELECT count(*),md5(coalesce(string_agg(row::text,'' ORDER BY row::text),'')) FROM (SELECT to_jsonb(t)-ARRAY['engine_version','signature_version','signature_at','signature_max_age_seconds'] AS row FROM red_house."+table+" t) q").fetchone()
def grants(conn):
 return conn.execute("SELECT n.nspname,c.relname,a.grantee,a.grantor,a.privilege_type,a.is_grantable FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace CROSS JOIN LATERAL aclexplode(coalesce(c.relacl,acldefault('r',c.relowner))) a WHERE (n.nspname LIKE 'access_%' OR n.nspname='red_house') AND c.relkind IN ('r','v','p') ORDER BY 1,2,3,4,5,6").fetchall()
def columns(conn):
 return conn.execute("SELECT n.nspname,c.relname,t.attname,a.grantee,a.grantor,a.privilege_type,a.is_grantable FROM pg_attribute t JOIN pg_class c ON c.oid=t.attrelid JOIN pg_namespace n ON n.oid=c.relnamespace CROSS JOIN LATERAL aclexplode(t.attacl) a WHERE (n.nspname LIKE 'access_%' OR n.nspname='red_house') AND t.attnum>0 AND NOT t.attisdropped ORDER BY 1,2,3,4,5,6,7").fetchall()
def snapshot(conn):
 version=conn.execute('SELECT max(version) FROM red_house.schema_migration').fetchone()[0]
 result={'version':version,'records':{t:fingerprint(conn,t) for t in ('stored_file','file_scans','export_jobs')},'grants':grants(conn),'columns':columns(conn)}
 result['new_metadata_rows']=conn.execute("SELECT count(*) FROM red_house.file_scans WHERE engine_version IS NOT NULL OR signature_version IS NOT NULL OR signature_at IS NOT NULL OR signature_max_age_seconds IS NOT NULL").fetchone()[0] if version==20 else 0
 return json.loads(json.dumps(result))
expected=json.load(sys.stdin)
with psycopg.connect(dsn) as conn:
 conn.execute("SET LOCAL lock_timeout='10s'")
 conn.execute("SET LOCAL statement_timeout='120s'")
 conn.execute('SET LOCAL ROLE rh_shared_owner')
 version=conn.execute('SELECT max(version) FROM red_house.schema_migration').fetchone()[0]
 assert version==19, 'Unexpected schema; do not repeat migration blindly'
 conn.execute('LOCK TABLE red_house.stored_file,red_house.file_scans,red_house.export_jobs IN SHARE ROW EXCLUSIVE MODE')
 before=snapshot(conn)
 assert before==expected, 'Database changed since durable migration intent'
 assert upgrade(conn)==20
 assert snapshot(conn)==dict(before,version=20)
 assert not conn.execute("SELECT has_table_privilege('rh_inventario','access_inventario.operations','DELETE')").fetchone()[0]
 assert not conn.execute("SELECT has_table_privilege('rh_documentos','access_documentos.file_scans','UPDATE') OR has_table_privilege('rh_documentos','access_documentos.file_scans','DELETE')").fetchone()[0]
 print(json.dumps({'version':20,'historical_rows_preserved':True,'table_and_column_grants_preserved':True,'historical_scan_metadata':'NULL','counts':{t:v[0] for t,v in before['records'].items()}}))
'''

INSPECT = MIGRATE[:MIGRATE.index('expected=json.load(sys.stdin)')] + '''
with psycopg.connect(dsn) as conn:
 conn.execute('SET TRANSACTION READ ONLY')
 conn.execute("SET LOCAL statement_timeout='120s'")
 print(json.dumps(snapshot(conn)))
'''


def migration_command(program):
    return ['docker', 'run', '--rm', '-i', '--user', '0:0', '--read-only',
            '--network', PROJECT + '_data', '--mount',
            f'type=bind,src={CFG},dst=/run/install,readonly',
            '--entrypoint', 'python', read('builds.json')['web']['id'], '-c', program]


def preflight():
    base.preflight()
    current_document = json.loads((CFG / 'apps/documentos.json').read_text())
    assert current_document['STORAGE_PROVIDER'] == 'local'
    assert current_document.get('CLAMD_VERSION_TIMEZONE', 'UTC') == 'UTC'
    assert current_document.get('CLAMD_SIGNATURE_MAX_AGE_SECONDS', 172800) == 172800
    current_override = json.loads((CFG / 'gcs.compose.yaml').read_text())
    assert isinstance(current_override['services']['clamav'].get('environment', {}), dict)
    size = int(sql("SELECT pg_database_size('red_house');"))
    assert shutil.disk_usage(ROOT).free > size * 2 + 1_500_000_000
    assert sql("SELECT count(*) FROM pg_database WHERE datname='" + REHEARSAL + "';") == '0'
    print(json.dumps({'rehearsal_space_checked': True, 'database_bytes': size}))


def prepare():
    base.prepare()
    shutil.copy2(INPUT / 'release_base.py', BACKUP / 'release_base.py')


def rehearse():
    target()
    assert digest(BACKUP / 'database.dump') == read('database-backup.json')['sha256']
    assert sql("SELECT count(*) FROM pg_database WHERE datname='" + REHEARSAL + "';") == '0'
    assert storage()['schema'] == 19
    size = int(sql("SELECT pg_database_size('red_house');"))
    assert shutil.disk_usage(ROOT).free > size * 2 + 1_500_000_000
    before = containers()
    started = time.monotonic()
    sql('CREATE DATABASE ' + REHEARSAL + ' OWNER rh_shared_owner TEMPLATE template0;')
    sql('REVOKE CONNECT ON DATABASE ' + REHEARSAL + ' FROM PUBLIC;')
    passed = False
    try:
        command = ('export PGPASSWORD="$(cat /run/secrets/postgres_password)"; '
                   'exec pg_restore --exit-on-error -U rh_bootstrap -d ' + REHEARSAL)
        with (BACKUP / 'database.dump').open('rb') as stream:
            result = subprocess.run(['docker', 'exec', '-i', before['postgres']['id'], 'sh', '-c', command],
                                    stdin=stream, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=900)
        (BACKUP / 'restore.private.log').write_bytes(result.stdout + result.stderr)
        assert result.returncode == 0, 'Restore failed; preserve private database'
        assert sql("SELECT count(*) FROM pg_roles WHERE rolcanlogin AND NOT rolsuper AND has_database_privilege(rolname,'" + REHEARSAL + "','CONNECT');") == '0'
        assert sql_database('SELECT max(version) FROM red_house.schema_migration;', REHEARSAL) == '19'
        program = MIGRATE.replace("database='red_house'", "database='" + REHEARSAL + "'")
        assert program != MIGRATE
        before_program = INSPECT.replace("database='red_house'", "database='" + REHEARSAL + "'")
        intent = json.loads(capture(migration_command(before_program)))
        assert intent['version'] == 19
        result = json.loads(capture(migration_command(program), json.dumps(intent)))
        assert sql_database('SELECT max(version) FROM red_house.schema_migration;', REHEARSAL) == '20'
        assert storage()['schema'] == 19 and containers() == before
        save('rehearsal.json', {'database': REHEARSAL, 'restored_from_schema': 19,
             'migration': result, 'elapsed_seconds': time.monotonic() - started,
             'production_schema': 19, 'runtime_unchanged': True,
             'scope': 'Private PostgreSQL restore and migration; not coordinated platform recovery'})
        passed = True
    finally:
        if passed:
            sql('DROP DATABASE ' + REHEARSAL + ';')
            save('rehearsal-cleanup.json', {'dropped_only_private_database': REHEARSAL})
    print(json.dumps(read('rehearsal.json')))


def write_json(path, value):
    # Existing files are bind-mounted: preserve their inode and permissions.
    with path.open('w') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def durable_record(name, value):
    destination = BACKUP / name
    temporary = BACKUP / (name + '.partial')
    write_json(temporary, value)
    os.replace(temporary, destination)
    descriptor = os.open(BACKUP, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def migrate_or_recover():
    current = json.loads(capture(migration_command(INSPECT)))
    if (BACKUP / 'migration.json').exists():
        assert current['version'] == 20
        return
    if not (BACKUP / 'migration-intent.json').exists():
        assert current['version'] == 19
        durable_record('migration-intent.json', current)
    intent = read('migration-intent.json')
    assert intent['version'] == 19
    if current['version'] == 19:
        assert current == intent, 'Inspect changed database before replacing migration intent'
        result = json.loads(capture(migration_command(MIGRATE), json.dumps(intent)))
    else:
        # The SQL commit may have completed before Python saved its response.
        # Recover only if schema, preserved rows, NULL metadata and all table/
        # column grants match the durable intent from before that commit.
        assert current == dict(intent, version=20), 'Unrecognized schema-20 state'
        result = {'version': 20, 'recovered_after_commit': True,
                  'historical_rows_preserved': True,
                  'table_and_column_grants_preserved': True,
                  'historical_scan_metadata': 'NULL'}
    durable_record('migration.json', result)


def runtime_for_resume():
    ids = capture(['docker', 'ps', '-aq', '--filter', f'label=com.docker.compose.project={PROJECT}']).split()
    selected = json.loads(capture(['docker', 'inspect', *ids]))
    expected = set(effective_config()['services']) - {'bootstrap', 'storage-init'}
    candidates = [v for v in selected if v['Config']['Labels'].get('com.docker.compose.oneoff', '').lower() != 'true'
                and v['Config']['Labels'].get('com.docker.compose.service') in expected]
    selected = []
    for value in candidates:
        labels = value['Config']['Labels']
        service = labels['com.docker.compose.service']
        if (value['Name'] == '/' + PROJECT + '-' + service + '-1'
                and labels.get('com.docker.compose.project.working_dir') == str(ROOT)):
            selected.append(value)
        else:
            # Four retained Mongo restore containers share the old service label.
            # Read-only inventory identified them before any deployment mutation.
            assert (service == 'mongodb' and not value['State']['Running']
                    and value['Name'].startswith('/redhouse-restore-mongo-')
                    and not labels.get('com.docker.compose.project.working_dir')
                    and not labels.get('com.docker.compose.project.config_files')), 'Unknown noncanonical container'
    names = [v['Config']['Labels']['com.docker.compose.service'] for v in selected]
    assert len(names) == len(set(names)) and set(names) == expected
    return {v['Config']['Labels']['com.docker.compose.service']: v for v in selected}


def containers():
    return {name: {'id': value['Id'], 'image': value['Image'], 'tag': value['Config']['Image'],
                   'running': value['State']['Running'], 'started_at': value['State']['StartedAt'],
                   'health': value['State'].get('Health', {}).get('Status')}
            for name, value in runtime_for_resume().items()}


base.containers = containers


def reviewed_source_or_interrupted_copy(name, before, after):
    path = ROOT / name
    if path.is_symlink() or not path.resolve().is_relative_to(ROOT.resolve()):
        return False
    if digest(path) in (before, after):
        return True
    if not (BACKUP / 'migration.json').exists() or not path.is_file():
        return False
    payload = (BACKUP / 'payload' / name).read_bytes()
    assert digest(BACKUP / 'payload' / name) == after
    return payload.startswith(path.read_bytes())


def validate_resumable_configuration(previous, builds):
    expected = read('compose-before.private.json')
    current = effective_config()
    for name in targets(previous['runtime']):
        before_image = expected['services'][name]['image']
        assert current['services'][name]['image'] in (before_image, builds[owner(name)]['tag'])
        current['services'][name]['image'] = before_image
    old_env = expected['services']['clamav'].get('environment', {})
    present = current['services']['clamav'].get('environment', {})
    assert present in (old_env, dict(old_env, TZ='UTC', FRESHCLAM_CHECKS='12', CLAMD_CONF_ConcurrentDatabaseReload='no'))
    if 'environment' in expected['services']['clamav']:
        current['services']['clamav']['environment'] = old_env
    else:
        current['services']['clamav'].pop('environment', None)
    assert current == expected, 'Unexpected effective configuration during resume'
    old_document = json.loads((BACKUP / 'configuration/apps/documentos.json').read_text())
    new_document = dict(old_document, CLAMD_VERSION_TIMEZONE='UTC', CLAMD_SIGNATURE_MAX_AGE_SECONDS=172800)
    assert old_document['STORAGE_PROVIDER'] == 'local'
    assert old_document.get('CLAMD_VERSION_TIMEZONE', 'UTC') == 'UTC'
    assert old_document.get('CLAMD_SIGNATURE_MAX_AGE_SECONDS', 172800) == 172800
    assert json.loads((CFG / 'apps/documentos.json').read_text()) in (old_document, new_document)


def recover_configuration():
    """Repair only an interrupted prefix write of our two mounted JSON files."""
    target()
    gate = read('gate-state.json')
    assert digest(CFG / 'public.nginx.conf') == gate['sha256']
    gateway = json.loads(capture(['docker', 'inspect', gate['gateway']['id']]))[0]
    assert gateway['State']['Running'] and gateway['Image'] == gate['gateway']['image']
    # This direct probe works even if an incomplete JSON file prevents Compose
    # from reading its configuration. No public writes are reopened here.
    request = base.Request('https://34.18.186.116/services/identidad-acceso/api/v1/auth/reauthenticate',
                           data=b'{}', headers={'Content-Type': 'application/json'}, method='POST')
    try:
        base.urlopen(request, timeout=10)
        raise AssertionError('Write gate missing')
    except base.HTTPError as response:
        assert response.code == 503 and response.headers.get('X-RedHouse-Maintenance') == 'scanner20-20261113'
    assert read('migration.json')['version'] == 20
    assert json.loads(capture(migration_command(INSPECT)))['version'] == 20
    previous, builds = read('preflight.json'), read('builds.json')
    current_configuration = config_hashes()
    assert all(current_configuration[n] == value for n, value in previous['configuration'].items()
               if n not in ('public.nginx.conf', 'gcs.compose.yaml', 'apps/documentos.json'))
    documents = json.loads((BACKUP / 'configuration/apps/documentos.json').read_text())
    documents.update(CLAMD_VERSION_TIMEZONE='UTC', CLAMD_SIGNATURE_MAX_AGE_SECONDS=172800)
    override = json.loads((BACKUP / 'configuration/gcs.compose.yaml').read_text())
    for name in targets(previous['runtime']):
        override['services'].setdefault(name, {})['image'] = builds[owner(name)]['tag']
    override['services']['clamav'].setdefault('environment', {}).update(TZ='UTC', FRESHCLAM_CHECKS='12', CLAMD_CONF_ConcurrentDatabaseReload='no')
    desired = {'apps/documentos.json': documents, 'gcs.compose.yaml': override}
    for name, value in desired.items():
        existing = (CFG / name).read_bytes()
        original = (BACKUP / 'configuration' / name).read_bytes()
        expected = (json.dumps(value, indent=2) + '\n').encode()
        assert existing == original or expected.startswith(existing), 'Unrecognized configuration modification'
    for name, value in desired.items():
        saved = BACKUP / 'configuration-recovery-before' / name
        saved.parent.mkdir(parents=True, exist_ok=True)
        if not saved.exists():
            shutil.copy2(CFG / name, saved)
        write_json(CFG / name, value)
    run(compose() + ['config', '--quiet'])
    validate_resumable_configuration(previous, builds)
    durable_record('configuration-recovered.json', {'only_known_prefix_writes_repaired': True})


def publish():
    target()
    assert (BACKUP / 'rehearsal-cleanup.json').exists()
    assert read('rehearsal.json')['migration']['version'] == 20
    assert digest(BACKUP / 'database.dump') == read('database-backup.json')['sha256']
    assert time.time() - read('writes-closed.json')['at'] >= 125
    check_gate()
    previous, files, builds = read('preflight.json'), read('manifest.json'), read('builds.json')
    runtime = runtime_for_resume()
    names = targets(previous['runtime'])
    for name, state in runtime.items():
        allowed = {previous['runtime'][name]['image']}
        if name in names:
            allowed.add(builds[owner(name)]['id'])
        assert state['Image'] in allowed, 'Unexpected image during resume'
        if name not in names + ['clamav']:
            assert state['Id'] == previous['runtime'][name]['id'] and state['State']['Running']
    assert all(reviewed_source_or_interrupted_copy(n, previous['source_hashes'][n], files[n]) for n in files)
    validate_resumable_configuration(previous, builds)
    current_configuration = config_hashes()
    assert all(current_configuration[n] == value for n, value in previous['configuration'].items()
               if n not in ('public.nginx.conf', 'gcs.compose.yaml', 'apps/documentos.json'))
    save('publication-started.json', {'migration': 20, 'storage_provider_unchanged': True})
    migrate_or_recover()
    for name in files:
        destination = ROOT / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(BACKUP / 'payload' / name, destination)
        destination.chmod(0o644)
    document_path = CFG / 'apps/documentos.json'
    document = json.loads(document_path.read_text())
    assert document['STORAGE_PROVIDER'] == 'local'
    assert document.get('CLAMD_VERSION_TIMEZONE', 'UTC') == 'UTC'
    assert document.get('CLAMD_SIGNATURE_MAX_AGE_SECONDS', 172800) == 172800
    document['CLAMD_VERSION_TIMEZONE'] = 'UTC'
    document['CLAMD_SIGNATURE_MAX_AGE_SECONDS'] = 172800
    write_json(document_path, document)
    override = json.loads((CFG / 'gcs.compose.yaml').read_text())
    for name in targets(previous['runtime']):
        override['services'].setdefault(name, {})['image'] = builds[owner(name)]['tag']
    override['services']['clamav'].setdefault('environment', {}).update(TZ='UTC', FRESHCLAM_CHECKS='12', CLAMD_CONF_ConcurrentDatabaseReload='no')
    write_json(CFG / 'gcs.compose.yaml', override)
    run(compose() + ['config', '--quiet'])
    expected = read('compose-before.private.json')
    for name in targets(previous['runtime']):
        expected['services'][name]['image'] = builds[owner(name)]['tag']
    expected['services']['clamav'].setdefault('environment', {}).update(TZ='UTC', FRESHCLAM_CHECKS='12', CLAMD_CONF_ConcurrentDatabaseReload='no')
    assert effective_config() == expected, 'Configuration changed outside reviewed images/timezone/update frequency'
    desired_nginx = (BACKUP / 'configuration/public.nginx.conf').read_text()
    validate_nginx(desired_nginx)
    (BACKUP / 'desired.nginx.conf').write_text(desired_nginx)
    (BACKUP / 'desired-gated.nginx.conf').write_text(gated(desired_nginx))
    install_nginx(gated(desired_nginx))
    for name in ['clamav'] + targets(previous['runtime']):
        check_gate()
        print('ROLLOUT ' + name, flush=True)
        run(compose() + ['up', '-d', '--no-deps', '--no-build', '--wait', '--wait-timeout', '240', name])
    state = containers()
    assert len(state) == 30 and all(v['running'] and v['health'] == 'healthy' for v in state.values())
    names = targets(previous['runtime'])
    assert all(state[n]['image'] == builds[owner(n)]['id'] for n in names)
    assert all(state[n] == previous['runtime'][n] for n in state if n not in names + ['clamav'])
    assert state['clamav']['image'] == previous['runtime']['clamav']['image']
    assert all(digest(ROOT / n) == value for n, value in files.items())
    current = config_hashes()
    assert all(current[n] == value for n, value in previous['configuration'].items()
               if n not in ('public.nginx.conf', 'gcs.compose.yaml', 'apps/documentos.json'))
    assert storage()['schema'] == 20
    assert {k:v for k,v in storage().items() if k!='schema'} == {k:v for k,v in previous['storage'].items() if k!='schema'}
    check_gate()
    save('runtime-final.json', state)
    save('publication.json', {'healthy': 30, 'schema': 20, 'files': len(files),
         'storage_before': previous['storage'], 'storage_after': storage(),
         'public_validation_pending': True, 'writes_closed': True})
    print(json.dumps(read('publication.json')))


if __name__ == '__main__':
    os.umask(0o077)
    assert os.geteuid() == 0 and ROOT.exists()
    {'preflight': preflight, 'prepare': prepare, 'backup': base.backup_database,
     'rehearse': rehearse, 'close-writes': base.close_writes,
     'recover-config': recover_configuration,
     'recover-nginx': base.recover_nginx, 'publish': publish,
     'open-writes': base.open_writes}[sys.argv[1]]()
