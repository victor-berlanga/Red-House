"""Web-only release. This module is inert on import; commands run on the verified VM.

Adapted from clientes-20261113/procedimiento/deploy.py's target, compose,
container and image checks. No schema-19 guard, migration or global write gate.
"""
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import ssl
import subprocess
from urllib.request import ProxyHandler, Request, build_opener

ROOT = Path('/opt/redhouse')
CFG = ROOT / '.local/compose'
INPUT = Path('/tmp/redhouse-portal-documentos-20261114')
BACKUP = ROOT / '.local/deploy-portal-documentos-20261114'
OVERRIDE = CFG / 'gcs.compose.yaml'
PROJECT = 'redhouse-parcial2'
TARGET = {'project': 'sistemas-integracion-01', 'instance': 'red-house',
          'zone': 'me-central1-a', 'id': '2861822465669755197', 'ip': '34.18.186.116'}
FILES = ('apps/web/src/integration/routes/common.py',
         'apps/web/src/integration/routes/documents.py',
         'apps/web/src/presentation/templates/integration/document_upload.html')
NEW_TAG = 'redhouse-web:portal-documentos-20261114'
OLD_TAG = 'redhouse-web:before-portal-documentos-20261114'
BASELINE_REF = '982d592^'


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def capture(args, data=None, timeout=180):
    result = subprocess.run(args, cwd=ROOT, input=data, text=True,
                            capture_output=True, timeout=timeout)
    if result.returncode:
        # stderr can contain private configuration. Keep it out of public output.
        if BACKUP.is_dir():
            (BACKUP / 'command-error.private.log').write_text(result.stderr)
        raise RuntimeError('Command failed: ' + ' '.join(args[:3]))
    return result.stdout.strip()


def save(name, value):
    atomic(BACKUP / name, (json.dumps(value, indent=2) + '\n').encode(), 0o600)


def read(name):
    return json.loads((BACKUP / name).read_text())


def atomic(path, content, mode):
    temporary = path.with_name(path.name + '.portal-new')
    require(not temporary.exists() and not temporary.is_symlink(), 'Unknown temporary file')
    with temporary.open('xb') as output:
        output.write(content)
        output.flush()
        os.fsync(output.fileno())
    temporary.chmod(mode)
    os.replace(temporary, path)


def safe_path(path):
    require(path.is_relative_to(ROOT), 'Path outside installation')
    current = ROOT
    require(not current.is_symlink(), 'Installation symlink')
    for part in path.relative_to(ROOT).parts:
        current /= part
        require(not current.is_symlink(), 'Deployment path symlink')


def target():
    opener = build_opener(ProxyHandler({}))
    expected = {'instance/id': TARGET['id'], 'instance/name': TARGET['instance'],
                'project/project-id': TARGET['project'],
                'instance/network-interfaces/0/access-configs/0/external-ip': TARGET['ip']}
    for key, value in expected.items():
        req = Request('http://metadata.google.internal/computeMetadata/v1/' + key,
                      headers={'Metadata-Flavor': 'Google'})
        with opener.open(req, timeout=3) as response:
            require(response.read().decode() == value, 'Wrong VM identity')
    req = Request('http://metadata.google.internal/computeMetadata/v1/instance/zone',
                  headers={'Metadata-Flavor': 'Google'})
    with opener.open(req, timeout=3) as response:
        require(response.read().decode().endswith('/zones/' + TARGET['zone']), 'Wrong zone')


def compose():
    return ['docker', 'compose', '-f', str(ROOT / 'compose.yaml'),
            '-f', str(OVERRIDE), '-f', str(CFG / 'public.compose.yaml')]


def effective():
    return json.loads(capture(compose() + ['config', '--format', 'json']))


def config_hashes():
    paths = [ROOT / 'compose.yaml', *CFG.rglob('*')]
    for path in paths:
        safe_path(path)
    return {str(p.relative_to(ROOT)): sha(p) for p in paths if p.is_file()}


def containers(*, allow_missing_web=False):
    ids = capture(['docker', 'ps', '-q', '--filter',
                   'label=com.docker.compose.project=' + PROJECT]).split()
    require(bool(ids), 'No runtime containers')
    rows = json.loads(capture(['docker', 'inspect', *ids]))
    expected = set(effective()['services']) - {'bootstrap', 'storage-init'}
    selected = [r for r in rows if
                r['Config']['Labels'].get('com.docker.compose.oneoff', '').lower() != 'true']
    names = [r['Config']['Labels'].get('com.docker.compose.service') for r in selected]
    allowed = [expected, expected - {'web'}] if allow_missing_web else [expected]
    require(len(expected) == 30 and len(names) == len(set(names)) and set(names) in allowed,
            'Runtime must contain exactly the expected 30 services')
    return {r['Config']['Labels']['com.docker.compose.service']: {
        'id': r['Id'], 'image': r['Image'], 'tag': r['Config']['Image'],
        'running': r['State']['Running'], 'started_at': r['State']['StartedAt'],
        'health': r['State'].get('Health', {}).get('Status')} for r in selected}


def healthy(state):
    require(all(r['running'] and r['health'] == 'healthy' for r in state.values()),
            'Not all 30 services are healthy')


def unchanged_others(before, after):
    require(set(before) - {'web'} == set(after) - {'web'}, 'Runtime service set changed')
    require(all(after[n] == before[n] for n in before if n != 'web'),
            'One of the other 29 containers changed')


def schema_version(state):
    command = ('export PGPASSWORD="$(cat /run/secrets/postgres_password)"; '
               'exec psql -X -v ON_ERROR_STOP=1 -U rh_bootstrap -d red_house -At '
               '-c "SELECT max(version) FROM red_house.schema_migration"')
    return capture(['docker', 'exec', state['postgres']['id'], 'sh', '-c', command])


def local_storage():
    for name in ('web.json', 'apps/documentos.json'):
        require(json.loads((CFG / name).read_text())['STORAGE_PROVIDER'] == 'local',
                'Unexpected storage provider')


def image(identifier):
    return json.loads(capture(['docker', 'image', 'inspect', identifier]))[0]


def payload():
    manifest = json.loads((INPUT / 'manifest.json').read_text())
    require(set(manifest) == set(FILES), 'Payload must contain exactly three web sources')
    provenance = json.loads((INPUT / 'source.json').read_text())
    require(provenance['target'] == TARGET and provenance['files'] == manifest and
            provenance['deploy_sha256'] == sha(INPUT / 'deploy.py'), 'Package provenance mismatch')
    require(provenance['baseline_ref'] == BASELINE_REF and
            set(provenance['baseline_hashes']) == set(FILES), 'Missing known baseline')
    for name in FILES:
        path = INPUT / 'payload' / name
        require(path.is_file() and not path.is_symlink() and sha(path) == manifest[name],
                'Payload source mismatch')
    require({str(p.relative_to(INPUT / 'payload')) for p in (INPUT / 'payload').rglob('*')
             if p.is_file()} == set(FILES), 'Unexpected payload file')
    return manifest


def source_probe(container_id, expected=None, *, image_id=False):
    program = ('import hashlib,json;from pathlib import Path;from jinja2 import Environment;'
               'names=' + repr(FILES) + ';'
               'actual={n:hashlib.sha256((Path("/app")/n).read_bytes()).hexdigest() for n in names};'
               '[compile((Path("/app")/n).read_text(),n,"exec") for n in names if n.endswith(".py")];'
               'Environment().parse((Path("/app")/names[2]).read_text());print(json.dumps(actual))')
    command = (['docker', 'run', '--rm', '--network=none', '--read-only', '--cap-drop=ALL',
                '--security-opt=no-new-privileges', '--entrypoint', 'python', container_id]
               if image_id else ['docker', 'exec', container_id, 'python'])
    actual = json.loads(capture(command + ['-c', program]))
    if expected is not None:
        require(actual == expected, 'Container source hashes mismatch')
    return actual


def tls_evidence():
    # Future remote read only: authenticate the actual public IP using system roots.
    with socket.create_connection((TARGET['ip'], 443), timeout=15) as connection:
        with ssl.create_default_context().wrap_socket(
                connection, server_hostname=TARGET['ip']) as secure:
            certificate = secure.getpeercert()
            fingerprint = hashlib.sha256(secure.getpeercert(binary_form=True)).hexdigest()
    expires = datetime.fromtimestamp(ssl.cert_time_to_seconds(certificate['notAfter']), timezone.utc)
    timer = subprocess.run(['systemctl', 'show', 'redhouse-certbot.timer',
                            '--property=LoadState,ActiveState,UnitFileState,NextElapseUSecRealtime,LastTriggerUSec'],
                           text=True, capture_output=True, timeout=15)
    properties = dict(line.split('=', 1) for line in timer.stdout.splitlines() if '=' in line)
    service = subprocess.run(['systemctl', 'show', 'redhouse-certbot.service',
                              '--property=LoadState,Result,ExecMainStatus,ExecMainExitTimestamp'],
                             text=True, capture_output=True, timeout=15)
    return {'checked_at': datetime.now(timezone.utc).isoformat(), 'not_after': expires.isoformat(),
            'certificate_sha256': fingerprint, 'tls_trust_and_ip_validated': True,
            'delivery_day_end_utc': '2026-11-24T06:00:00+00:00',
            'covers_delivery_day_end': expires > datetime(2026, 11, 24, 6, tzinfo=timezone.utc),
            'renewal_timer': properties, 'timer_query_exit_code': timer.returncode,
            'renewal_service': dict(line.split('=', 1) for line in service.stdout.splitlines() if '=' in line),
            'service_query_exit_code': service.returncode,
            'renewal_performed': False}


def preflight():
    target()
    require(not BACKUP.exists(), 'Backup already exists; do not overwrite evidence')
    new = payload()
    for name in FILES:
        safe_path(ROOT / name)
    state = containers()
    healthy(state)
    require(schema_version(state) == '20', 'Expected schema 20')
    local_storage()
    require(capture(['systemctl', 'is-active', 'redhouse']) == 'active', 'Supervisor inactive')
    require(shutil.disk_usage(ROOT).free > 1_500_000_000, 'Insufficient free disk')
    old_sources = {n: sha(ROOT / n) for n in FILES}
    provenance = json.loads((INPUT / 'source.json').read_text())
    require(old_sources in (provenance['baseline_hashes'], new),
            'Unknown source baseline; compare against reviewed baseline before proceeding')
    source_probe(state['web']['id'], old_sources)
    source_probe(state['web']['image'], old_sources, image_id=True)
    tls = tls_evidence()
    details = json.loads(capture(['docker', 'inspect', state['web']['id']]))[0]
    require(not any(m['Destination'] == '/app' or m['Destination'].startswith('/app/')
                    for m in details['Mounts']), 'Source bind mount would mask image')
    config, hashes = effective(), config_hashes()
    require(config['services']['web']['image'] == state['web']['tag'], 'Image/config drift')
    old_image = image(state['web']['image'])
    require(not old_image['Config'].get('OnBuild'), 'Base image contains ONBUILD hooks')
    for tag in (NEW_TAG, OLD_TAG):
        require(not capture(['docker', 'image', 'ls', '-q', tag]), 'Release tag already exists')
    BACKUP.mkdir(mode=0o700)
    shutil.copytree(CFG, BACKUP / 'configuration')
    shutil.copy2(ROOT / 'compose.yaml', BACKUP / 'compose.yaml')
    for name in FILES:
        dest = BACKUP / 'sources' / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, dest)
        require(sha(dest) == old_sources[name], 'Source backup mismatch')
    shutil.copy2(INPUT / 'deploy.py', BACKUP / 'deploy.py')
    shutil.copy2(INPUT / 'source.json', BACKUP / 'source.json')
    save('image-before.private.json', old_image)
    save('compose-before.private.json', config)
    save('container-before.private.json', details)
    save('preflight.json', {'target': TARGET, 'runtime': state, 'configuration': hashes,
                          'old_sources': old_sources, 'new_sources': new,
                          'baseline_ref': BASELINE_REF, 'baseline_commit': provenance['baseline_commit'],
                          'tls': tls})
    require(config_hashes() == hashes and containers() == state, 'State changed during backup')
    for relative, digest in hashes.items():
        saved = BACKUP / ('compose.yaml' if relative == 'compose.yaml' else
                          'configuration/' + str(Path(relative).relative_to('.local/compose')))
        require(sha(saved) == digest, 'Configuration backup mismatch')
    capture(['docker', 'tag', state['web']['image'], OLD_TAG])
    save('backup-complete.json', {'previous_image': state['web']['image'], 'retained_tag': OLD_TAG})
    print(json.dumps({'preflight': 'passed', 'target': TARGET, 'sources': 3, 'schema': 20,
                      'base_image': state['web']['image'], 'healthy': 30}))


def prepare(retry=False):
    target()
    before = read('preflight.json')
    require(read('backup-complete.json')['previous_image'] == before['runtime']['web']['image'],
            'Backup incomplete')
    require(not (BACKUP / 'prepared.json').exists(), 'Candidate already prepared')
    require(containers() == before['runtime'] and config_hashes() == before['configuration'],
            'Runtime/configuration changed after preflight')
    require(payload() == before['new_sources'], 'Candidate changed after review')
    context = BACKUP / 'build'
    require(image(OLD_TAG)['Id'] == before['runtime']['web']['image'], 'Pinned base tag moved')
    old_dockerfile = 'FROM ' + before['runtime']['web']['image'] + '\n'
    copies = ''.join('COPY --chmod=0644 ' + n + ' /app/' + n + '\n' for n in FILES)
    if retry:
        require(context.is_dir() and not context.is_symlink(), 'Missing owned failed build context')
        require(not (BACKUP / 'build-attempt-1').exists(), 'Retry already attempted')
        require((context / 'Dockerfile').read_text() == old_dockerfile + copies,
                'Failed Dockerfile does not match the reviewed first attempt')
        require({str(p.relative_to(context)) for p in context.rglob('*') if p.is_file()}
                == set(FILES) | {'Dockerfile'}, 'Unexpected build context file')
        for name in FILES:
            require(sha(context / name) == before['new_sources'][name], 'Failed build source drift')
        require(not capture(['docker', 'image', 'ls', '-q', NEW_TAG]), 'Candidate tag already exists')
        attempt = BACKUP / 'build-attempt-1'
        attempt.mkdir(mode=0o700)
        for source in (context / 'Dockerfile', BACKUP / 'command-error.private.log', BACKUP / 'deploy.py'):
            shutil.copy2(source, attempt / source.name)
        save('prepare-retry.json', {'reason': 'BuildKit treated the image ID as a registry name',
                                   'retained_base': OLD_TAG, 'base_image': before['runtime']['web']['image'],
                                   'deploy_sha256': sha(Path(__file__)),
                                   'package_source': json.loads((INPUT / 'source.json').read_text())})
        shutil.copy2(Path(__file__), BACKUP / 'deploy-reviewed.py')
    else:
        context.mkdir(mode=0o700)
    for name in FILES:
        dest = context / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(INPUT / 'payload' / name, dest)
    # BuildKit interprets FROM sha256:<image ID> as a registry image name.
    # Resolve the retained local tag to the exact ID before and after building.
    dockerfile = 'FROM ' + OLD_TAG + '\n' + copies
    (context / 'Dockerfile').write_text(dockerfile)
    capture(['docker', 'build', '--network=none', '--pull=false', '-t', NEW_TAG, str(context)], timeout=900)
    candidate, old = image(NEW_TAG), read('image-before.private.json')
    require(image(OLD_TAG)['Id'] == old['Id'], 'Pinned base tag moved during build')
    require(candidate['Config'] == old['Config'], 'Image runtime configuration changed')
    base_layers = old['RootFS']['Layers']
    require(candidate['RootFS']['Layers'][:len(base_layers)] == base_layers,
            'Candidate is not derived from the pinned base')
    source_probe(candidate['Id'], before['new_sources'], image_id=True)
    override = json.loads((BACKUP / 'configuration/gcs.compose.yaml').read_text())
    override.setdefault('services', {}).setdefault('web', {})['image'] = NEW_TAG
    save('override-candidate.json', override)
    save('prepared.json', {'image': candidate['Id'], 'tag': NEW_TAG,
                           'base_image': old['Id'], 'dockerfile_sha256': sha(context / 'Dockerfile'),
                           'override_sha256': sha(BACKUP / 'override-candidate.json')})
    print(json.dumps({'prepared': True, 'image': candidate['Id'], 'changed_sources': 3}))


def prepare_retry():
    prepare(retry=True)


def verify_config(before, expected_override):
    actual = config_hashes()
    desired = dict(before['configuration'])
    desired['.local/compose/gcs.compose.yaml'] = expected_override
    require(actual == desired, 'Configuration changed outside web image override')


def validate(*, rollback=False):
    target()
    before, prepared = read('preflight.json'), read('prepared.json')
    state = containers()
    unchanged_others(before['runtime'], state)
    healthy(state)
    desired_image = before['runtime']['web']['image'] if rollback else prepared['image']
    require(state['web']['image'] == desired_image, 'Wrong running web image')
    expected_sources = before['old_sources'] if rollback else before['new_sources']
    require({n: sha(ROOT / n) for n in FILES} == expected_sources, 'Host source mismatch')
    source_probe(state['web']['id'], expected_sources)
    expected_override = (before['configuration']['.local/compose/gcs.compose.yaml'] if rollback
                         else prepared['override_sha256'])
    verify_config(before, expected_override)
    expected_compose = read('compose-before.private.json')
    if not rollback:
        expected_compose['services']['web']['image'] = NEW_TAG
    require(effective() == expected_compose, 'Effective configuration changed beyond web image')
    require(schema_version(state) == '20', 'Schema changed')
    local_storage()
    opener = build_opener(ProxyHandler({}))
    with opener.open('https://' + TARGET['ip'] + '/health/live', timeout=15) as response:
        require(response.status == 200, 'Public health failed')
        health = json.load(response)
        require(health.get('component') == 'red-house-web' and health.get('status') == 'alive',
                'Unexpected public web health')
    with opener.open('https://' + TARGET['ip'] + '/login', timeout=15) as response:
        require(response.status == 200 and response.geturl() == 'https://' + TARGET['ip'] + '/login',
                'Public login failed or redirected')
    report = {'status': 'passed', 'action': 'rollback' if rollback else 'publication',
              'target': TARGET, 'healthy': 30, 'other_containers_unchanged': 29,
              'image': desired_image, 'source_hashes': expected_sources, 'schema': 20,
              'base_image': prepared['base_image'], 'candidate_head': read('source.json')['head'],
              'image_runtime_configuration_preserved': True,
              'storage_provider': 'local', 'public_health': health,
              'tls': tls_evidence(),
              'private_document_flow': 'validated_locally_not_repeated_on_production'}
    save('rollback.json' if rollback else 'validation.json', report)
    print(json.dumps(report))


def rollback():
    target()
    before, prepared = read('preflight.json'), read('prepared.json')
    # Never restore databases, secrets or unrelated files; refuse unknown state.
    actual = config_hashes()
    require(actual.get('.local/compose/gcs.compose.yaml') in
            (before['configuration']['.local/compose/gcs.compose.yaml'], prepared['override_sha256']),
            'Unknown override: manual reconciliation required')
    verify_config(before, actual['.local/compose/gcs.compose.yaml'])
    unchanged_others(before['runtime'], containers(allow_missing_web=True))
    for name in FILES:
        safe_path(ROOT / name)
        require(sha(ROOT / name) in (before['old_sources'][name], before['new_sources'][name]),
                'Unknown source: manual reconciliation required')
        saved = BACKUP / 'sources' / name
        require(sha(saved) == before['old_sources'][name], 'Source backup changed')
        atomic(ROOT / name, saved.read_bytes(), saved.stat().st_mode & 0o777)
    saved_override = BACKUP / 'configuration/gcs.compose.yaml'
    require(sha(saved_override) == before['configuration']['.local/compose/gcs.compose.yaml'],
            'Override backup changed')
    old_tag = before['runtime']['web']['tag']
    require(image(old_tag)['Id'] == before['runtime']['web']['image'], 'Previous image tag moved')
    atomic(OVERRIDE, saved_override.read_bytes(), saved_override.stat().st_mode & 0o777)
    capture(compose() + ['up', '-d', '--no-deps', '--no-build', '--pull', 'never',
                         '--wait', '--wait-timeout', '180', 'web'], timeout=240)
    validate(rollback=True)


def release():
    target()
    before, prepared = read('preflight.json'), read('prepared.json')
    require(not (BACKUP / 'publication-intent.json').exists(), 'Publication already attempted; inspect first')
    require(containers() == before['runtime'] and config_hashes() == before['configuration'],
            'Runtime/configuration drift before release')
    require({n: sha(ROOT / n) for n in FILES} == before['old_sources'], 'Host source drift')
    require(payload() == before['new_sources'], 'Payload drift')
    require(image(NEW_TAG)['Id'] == prepared['image'], 'Candidate tag moved')
    require(sha(BACKUP / 'override-candidate.json') == prepared['override_sha256'], 'Override drift')
    require(schema_version(before['runtime']) == '20', 'Schema changed before release')
    save('publication-intent.json', {'target': TARGET, 'image': prepared['image'], 'scope': list(FILES)})
    try:
        for name in FILES:
            safe_path(ROOT / name)
            original = BACKUP / 'sources' / name
            atomic(ROOT / name, (INPUT / 'payload' / name).read_bytes(), original.stat().st_mode & 0o777)
        atomic(OVERRIDE, (BACKUP / 'override-candidate.json').read_bytes(), OVERRIDE.stat().st_mode & 0o777)
        desired = copy.deepcopy(read('compose-before.private.json'))
        desired['services']['web']['image'] = NEW_TAG
        require(effective() == desired, 'Unexpected compose mutation')
        capture(compose() + ['up', '-d', '--no-deps', '--no-build', '--pull', 'never',
                             '--wait', '--wait-timeout', '180', 'web'], timeout=240)
        validate()
    except BaseException:
        rollback()
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('preflight', 'prepare', 'prepare_retry', 'release', 'validate', 'rollback'))
    parser.add_argument('--package', type=Path, default=INPUT)
    args = parser.parse_args()
    os.umask(0o077)
    require(os.geteuid() == 0, 'Run on the verified VM with sudo')
    require(args.package in (INPUT, Path(str(INPUT) + '-retry')), 'Unexpected package directory')
    INPUT = args.package
    globals()[args.action]()
