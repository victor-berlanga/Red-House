import json, subprocess, sys
from pathlib import Path
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
password=json.loads((ROOT/'.local/password-maintenance-20261111/remote-input.json').read_text())['password']
cmd=['ssh','-i',str(OUT/'ssh_key'),'-o','IdentitiesOnly=yes','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','UpdateHostKeys=no','-o','HostKeyAlias=compute.2861822465669755197','-o','UserKnownHostsFile=/Users/victorberlanga/.ssh/google_compute_known_hosts','victor_berlangam_gmail_com@34.18.186.116','sudo -n python3 /tmp/redhouse-clientes-20261113/validate_internal.py']
r=subprocess.run(cmd,input=json.dumps({'password':password}),text=True,capture_output=True,timeout=300)
(OUT/'internal-command.log').write_text(r.stdout+r.stderr)
print('validation_exit',r.returncode)
print(r.stdout)
sys.exit(r.returncode)
