"""Temporary OS Login access for the explicitly verified Red House VM."""
import json, os, subprocess
from pathlib import Path
OUT=Path(__file__).resolve().parent
GCLOUD='/Users/victorberlanga/Downloads/google-cloud-sdk/bin/gcloud'
PROJECT='sistemas-integracion-01'
def cloud(args):
    result=subprocess.run([GCLOUD,*args,'--project='+PROJECT,'--format=json'],capture_output=True,text=True,timeout=90)
    if result.returncode:
        (OUT/'access-command-error.private.log').write_text(result.stderr)
        raise RuntimeError('gcloud failed; private diagnostic retained')
    return json.loads(result.stdout)
if __name__=='__main__':
    os.umask(0o077); OUT.chmod(0o700)
    assert not (OUT/'ssh_key').exists() and not (OUT/'oslogin-before.private.json').exists()
    vm=cloud(['compute','instances','describe','red-house','--zone=me-central1-a'])
    assert str(vm['id'])=='2861822465669755197' and vm['name']=='red-house' and vm['status']=='RUNNING'
    assert vm['zone'].endswith('/zones/me-central1-a')
    interface=vm['networkInterfaces'][0]
    assert interface['networkIP']=='10.212.0.3' and interface['accessConfigs'][0]['natIP']=='34.18.186.116'
    (OUT/'target.json').write_text(json.dumps({'project':PROJECT,'instance':vm['name'],'id':vm['id'],'zone':'me-central1-a','private_ip':interface['networkIP'],'public_ip':interface['accessConfigs'][0]['natIP']},indent=2)+'\n')
    before=cloud(['compute','os-login','describe-profile'])
    (OUT/'oslogin-before.private.json').write_text(json.dumps(before,indent=2)+'\n')
    subprocess.run(['ssh-keygen','-q','-t','ed25519','-f',str(OUT/'ssh_key'),'-N','','-C','redhouse-clients-20261113'],check=True,capture_output=True)
    added=cloud(['compute','os-login','ssh-keys','add','--key-file='+str(OUT/'ssh_key.pub'),'--ttl=30m'])
    (OUT/'oslogin-add.private.json').write_text(json.dumps(added,indent=2)+'\n')
    after=cloud(['compute','os-login','describe-profile'])
    (OUT/'oslogin-active.private.json').write_text(json.dumps(after,indent=2)+'\n')
    old=before.get('sshPublicKeys',{}); new=after.get('sshPublicKeys',{}); keys=set(new)-set(old)
    assert len(keys)==1 and all(new[k]==v for k,v in old.items())
    accounts=after['posixAccounts']; username=next(a['username'] for a in accounts if a.get('primary',False))
    assert username=='victor_berlangam_gmail_com'
    (OUT/'access.json').write_text(json.dumps({'fingerprint':next(iter(keys)),'username':username,'previous_keys':len(old),'ttl':'30m'},indent=2)+'\n')
    print(json.dumps({'target_verified':True,'temporary_key_added':True,'previous_keys_preserved':len(old)}))
