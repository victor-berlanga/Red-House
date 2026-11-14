import json
from datetime import datetime, timezone
from pathlib import Path
import sys

sys.path.insert(0, '/opt/redhouse/.local/deploy-scanner20-20261113')
import release_base as base

base.target()
directory = base.ROOT / '.local/deploy-scanner-health-20261113'
before = json.loads((directory / 'preflight.json').read_text())
validation = json.loads((directory / 'validation.json').read_text())
current = base.containers()
assert len(current) == 30 and all(v['running'] and v['health'] == 'healthy' for v in current.values())
assert all(current[name] == before['runtime'][name] for name in current if name != 'clamav')
assert current['clamav']['id'] != before['runtime']['clamav']['id']
assert current['clamav']['image'] == before['runtime']['clamav']['image']
details = json.loads(base.capture(['docker', 'inspect', current['clamav']['id']]))[0]
health = details['State']['Health']
entries = [{'start': e['Start'], 'end': e['End'], 'exit_code': e['ExitCode']} for e in health['Log'] if e['ExitCode'] == 0 and e['Output'].strip() == 'healthy: signatures current']
assert len(entries) >= 2
assert base.digest(base.CFG / 'apps/documentos.json') == before['document_sha256']
sources = {name: base.digest(base.ROOT / name) for name in before['sources']}
assert all(sources[name] == before['sources'][name]['new'] for name in sources)
print(json.dumps({
    'verified_at': datetime.now(timezone.utc).isoformat(),
    'target': {'project': 'sistemas-integracion-01', 'instance': 'red-house', 'zone': 'me-central1-a', 'instance_id': '2861822465669755197'},
    'healthy_containers': 30, 'other_containers_unchanged': 29,
    'clamav_recreated': True, 'image_unchanged': True,
    'readiness_executions': entries,
    'document_config_unchanged': True, 'source_sha256': sources,
    'validation': validation,
}, indent=2))
