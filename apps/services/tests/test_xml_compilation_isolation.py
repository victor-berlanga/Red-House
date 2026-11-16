"""Cold concurrent runtime constructors; no databases, sockets or service startup."""
import json
from pathlib import Path
import subprocess
import sys


def _cold_runtime_constructors():
    # Imports happen only in the new interpreter. Nothing precompiles a schema.
    from concurrent.futures import ThreadPoolExecutor
    import threading

    from flask import Flask
    from ms_inventario.routes import ResourceCreate
    from ms_transporte.tracking_contracts import decode
    from redhouse.codec import parse
    from redhouse.errors import APIError
    from redhouse.xml_response import envelope, validate_response

    assert envelope.cache_info().currsize == 0
    app = Flask(__name__)
    barrier = threading.Barrier(9)
    resource = b'<request><folio>XML-ISOLATED-ONLY</folio><kind>BLOOD</kind><component>RBC</component><blood_group>O-</blood_group><expires_at>2030-01-01T00:00:00Z</expires_at></request>'
    resource_duplicate = resource.replace(b'</request>', b'<folio>OTHER-VALID-FOLIO</folio></request>')
    heartbeat = '<request><type>heartbeat</type></request>'
    heartbeat_duplicate = '<request><type>heartbeat</type><type>heartbeat</type></request>'
    xxe = '<!DOCTYPE request [<!ENTITY leak SYSTEM "file:///DO-NOT-READ">]><request><type>&leak;</type></request>'
    response = b'<response type="object"><field name="quantity" type="integer">12</field></response>'
    response_duplicate = response.replace(b'</response>', b'<field name="quantity" type="integer">13</field></response>')
    response_xxe = b'<!DOCTYPE response [<!ENTITY leak SYSTEM "file:///DO-NOT-READ">]><response type="object"><field name="quantity" type="integer">&leak;</field></response>'
    response_schema = {'type': 'object', 'required': ['quantity'],
                       'additionalProperties': False,
                       'properties': {'quantity': {'type': 'integer'}}}

    def parse_resource(raw):
        with app.test_request_context('/', method='POST', data=raw, content_type='application/xml'):
            return parse(ResourceCreate)

    def reject(call, error_type, expected_code=None):
        try:
            call()
        except error_type as exc:
            if expected_code is not None:
                assert exc.status == 400 and exc.code == expected_code
        else:
            raise AssertionError('Invalid XML accepted')

    def worker(index):
        kind = ('request', 'tracking', 'response')[index % 3]
        barrier.wait(timeout=5)
        for _ in range(8):
            if kind == 'request':
                assert parse_resource(resource)['folio'] == 'XML-ISOLATED-ONLY'
                reject(lambda: parse_resource(resource_duplicate), APIError, 'invalid_body')
                reject(lambda: parse_resource(xxe.encode()), APIError, 'invalid_body')
            elif kind == 'tracking':
                assert decode(heartbeat, representation='xml')['type'] == 'heartbeat'
                reject(lambda: decode(heartbeat_duplicate, representation='xml'), APIError, 'invalid_message')
                reject(lambda: decode(xxe, representation='xml'), APIError, 'invalid_message')
            else:
                assert validate_response(response, response_schema) == {'quantity': 12}
                reject(lambda: validate_response(response_duplicate, response_schema), ValueError)
                reject(lambda: validate_response(response_xxe, response_schema), ValueError)
        return kind

    with ThreadPoolExecutor(max_workers=9) as pool:
        kinds = list(pool.map(worker, range(9)))
    assert sorted(kinds) == ['request'] * 3 + ['response'] * 3 + ['tracking'] * 3
    print(json.dumps({'passed': True, 'constructors': 3, 'threads': 9,
                      'valid_per_constructor': 24, 'rejected_per_constructor': 48,
                      'attempts': 216, 'cold_envelope': True}))


def test_three_runtime_xml_constructors_in_fresh_process():
    completed = subprocess.run(
        [sys.executable, '-B', str(Path(__file__).resolve()), '--cold-xml'],
        capture_output=True, text=True, timeout=25,
    )
    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {
        'passed': True, 'constructors': 3, 'threads': 9,
        'valid_per_constructor': 24, 'rejected_per_constructor': 48,
        'attempts': 216, 'cold_envelope': True,
    }


if __name__ == '__main__':
    assert sys.argv[1:] == ['--cold-xml']
    _cold_runtime_constructors()
