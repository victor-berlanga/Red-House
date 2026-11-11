"""Actualización autorizada de la VM existente; fases con respaldo y hashes.

Ejecutar solo como root en /opt/redhouse. No crea VM/bucket ni restaura bases locales.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

os.umask(0o077)
ROOT = Path('/opt/redhouse')
PRIVATE = ROOT / '.local/deploy-portal03-20261106'
CONFIG = ROOT / '.local/compose'
INPUT = Path('/tmp/redhouse-portal03-20261106')
TAG = 'portal03-20261106'


def run(args):
    subprocess.run(args, cwd=ROOT, check=True)


def capture(args):
    return subprocess.check_output(args, cwd=ROOT, text=True).strip()


def compose():
    args = ['docker', 'compose', '-f', str(ROOT / 'compose.yaml')]
    for name in ('gcs.compose.yaml', 'public.compose.yaml'):
        if (CONFIG / name).exists():
            args += ['-f', str(CONFIG / name)]
    return args


def save(name, data):
    (PRIVATE / name).write_text(json.dumps(data, indent=2) + '\n')


def sql(query):
    return json.loads(capture(['docker', 'exec', 'redhouse-parcial2-postgres-1',
                              'psql', '-U', 'rh_bootstrap', '-d', 'red_house',
                              '-qAt', '-v', 'ON_ERROR_STOP=1', '-c', query]))


def state(columns=None):
    if columns is None:
        columns = sql("SELECT json_object_agg(t,cols) FROM (SELECT table_name t,"
                      "json_agg(column_name ORDER BY ordinal_position) cols "
                      "FROM information_schema.columns WHERE table_schema='red_house' "
                      "GROUP BY table_name) x")
    result = {}
    for name, cols in columns.items():
        assert name.replace('_', '').isalnum()
        assert all(c.replace('_', '').isalnum() for c in cols)
        projection = ','.join('"' + c + '"' for c in cols)
        result[name] = sql("SELECT json_build_object('rows',count(*),'digest',"
                           "md5(coalesce(string_agg(md5(row_to_json(t)::text),'' "
                           "ORDER BY md5(row_to_json(t)::text)),''))) FROM (SELECT "
                           + projection + ' FROM red_house."' + name + '") t')
    return {'columns': columns, 'tables': result}


def main():
    assert ROOT.exists() and os.geteuid() == 0
    phase = sys.argv[1]
    if phase == 'backup':
        assert shutil.disk_usage(ROOT).free > 2_000_000_000
        PRIVATE.mkdir(exist_ok=False)
        with tarfile.open(PRIVATE / 'source-before.tar.gz', 'w:gz') as archive:
            for path in ROOT.iterdir():
                if path.name not in {'.local', '.git', '.codegraph'}:
                    archive.add(path, arcname=path.name)
        shutil.copytree(CONFIG, PRIVATE / 'configuration-before',
                        ignore=shutil.ignore_patterns('backups', 'demo-20261021', 'labels-20261021'))
        ids = capture(['docker', 'ps', '-aq', '--filter',
                       'label=com.docker.compose.project=redhouse-parcial2']).split()
        images = json.loads(capture(['docker', 'inspect', *ids]))
        save('images-before.json', [{'name': c['Name'], 'image': c['Image']} for c in images])
        run(['systemctl', 'stop', 'redhouse'])
        run(compose() + ['up', '-d', '--wait', 'postgres', 'mongodb', 'redis'])
        run(['python3', 'deployment/backup.py', '--verify', '--leave-stopped',
             '--output', str(PRIVATE / 'backup-report.json')])
        report = json.loads((PRIVATE / 'backup-report.json').read_text())
        assert report['restore'] == 'passed'
        assert sql('SELECT max(version) FROM red_house.schema_migration') == 16
        save('data-before.json', state())
        print(json.dumps({'backup': 'passed', 'restore': 'passed', 'schema_before': 16}), flush=True)
    elif phase == 'install':
        assert json.loads((PRIVATE / 'backup-report.json').read_text())['restore'] == 'passed'
        manifest = json.loads((INPUT / 'source-manifest.json').read_text())
        with tarfile.open(INPUT / 'project.tar.gz') as archive:
            members = archive.getmembers()
            assert len(members) == len(manifest)
            for member in members:
                assert member.isfile() and member.name in manifest
                assert not Path(member.name).is_absolute() and '..' not in Path(member.name).parts
                assert hashlib.sha256(archive.extractfile(member).read()).hexdigest() == manifest[member.name]
            for member in members:
                path = ROOT / member.name
                path.parent.mkdir(parents=True, exist_ok=True, mode=0o755)
                path.write_bytes(archive.extractfile(member).read())
                path.chmod(member.mode)
                for parent in path.parents:
                    if parent == ROOT:
                        break
                    parent.chmod(0o755)
        assert all(hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == h for p, h in manifest.items())
        save('source-manifest.json', manifest)
        override_path = CONFIG / 'gcs.compose.yaml'
        override = json.loads(override_path.read_text())
        base = json.loads((ROOT / 'compose.yaml').read_text())
        for name, spec in base['services'].items():
            if '${REDHOUSE_TAG:' in spec.get('image', ''):
                image = spec['image'].split(':', 1)[0] + ':' + TAG
                override.setdefault('services', {}).setdefault(name, {})['image'] = image
        override['services'].setdefault('bootstrap', {})['image'] = 'redhouse/bootstrap:' + TAG
        override_path.write_text(json.dumps(override, indent=2) + '\n')
        run(compose() + ['config', '--quiet'])
        print(json.dumps({'installed_files': len(manifest), 'tag': TAG}), flush=True)
    elif phase == 'build':
        assert (PRIVATE / 'source-manifest.json').exists()
        run(compose() + ['--parallel', '1', '--profile', 'install', 'build'])
    elif phase == 'migrate':
        report = json.loads((PRIVATE / 'backup-report.json').read_text())
        assert report['restore'] == 'passed'
        backup = Path(report['private_path']) / 'postgres.dump'
        run(compose() + ['--profile', 'install', 'run', '--rm', '--entrypoint', 'python',
                         'bootstrap', '/app/apps/services/scripts/upgrade_compose.py',
                         '--backup', str(Path('/run/install') / backup.relative_to(CONFIG))])
        before = json.loads((PRIVATE / 'data-before.json').read_text())
        after = state(before['columns'])
        differences = sorted(t for t, v in before['tables'].items() if after['tables'][t] != v)
        assert differences == ['schema_migration'], differences
        assert sql('SELECT max(version) FROM red_house.schema_migration') == 17
        save('data-preservation.json', {'compared_tables': len(before['tables']),
             'unchanged_tables': len(before['tables']) - 1, 'expected_change': 'schema_migration',
             'unexpected_changes': [], 'schema': 17})
        save('data-after.json', after)
        comparisons = 0
        for relative in ['postgres-password', 'mongo-password', 'redis-password', 'redis.acl']:
            assert (CONFIG / relative).read_bytes() == (PRIVATE / 'configuration-before' / relative).read_bytes(), relative
            comparisons += 1
        preserved_config = PRIVATE / 'configuration-before'
        for path in [*(preserved_config / 'apps').glob('*.json'), preserved_config / 'web.json']:
            if path.name == 'state.json':
                continue
            before_cfg = json.loads(path.read_text())
            after_cfg = json.loads((CONFIG / path.relative_to(preserved_config)).read_text())
            for key, value in before_cfg.items():
                if any(word in key for word in ['KEY', 'SECRET', 'PASSWORD', 'DATABASE_URL', 'REDIS_URL', 'MONGODB']):
                    assert after_cfg.get(key) == value, path.name + ':' + key
                    comparisons += 1
        save('configuration-preservation.json', {'sensitive_fields_files_compared': comparisons,
             'matches': True, 'values_published': False, 'image_override': TAG})
        run(compose() + ['config', '--quiet'])
        print(json.dumps({'schema': 17, 'data_preserved': True, 'configuration_preserved': True}), flush=True)
    elif phase == 'start':
        assert json.loads((PRIVATE / 'data-preservation.json').read_text())['schema'] == 17
        run(['systemctl', 'start', '--no-block', 'redhouse'])
    elif phase == 'status':
        names = capture(['docker', 'ps', '-a', '--filter', 'label=com.docker.compose.project=redhouse-parcial2',
                         '--format', '{{.Names}} {{.Status}}'])
        print(capture(['systemctl', 'show', 'redhouse', '-p', 'ActiveState', '-p', 'SubState']))
        print(names)
        print('free_bytes', shutil.disk_usage(ROOT).free)
    else:
        raise ValueError('Unknown phase')


if __name__ == '__main__':
    main()
