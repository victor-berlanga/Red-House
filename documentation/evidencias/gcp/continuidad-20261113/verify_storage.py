"""Bounded synthetic file smoke on the authorized academic Red House deployment.

No custody, consent or clinical decision is recorded. The PDF identifies itself
as a technical test. Credentials/capability URLs never enter the public report.
"""

import hashlib
import json
import os
from io import BytesIO
from pathlib import Path
from urllib.parse import urlsplit
from uuid import uuid4

import requests
from lxml import etree
from reportlab.pdfgen.canvas import Canvas

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
BASE = 'https://34.18.186.116'
PASSWORD = json.loads((ROOT / '.local/password-maintenance-20261111/remote-input.json').read_text())['password']
RESULT = {'tls_verified': True, 'checks': [], 'scope': 'Synthetic PDF evidence only; no custody or clinical transition'}
PRIVATE_PATH = OUT / 'storage-smoke-private.json'
PRIVATE = json.loads(PRIVATE_PATH.read_text()) if PRIVATE_PATH.exists() else {}


def record(label, response, expected):
    RESULT['checks'].append({'label': label, 'http': response.status_code})
    assert response.status_code in ((expected,) if isinstance(expected, int) else expected), label


def api(session, service, path, method='GET', body=None, key=None, mime='application/json'):
    headers = {'Accept': mime}
    if key:
        headers['Idempotency-Key'] = key
    if mime == 'application/xml' and body is not None:
        document = etree.Element('request')
        for name, value in body.items():
            assert isinstance(value, (str, int)) and not isinstance(value, bool)
            etree.SubElement(document, name).text = str(value)
        headers['Content-Type'] = 'application/xml'
        return session.request(method, BASE + '/services/' + service + path,
                               data=etree.tostring(document, encoding='UTF-8', xml_declaration=True),
                               headers=headers, timeout=30, allow_redirects=False)
    return session.request(method, BASE + '/services/' + service + path,
                           json=body, headers=headers, timeout=30, allow_redirects=False)


def login(username):
    session = requests.Session()
    response = api(session, 'identidad-acceso', '/api/v1/auth/login', 'POST',
                   {'username': username, 'password': PASSWORD})
    record('login:' + username, response, 200)
    tokens = response.json()['data']
    session.headers['Authorization'] = 'Bearer ' + tokens['access_token']
    return session, tokens


def revoke(session, tokens):
    response = api(session, 'identidad-acceso', '/api/v1/auth/revoke', 'POST',
                   {'refresh_token': tokens['refresh_token']})
    record('revoke', response, 200)


def target(url, provider):
    parsed = urlsplit(url)
    assert parsed.scheme == 'https' and not parsed.username and not parsed.password and not parsed.fragment
    if provider == 'local':
        assert parsed.netloc == urlsplit(BASE).netloc and parsed.path.startswith('/storage/v1/objects/')
    else:
        assert parsed.netloc == 'storage.googleapis.com'
    return url


def payload(fmt):
    output = BytesIO()
    page = Canvas(output, invariant=1)
    page.setTitle('Red House: prueba tecnica de almacenamiento')
    page.drawString(40, 780, 'PRUEBA TECNICA SINTETICA - SIN VALIDEZ CLINICA')
    page.drawString(40, 750, 'Publicacion 2026-11-13. Contrato de respuesta: ' + fmt)
    page.drawString(40, 720, 'No acredita entrega, recoleccion, consentimiento ni autorizacion medica.')
    page.save()
    return output.getvalue()


def main():
    health = requests.get(BASE + '/services/documentos/health/storage', timeout=20)
    record('storage-local-health', health, 200)
    assert health.json()['data']['provider'] == 'local'
    session, tokens = login('transport1')
    donor = donor_tokens = None
    revoked = False
    try:
        response = api(session, 'transporte', '/api/v1/shipments?page_size=100')
        record('authorized-shipments', response, 200)
        shipments = response.json()['data']['items']
        active = next(x for x in shipments if x['status'] not in ('ACCEPTED', 'CANCELLED', 'REJECTED')
                      and not x['inventory_pending'] and (not PRIVATE.get('shipment_id') or x['id'] == PRIVATE['shipment_id']))
        PRIVATE['shipment_id'] = active['id']
        # Existing historical objects must remain readable through their own
        # provider after local writes become the default.
        historical = False
        historical_candidates = 0
        for shipment in shipments:
            response = api(session, 'documentos', '/api/v1/shipments/' + shipment['id'] + '/files?page_size=20')
            record('historical-files', response, 200)
            for item in response.json()['data']['items']:
                if item['status'] != 'VERIFIED':
                    continue
                historical_candidates += 1
                access = api(session, 'documentos', '/api/v1/files/' + item['id'] + '/download')
                if access.status_code == 409:
                    continue
                record('historical-download-authorized', access, 200)
                url = access.json()['data']['download_url']
                if urlsplit(url).netloc != 'storage.googleapis.com':
                    continue
                with requests.get(target(url, 'gcs'), timeout=30, allow_redirects=False, stream=True) as downloaded:
                    record('historical-gcs-download', downloaded, 200)
                    chunks, size = [], 0
                    for chunk in downloaded.iter_content(65536):
                        size += len(chunk)
                        assert size <= 10485760
                        chunks.append(chunk)
                    assert size == item['size']
                    assert hashlib.sha256(b''.join(chunks)).hexdigest() == item['sha256']
                RESULT['historical_gcs'] = {'read': True, 'bytes': size, 'sha256_matches': True}
                historical = True
                break
            if historical:
                break
        RESULT['historical_gcs_candidates'] = historical_candidates
        RESULT['historical_gcs_checked'] = historical
        donor, donor_tokens = login('donor1')
        downloads = []
        for fmt in ('json', 'xml'):
            content = payload(fmt)
            body = {'mime_type': 'application/pdf', 'size': len(content),
                    'sha256': hashlib.sha256(content).hexdigest()}
            command = PRIVATE.setdefault(fmt, {'idempotency_key': str(uuid4()), 'sha256': body['sha256']})
            assert command['sha256'] == body['sha256']
            key = command['idempotency_key']
            PRIVATE_PATH.write_text(json.dumps(PRIVATE, indent=2) + '\n')
            path = '/api/v1/shipments/' + active['id'] + '/files'
            response = api(session, 'documentos', path, 'POST', body, key, 'application/' + fmt)
            record('prepare:' + fmt, response, 201)
            if fmt == 'json':
                prepared = response.json()['data']
                identifier = prepared['file']['id']
                url, headers = prepared['upload_url'], prepared['upload_headers']
            else:
                doc = etree.fromstring(response.content, etree.XMLParser(resolve_entities=False, no_network=True))
                identifier = doc.findtext("field[@name='data']/field[@name='file']/field[@name='id']")
                url = doc.findtext("field[@name='data']/field[@name='upload_url']")
                headers = {'Content-Type': 'application/pdf'}
            assert identifier and url
            PRIVATE[fmt] = {'file_id': identifier, 'idempotency_key': key, 'sha256': body['sha256']}
            (OUT / 'storage-smoke-private.json').write_text(json.dumps(PRIVATE, indent=2) + '\n')
            assert 'storage_provider' not in response.text
            upload = requests.put(target(url, 'local'), data=content, headers=headers, timeout=30, allow_redirects=False)
            record('upload:' + fmt, upload, 201)
            replay = requests.put(target(url, 'local'), data=content, headers=headers, timeout=30, allow_redirects=False)
            record('immutable-upload:' + fmt, replay, 412)
            verified = api(session, 'documentos', '/api/v1/files/' + identifier + '/verify', 'POST', {}, str(uuid4()))
            record('verify-clamav:' + fmt, verified, 200)
            assert verified.json()['data']['status'] == 'VERIFIED'
            denied = api(donor, 'documentos', '/api/v1/files/' + identifier + '/download')
            record('donor-denied:' + fmt, denied, (403, 404))
            access = api(session, 'documentos', '/api/v1/files/' + identifier + '/download')
            record('download-authorized:' + fmt, access, 200)
            download = target(access.json()['data']['download_url'], 'local')
            received = requests.get(download, timeout=30, allow_redirects=False)
            record('download:' + fmt, received, 200)
            assert received.content == content and received.headers['Cache-Control'] == 'no-store'
            downloads.append(download)
        revoke(session, tokens)
        revoked = True
        for download in downloads:
            record('revoked-capability', requests.get(download, timeout=20, allow_redirects=False), 401)
        RESULT['local_result'] = 'passed'
        RESULT['result'] = 'passed' if historical else 'partial'
        RESULT['created_synthetic_files'] = 2
    finally:
        if not revoked:
            revoke(session, tokens)
        session.close()
        if donor is not None:
            revoke(donor, donor_tokens)
            donor.close()


if __name__ == '__main__':
    os.umask(0o077)
    try:
        main()
    except Exception as exc:
        RESULT.update(result='failed', error_type=type(exc).__name__)
    finally:
        (OUT / 'storage-smoke.json').write_text(json.dumps(RESULT, indent=2) + '\n')
        print(json.dumps({'result': RESULT.get('result'), 'checks': len(RESULT['checks'])}))
    raise SystemExit(0 if RESULT.get('result') == 'passed' else 1)
