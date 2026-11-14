"""Collect only allowlisted deployment metadata, without private configuration."""
import json
import subprocess
from pathlib import Path

HERE=Path(__file__).resolve().parent
PROGRAM=r'''
import importlib.util,json,time
spec=importlib.util.spec_from_file_location('release','/tmp/redhouse-scanner20-20261113/deploy.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
r.target()
names=['source.json','manifest.json','preflight.json','backup-complete.json','builds.json',
       'prepared.json','database-backup.json','runtime-final.json','publication.json',
       'internal-validation.json','validation-approved.json','writes-opened.json',
       'rehearsal.json','rehearsal-cleanup.json','migration.json','scanner-before.json',
       'scanner-validation.json','historical-backup-references.json',
       'scanner-alignment.json','scanner-alignment-final.json','host-payload-update.json']
result={n:r.read(n) for n in names}
state=r.containers()
assert state==r.read('runtime-final.json')
assert all(v['health']=='healthy' for v in state.values())
assert r.storage()==r.read('publication.json')['storage_after']
nginx=(r.CFG/'public.nginx.conf').read_text()
assert r.digest(r.CFG/'public.nginx.conf')==r.read('preflight.json')['configuration']['public.nginx.conf']
assert 'X-RedHouse-Maintenance' not in nginx
assert '/storage/v1/objects/' in nginx and '/portal-storage/v1/objects/' in nginx
assert not (r.BACKUP/'gate-state.json').exists()
result['post-public-check.json']={'at':time.time(),'healthy':len(state),'storage':r.storage(),
    'maintenance_removed':True,'proxy_original_hash_restored':True,'separate_routes_present':True,
    'inventory_operation_delete_allowed':r.sql("SELECT has_table_privilege('rh_inventario','access_inventario.operations','DELETE');")=='t'}
print(json.dumps(result))
'''
command=['ssh','-i',str(HERE/'ssh_key'),'-o','IdentitiesOnly=yes',
         '-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','UpdateHostKeys=no','-o','UserKnownHostsFile=/Users/victorberlanga/.ssh/google_compute_known_hosts',
         '-o','HostKeyAlias=compute.2861822465669755197',
         'victor_berlangam_gmail_com@34.18.186.116','sudo python3 -']
process=subprocess.run(command,input=PROGRAM,text=True,capture_output=True,timeout=180)
if process.returncode:
    (HERE/'collect-error.log').write_text(process.stderr)
    raise SystemExit('Metadata verification failed; private log saved.')
result=json.loads(process.stdout)
for name,value in result.items():
    (HERE/name).write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps({'metadata_files':len(result),'final':result['post-public-check.json']}))
