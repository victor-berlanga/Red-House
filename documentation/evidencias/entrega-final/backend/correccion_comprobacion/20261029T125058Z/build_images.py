from pathlib import Path
import json,subprocess,os
c=json.loads(Path('compose.yaml').read_text())
targets=[n for n,v in c['services'].items() if 'build' in v and n!='mongodb']
r=Path('documentation/evidencias/entrega-final/backend/correccion_comprobacion/20261029T125058Z')
prior=[]
for n in targets:
 tag=c['services'][n].get('image','redhouse-parcial2-bootstrap:latest').replace('${REDHOUSE_TAG:-0.4.1}','0.4.1')
 result=subprocess.run(['docker','image','inspect',tag],capture_output=True,text=True)
 if result.returncode==0:
  old=json.loads(result.stdout)[0]['Id'];backup=tag.rsplit(':',1)[0]+':before-correction-20261029T125058Z'
  subprocess.run(['docker','tag',old,backup],check=True)
  prior.append({'tag':tag,'id':old,'preserved_as':backup})
if not (r/'imagenes-previas.json').exists():(r/'imagenes-previas.json').write_text(json.dumps(prior,indent=2)+'\n')
subprocess.run(['docker','compose','--profile','install','--parallel','1','--progress','plain','build',*targets],check=True,env={**os.environ,'REDHOUSE_TAG':'0.4.1'})
print('Imágenes construidas:',len(targets),flush=True)
