"""Public HTTPS read checks; credentials remain in the existing private file."""
import json
import re
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = Path(__file__).resolve().parent
BASE = 'https://34.18.186.116'
PASSWORD = json.loads((ROOT / '.local/password-maintenance-20261111/remote-input.json').read_text())['password']
LABEL = sys.argv[1]
PHASE = 'after'
result = {'phase': LABEL, 'checks': [], 'tls_verification': True}

def record(label, response, start):
    result['checks'].append({'label': label, 'http': response.status_code,
                            'milliseconds': round((time.monotonic() - start) * 1000, 3)})

def web(username, paths):
    with requests.Session() as session:
        session.headers.update({'Origin': BASE, 'Referer': BASE + '/login'})
        page = session.get(BASE + '/login', timeout=20)
        token = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', page.text).group(1)
        response = session.post(BASE + '/login', data={'login_email': username, 'password': PASSWORD,
                                'csrf_token': token}, timeout=30, allow_redirects=False)
        assert response.status_code == 302 and '/login' not in response.headers.get('Location', ''), ('login', username, response.status_code)
        try:
            for path in paths:
                start = time.monotonic()
                response = session.get(BASE + path, timeout=40, allow_redirects=False)
                record(username + ':' + path, response, start)
                if PHASE == 'after':
                    assert response.status_code == 200, (path, response.status_code)
                if response.status_code == 200 and path == '/sesion/estado':
                    assert response.headers['Cache-Control'] == 'no-store'
                    assert set(response.json()) == {'expires_at', 'server_time'}
                if PHASE == 'after' and username == 'donor1' and path == '/panel':
                    scripts = re.findall(r'<script[^>]+src="([^"]+)"', response.text)
                    result['donor_chart_scripts'] = [x for x in scripts if 'highcharts' in x or 'charts.js' in x]
                    assert not result['donor_chart_scripts']
            if username=='donor1':
                page=session.get(BASE+'/donantes/donor',timeout=30)
                links=re.findall(r'href=["\'](/donantes/donor/[0-9a-f-]{36}/mis-datos)["\']',page.text)
                assert links, 'Own personal edit action missing'
                start=time.monotonic()
                response=session.get(BASE+links[0],timeout=30,allow_redirects=False)
                record('donor1:personal-form',response,start)
                assert response.status_code==200
                assert 'display_name' in response.text and 'csrf_token' in response.text
                result['personal_form_read_only']=True
        finally:
            page = session.get(BASE + '/panel', timeout=30)
            token = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', page.text)
            if token:
                response = session.post(BASE + '/logout', data={'csrf_token': token.group(1)}, timeout=20, allow_redirects=False)
                assert response.status_code in (302, 303)
                assert session.get(BASE + '/sesion/estado', timeout=20).status_code == 401

def api(username, reads):
    session = requests.Session()
    token = None
    try:
        response = session.post(BASE + '/services/identidad-acceso/api/v1/auth/login',
                                json={'username': username, 'password': PASSWORD}, timeout=20)
        assert response.status_code == 200, ('api-login', username, response.status_code)
        token = response.json()['data']
        session.headers['Authorization'] = 'Bearer ' + token['access_token']
        for service, path, mime, expected in reads:
            start = time.monotonic()
            response = session.get(BASE + '/services/' + service + path,
                                   headers={'Accept': mime}, timeout=25)
            record(username + ':' + service + path + ':' + mime, response, start)
            assert response.status_code == expected, (service, path, response.status_code)
            if mime == 'application/json':
                payload = response.json()
                assert 'meta' in payload and ('data' if expected == 200 else 'error') in payload
            else:
                from lxml import etree
                assert etree.fromstring(response.content, etree.XMLParser(resolve_entities=False, no_network=True)).tag
        if username == 'donor1' and LABEL != 'compatibility':
            for path in ('/api/v1/appointments/next', '/api/v1/appointments/agenda?page_size=20'):
                for mime in ('application/json', 'application/xml'):
                    start = time.monotonic()
                    response = session.get(BASE+'/services/donantes'+path, headers={'Accept':mime}, timeout=25)
                    record(username+':'+path+':'+mime,response,start)
                    assert response.status_code == 200
        if username == 'transport1':
            shipment_response = session.get(BASE+'/services/transporte/api/v1/shipments?page_size=20',timeout=25)
            assert shipment_response.status_code == 200
            shipments = shipment_response.json()['data']['items']
            result['shipment_file_checks'] = 0
            for shipment in shipments[:3]:
                path = '/services/documentos/api/v1/shipments/'+shipment['id']+'/files?page_size=20'
                for mime in ('application/json', 'application/xml'):
                    start = time.monotonic()
                    response = session.get(BASE+path,headers={'Accept':mime},timeout=25)
                    record('transport1:shipment-files:'+mime,response,start)
                    assert response.status_code == 200
                    assert 'storage_provider' not in response.text
                    result['shipment_file_checks'] += 1
            import websocket
            for fmt in ('json', 'xml'):
                from ms_transporte.tracking_contracts import Message, Event, encode, decode
                ws = websocket.create_connection(BASE.replace('https:', 'wss:') + '/services/transporte/ws/v1/tracking/' + fmt,
                     timeout=10, suppress_origin=True, subprotocols=['redhouse.tracking.v1.' + fmt],
                     sslopt={'ca_certs': requests.certs.where()})
                try:
                    ws.send(encode({'type':'authenticate','credential_kind':'user','credential':token['access_token']},fmt,Message))
                    assert decode(ws.recv(),Event,fmt)['type']=='authenticated'
                    ws.send(encode({'type':'heartbeat'},fmt,Message))
                    assert decode(ws.recv(),Event,fmt)['type']=='heartbeat'
                    result.setdefault('wss', []).append({'format':fmt,'tls_verified':True,'authenticated':True,'heartbeat':True,'position_published':False})
                finally:
                    ws.close()
    finally:
        if token:
            response = session.post(BASE + '/services/identidad-acceso/api/v1/auth/revoke',
                                    json={'refresh_token':token['refresh_token']},timeout=20)
            assert response.status_code == 200
        session.close()

try:
    if PHASE == 'before':
        web('auditor1', ['/monitoreo'])
    else:
        for service in 'identidad-acceso donantes receptores inventario compatibilidad priorizacion-geografia transporte custodia alertas auditoria monitoreo documentos'.split():
            start=time.monotonic(); response=requests.get(BASE+'/services/'+service+'/health/ready',timeout=20)
            record(service+':ready',response,start); assert response.status_code==200
        for mime in ('application/json','application/xml'):
            for query,expected in (('?page=1&page_size=20',200),('?q=%00',400)):
                start=time.monotonic()
                response=requests.get(BASE+'/services/donantes/api/v1/public/campaign-feed'+query,headers={'Accept':mime},timeout=25,allow_redirects=False)
                record('public-campaign-feed:'+query+':'+mime,response,start)
                assert response.status_code==expected
        web('auditor1',['/monitoreo','/monitoreo','/sesion/estado'])
        web('donor1',['/panel','/citas','/campanas','/donantes/donor','/sesion/estado'])
        web('operator1',['/panel','/inventario','/traslados'])
        api('auditor1',[('monitoreo','/api/v1/status','application/json',200),('monitoreo','/api/v1/status','application/xml',200)])
        api('donor1',[('donantes','/api/v1/campaign-slots?page_size=20','application/json',200),('inventario','/api/v1/resources','application/json',403)])
        api('operator1',[('inventario','/api/v1/resources?page_size=20','application/json',200),('inventario','/api/v1/resources?page_size=20','application/xml',200)])
        api('transport1',[('transporte','/api/v1/shipments?page_size=20','application/json',200)])
    result['result']='passed'
except Exception as exc:
    result['result']='failed'; result['error_type']=type(exc).__name__
    # Never serialize response bodies, headers or credential-bearing requests.
    raise
finally:
    (OUTPUT / ('https-'+LABEL+'.json')).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'phase':LABEL,'result':result.get('result'),'checks':len(result['checks'])}))
