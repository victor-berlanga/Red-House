"""Keep remote credentials on the VM; export only explicit verification artifacts."""
import json,subprocess,tarfile
from pathlib import Path
root=Path('/opt/redhouse');private=root/'.local/deploy-mobile04-20261110';inputs=Path('/tmp/redhouse-mobile04-20261110')
if not (private/'runtime-final.json').exists():
    subprocess.run(['python3',str(inputs/'verify_remote.py')],check=True)
if (private/'mobile-http.json').exists() and not (private/'mobile-http-first.json').exists():
    (private/'mobile-http-first.json').write_bytes((private/'mobile-http.json').read_bytes())
state=json.loads((root/'.local/compose/state.json').read_text())
result=subprocess.run(['docker','exec','-i','redhouse-parcial2-web-1','python','-c',(inputs/'verify_mobile.py').read_text()],input=json.dumps({'password':state['password']}),text=True,capture_output=True)
(private/'mobile-http.json').write_text(result.stdout)
if result.returncode:
    (private/'mobile-verification-error.txt').write_text(result.stderr)
    raise SystemExit('MOBILE_CHECK_FAILED; diagnostics remain private on VM')
with tarfile.open(inputs/'evidence.tar.gz','w:gz') as archive:
    for name in ['backup-report.json','data-preservation.json','configuration-preservation.json','runtime-final.json','source-manifest.json','mobile-http.json','mobile-http-first.json']:
        archive.add(private/name,arcname=name)
(inputs/'evidence.tar.gz').chmod(0o644)
print('MOBILE_HTTPS_WSS_AND_RUNTIME_PASS')
