"""Candidate-image check: real codec, no network/credentials/DB/business handler.

Run inside each image with its configured USER, network=none and read-only.
The caller binds this program and records its SHA, image ID and exit code.
"""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import sys
import threading
import platform
import time

from flask import Flask
from lxml import etree
from typing import Annotated
from pydantic import Field
from redhouse.models import Model, Text, ID, Kind, Group

class ResourceCreate(Model):
    collected_at: Text | None = None
    location_id: ID | None = None
    folio: Annotated[
        str, Field(min_length=6, max_length=30, pattern=r"^[A-Za-z0-9_-]+$")
    ]
    kind: Kind
    component: Text
    blood_group: Group
    expires_at: Text
    donation_id: ID | None = None
from redhouse import codec
from redhouse.errors import APIError


def main(expected):
    source = Path('/app/apps/services/redhouse/codec.py')
    assert hashlib.sha256(source.read_bytes()).hexdigest() == expected
    # Generation only: do not warm XMLSchema before the cold concurrent barrier.
    xsd = codec.request_xsd(ResourceCreate)
    assert hashlib.sha256(xsd).hexdigest() == 'c44e841609216789820023fd487a27da4d1324fa95dd20a5a5edb6dc85caee44'
    valid = b'<request><folio>CODEC-PROBE-NOT-PERSISTED</folio><kind>BLOOD</kind><component>RBC</component><blood_group>O-</blood_group><expires_at>2030-01-01T00:00:00Z</expires_at></request>'
    duplicate = valid.replace(b'</request>', b'<folio>FORBIDDEN-DUPLICATE</folio></request>')
    xxe = b'<!DOCTYPE request [<!ENTITY leak SYSTEM "file:///not-read">]><request><folio>&leak;</folio></request>'
    corpus = [('valid', valid), ('duplicate_rejected', duplicate), ('xxe_rejected', xxe)]
    app = Flask(__name__)
    barrier = threading.Barrier(8)
    started = time.monotonic()

    def work(worker):
        row = {'counts': {label: 0 for label, _ in corpus}, 'error_count': 0, 'errors': [], 'cold_seconds': None}
        barrier.wait(timeout=5)
        for iteration in range(8):
            for label, raw in corpus:
                at = time.monotonic()
                try:
                    with app.test_request_context('/', method='POST', data=raw, content_type='application/xml'):
                        try:
                            value = codec.parse(ResourceCreate)
                        except APIError as exc:
                            assert label != 'valid' and exc.status == 400 and exc.code == 'invalid_body'
                        else:
                            assert label == 'valid' and value['kind'] == 'BLOOD' and value['blood_group'] == 'O-'
                    row['counts'][label] += 1
                except Exception as exc:
                    row['error_count'] += 1
                    if len(row['errors']) < 4:
                        error = {'worker': worker, 'iteration': iteration, 'corpus': label, 'type': type(exc).__name__}
                        if isinstance(exc, etree.XMLSchemaParseError):
                            error['libxml_types'] = sorted({entry.type_name for entry in exc.error_log})[:4]
                            error['builtin_type_failure'] = 'the given type is not a built-in type' in str(exc)
                        row['errors'].append(error)
                finally:
                    if iteration == 0 and label == 'valid':
                        row['cold_seconds'] = time.monotonic() - at
        return row

    with ThreadPoolExecutor(max_workers=8) as pool:
        rows = list(pool.map(work, range(8)))
    counts = {label: sum(row['counts'][label] for row in rows) for label, _ in corpus}
    errors = sum(row['error_count'] for row in rows)
    result = {'passed': errors == 0 and all(value == 64 for value in counts.values()),
              'source_sha256': expected, 'xsd_sha256': hashlib.sha256(xsd).hexdigest(),
              'corpus_sha256': {label: hashlib.sha256(raw).hexdigest() for label, raw in corpus},
              'counts': counts, 'attempts': 192, 'error_count': errors,
              'errors': [error for row in rows for error in row['errors']][:8],
              'cold_seconds': [row['cold_seconds'] for row in rows],
              'elapsed_seconds': time.monotonic() - started,
              'python': platform.python_version(), 'lxml': etree.LXML_VERSION,
              'libxml': etree.LIBXML_VERSION, 'compiled_libxml': etree.LIBXML_COMPILED_VERSION,
              'threads': 8, 'iterations_per_thread': 8, 'sequential_schema_warmup': False,
              'scope': 'codec only; no HTTP/auth/atomic/database; identical fresh-process corpus'}
    print(json.dumps(result))
    raise SystemExit(0 if result['passed'] else 1)


if __name__ == '__main__':
    main(sys.argv[1])

