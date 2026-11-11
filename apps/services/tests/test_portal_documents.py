"""Contratos y formularios con doble GCS explícito; no acredita almacenamiento real."""

from uuid import uuid4
import hashlib
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from .test_web_integration import web as web, login, post, form
from .test_final_delivery_documents import TestBucket
from .helpers import iso


def test_document_conservation_form_pending_and_foreign_download(p, web, monkeypatch):
    app = p.apps["documentos"]
    monkeypatch.setitem(app.config, "GCS_BUCKET", "private-test")
    monkeypatch.setitem(app.extensions, "gcs_client", TestBucket())
    confirm = dict(human_confirmation=True, reason="Ensayo sintético")
    accreditation = p.ok(
        "identidad_acceso",
        "POST",
        "/api/v1/accreditations",
        user="admin1",
        data=dict(
            confirm,
            issuer="Emisor ficticio",
            category="LICENSE",
            reference="SYN-" + uuid4().hex,
            valid_from=iso(days=-1),
            valid_until=iso(days=2),
        ),
    )
    document = p.ok(
        "documentos",
        "POST",
        "/api/v1/documents",
        user="admin1",
        data=dict(
            subject_kind="ACCREDITATION",
            subject_id=accreditation["id"],
            category="ACCREDITATION",
            mime_type="image/png",
            size=10,
            sha256=hashlib.sha256(b"not-upload").hexdigest(),
            policy_reference="Conservación ficticia",
        ),
    )
    client = login(web, p, "admin1")
    path = "/documentos/" + document["id"]
    assert client.get(path).status_code == 200
    assert (
        p.request(
            "documentos",
            "GET",
            "/api/v1/files/" + document["id"] + "/download",
            user="admin1",
        ).status_code
        == 409
    )
    assert login(web, p, "admin2").get(path).status_code == 403
    assert (
        p.request(
            "documentos",
            "GET",
            "/api/v1/files/" + document["id"] + "/download",
            user="admin2",
        ).status_code
        == 403
    )
    retention = (
        datetime.now(ZoneInfo("America/Monterrey")) + timedelta(days=7)
    ).strftime("%Y-%m-%dT%H:%M")
    post(
        client,
        path + "/conservacion",
        dict(
            legal_hold="on",
            retention_until=retention,
            policy_reference="Bloqueo de ensayo",
            human_confirmation="on",
            reason="Conservar documento ficticio",
        ),
    )
    saved = p.ok(
        "documentos",
        "GET",
        "/api/v1/documents/" + document["id"] + "/status",
        user="admin1",
    )
    assert saved["legal_hold"] and saved["policy_version"] == 2
    values = form(client, path + "/conservacion")
    values.update(
        policy_reference="Intentar retirar bloqueo",
        human_confirmation="on",
        reason="Ensayo negativo",
    )
    values.pop("legal_hold", None)
    assert client.post(path + "/conservacion", data=values).status_code == 409


def test_report_formats_preserve_scope_timezone_unknown_and_formula():
    from redhouse.report_formats import render
    from io import BytesIO
    from zipfile import ZipFile
    from pypdf import PdfReader

    rows = [
        {
            "label": "  =SUM(1,2)",
            "created_at": "2026-11-06T12:30:00Z",
            "measurement": None,
        }
    ]
    for zone, expected in (
        ("America/Monterrey", "06:30:00-06:00"),
        ("Europe/Madrid", "13:30:00+01:00"),
    ):
        context = dict(
            timezone=zone, filters={"q": "SYNTHETIC"}, scope="OWN", row_count=1
        )
        csv = render(rows, "CSV", context).decode("utf-8-sig")
        assert expected in csv and "Sin dato" in csv and "'  =SUM" in csv
        with ZipFile(BytesIO(render(rows, "XLSX", context))) as archive:
            xml = archive.read("xl/worksheets/sheet1.xml").decode()
            assert expected in xml and "<f>" not in xml and "Sin dato" in xml
        pdf = "\n".join(
            p.extract_text()
            for p in PdfReader(BytesIO(render(rows, "PDF", context))).pages
        )
        assert expected in pdf and "Sin dato" in pdf and "SYNTHETIC" in pdf
