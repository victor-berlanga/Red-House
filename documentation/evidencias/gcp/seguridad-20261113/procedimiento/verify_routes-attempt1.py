"""Read existing synthetic files and nominal identity over verified public TLS."""
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlsplit
import requests
from lxml import etree

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE = 'https://34.18.186.116'
PASSWORD = json.loads((ROOT / '.local/password-maintenance-20261111/remote-input.json').read_text())['password']
FIXTURE = json.loads((ROOT / '.local/deploy-continuidad-20261113/storage-smoke-private.json').read_text())
report = {'tls_verified': True, 'business_writes': False, 'checks': []}
api = requests.Session()
portal = requests.Session()
tokens = None
portal_logged = False
api_caps = []
portal_caps = []

def check(label, session, method, path, expected=200, **kwargs):
    response = session.request(method, BASE + path, timeout=30, allow_redirects=False, **kwargs)
    report['checks'].append({'check': label, 'http': response.status_code})
    assert response.status_code == expected, label
    return response

def capability(url, prefix):
    target = urlsplit(url)
    assert target.scheme == 'https' and target.netloc == urlsplit(BASE).netloc
    assert not target.query and not target.fragment
    assert re.fullmatch(re.escape(prefix) + r'[A-Za-z0-9_-]+', target.path)
    return target.path

def contents(label, path, digest):
    response = check(label, requests, 'GET', path)
    assert hashlib.sha256(response.content).hexdigest() == digest
    assert response.headers['Cache-Control'] == 'no-store'

try:
    tokens = check('api-login', api, 'POST', '/services/identidad-acceso/api/v1/auth/login',
                   json={'username':'transport1','password':PASSWORD}).json()['data']
    api.headers['Authorization'] = 'Bearer ' + tokens['access_token']
    shipment_path = '/services/transporte/api/v1/shipments/' + FIXTURE['shipment_id']
    shipment = check('shipment', api, 'GET', shipment_path).json()['data']
    for fmt in ('json', 'xml'):
        response = check('operational-handover:' + fmt, api, 'GET', shipment_path + '/operational-handover',
                         headers={'Accept': 'application/' + fmt})
        if fmt == 'json':
            data = response.json()['data']
            assert data['shipment_id'] == shipment['id'] and data['shipment_version'] == shipment['version']
            assert data['transport_user']['id'] == shipment['transport_user_id'] and data['transport_user']['name']
        else:
            doc = etree.fromstring(response.content, etree.XMLParser(resolve_entities=False, load_dtd=False, no_network=True))
            assert not doc.getroottree().docinfo.doctype
            data = doc.find("field[@name='data']")
            assert data.findtext("field[@name='shipment_id']") == shipment['id']
            assert int(data.findtext("field[@name='shipment_version']")) == shipment['version']
            assert data.findtext("field[@name='transport_user']/field[@name='id']") == shipment['transport_user_id']
            assert data.findtext("field[@name='transport_user']/field[@name='name']")
        file = FIXTURE[fmt]
        access = check('api-capability:' + fmt, api, 'GET', '/services/documentos/api/v1/files/' + file['file_id'] + '/download').json()['data']
        path = capability(access['download_url'], '/storage/v1/objects/')
        contents('api-binary:' + fmt, path, file['sha256'])
        api_caps.append(path)
    portal.headers.update({'Origin':BASE, 'Referer':BASE + '/login'})
    page = check('portal-login-form', portal, 'GET', '/login')
    csrf = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', page.text).group(1)
    response = check('portal-login', portal, 'POST', '/login', expected=302,
                     data={'login_email':'transport1','password':PASSWORD,'csrf_token':csrf})
    assert '/login' not in response.headers.get('Location','')
    portal_logged = True
    for fmt in ('json', 'xml'):
        file = FIXTURE[fmt]
        response = check('portal-capability:' + fmt, portal, 'GET', '/archivos/' + file['file_id'] + '/descargar', expected=303)
        path = capability(response.headers['Location'], '/portal-storage/v1/objects/')
        contents('portal-binary:' + fmt, path, file['sha256'])
        portal_caps.append(path)
    report['result'] = 'passed'
except Exception as exc:
    report.update(result='failed', error_type=type(exc).__name__)
finally:
    try:
        if tokens:
            check('api-revoke', api, 'POST', '/services/identidad-acceso/api/v1/auth/revoke', json={'refresh_token':tokens['refresh_token']})
            for path in api_caps:
                check('api-capability-revoked', requests, 'GET', path, expected=401)
        if portal_logged:
            page = check('portal-panel', portal, 'GET', '/panel')
            csrf = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', page.text).group(1)
            response = portal.post(BASE + '/logout', data={'csrf_token':csrf}, timeout=30, allow_redirects=False)
            assert response.status_code in (302, 303)
            check('portal-session-revoked', portal, 'GET', '/sesion/estado', expected=401)
            for path in portal_caps:
                check('portal-capability-revoked', requests, 'GET', path, expected=401)
    except Exception as exc:
        report.update(result='failed', cleanup_error_type=type(exc).__name__)
    api.close()
    portal.close()
    (HERE / 'public-routes.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'result':report.get('result'), 'checks':len(report['checks'])}))
raise SystemExit(0 if report.get('result') == 'passed' else 1)
