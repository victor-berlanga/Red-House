import hashlib,json,subprocess
from pathlib import Path
from datetime import datetime,timezone
r=Path('documentation/evidencias/entrega-final/backend/correccion_comprobacion/20261029T125058Z')
initial=json.loads((r/'fuentes-iniciales.json').read_text())
paths=subprocess.check_output(['git','ls-files','-co','--exclude-standard','-z']).decode().split('\0')
files={}
for name in sorted(set(paths)):
 p=Path(name)
 if not name or not p.is_file() or name.startswith('documentation/evidencias/') or name.endswith(('.pyc','.png','.jpg','.jpeg','.zip','.gz')):continue
 files[name]=hashlib.sha256(p.read_bytes()).hexdigest()
value={'fecha':datetime.now(timezone.utc).isoformat(),'commit':subprocess.check_output(['git','rev-parse','HEAD']).decode().strip(),'version':'0.4.1','schema':13,'files':files,'sha256':hashlib.sha256(json.dumps(files,sort_keys=True).encode()).hexdigest(),'note':'Hash de fuentes actuales; evidencias se manifiestan por separado. No incluye secretos ignorados, cachés ni instalaciones locales.'}
(r/'fuentes-finales.json').write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
print(len(files),value['sha256'])
