"""Resume the two original synthetic commands; never create replacement files."""
import hashlib
import json
import os

import requests
from lxml import etree

import verify_storage as smoke

os.umask(0o077)
result = {'scope': 'Completion of original JSON/XML commands; GCS tested separately', 'tls_verified': True}
session = donor = tokens = donor_tokens = None
revoked = False
try:
    assert set(('shipment_id', 'json', 'xml')).issubset(smoke.PRIVATE)
    session, tokens = smoke.login('transport1')
    donor, donor_tokens = smoke.login('donor1')
    downloads = []
    for fmt in ('json', 'xml'):
        content = smoke.payload(fmt)
        digest = hashlib.sha256(content).hexdigest()
        command = smoke.PRIVATE[fmt]
        assert command['sha256'] == digest
        response = smoke.api(session, 'documentos', '/api/v1/shipments/' + smoke.PRIVATE['shipment_id'] + '/files',
                             'POST', {'mime_type': 'application/pdf', 'size': len(content), 'sha256': digest},
                             command['idempotency_key'], 'application/' + fmt)
        smoke.record('original-prepare-replay:' + fmt, response, 201)
        if fmt == 'json':
            value = response.json()['data']
            identifier, status = value['file']['id'], value['file']['status']
            url = value['upload_url']
        else:
            doc = etree.fromstring(response.content, etree.XMLParser(resolve_entities=False, load_dtd=False, no_network=True))
            assert not doc.getroottree().docinfo.doctype
            field = "field[@name='data']/field[@name='file']/field[@name='%s']"
            identifier, status = doc.findtext(field % 'id'), doc.findtext(field % 'status')
            url = doc.findtext("field[@name='data']/field[@name='upload_url']")
        assert identifier and status
        assert not command.get('file_id') or command['file_id'] == identifier
        command['file_id'] = identifier
        smoke.PRIVATE_PATH.write_text(json.dumps(smoke.PRIVATE, indent=2) + '\n')
        if status == 'PENDING':
            url = smoke.target(url, 'local')
            for expected in (201, 412):
                sent = requests.put(url, data=content, headers={'Content-Type': 'application/pdf'}, timeout=30, allow_redirects=False)
                smoke.record(('upload:' if expected == 201 else 'immutable-upload:') + fmt, sent, expected)
            verified = smoke.api(session, 'documentos', '/api/v1/files/' + identifier + '/verify', 'POST', {}, command['idempotency_key'] + '-verify')
            smoke.record('verify-clamav:' + fmt, verified, 200)
            assert verified.json()['data']['status'] == 'VERIFIED'
        else:
            assert status == 'VERIFIED'
        denied = smoke.api(donor, 'documentos', '/api/v1/files/' + identifier + '/download')
        smoke.record('donor-denied:' + fmt, denied, 403)
        access = smoke.api(session, 'documentos', '/api/v1/files/' + identifier + '/download')
        smoke.record('download-authorized:' + fmt, access, 200)
        download = smoke.target(access.json()['data']['download_url'], 'local')
        received = requests.get(download, timeout=30, allow_redirects=False)
        smoke.record('download:' + fmt, received, 200)
        assert received.content == content and received.headers['Cache-Control'] == 'no-store'
        downloads.append(download)
    smoke.revoke(session, tokens)
    revoked = True
    for download in downloads:
        smoke.record('revoked-capability', requests.get(download, timeout=20, allow_redirects=False), 401)
    result.update(result='passed', original_commands=2, replacement_files_created=0)
except Exception as exc:
    result.update(result='failed', error_type=type(exc).__name__)
finally:
    try:
        if session is not None and not revoked:
            smoke.revoke(session, tokens)
        if donor is not None:
            smoke.revoke(donor, donor_tokens)
    except Exception as exc:
        result.update(result='failed', cleanup_error_type=type(exc).__name__)
    for client in (session, donor):
        if client is not None:
            client.close()
    result['checks'] = smoke.RESULT['checks']
    (smoke.OUT / 'storage-completion.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'result': result.get('result'), 'checks': len(result['checks'])}))
raise SystemExit(0 if result.get('result') == 'passed' else 1)
