from pathlib import Path
import json,xml.etree.ElementTree as ET
from datetime import datetime,timezone
r=Path('documentation/evidencias/entrega-final/backend/correccion_comprobacion/20261029T125058Z')
selected=['regresion-21.xml','limites-22.xml','focalizadas-23.xml']
# Añadir la ejecución operativa aprobada y repeticiones posteriores al confirmar sus resultados.
extra=r/'selected-final-reports.json'
if extra.exists(): selected+=json.loads(extra.read_text())
latest={}
for name in selected:
 p=r/name
 if not p.exists():continue
 for case in ET.parse(p).iter('testcase'):
  identity=case.get('classname')+'::'+case.get('name')
  status='failed' if case.find('failure') is not None or case.find('error') is not None else 'skipped' if case.find('skipped') is not None else 'passed'
  latest[identity]={'id':identity,'status':status,'evidence':name,'seconds':float(case.get('time','0'))}
expected={s.split('::',1)[0][:-3].replace('/','.')+'::'+s.strip().split('::',1)[1] for s in (r/'collected-final.txt').read_text().splitlines() if s.startswith('tests/')}
assert not (set(latest)-expected),set(latest)-expected
value={'date':datetime.now(timezone.utc).isoformat(),'version':'0.4.1','schema':13,'selected_reports':selected,'expected':len(expected),'passed':sum(x['status']=='passed' for x in latest.values()),'failed':[x for x in latest.values() if x['status']=='failed'],'skipped':[x for x in latest.values() if x['status']=='skipped'],'pending':sorted(expected-set(latest)),'cases':list(latest.values()),'note':'Último resultado por classname::name. Conserva fallos anteriores; no suma ejecuciones superpuestas. Producción e independencia de auditoría no se infieren de estas pruebas.'}
(r/'consolidado.json').write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')
print({k:v for k,v in value.items() if k not in ('cases','note','date','selected_reports')})
