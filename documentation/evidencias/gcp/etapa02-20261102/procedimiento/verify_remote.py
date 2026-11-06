import hashlib,json,subprocess,tarfile
from pathlib import Path
root=Path('/opt/redhouse');private=root/'.local/deploy-20261102'
def capture(args):return subprocess.check_output(args,cwd=root,text=True)
ids=capture(['docker','ps','-q','--filter','label=com.docker.compose.project=redhouse-parcial2']).split()
containers=json.loads(capture(['docker','inspect',*ids]));assert len(containers)==30
result={'containers':[],'version':'0.4.4'}
for c in containers:
 assert c['State']['Running'] and c['State']['Health']['Status']=='healthy',c['Name']
 result['containers'].append({'name':c['Name'],'image':c['Image'],'health':'healthy'})
assert capture(['systemctl','is-active','redhouse']).strip()=='active'
assert capture(['systemctl','is-active','redhouse-certbot.timer']).strip()=='active'
manifest=json.loads((private/'source-manifest-final.json').read_text())
assert all(hashlib.sha256((root/k).read_bytes()).hexdigest()==v for k,v in manifest.items())
result['host_manifest_matches']=len(manifest)
checks={'compatibilidad-a':['apps/services/ms_compatibilidad/reference_catalogue.py','apps/services/ms_compatibilidad/laboratory.py'],'compatibilidad-b':['apps/services/ms_compatibilidad/rules.py'],'priorizacion-geografia-a':['apps/services/ms_priorizacion_geografia/road_sources.py'],'priorizacion-geografia-b':['apps/services/ms_priorizacion_geografia/decisions.py'],'web':['apps/web/src/integration/presentation.py','apps/web/src/integration/routes/decision_support.py','apps/services/ms_compatibilidad/reference_catalogue.py']}
for service,paths in checks.items():
 code="import hashlib,json; print(json.dumps({p:hashlib.sha256(open('/app/'+p,'rb').read()).hexdigest() for p in "+repr(paths)+"}))"
 hashes=json.loads(capture(['docker','exec','redhouse-parcial2-'+service+'-1','python','-c',code]));assert all(hashes[p]==manifest[p] for p in paths)
result['image_sources_match']=True
for service in ['compatibilidad-a','compatibilidad-b','web']:
 code="import hashlib; print(hashlib.sha256(open('/run/hla-reference/3.66.0/Allelelist.txt','rb').read()).hexdigest())"
 assert capture(['docker','exec','redhouse-parcial2-'+service+'-1','python','-c',code]).strip()=='1913c5f748e6d649017996686e135dc6ffedc53215d4da7efad8f9165f3d2f35'
result['hla_catalogue_matches']=True
(private/'runtime-final.json').write_text(json.dumps(result,indent=2)+'\n')
source=(root/'deployment/gcp/check_storage.py').read_text().replace('ROOT = Path(__file__).resolve().parents[2]',"ROOT = Path('/app')")
proc=subprocess.run(['docker','exec','redhouse-parcial2-web-1','python','-c',source],cwd=root,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
if proc.returncode:
 (private/'gcs-error-private.log').write_text(proc.stderr)
 raise RuntimeError('GCS verification failed; private diagnostic retained on server')
gcs=json.loads(proc.stdout);assert gcs['result']=='passed';(private/'gcs-final.json').write_text(json.dumps(gcs,indent=2)+'\n')
with tarfile.open('/tmp/redhouse-stage02-evidence.tar.gz','w:gz') as archive:
 for name in ['backup-report.json','data-preservation.json','data-before.json','data-after.json','runtime-settings.json','runtime-final.json','gcs-final.json','source-manifest.json','source-manifest-final.json','deployment-delta.json']:
  archive.add(private/name,arcname=name)
Path('/tmp/redhouse-stage02-evidence.tar.gz').chmod(0o644)
print(json.dumps({'healthy_containers':30,'host_sources':len(manifest),'image_sources_match':True,'hla_catalogue_matches':True,'gcs':'passed'}))
