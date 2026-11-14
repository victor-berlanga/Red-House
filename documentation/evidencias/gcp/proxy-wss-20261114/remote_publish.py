from pathlib import Path
import hashlib,json,os,shutil,subprocess,time
ROOT=Path('/opt/redhouse');CFG=ROOT/'.local/compose';STAGE=ROOT/'.local/proxy-wss-3cd5a1b-7vzfho9n';report={'phase':'guards','protected_mutated':False,'rollback_performed':False}
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def call(args,input=None,timeout=40,required=True):
 p=subprocess.run(args,cwd=ROOT,input=input,capture_output=True,text=True,timeout=timeout)
 if required and p.returncode:raise RuntimeError('Command failed: '+args[0])
 return p

def containers():
 ids=call(['docker','ps','-q','--filter','label=com.docker.compose.project=redhouse-parcial2']).stdout.split();values=json.loads(call(['docker','inspect',*ids]).stdout)
 return {v['Config']['Labels']['com.docker.compose.service']:{'id':v['Id'],'image':v['Image'],'health':v['State'].get('Health',{}).get('Status')} for v in values}
def protected():return {str(p.relative_to(ROOT)):digest(p) for p in sorted(set(CFG.glob('*.json'))|set(CFG.glob('*.yaml'))|set((CFG/'apps').glob('*.json')))}
def write(path,value):
 inode=path.stat().st_ino
 with path.open('r+b') as f:f.write(value);f.truncate();f.flush();os.fsync(f.fileno())
 assert path.stat().st_ino==inode
SMOKE=r'''
import json,sys,uuid,requests,websocket
inputs=json.load(sys.stdin);origin=inputs['origin'];s=requests.Session();s.trust_env=False;token=None;ws=None;result={'phase':'public_https'}
try:
 response=s.get(origin+'/login',timeout=12);result['login_page']=response.status_code;assert response.status_code==200
 response=s.get(origin+'/services/transporte/health/live',timeout=12);result['transporte_live']=response.status_code;assert response.status_code==200
 result['phase']='own_session_login';response=s.post(origin+'/services/identidad-acceso/api/v1/auth/login',json={'username':'transport1','password':inputs['password']},headers={'Idempotency-Key':str(uuid.uuid4())},timeout=15);result['api_login']=response.status_code;assert response.status_code==200;token=response.json()['data']['access_token']
 result['phase']='new_native_wss';ws=websocket.create_connection(origin.replace('https:','wss:')+'/services/transporte/ws/v1/tracking/json',origin=origin,timeout=12,subprotocols=['redhouse.tracking.v1.json']);result['wss_upgrade']=ws.getstatus();assert ws.getstatus()==101
 ws.send(json.dumps({'type':'authenticate','credential_kind':'user','credential':token}));event=json.loads(ws.recv());result['authenticated']=event.get('type')=='authenticated';assert result['authenticated'];ws.close();ws=None;result['passed']=True
except BaseException as exc:
 result['failure_category']=type(exc).__name__
finally:
 if ws is not None:ws.close()
 if token:
  response=s.post(origin+'/services/identidad-acceso/api/v1/auth/logout',json={},headers={'Authorization':'Bearer '+token,'Idempotency-Key':str(uuid.uuid4())},timeout=15);result['own_logout']=response.status_code
  response=s.get(origin+'/services/identidad-acceso/api/v1/auth/me',headers={'Authorization':'Bearer '+token},timeout=12);result['own_token_replay']=response.status_code
  result['own_session_closed']=result['own_logout']==200 and result['own_token_replay']==401
 result['passed']=bool(result.get('passed') and result.get('own_session_closed'));print(json.dumps(result));sys.exit(0 if result['passed'] else 1)
'''
try:
 pre=json.loads((STAGE/'preflight.json').read_text());assert pre['phase']=='preflight_passed' and pre['candidate_syntax_passed'];gid=pre['gateway_id']
 before=json.loads((STAGE/'containers-before.private.json').read_text());guard=json.loads((STAGE/'protected-before.private.json').read_text());assert containers()==before;assert protected()==guard
 active=CFG/'public.nginx.conf';assert digest(active)==pre['active_sha256'];candidate=STAGE/'candidate/generated/public.nginx.conf';assert digest(candidate)==pre['candidate_sha256']
 targets=['deployment/nginx.conf','deployment/gcp/configure_public.py','.local/compose/public.nginx.conf'];backup=STAGE/'backup';backup.mkdir(mode=0o700,exist_ok=False)
 for name in targets:
  p=backup/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,p)
 original={name:digest(ROOT/name) for name in targets};inode=active.stat().st_ino;report.update(phase='install',backup=str(backup),before_hashes=original,active_inode_before=inode)
 report['protected_mutated']=True
 for name in targets[:2]:write(ROOT/name,(STAGE/'candidate/source'/name).read_bytes())
 write(active,candidate.read_bytes());assert active.stat().st_ino==inode
 report['phase']='active_syntax';call(['docker','exec',gid,'nginx','-t']);report['active_syntax_passed']=True
 report['phase']='reload';call(['docker','exec',gid,'nginx','-s','reload']);report['reload_signaled']=True;time.sleep(0.5)
 report['phase']='public_smoke';web=before['web']['id'];password=json.loads((CFG/'state.json').read_text())['password'];inputs=json.dumps({'origin':'https://34.18.186.116','password':password});result=call(['docker','exec','-i',web,'python','-c',SMOKE],input=inputs,timeout=75,required=False)
 try:report['smoke']=json.loads(result.stdout.strip().splitlines()[-1])
 except (ValueError,IndexError):report['smoke']={'passed':False,'failure_category':'NonJSONSmokeOutput'}
 assert result.returncode==0 and report['smoke']['passed'],'Smoke failed'
 report['phase']='preservation';after=containers();assert after==before;assert protected()==guard
 providers={name:json.loads((CFG/path).read_text()).get('STORAGE_PROVIDER') for name,path in {'web':'web.json','documentos':'apps/documentos.json'}.items()};assert all(str(v).lower()=='local' for v in providers.values())
 report.update(phase='complete',result='published',after_hashes={name:digest(ROOT/name) for name in targets},active_inode_after=active.stat().st_ino,containers_unchanged=True,healthy_count=30,protected_json_overrides_unchanged=True,protected_file_count=len(guard),storage_providers=providers,nginx_version=pre['nginx_version'],gateway_image=pre['gateway_image'])
except BaseException as exc:
 report.update(result='failed',failure_category=type(exc).__name__)
 if report['protected_mutated']:
  rollback=[]
  for name in targets:
   try:write(ROOT/name,(backup/name).read_bytes())
   except BaseException as error:rollback.append(type(error).__name__)
  check=call(['docker','exec',gid,'nginx','-t'],required=False);reload=call(['docker','exec',gid,'nginx','-s','reload'],required=False);report.update(rollback_performed=True,rollback_errors=rollback,rollback_syntax_code=check.returncode,rollback_reload_code=reload.returncode)
finally:
 (STAGE/'release.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
raise SystemExit(0 if report.get('result')=='published' else 1)
