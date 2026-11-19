"""Exportaciones locales y proveedor fijado antes de cargar. ClamD es un doble."""

from io import BytesIO
from zipfile import ZipFile

import pytest
from pypdf import PdfReader

from .final_receivers import clamd_receiver
from .helpers import iso, park_foreign_export_jobs
from .test_final_operations import CONFIRM


@pytest.mark.parametrize("format", ["CSV", "PDF", "XLSX"])
def test_local_report_provider_survives_retry(p, tmp_path, monkeypatch, format):
    from ms_documentos.reports import process
    from redhouse.errors import APIError

    park_foreign_export_jobs(p)
    app = p.apps["documentos"]
    monkeypatch.setitem(app.config, "STORAGE_PROVIDER", "local")
    monkeypatch.setitem(app.config, "STORAGE_LOCAL_ROOT", str(tmp_path))
    monkeypatch.setitem(app.config, "STORAGE_PUBLIC_BASE_URL", "https://example.test")
    job = p.ok(
        "documentos",
        "POST",
        "/api/v1/export-jobs",
        user="medical1",
        data={
            "report": "INVENTORY",
            "format": format,
            "from_at": iso(days=-1),
            "until_at": iso(days=1),
        },
    )
    assert "storage_provider" not in job
    with p.owner("documentos") as conn:
        assert (
            conn.execute(
                "SELECT storage_provider FROM export_jobs WHERE id=%s", (job["id"],)
            ).fetchone()[0]
            == "local"
        )

    def fail_scan(_content):
        raise APIError("scan_unavailable", "Prueba", 503)

    with monkeypatch.context() as changes:
        changes.setattr("redhouse.malware.scan", fail_scan)
        with app.app_context():
            process(limit=1)
    failed = p.ok(
        "documentos", "GET", "/api/v1/export-jobs/" + job["id"], user="medical1"
    )
    assert failed["status"] == "RETRYABLE"
    assert len(list(tmp_path.iterdir())) == 1
    monkeypatch.setitem(app.config, "STORAGE_PROVIDER", "gcs")
    p.ok(
        "documentos",
        "POST",
        "/api/v1/export-jobs/" + job["id"] + "/retry",
        user="medical1",
        data=CONFIRM,
    )
    with clamd_receiver() as (port, scanned):
        monkeypatch.setitem(app.config, "CLAMD_HOST", "127.0.0.1")
        monkeypatch.setitem(app.config, "CLAMD_PORT", port)
        with app.app_context():
            process(limit=1)
        ready = p.ok(
            "documentos", "GET", "/api/v1/export-jobs/" + job["id"], user="medical1"
        )
        assert ready["status"] == "COMPLETE" and len(scanned) == 1
    with p.owner("documentos") as conn:
        assert (
            conn.execute(
                "SELECT storage_provider FROM files WHERE id=%s", (ready["file_id"],)
            ).fetchone()[0]
            == "local"
        )
    with app.app_context():
        from redhouse.storage import object_bucket

        blob = object_bucket("local").blob(ready["file_id"])
        output = blob.download_as_bytes()
    assert output == scanned[0]
    if format == "CSV":
        assert output.decode("utf-8-sig")
    elif format == "PDF":
        assert len(PdfReader(BytesIO(output)).pages) > 0
    else:
        with ZipFile(BytesIO(output)) as archive:
            assert "xl/worksheets/sheet1.xml" in archive.namelist()


@pytest.mark.parametrize("fmt", ["json", "xml"])
def test_shipment_file_published_contract(p, tmp_path, monkeypatch, fmt):
    import hashlib
    from urllib.parse import urlsplit

    from PIL import Image

    from .test_documents_storage import planned
    from .test_final_quality import api

    app = p.apps["documentos"]
    monkeypatch.setitem(app.config, "STORAGE_PROVIDER", "local")
    monkeypatch.setitem(app.config, "STORAGE_LOCAL_ROOT", str(tmp_path))
    monkeypatch.setitem(app.config, "STORAGE_PUBLIC_BASE_URL", "https://example.test")
    shipment = planned(p)
    content = BytesIO()
    Image.new("RGB", (4, 4), "red").save(content, format="PNG")
    content = content.getvalue()
    path = "/api/v1/shipments/" + shipment["id"] + "/files"
    item = api(
        p,
        "documentos",
        path,
        {
            "mime_type": "image/png",
            "size": len(content),
            "sha256": hashlib.sha256(content).hexdigest(),
        },
        user="operator1",
        fmt=fmt,
    )
    assert "storage_provider" not in item["file"]
    client = app.test_client()
    assert (
        client.put(
            urlsplit(item["upload_url"]).path, data=content, content_type="image/png"
        ).status_code
        == 201
    )
    with clamd_receiver() as (port, scanned):
        monkeypatch.setitem(app.config, "CLAMD_HOST", "127.0.0.1")
        monkeypatch.setitem(app.config, "CLAMD_PORT", port)
        result = api(
            p,
            "documentos",
            "/api/v1/files/" + item["file"]["id"] + "/verify",
            user="operator1",
            fmt=fmt,
        )
        assert "storage_provider" not in result and result["status"] == "VERIFIED"
        assert scanned == [content]
    files = api(p, "documentos", path, user="operator1", fmt=fmt, method="GET")
    assert all("storage_provider" not in file for file in files["items"])
    download = api(
        p,
        "documentos",
        "/api/v1/files/" + item["file"]["id"] + "/download",
        user="operator1",
        fmt=fmt,
        method="GET",
    )
    assert client.get(urlsplit(download["download_url"]).path).data == content
