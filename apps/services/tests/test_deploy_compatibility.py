"""GCS-only baseline modules against shared schema 19; storage and ClamD are doubles."""

import hashlib
import importlib.util
import json
import subprocess
import sys
from io import BytesIO
from pathlib import Path
from uuid import uuid4

import jsonschema
import pytest
from PIL import Image
from redhouse.examples import request_xml
from redhouse.xml_response import validate_response

from .final_receivers import clamd_receiver
from .helpers import iso
from .test_documents_storage import planned
from .test_final_delivery_documents import TestBucket

ROOT = Path(__file__).resolve().parents[3]
GENERATOR = ROOT / "deployment/gcp/storage19_compatibility.py"
REVISION = "6d8b88d0c8e5de6e1c9267c68fac2a6a8a4cd837"


def old_schema(name):
    raw = subprocess.check_output(
        [
            "git",
            "show",
            f"{REVISION}:apps/services/ms_documentos/contracts/{name}.response.json",
        ],
        cwd=ROOT,
    )
    return json.loads(raw)


def load(name, path):
    spec = importlib.util.spec_from_file_location("ms_documentos." + name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.skipif(
    not GENERATOR.is_file(), reason="Generador de compatibilidad no disponible"
)
@pytest.mark.parametrize("fmt", ["json", "xml"])
def test_old_gcs_contracts_hide_schema19_provider(p, tmp_path, monkeypatch, fmt):
    generator_spec = importlib.util.spec_from_file_location(
        "compatibility_generator", GENERATOR
    )
    generator = importlib.util.module_from_spec(generator_spec)
    generator_spec.loader.exec_module(generator)
    output = tmp_path / "compat"
    generator.build(output)
    import ms_documentos

    with monkeypatch.context() as changes:
        for name in ("files", "reports"):
            changes.setitem(
                sys.modules,
                "ms_documentos." + name,
                load(name, output / (name + ".py")),
            )
        app = ms_documentos.create_app(dict(p.apps["documentos"].config))
        store = TestBucket()
        changes.setitem(app.config, "GCS_BUCKET", "synthetic-test-double")
        changes.setitem(app.extensions, "gcs_client", store)
        shipment = planned(p)
        path = "/api/v1/shipments/" + shipment["id"] + "/files"
        image = BytesIO()
        Image.new("RGB", (4, 4), "red").save(image, format="PNG")
        content = image.getvalue()
        client = app.test_client()

        def call(method, url, user, name, data=None):
            headers = {
                "Authorization": "Bearer " + p.tokens[user],
                "Idempotency-Key": uuid4().hex,
                "Accept": "application/xml" if fmt == "xml" else "application/json",
            }
            if fmt == "xml":
                headers["Content-Type"] = "application/xml"
                response = client.open(
                    url,
                    method=method,
                    data=request_xml(data).encode() if data else None,
                    headers=headers,
                )
            else:
                response = client.open(url, method=method, json=data, headers=headers)
            assert response.status_code < 300, response.get_data(as_text=True)
            contract = old_schema(name)
            value = (
                validate_response(response.data, contract)
                if fmt == "xml"
                else response.get_json()
            )
            jsonschema.validate(value, contract)
            return value["data"]

        prepared = call(
            "POST",
            path,
            "operator1",
            "file_prepare",
            {
                "mime_type": "image/png",
                "size": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
            },
        )
        assert "storage_provider" not in prepared["file"]
        store.objects[prepared["file"]["object_path"]] = content, "image/png"
        with clamd_receiver() as (port, scanned):
            changes.setitem(app.config, "CLAMD_HOST", "127.0.0.1")
            changes.setitem(app.config, "CLAMD_PORT", port)
            verified = call(
                "POST",
                "/api/v1/files/" + prepared["file"]["id"] + "/verify",
                "operator1",
                "file_verify",
            )
            assert (
                verified["status"] == "VERIFIED" and "storage_provider" not in verified
            )
            assert scanned == [content]
            replay = call(
                "POST",
                "/api/v1/files/" + prepared["file"]["id"] + "/verify",
                "operator1",
                "file_verify",
            )
            assert "storage_provider" not in replay
        listed = call("GET", path, "operator1", "file_list")
        assert all("storage_provider" not in row for row in listed["items"])
        call(
            "GET",
            "/api/v1/files/" + prepared["file"]["id"] + "/download",
            "operator1",
            "file_download",
        )
        body = {
            "report": "INVENTORY",
            "format": "CSV",
            "from_at": iso(days=-1),
            "until_at": iso(days=1),
        }
        job = call("POST", "/api/v1/export-jobs", "medical1", "export_create", body)
        assert "storage_provider" not in job
        detail = call(
            "GET", "/api/v1/export-jobs/" + job["id"], "medical1", "export_detail"
        )
        assert "storage_provider" not in detail
        listing = call("GET", "/api/v1/export-jobs", "medical1", "export_list")
        assert all("storage_provider" not in row for row in listing["items"])


@pytest.mark.skipif(
    not GENERATOR.is_file(), reason="Generador de compatibilidad no disponible"
)
def test_compat_filters_with_and_without_schema19(tmp_path):
    spec = importlib.util.spec_from_file_location(
        "compatibility_generator_static", GENERATOR
    )
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    output = tmp_path / "compat"
    generator.build(output)
    files = load("files", output / "files.py")
    reports = load("reports", output / "reports.py")
    assert files.public_file({"id": "synthetic"}) == {"id": "synthetic"}
    assert files.public_file({"id": "synthetic", "storage_provider": "gcs"}) == {
        "id": "synthetic"
    }
    assert reports.public({"id": "synthetic"}) == {"id": "synthetic"}
    assert reports.public({"id": "synthetic", "storage_provider": "gcs"}) == {
        "id": "synthetic"
    }
