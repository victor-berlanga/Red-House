from pathlib import Path
import json,subprocess,hashlib
r=Path('documentation/evidencias/entrega-final/backend/correccion_comprobacion/20261029T125058Z')
c=json.loads(Path('compose.yaml').read_text());rows=[]
program='''import importlib,json,sys,pathlib,os
from redhouse import VERSION
service=sys.argv[1]
module='servicio_monitoreo' if service=='monitoreo' else 'ms_'+service
app=importlib.import_module(module).create_app({'DATABASE_URL':'unused','JWT_PUBLIC_KEY':'unused','JWT_PRIVATE_KEY':'unused'})
client=app.test_client();o=client.get('/openapi.json');h=client.get('/health/live')
assert VERSION=='0.4.1' and o.status_code==200 and h.status_code==200
other=[p.name for p in pathlib.Path('/app/apps/services').iterdir() if (p.name.startswith('ms_') or p.name=='servicio_monitoreo') and p.name!=module]
assert not other,other
assert os.getuid()==10001
print(json.dumps({'version':VERSION,'openapi_paths':len(o.json['paths']),'live':h.status_code,'uid':os.getuid(),'other_domain_packages':other}))
'''
for name,v in c['services'].items():
 if 'build' not in v or name=='mongodb':continue
 tag=v.get('image','redhouse-parcial2-bootstrap').replace('${REDHOUSE_TAG:-0.4.1}','0.4.1')
 inspect=json.loads(subprocess.check_output(['docker','image','inspect',tag],text=True))[0]
 row={'compose_service':name,'tag':tag,'id':inspect['Id'],'created':inspect['Created'],'size':inspect['Size']}
 if name.endswith('-a'):
  service=tag.split('/')[1].split(':')[0]
  result=subprocess.run(['docker','run','--rm','--network','none','--entrypoint','python',tag,'-c',program,service],capture_output=True,text=True,timeout=90)
  assert result.returncode==0,(name,result.stderr[-2000:])
  row['smoke']=json.loads(result.stdout)
 else:
  result=subprocess.run(['docker','run','--rm','--network','none','--entrypoint','python',tag,'-c',"from redhouse import VERSION; assert VERSION=='0.4.1'; print(VERSION)"],capture_output=True,text=True,timeout=90)
  assert result.returncode==0,(name,result.stderr[-2000:]);row['embedded_version']=result.stdout.strip()
 hash_program="import pathlib,hashlib,json; root=pathlib.Path('/app'); print(json.dumps({str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file() and p.suffix in ('.py','.json','.xsd','.toml','.js','.css','.html','.txt','.sql','.yaml')}))"
 file_hashes=json.loads(subprocess.check_output(['docker','run','--rm','--network','none','--entrypoint','python',tag,'-c',hash_program],text=True,timeout=90))
 for path,digest in file_hashes.items():
  assert Path(path).exists() and hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest,(name,path,'fuente no coincide')
 row['source_files_verified']=len(file_hashes);row['source_files']=file_hashes
 rows.append(row);print(name,row['id'][:19],flush=True)
 (r/'imagenes.json').write_text(json.dumps({'version':'0.4.1','network':'none','images':rows,'scope':'Construcción e inicio aislado de cada paquete; liveness/OpenAPI sin almacenes. No acredita readiness, carga ni despliegue productivo.'},indent=2,ensure_ascii=False)+'\n')
