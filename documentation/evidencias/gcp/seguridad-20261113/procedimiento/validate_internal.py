"""Read checks on both deployed replicas while public HTTP writes are paused.

Input is the existing demonstration password over SSH stdin. It is never saved
on the VM, passed in process arguments, or included in output.
"""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path('/opt/redhouse')
BACKUP = ROOT / '.local/deploy-sec-20261113'
spec = importlib.util.spec_from_file_location('release', '/tmp/redhouse-sec-20261113/deploy.py')
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)

CHECK = r'''
import json,sys
import requests
credentials=json.load(sys.stdin)
session=requests.Session()
session.trust_env=False
session.headers['Accept']='application/json'
checks=[]

def call(base, method, path, expected=200, **kwargs):
    response=session.request(method,base+path,timeout=15,allow_redirects=False,**kwargs)
    checks.append({'check':base.split('//')[1].split(':')[0]+path,'http':response.status_code})
    assert response.status_code==expected
    return response

try:
    names='identidad-acceso donantes receptores inventario compatibilidad priorizacion-geografia transporte custodia alertas auditoria monitoreo documentos'.split()
    for name in names:
        for replica in ('a','b'):
            base='http://'+name+'-'+replica+'-private:8080'
            call(base,'GET','/health/ready')
    for replica in ('a','b'):
        base='http://identidad-acceso-'+replica+'-private:8080'
        payload=call(base,'POST','/api/v1/auth/login',json={'username':'operator1','password':credentials['password']}).json()['data']
        session.headers['Authorization']='Bearer '+payload['access_token']
        try:
            identity=call(base,'GET','/api/v1/auth/me').json()['data']
            assert identity['role']=='OPERATOR'
            call(base,'POST','/api/v1/auth/reauthenticate',expected=410,json={})
            response=call(base,'POST','/api/v1/auth/reauthentication-proofs',expected=403,json={'password':credentials['password'],'challenge':'A'*40})
            assert response.json()['error']['code']=='reauthentication_required'
            for owner in ('transporte','documentos','inventario'):
                target='http://'+owner+'-'+replica+'-private:8080'
                paths={'transporte':'/api/v1/shipments?page_size=1','inventario':'/api/v1/resources?page_size=1','documentos':'/api/v1/export-jobs?page_size=1'}
                call(target,'GET',paths[owner])
        finally:
            call(base,'POST','/api/v1/auth/revoke',json={'refresh_token':payload['refresh_token']})
            session.headers.pop('Authorization',None)
    print(json.dumps({'result':'passed','checks':checks,'business_writes':False,'transport':'private HTTP; public TLS checked separately'}))
except Exception as exc:
    print(json.dumps({'result':'failed','error_type':type(exc).__name__,'checks':checks}))
    sys.exit(1)
finally:
    session.close()
'''


if __name__ == '__main__':
    release.target()
    release.check_gate()
    assert release.containers() == release.read('runtime-final.json')
    credentials = json.load(sys.stdin)
    assert set(credentials) == {'password'}
    web = release.containers()['web']['id']
    result = subprocess.run(['docker','exec','-i',web,'python','-c',CHECK],
                            input=json.dumps(credentials),text=True,capture_output=True,timeout=180)
    try:
        report = json.loads(result.stdout)
    except (ValueError, TypeError):
        report = {'result':'failed','error_type':'InvalidValidationOutput'}
    release.save('internal-validation.json',report)
    print(json.dumps({'result':report['result'],'checks':len(report.get('checks',[]))}))
    if result.returncode or report['result'] != 'passed':
        sys.exit(1)
    release.check_gate()
    release.save('validation-approved.json',{'approved':True,'checks':len(report['checks']),
                 'scope':'both replicas ready, identity protocol, authorized reads; no critical business mutation',
                 'public_smoke_pending':True})
