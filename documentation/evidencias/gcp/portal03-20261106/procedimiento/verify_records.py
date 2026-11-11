"""Corrobora por SQL de lectura los registros ficticios creados desde Chrome."""
import json
import sys
from pathlib import Path
from uuid import UUID
from deploy import sql

report = json.loads(Path(sys.argv[1]).read_text())
assert report['passed']
campaign = str(UUID(report['records']['campaign']))
device = str(UUID(report['records']['device']))
result = sql("SELECT json_build_object('campaign_rows',(SELECT count(*) FROM red_house.campaign WHERE campaign_id='" + campaign + "'),"
             "'publication',(SELECT json_build_object('version',version,'published',published) FROM red_house.campaign_publications WHERE id='" + campaign + "'),"
             "'slots',(SELECT count(*) FROM red_house.campaign_slots WHERE campaign_id='" + campaign + "'),"
             "'device_active',(SELECT active FROM red_house.devices WHERE id='" + device + "'),"
             "'assignments',(SELECT count(*) FROM red_house.tracking_assignments WHERE device_id='" + device + "'))")
assert result == {'campaign_rows': 1, 'publication': {'version': 1, 'published': False},
                  'slots': 1, 'device_active': False, 'assignments': 1}, result
result.update(campaign=campaign, device=device, result='passed', source='PostgreSQL remoto; lectura posterior al navegador')
Path('/tmp/redhouse-portal03-20261106/persistence.json').write_text(json.dumps(result, indent=2) + '\n')
Path('/tmp/redhouse-portal03-20261106/persistence.json').chmod(0o644)
print(json.dumps(result))
