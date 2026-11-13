"""Authorized, bounded production update with pinned base images and rollback."""
import gzip
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import time
from pathlib import Path

ROOT = Path('/opt/redhouse')
INPUT = Path('/tmp/redhouse-optimization-20261112')
BACKUP = ROOT / '.local/deploy-optimization-20261112'
CFG = ROOT / '.local/compose'
TAG = 'optimization-20261112'
OWNERS = ['identidad-acceso', 'donantes', 'inventario', 'transporte', 'monitoreo']
TARGETS = [owner + '-' + replica for owner in OWNERS for replica in ('a', 'b')] + ['web']
CACHE = 'apps/services/redhouse/cache.py'
MODULES = {'donantes': 'apps/services/ms_donantes/agenda.py',
           'transporte': 'apps/services/ms_transporte/tracking_socket.py',
           'monitoreo': 'apps/services/servicio_monitoreo/routes.py'}

def capture(args, data=None):
    result = subprocess.run(args, cwd=ROOT, input=data, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError('Command failed: ' + ' '.join(args[:4]) + ': ' + result.stderr[-1800:])
    return result.stdout.strip()

def run(args):
    subprocess.run(args, cwd=ROOT, check=True)

def save(name, value):
    (BACKUP / name).write_text(json.dumps(value, indent=2) + '\n')

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def compose():
    return ['docker', 'compose', '-f', str(ROOT / 'compose.yaml'),
            '-f', str(CFG / 'gcs.compose.yaml'), '-f', str(CFG / 'public.compose.yaml')]

def containers():
    ids = capture(['docker', 'ps', '-q', '--filter',
                   'label=com.docker.compose.project=redhouse-parcial2']).split()
    values = json.loads(capture(['docker', 'inspect', *ids]))
    return {v['Config']['Labels']['com.docker.compose.service']:
            {'id': v['Id'], 'image': v['Image'], 'tag': v['Config']['Image'],
             'health': v['State'].get('Health', {}).get('Status'),
             'name': v['Name'].lstrip('/')} for v in values}

def protected_configuration():
    paths = [*sorted((CFG / 'apps').glob('*.json')),
             *(CFG / name for name in ('web.json', 'postgres-password', 'mongo-password',
                                       'redis-password', 'redis.acl')),
             ROOT / 'compose.yaml', CFG / 'public.compose.yaml', CFG / 'public.nginx.conf']
    return {str(p.relative_to(ROOT)): digest(p) for p in paths if p.exists()}

def prepare():
    manifest = json.loads((INPUT / 'manifest.json').read_text())
    expected = json.loads((INPUT / 'expected-before.json').read_text())
    assert len(manifest) == 7 and set(manifest) == set(expected)
    assert all(n.startswith(('apps/services/', 'apps/web/')) and '..' not in Path(n).parts for n in manifest)
    assert all(digest(ROOT / n) == sha for n, sha in expected.items()), 'Remote source changed'
    before = containers()
    preflight = json.loads((INPUT / 'preflight.json').read_text())
    assert before == preflight['containers'], 'Runtime changed after preflight'
    assert len(before) == 30 and all(v['health'] == 'healthy' for v in before.values())
    assert shutil.disk_usage(ROOT).free > 1_000_000_000
    if BACKUP.exists():
        assert not (BACKUP / 'index.json').exists() and not (BACKUP / 'result.json').exists()
        assert json.loads((BACKUP / 'runtime-before.json').read_text()) == before
        assert json.loads((BACKUP / 'manifest.json').read_text()) == manifest
        assert protected_configuration() == json.loads((BACKUP / 'protected-config-before.json').read_text())
        assert all(digest(BACKUP / 'sources' / n) == h for n, h in expected.items())
        assert (BACKUP / 'gcs.compose.yaml').read_bytes() == (CFG / 'gcs.compose.yaml').read_bytes()
    else:
        BACKUP.mkdir(mode=0o700, exist_ok=False)
        save('runtime-before.json', before)
        save('manifest.json', manifest)
        save('protected-config-before.json', protected_configuration())
        for name in manifest:
            destination = BACKUP / 'sources' / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, destination)
        shutil.copy2(CFG / 'gcs.compose.yaml', BACKUP / 'gcs.compose.yaml')
    shutil.copy2(INPUT / 'deploy.py', BACKUP / 'deploy.py')
    (BACKUP / 'rollback.py').write_text(
        "import runpy,sys\nsys.argv=['deploy.py','rollback']\nrunpy.run_path(" +
        repr(str(BACKUP / 'deploy.py')) + ",run_name='__main__')\n")
    payload = BACKUP / 'payload'
    with tarfile.open(INPUT / 'payload.tar.gz') as archive:
        members = archive.getmembers()
        assert len(members) == len(manifest) and {m.name for m in members} == set(manifest)
        for member in members:
            assert member.isfile()
            content = archive.extractfile(member).read()
            assert hashlib.sha256(content).hexdigest() == manifest[member.name]
            destination = payload / member.name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(content)
            destination.chmod(0o644)
    builds = {}
    for owner in [*OWNERS, 'web']:
        representative = owner if owner == 'web' else owner + '-a'
        original = before[representative]
        if owner != 'web':
            assert original['image'] == before[owner + '-b']['image']
        repository = original['tag'].split(':')[0]
        old_tag = repository + ':optimization-before-20261112'
        new_tag = repository + ':' + TAG
        run(['docker', 'tag', original['image'], old_tag])
        files = list(manifest) if owner == 'web' else [CACHE] + ([MODULES[owner]] if owner in MODULES else [])
        build = BACKUP / 'build' / owner
        for name in files:
            destination = build / 'payload' / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(payload / name, destination)
            for parent in destination.parents:
                if parent == build:
                    break
                parent.chmod(0o755)
        (build / 'Dockerfile').write_text('FROM ' + old_tag + '\nCOPY payload/ /app/\n')
        print('BUILD ' + owner, flush=True)
        run(['docker', 'build', '--network=none', '--pull=false', '-t', new_tag, str(build)])
        hashes = {n: manifest[n] for n in files}
        check = ('import hashlib;from pathlib import Path;expected=' + repr(hashes) +
                 ';assert all(hashlib.sha256((Path("/app")/n).read_bytes()).hexdigest()==h for n,h in expected.items());'
                 '[compile((Path("/app")/n).read_text(),n,"exec") for n in expected if n.endswith(".py")];print("Verified image payload")')
        run(['docker', 'run', '--rm', '--network=none', '--entrypoint', 'python', new_tag, '-c', check])
        image = json.loads(capture(['docker', 'image', 'inspect', new_tag]))[0]
        old = json.loads(capture(['docker', 'image', 'inspect', old_tag]))[0]
        assert all(image['Config'].get(key) == old['Config'].get(key)
                   for key in ('Env', 'Entrypoint', 'Cmd', 'User', 'WorkingDir'))
        builds[owner] = {'tag': new_tag, 'id': image['Id'], 'base': original['image'], 'files': hashes}
    save('builds.json', builds)
    print(json.dumps({'phase': 'prepared', 'images': len(builds), 'files': len(manifest)}), flush=True)

MONGO_BACKUP = '''import json,os,subprocess,tempfile
password=open('/run/secrets/mongo_password').read().strip()
fd,path=tempfile.mkstemp(suffix='.json')
try:
 with os.fdopen(fd,'w') as f:json.dump({'uri':'mongodb://rh_bootstrap@127.0.0.1/?authSource=admin','password':password},f)
 result=subprocess.run(['mongodump','--config',path,'--db','rh_monitoreo','--collection','events','--archive','--gzip'],stderr=subprocess.PIPE)
 if result.returncode:raise SystemExit(result.stderr.decode(errors='replace').replace(password,'[REDACTED]')[-1200:])
finally:os.unlink(path)
'''
MONGO_INDEX = '''import json,time
from pymongo import MongoClient
password=open('/run/secrets/mongo_password').read().strip()
with MongoClient('mongodb://127.0.0.1',username='rh_bootstrap',password=password,authSource='admin') as client:
 collection=client.rh_monitoreo.events
 before=collection.estimated_document_count()
 prior=collection.index_information()
 start=time.monotonic()
 collection.create_index([('service',1),('checked_at',-1),('event_id',1)],name='monitor_latest',partialFilterExpression={'source':'monitoreo','checked_at':{'$exists':True}})
 elapsed=(time.monotonic()-start)*1000
 current=collection.index_information()
 assert current['monitor_latest']['key']==[('service',1),('checked_at',-1),('event_id',1)]
 assert current['monitor_latest']['partialFilterExpression']=={'source':'monitoreo','checked_at':{'$exists':True}}
 assert all(current.get(k)==v for k,v in prior.items())
 print(json.dumps({'index':'monitor_latest','build_ms':elapsed,'existed': 'monitor_latest' in prior,'estimated_documents_before':before,'estimated_documents_after':collection.estimated_document_count(),'prior_indexes_preserved':True,'index_bytes':client.rh_monitoreo.command('collStats','events')['indexSizes']['monitor_latest']}))
'''

def index():
    assert (BACKUP / 'builds.json').exists()
    mongo = containers()['mongodb']['id']
    destination = BACKUP / 'monitor-events-before.archive.gz'
    with destination.open('wb') as stream:
        result = subprocess.run(['docker', 'exec', mongo, 'python3', '-c', MONGO_BACKUP],
                                stdout=stream, stderr=subprocess.PIPE)
    assert result.returncode == 0, result.stderr.decode(errors='replace')[-1800:]
    with gzip.open(destination, 'rb') as stream:
        while stream.read(1024 * 1024):
            pass
    save('backup-report.json', {'scope': 'rh_monitoreo.events; live logical archive',
         'bytes': destination.stat().st_size, 'sha256': digest(destination),
         'gzip_integrity': True, 'restore_test': False,
         'path': str(destination), 'application_sources_and_images_preserved': True})
    result = json.loads(capture(['docker', 'exec', mongo, 'python3', '-c', MONGO_INDEX]))
    save('index.json', result)
    print(json.dumps(result), flush=True)

def rollback():
    before = json.loads((BACKUP / 'runtime-before.json').read_text())
    for name in json.loads((BACKUP / 'manifest.json').read_text()):
        shutil.copy2(BACKUP / 'sources' / name, ROOT / name)
    shutil.copy2(BACKUP / 'gcs.compose.yaml', CFG / 'gcs.compose.yaml')
    run(compose() + ['config', '--quiet'])
    for name in TARGETS:
        run(compose() + ['up', '-d', '--no-deps', '--no-build', '--wait', '--wait-timeout', '180', name])
    after = containers()
    assert all(after[n]['image'] == before[n]['image'] and after[n]['health'] == 'healthy' for n in TARGETS)
    save('rollback-result.json', {'passed': True, 'retained_additive_mongo_index': True})
    print('Rollback verified; additive index retained', flush=True)

def rollout():
    assert (BACKUP / 'index.json').exists()
    before = json.loads((BACKUP / 'runtime-before.json').read_text())
    assert containers() == before, 'Runtime changed before rollout'
    assert protected_configuration() == json.loads((BACKUP / 'protected-config-before.json').read_text())
    assert (CFG / 'gcs.compose.yaml').read_bytes() == (BACKUP / 'gcs.compose.yaml').read_bytes()
    manifest = json.loads((BACKUP / 'manifest.json').read_text())
    builds = json.loads((BACKUP / 'builds.json').read_text())
    updated = json.loads((BACKUP / 'gcs.compose.yaml').read_text())
    for name in TARGETS:
        owner = name if name == 'web' else name[:-2]
        updated['services'][name]['image'] = builds[owner]['tag']
    try:
        for name in manifest:
            shutil.copy2(BACKUP / 'payload' / name, ROOT / name)
        (CFG / 'gcs.compose.yaml').write_text(json.dumps(updated, indent=2) + '\n')
        run(compose() + ['config', '--quiet'])
        for name in TARGETS:
            print('ROLLOUT ' + name, flush=True)
            run(compose() + ['up', '-d', '--no-deps', '--no-build', '--wait', '--wait-timeout', '180', name])
        after = containers()
        assert len(after) == 30 and all(v['health'] == 'healthy' for v in after.values())
        assert all(after[n] == item for n, item in before.items() if n not in TARGETS)
        assert all(after[n]['image'] == builds[n if n == 'web' else n[:-2]]['id'] for n in TARGETS)
        assert protected_configuration() == json.loads((BACKUP / 'protected-config-before.json').read_text())
        assert all(digest(ROOT / n) == sha for n, sha in manifest.items())
        run(['docker', 'exec', after['gateway']['id'], 'nginx', '-t'])
        assert capture(['systemctl', 'is-active', 'redhouse']) == 'active'
        save('runtime-after.json', after)
        save('result.json', {'tag': TAG, 'healthy_containers': 30, 'updated_containers': len(TARGETS),
             'unchanged_containers': 30 - len(TARGETS), 'images': len(builds), 'files': len(manifest),
             'protected_configuration_preserved': True, 'postgres_schema_changed': False,
             'backup': str(BACKUP), 'rollback_prepared': True})
        print((BACKUP / 'result.json').read_text(), flush=True)
    except BaseException:
        rollback()
        raise

if __name__ == '__main__':
    os.umask(0o077)
    assert os.geteuid() == 0 and ROOT.exists()
    {'prepare': prepare, 'index': index, 'rollout': rollout, 'rollback': rollback}[sys.argv[1]]()
