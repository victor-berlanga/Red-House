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
BACKUP = ROOT / '.local/deploy-scanner20-20261113'
spec = importlib.util.spec_from_file_location('release', '/tmp/redhouse-scanner20-20261113/deploy.py')
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)

CHECK = r'''
import json,sys,time
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
    from lxml import etree
    def parse_xml(raw):
        assert len(raw)<=1048576
        root=etree.fromstring(raw,etree.XMLParser(resolve_entities=False,load_dtd=False,no_network=True))
        assert root.tag=='response' and not root.getroottree().docinfo.doctype
        def value(node):
            kind=node.get('type')
            if kind=='object': return {item.get('name'):value(item) for item in node}
            if kind=='array': return [value(item) for item in node]
            if kind=='integer': return int(node.text)
            if kind=='string': return node.text or ''
            if kind=='null': return None
            if kind=='boolean': return node.text=='true'
            raise AssertionError('Unexpected XML type')
        return value(root)
    public_fields={'title','starts_at','ends_at','venue','information'}
    for replica in ('a','b'):
        donor='http://donantes-'+replica+'-private:8080'
        spec=call(donor,'GET','/openapi.json').json()
        assert 'patch' in spec['paths']['/api/v1/donors/{identifier}/personal']
        for mime in ('application/json','application/xml'):
            response=call(donor,'GET','/api/v1/public/campaign-feed?page_size=20',headers={'Accept':mime})
            payload=response.json() if mime=='application/json' else parse_xml(response.content)
            page=payload['data']
            assert set(page)=={'items','page','page_size','total'}
            assert page['page']==1 and page['page_size']==20 and len(page['items'])<=20
            assert all(set(item)==public_fields for item in page['items'])
        call(donor,'GET','/api/v1/public/campaign-feed?q=%00',expected=400)
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
    for replica in ('a','b'):
        base='http://identidad-acceso-'+replica+'-private:8080'
        otp=credentials['admin_otp'][0 if replica=='a' else 1]
        wait=otp['counter']*30+2-time.time()
        assert wait<=65 and wait>-25, 'OTP preparation expired; no login attempted'
        if wait>0: time.sleep(wait)
        payload=call(base,'POST','/api/v1/auth/login',json={'username':'admin1','password':credentials['password'],'otp':otp['code']}).json()['data']
        session.headers['Authorization']='Bearer '+payload['access_token']
        try:
            spec=call(base,'GET','/openapi.json').json()
            assert 'get' in spec['paths']['/api/v1/user-creation-receipt']
            call(base,'GET','/api/v1/user-creation-receipt',expected=400)
            for mime in ('application/json','application/xml'):
                response=call(base,'GET','/api/v1/devices?q=release-scanner20-no-such-device-20261113&page_size=1',headers={'Accept':mime})
                data=(response.json() if mime=='application/json' else parse_xml(response.content))['data']
                assert data['items']==[] and data['total']==0
                call(base,'GET','/api/v1/user-creation-receipt',expected=404,headers={'Accept':mime,'Idempotency-Key':'release-scanner20-no-such-command-20261113'})
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


SCANNER = r'''
import json,sys
from pathlib import Path
sys.path.insert(0,'/app/apps/services')
from flask import Flask
from redhouse.malware import scan
config=json.loads(Path('/run/secrets/config').read_text())
app=Flask('scanner-release-probe')
app.config.update({k:config[k] for k in ('CLAMD_HOST','CLAMD_PORT','CLAMD_VERSION_TIMEZONE','CLAMD_SIGNATURE_MAX_AGE_SECONDS')})
assert app.config['CLAMD_VERSION_TIMEZONE']=='UTC'
assert app.config['CLAMD_SIGNATURE_MAX_AGE_SECONDS']==172800
with app.app_context():
    clean=scan(b'Red House synthetic scanner release check\n')
    infected=scan(br'X5O!P%@AP[4\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*')
    assert clean=='CLEAN' and infected=='INFECTED'
    assert clean.metadata==infected.metadata
    print(json.dumps({'result':'passed','clean':str(clean),'eicar':str(infected),
          'engine':clean.metadata['engine_version'],'signatures':clean.metadata['signature_version'],
          'signature_at':clean.metadata['signature_at'].isoformat(),'max_age_seconds':172800,
          'bytes_only_no_database_or_object_writes':True}))
'''


if __name__ == '__main__':
    release.target()
    release.check_gate()
    assert release.containers() == release.read('runtime-final.json')
    credentials = json.load(sys.stdin)
    assert set(credentials) == {'password','admin_otp'}
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
    scanner_checks = []
    runtime = release.containers()
    daemon = json.loads(release.capture(['docker','inspect',runtime['clamav']['id']]))[0]
    assert 'TZ=UTC' in daemon['Config']['Env']
    for replica in ('a','b'):
        name = 'documentos-' + replica
        checked = subprocess.run(['docker','exec',runtime[name]['id'],'python','-c',SCANNER],
                                 text=True,capture_output=True,timeout=90)
        try:
            scanner = json.loads(checked.stdout)
        except (ValueError,TypeError):
            scanner = {'result':'failed','error_type':'InvalidScannerOutput'}
        scanner_checks.append(dict(scanner,replica=replica))
        release.save('scanner-validation.json',{'checks':scanner_checks})
        assert checked.returncode==0 and scanner['result']=='passed'
    from verify_scanner_alignment import verify
    verify(False, 'scanner-alignment-final.json')
    release.check_gate()
    release.save('validation-approved.json',{'approved':True,'checks':len(report['checks']),
                 'scope':'both replicas ready, public feed JSON/XML, personal contract, identity protocol, device search and receipt denial JSON/XML, fresh real ClamD; no business mutation',
                 'public_smoke_pending':True})
