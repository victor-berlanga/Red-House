"""Read one existing authorized, clean GCS report after local activation."""
import hashlib
import json
import os

import requests

import verify_storage as smoke

result = {'scope': 'Read-only historical GCS report; no new bucket object', 'tls_verified': True}
session = tokens = None
try:
    os.umask(0o077)
    session, tokens = smoke.login('medical2')
    response = smoke.api(session, 'documentos', '/api/v1/export-jobs?page_size=100')
    smoke.record('existing-report-jobs', response, 200)
    jobs = response.json()['data']['items']
    checked = False
    for job in jobs:
        if job['status'] != 'COMPLETE' or not job['file_id']:
            continue
        verified = smoke.api(session, 'documentos', '/api/v1/documents/' + job['file_id'] + '/verified')
        smoke.record('historical-report-clean', verified, 200)
        metadata = verified.json()['data']
        assert metadata['analysis'] == 'CLEAN' and metadata['file_status'] == 'VERIFIED'
        access = smoke.api(session, 'documentos', '/api/v1/files/' + job['file_id'] + '/download')
        smoke.record('historical-report-download-authorized', access, 200)
        url = smoke.target(access.json()['data']['download_url'], 'gcs')
        with requests.get(url, timeout=30, allow_redirects=False, stream=True) as downloaded:
            smoke.record('historical-gcs-report-download', downloaded, 200)
            digest, size = hashlib.sha256(), 0
            for chunk in downloaded.iter_content(65536):
                size += len(chunk)
                assert size <= 10485760
                digest.update(chunk)
            assert digest.hexdigest() == metadata['sha256']
            assert downloaded.headers['x-goog-generation'] == metadata['generation']
        (smoke.OUT / 'historical-gcs-private.json').write_text(json.dumps({'job_id': job['id'], 'file_id': job['file_id']}, indent=2) + '\n')
        result.update(bytes=size, sha256_matches=True, generation_matches=True, result='passed')
        checked = True
        break
    assert checked, 'No authorized historical report checked'
except Exception as exc:
    result.update(result='failed', error_type=type(exc).__name__)
finally:
    if session is not None:
        try:
            smoke.revoke(session, tokens)
        except Exception as exc:
            result.update(result='failed', cleanup_error_type=type(exc).__name__)
        session.close()
    result['checks'] = smoke.RESULT['checks']
    (smoke.OUT / 'historical-gcs.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'result': result.get('result'), 'checks': len(result['checks'])}))
raise SystemExit(0 if result.get('result') == 'passed' else 1)
