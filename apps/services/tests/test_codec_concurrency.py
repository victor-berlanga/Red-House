"""Pure regression: real parsers/models, no service startup or persistence."""

import json
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest
from flask import Flask
from lxml import etree
from ms_compatibilidad.laboratory import ResultCreate, SampleCreate
from ms_inventario.editing import ResourceEdit
from ms_inventario.routes import ResourceCreate
from redhouse import codec
from redhouse.errors import APIError
from scripts.load_client import request_xml

BODY = {
    "folio": "LOAD-XML-PURE-ONLY",
    "kind": "BLOOD",
    "component": "RBC",
    "blood_group": "O-",
    "expires_at": "2026-11-18T22:57:00+00:00",
}
ID = "00000000-0000-4000-8000-000000000001"


def parse_xml(app, model, raw):
    with app.test_request_context(
        "/", method="POST", data=raw, content_type="application/xml"
    ):
        return codec.parse(model)


def test_parallel_resource_xml_keeps_validity_and_rejection_independent():
    app = Flask(__name__)
    barrier = threading.Barrier(8)
    valid = request_xml(BODY)
    # A duplicate field is invalid XSD even if a plain dict decoder overwrote it.
    invalid = valid.replace(b"</request>", b"<folio>OTHER-FOLIO</folio></request>")
    expected = ResourceCreate.model_validate(BODY).model_dump()

    def worker(_):
        barrier.wait(timeout=5)
        for _ in range(40):
            assert parse_xml(app, ResourceCreate, valid) == expected
            with pytest.raises(APIError) as rejected:
                parse_xml(app, ResourceCreate, invalid)
            assert rejected.value.status == 400

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(worker, range(8)))


@pytest.mark.parametrize(
    "model,body",
    [
        (ResourceCreate, BODY),
        (
            ResourceEdit,
            dict(
                BODY, version=1, human_confirmation=True, reason="Corrección sintética"
            ),
        ),
        (
            SampleCreate,
            {
                "resource_id": ID,
                "profile_id": ID,
                "identifier": "SYNTHETIC",
                "collected_at": "2026-11-16T20:00:00+00:00",
            },
        ),
        (
            ResultCreate,
            {
                "sample_id": ID,
                "test_code": "HLA",
                "result_state": "CORRECTED",
                "supersedes": ID,
                "method": "Método sintético",
                "laboratory": "Laboratorio sintético",
                "reference": "Evidencia sintética",
                "measured_at": "2026-11-16T20:00:00+00:00",
                "issued_at": "2026-11-16T21:00:00+00:00",
                "document_id": ID,
                "hla": {
                    "nomenclature": "HLA-colon-2010",
                    "nomenclature_version": "2010:syntax-2",
                    "resolution": "Declaración sintética",
                    "loci": [{"locus": "A", "alleles": ["A*01:01"]}],
                },
            },
        ),
    ],
)
def test_affected_models_preserve_json_xml_parity(model, body):
    app = Flask(__name__)
    with app.test_request_context(
        "/", method="POST", data=json.dumps(body), content_type="application/json"
    ):
        expected = codec.parse(model)
    assert parse_xml(app, model, request_xml(body)) == expected


@pytest.mark.parametrize(
    "raw",
    [
        b'<!DOCTYPE request [<!ENTITY leak SYSTEM "file:///DO-NOT-READ">]><request><folio>&leak;</folio></request>',
        b'<!DOCTYPE request SYSTEM "https://invalid.test/never-fetch"><request/>',
        b"<request><folio>broken",
        request_xml(dict(BODY, unknown="forbidden")),
        request_xml(dict(BODY, blood_group="UNKNOWN")),
    ],
)
def test_untrusted_xml_remains_rejected(raw):
    with pytest.raises(APIError) as rejected:
        parse_xml(Flask(__name__), ResourceCreate, raw)
    assert rejected.value.status in (400, 422)


def test_schema_compilation_error_is_not_accepted_or_relabelled(monkeypatch):
    def fail(_):
        raise etree.XMLSchemaParseError("synthetic schema compiler failure")

    monkeypatch.setattr(codec.E, "XMLSchema", fail)
    with pytest.raises(etree.XMLSchemaParseError):
        parse_xml(Flask(__name__), ResourceCreate, request_xml(BODY))
