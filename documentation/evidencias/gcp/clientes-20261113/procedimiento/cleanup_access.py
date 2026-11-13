import json,sys,subprocess
from pathlib import Path
from access import cloud,GCLOUD,PROJECT
OUT=Path(__file__).resolve().parent
record=json.loads((OUT/'access.json').read_text())
before=json.loads((OUT/'oslogin-before.private.json').read_text()).get('sshPublicKeys',{})
current=cloud(['compute','os-login','describe-profile']).get('sshPublicKeys',{})
fingerprint=record['fingerprint']
assert fingerprint not in before
if fingerprint in current:
    expected=(OUT/'ssh_key.pub').read_text().split()[:2]
    assert current[fingerprint]['key'].split()[:2]==expected
    removed=subprocess.run([GCLOUD,'compute','os-login','ssh-keys','remove','--key='+fingerprint,'--quiet','--project='+PROJECT],text=True,capture_output=True,timeout=90)
    assert removed.returncode==0, 'Temporary key removal failed'
after=cloud(['compute','os-login','describe-profile']).get('sshPublicKeys',{})
assert fingerprint not in after and all(after.get(k)==v for k,v in before.items())
for name in ('ssh_key','ssh_key.pub'):
    (OUT/name).unlink(missing_ok=True)
report={'temporary_key_removed':True,'prior_keys_preserved':len(before),'private_key_deleted':not (OUT/'ssh_key').exists()}
(OUT/'access-cleanup.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
