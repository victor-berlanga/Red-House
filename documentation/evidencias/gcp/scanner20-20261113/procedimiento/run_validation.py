import base64,hashlib,hmac,json,struct,subprocess,sys,time
from pathlib import Path
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
password=json.loads((ROOT/'.local/password-maintenance-20261111/remote-input.json').read_text())['password']
factor=json.loads((ROOT/'.local/gcp-update-20261031/demo-checkpoint.json').read_text())['factors']['admin1']
assert factor['confirmed']
def otp(counter):
    raw=hmac.new(base64.b32decode(factor['secret']),struct.pack('>Q',counter),hashlib.sha1).digest()
    index=raw[-1]&15
    return str((struct.unpack('>I',raw[index:index+4])[0]&0x7fffffff)%1000000).zfill(6)
counter=int(time.time())//30
codes=[{'counter':counter+n,'code':otp(counter+n)} for n in (1,2)]
cmd=['ssh','-i',str(OUT/'ssh_key'),'-o','IdentitiesOnly=yes','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','UpdateHostKeys=no','-o','HostKeyAlias=compute.2861822465669755197','-o','UserKnownHostsFile=/Users/victorberlanga/.ssh/google_compute_known_hosts','victor_berlangam_gmail_com@34.18.186.116','sudo -n python3 /tmp/redhouse-scanner20-20261113/validate_internal.py']
r=subprocess.run(cmd,input=json.dumps({'password':password,'admin_otp':codes}),text=True,capture_output=True,timeout=300)
(OUT/'internal-command.log').write_text(r.stdout+r.stderr)
print('validation_exit',r.returncode)
print(r.stdout)
sys.exit(r.returncode)
