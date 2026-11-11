"""Verificación de publicación: lectura, sin escribir objetos ni cortar servicios."""
import hashlib
import json
import subprocess
import tarfile
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('/opt/redhouse')
PRIVATE = ROOT / '.local/deploy-portal03-20261106'


def capture(args):
    return subprocess.check_output(args, cwd=ROOT, text=True).strip()


def main():
    deadline = time.monotonic() + 300
    while True:
        state = capture(['systemctl', 'show', 'redhouse', '-p', 'ActiveState', '--value'])
        if state == 'active':
            break
        assert state == 'activating' and time.monotonic() < deadline, state
        time.sleep(3)
    manifest = json.loads((PRIVATE / 'source-manifest.json').read_text())
    ids = capture(['docker', 'ps', '-q', '--filter',
                   'label=com.docker.compose.project=redhouse-parcial2']).split()
    containers = json.loads(capture(['docker', 'inspect', *ids]))
    assert len(containers) == 30
    result = {'at': datetime.now(timezone.utc).isoformat(), 'containers': [],
              'tag': 'portal03-20261106', 'schema': 17, 'image_sources': {}}
    for container in containers:
        name = container['Name'].lstrip('/')
        assert container['State']['Running'] and container['State']['Health']['Status'] == 'healthy', name
        result['containers'].append({'name': name, 'image': container['Image'], 'health': 'healthy'})
        if '/app/apps/' not in ' '.join(container['Config'].get('Entrypoint') or []):
            # Entry point is deployment/container.py; image tag identifies application images.
            if not container['Config']['Image'].endswith(':portal03-20261106'):
                continue
        service = container['Config']['Labels']['com.docker.compose.service']
        module = service.rsplit('-', 1)[0].replace('-', '_')
        own = 'servicio_monitoreo' if module == 'monitoreo' else 'ms_' + module
        prefixes = ['apps/services/redhouse/']
        prefixes += ['apps/web/', 'apps/services/'] if service == 'web' else ['apps/services/' + own + '/']
        paths = [p for p in manifest if any(p.startswith(prefix) for prefix in prefixes)]
        payload = json.dumps(paths)
        code = "import hashlib,json,sys; print(json.dumps({p:hashlib.sha256(open('/app/'+p,'rb').read()).hexdigest() for p in json.load(sys.stdin)}))"
        actual = json.loads(subprocess.check_output(['docker', 'exec', '-i', name,
                            'python', '-c', code], input=payload, text=True))
        assert all(actual[p] == manifest[p] for p in paths), name
        result['image_sources'][service] = len(paths)
    assert len(result['image_sources']) == 25
    assert capture(['systemctl', 'is-active', 'redhouse']) == 'active'
    assert capture(['systemctl', 'is-active', 'redhouse-certbot.timer']) == 'active'
    result['systemd'] = {'redhouse': 'active', 'redhouse-certbot.timer': 'active'}
    assert all(hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == h for p, h in manifest.items())
    result['host_manifest_matches'] = len(manifest)
    for service in ['compatibilidad-a', 'compatibilidad-b', 'web']:
        code = "import hashlib; print(hashlib.sha256(open('/run/hla-reference/3.66.0/Allelelist.txt','rb').read()).hexdigest())"
        assert capture(['docker', 'exec', 'redhouse-parcial2-' + service + '-1', 'python', '-c', code]) == '1913c5f748e6d649017996686e135dc6ffedc53215d4da7efad8f9165f3d2f35'
    result['hla_catalogue_matches'] = True
    web = json.loads((ROOT / '.local/compose/web.json').read_text())
    assert web['BACKEND_MODE'] == 'monolith'
    code = "import json; from pathlib import Path; from redhouse.config import SERVICES; w=json.loads(Path('/run/secrets/config').read_text()); c=w['DOMAIN_CONFIGS']; configs={n:json.loads((Path(c)/(n+'.json')).read_text()) for n in SERVICES} if isinstance(c,str) else c; assert set(configs)==set(SERVICES); print(len(configs))"
    owners = int(capture(['docker', 'exec', 'redhouse-parcial2-web-1', 'python', '-c', code]))
    assert owners == 12
    result['web_backend_mode'] = web['BACKEND_MODE']
    result['domain_owners'] = owners
    capture(['docker', 'exec', 'redhouse-parcial2-gateway-1', 'nginx', '-t'])
    result['nginx_config_valid'] = True
    for database in ['postgres', 'mongodb', 'redis']:
        container = next(c for c in containers if c['Config']['Labels']['com.docker.compose.service'] == database)
        assert not container['HostConfig'].get('PortBindings')
    result['database_ports_published'] = False
    result['result'] = 'passed'
    (PRIVATE / 'runtime-final.json').write_text(json.dumps(result, indent=2) + '\n')
    archive_path = Path('/tmp/redhouse-portal03-20261106/evidence.tar.gz')
    with tarfile.open(archive_path, 'w:gz') as archive:
        for name in ['backup-report.json', 'data-preservation.json',
                     'configuration-preservation.json', 'runtime-final.json', 'source-manifest.json']:
            archive.add(PRIVATE / name, arcname=name)
    archive_path.chmod(0o644)
    print(json.dumps({'result': 'passed', 'healthy_containers': 30,
                      'image_sources_checked': 25, 'host_sources': len(manifest),
                      'mode': 'monolith'}))


if __name__ == '__main__':
    main()
