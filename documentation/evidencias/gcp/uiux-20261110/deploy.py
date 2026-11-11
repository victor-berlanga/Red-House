"""Nine-file UI deployment; no migrations, credentials changes or store restarts."""
import hashlib,json,os,shutil,subprocess,sys,tarfile
from pathlib import Path
ROOT=Path('/opt/redhouse'); INPUT=Path('/tmp/redhouse-uiux-20261110'); BACKUP=ROOT/'.local/deploy-uiux-20261110'; CFG=ROOT/'.local/compose'; TAG='redhouse/web:uiux-20261110'
def run(args):subprocess.run(args,cwd=ROOT,check=True)
def capture(args):return subprocess.check_output(args,cwd=ROOT,text=True).strip()
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(name,value):(BACKUP/name).write_text(json.dumps(value,indent=2)+'\n')
def compose():return ['docker','compose','-f',str(ROOT/'compose.yaml'),'-f',str(CFG/'gcs.compose.yaml'),'-f',str(CFG/'public.compose.yaml')]
def containers():
 ids=capture(['docker','ps','-aq','--filter','label=com.docker.compose.project=redhouse-parcial2']).split()
 return {v['Name'].lstrip('/'):{'id':v['Id'],'image':v['Image'],'health':v['State'].get('Health',{}).get('Status'),'running':v['State']['Running']} for v in json.loads(capture(['docker','inspect',*ids]))}
def rollback():
 before=json.loads((BACKUP/'runtime-before.json').read_text())
 for name in json.loads((INPUT/'manifest.json').read_text()):shutil.copy2(BACKUP/'sources'/name,ROOT/name)
 shutil.copy2(BACKUP/'gcs.compose.yaml',CFG/'gcs.compose.yaml')
 run(compose()+['up','-d','--no-deps','--no-build','--wait','--wait-timeout','180','web'])
 assert containers()['redhouse-parcial2-web-1']['image']==before['redhouse-parcial2-web-1']['image']
 print('Rollback verified')
def main():
 assert os.geteuid()==0
 if sys.argv[1]=='rollback':rollback();return
 manifest=json.loads((INPUT/'manifest.json').read_text());expected=json.loads((INPUT/'expected-before.json').read_text())
 assert len(manifest)==9 and set(manifest)==set(expected)
 for name,sha in expected.items():
  assert name.startswith('apps/web/src/presentation/') and '..' not in Path(name).parts
  assert digest(ROOT/name)==sha,'Unexpected remote source: '+name
 before=containers();assert sum(v['running'] for v in before.values())==30 and all(v['health']=='healthy' for v in before.values() if v['running'])
 BACKUP.mkdir(mode=0o700,exist_ok=False)
 save('runtime-before.json',before)
 for name in manifest:
  dest=BACKUP/'sources'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,dest)
 shutil.copy2(CFG/'gcs.compose.yaml',BACKUP/'gcs.compose.yaml')
 old=before['redhouse-parcial2-web-1']['image'];run(['docker','tag',old,'redhouse/web:uiux-before-20261110'])
 build=BACKUP/'build';build.mkdir()
 with tarfile.open(INPUT/'presentation.tar.gz') as tar:
  members=tar.getmembers();assert {m.name for m in members}==set(manifest)
  for m in members:
   assert m.isfile();data=tar.extractfile(m).read();assert hashlib.sha256(data).hexdigest()==manifest[m.name]
   p=build/'payload'/m.name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);p.chmod(0o644)
 (build/'Dockerfile').write_text('FROM redhouse/web:uiux-before-20261110\nCOPY payload/ /app/\n')
 run(['docker','build','--network=none','-t',TAG,str(build)])
 # Check exact files in the built image before replacing the running service.
 check='import hashlib,json;from pathlib import Path;expected='+repr(manifest)+';assert all(hashlib.sha256((Path("/app")/n).read_bytes()).hexdigest()==h for n,h in expected.items());print("Image payload verified")'
 run(['docker','run','--rm','--network=none','--entrypoint','python',TAG,'-c',check])
 original=json.loads((CFG/'gcs.compose.yaml').read_text());updated=json.loads(json.dumps(original));updated.setdefault('services',{}).setdefault('web',{})['image']=TAG
 try:
  for name in manifest:shutil.copy2(build/'payload'/name,ROOT/name)
  (CFG/'gcs.compose.yaml').write_text(json.dumps(updated,indent=2)+'\n')
  run(compose()+['config','--quiet'])
  run(compose()+['up','-d','--no-deps','--no-build','--wait','--wait-timeout','180','web'])
  after=containers();assert all(after[n]['id']==v['id'] and after[n]['image']==v['image'] and after[n]['running']==v['running'] for n,v in before.items() if n!='redhouse-parcial2-web-1')
  assert all(v['health']=='healthy' for v in after.values() if v['running'])
  save('runtime-after.json',after);save('manifest.json',manifest)
  save('result.json',{'tag':TAG,'files':len(manifest),'containers':sum(v['running'] for v in after.values()),'unchanged_other_containers':29,'healthy':True,'database_migrations':False,'backup':str(BACKUP),'old_image':old,'new_image':after['redhouse-parcial2-web-1']['image']})
  print((BACKUP/'result.json').read_text())
 except BaseException:
  rollback();raise
if __name__=='__main__':main()
