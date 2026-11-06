import hashlib
import json
import time
from io import BytesIO
from uuid import uuid4
from zipfile import ZipFile

import pytest
from flask import g
from PIL import Image
from pypdf import PdfReader

from .final_receivers import clamd_receiver, smtp_receiver, push_receiver
from .helpers import iso, resource
from .test_final_identity import email_token
from .test_final_operations import CONFIRM
from .test_final_quality import api


class TestBucket:
    __test__ = False
    """Doble del SDK GCS. Se prueba aparte el adaptador ClamD por TCP real."""

    def __init__(self):
        self.objects = {}

    def bucket(self, _):
        return self

    def blob(self, path, generation=None):
        bucket = self

        class Blob:
            def __init__(self):
                self.path = path
                self.generation = generation

            def reload(self, **_):
                from google.api_core.exceptions import NotFound

                if path not in bucket.objects:
                    raise NotFound("missing")
                payload, mime = bucket.objects[path]
                self.size, self.content_type, self.generation = len(payload), mime, 1

            def upload_from_string(
                self, payload, content_type, if_generation_match, **_
            ):
                from google.api_core.exceptions import PreconditionFailed

                assert if_generation_match == 0
                if path in bucket.objects:
                    raise PreconditionFailed("exists")
                bucket.objects[path] = payload, content_type
                self.reload()

            def download_as_bytes(self, if_generation_match, **_):
                assert int(if_generation_match) == 1
                return bucket.objects[path][0]

            def generate_signed_url(self, **kwargs):
                assert kwargs["version"] == "v4"
                return (
                    "https://private-storage.example.invalid/"
                    + path
                    + "?method="
                    + kwargs["method"]
                )

        return Blob()


@pytest.mark.parametrize("fmt", ["json", "xml"])
def test_smtp_push_retry_escalation_dedup_and_close(p, monkeypatch, fmt):
    from ms_identidad_acceso.strong_auth import deliver_pending
    from ms_alertas.delivery import process
    from redhouse.events import emit

    identity, alerts = p.apps["identidad_acceso"], p.apps["alertas"]
    # Un suscriptor propio por ejecución; evitar mutar cuentas compartidas de la suite.
    name = "notice-" + uuid4().hex[:12]
    password = "Synthetic-notification-password"
    user = api(
        p,
        "identidad_acceso",
        "/api/v1/users",
        {
            "username": name,
            "password": password,
            "tenant_id": p.env.state["tenants"][0],
            "role": "OPERATOR",
        },
        "admin1",
        fmt,
    )
    session = api(
        p,
        "identidad_acceso",
        "/api/v1/auth/login",
        {"username": name, "password": password},
        None,
        fmt,
    )
    p.tokens[name] = session["access_token"]
    with smtp_receiver() as (port, emails), push_receiver() as (url, pushes, receiver):
        for app in (identity, alerts):
            for key, value in {
                "SMTP_HOST": "127.0.0.1",
                "SMTP_PORT": port,
                "SMTP_FROM": "tests@redhouse.invalid",
                "SMTP_TEST_RECEIVER": True,
                "PUSH_ADAPTER_URL": url,
                "PUSH_TEST_RECEIVER": True,
            }.items():
                monkeypatch.setitem(app.config, key, value)
        api(
            p,
            "identidad_acceso",
            "/api/v1/auth/contact",
            {"password": password, "email": name + "@example.invalid"},
            name,
            fmt,
        )
        with identity.app_context():
            deliver_pending()
        api(
            p,
            "identidad_acceso",
            "/api/v1/auth/contact/verify",
            {"token": email_token(emails[-1])},
            name,
            fmt,
        )
        email_sub = api(
            p, "alertas", "/api/v1/alert-subscriptions", {"channel": "EMAIL"}, name, fmt
        )
        push_sub = api(
            p,
            "alertas",
            "/api/v1/alert-subscriptions",
            {"channel": "PUSH", "push_destination": "test-device-" + uuid4().hex},
            name,
            fmt,
        )
        code = "TEST_FINAL_" + uuid4().hex[:10].upper()
        policy = api(
            p,
            "alertas",
            "/api/v1/alert-policies",
            {
                "message_code": code,
                "severity": "CRITICAL",
                "reminder_seconds": 1,
                "escalate_seconds": 2,
                "escalation_role": "OPERATOR",
                "source": "Política operativa sintética para receptor local",
                "effective_at": iso(),
            },
            "admin1",
            fmt,
        )
        with p.apps["donantes"].app_context():
            from redhouse.db import transaction

            g.actor = {
                "id": p.env.state["accounts"]["medical1"]["id"],
                "tenant_id": p.env.state["tenants"][0],
                "region_id": p.env.state["region_id"],
            }
            with transaction() as conn:
                emit(
                    conn, code, str(uuid4()), g.actor["tenant_id"], targets=("alertas",)
                )
        p.drain()
        receiver["fail"] = True
        with alerts.app_context():
            process(10000)
        with p.owner("alertas") as conn:
            alert_id = str(
                conn.execute(
                    "SELECT id FROM alerts WHERE message_code=%s", (code,)
                ).fetchone()[0]
            )
            pending = conn.execute(
                "SELECT last_error FROM alert_deliveries WHERE alert_id=%s AND status='PENDING'",
                (alert_id,),
            ).fetchall()
            assert pending and all(row[0] == "push_unavailable" for row in pending), (
                pending
            )
        receiver["fail"] = False
        time.sleep(2.2)
        with alerts.app_context():
            process(10000)
            process(10000)
        deliveries = api(
            p,
            "alertas",
            f"/api/v1/alerts/{alert_id}/deliveries",
            user=name,
            fmt=fmt,
            method="GET",
        )
        assert len(deliveries["items"]) == 6
        assert all(d["status"] == "ACCEPTED_BY_ADAPTER" for d in deliveries["items"])
        matching = [v for v in pushes if v["message_code"] == code]
        assert len(matching) == 3
        assert len({v["event_id"] for v in matching}) == 3
        api(p, "alertas", f"/api/v1/alerts/{alert_id}/acknowledge", user=name, fmt=fmt)
        api(p, "alertas", f"/api/v1/alerts/{alert_id}/close", CONFIRM, name, fmt)
        api(
            p,
            "alertas",
            "/api/v1/alert-policies/" + policy["id"],
            user="admin1",
            fmt=fmt,
            method="GET",
        )
        api(
            p,
            "alertas",
            "/api/v1/alert-subscriptions",
            user=name,
            fmt=fmt,
            method="GET",
        )
        for subscription in (email_sub, push_sub):
            api(
                p,
                "alertas",
                f"/api/v1/alert-subscriptions/{subscription['id']}/revoke",
                CONFIRM,
                name,
                fmt,
            )
    p.tokens.pop(name)


@pytest.mark.parametrize("fmt", ["json", "xml"])
def test_documents_scan_private_access_and_export_formats(p, monkeypatch, fmt):
    from ms_documentos.reports import process

    transport = p.apps["documentos"]
    storage = TestBucket()
    monkeypatch.setitem(transport.config, "GCS_BUCKET", "private-test")
    monkeypatch.setitem(transport.extensions, "gcs_client", storage)
    accreditation = api(
        p,
        "identidad_acceso",
        "/api/v1/accreditations",
        {
            **CONFIRM,
            "issuer": "Emisor ficticio",
            "category": "LICENSE",
            "reference": "Documento sintético",
            "valid_from": iso(days=-1),
            "valid_until": iso(days=1),
        },
        "admin1",
        fmt,
    )
    content = BytesIO()
    Image.new("RGB", (4, 4), color="red").save(content, format="PNG")
    payload = content.getvalue()
    document = api(
        p,
        "transporte",
        "/api/v1/documents",
        {
            "subject_kind": "ACCREDITATION",
            "subject_id": accreditation["id"],
            "category": "ACCREDITATION",
            "mime_type": "image/png",
            "size": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "policy_reference": "Política sintética; no borrar",
        },
        "admin1",
        fmt,
    )
    with p.owner("documentos") as conn:
        path = conn.execute(
            "SELECT object_path FROM files WHERE id=%s", (document["id"],)
        ).fetchone()[0]
    storage.objects[path] = payload, "image/png"
    assert (
        p.request(
            "transporte",
            "GET",
            f"/api/v1/files/{document['id']}/download",
            user="admin1",
        ).status_code
        == 409
    )
    assert (
        p.request(
            "transporte", "GET", "/api/v1/documents/" + document["id"], user="admin2"
        ).status_code
        == 403
    )
    with clamd_receiver() as (port, scanned):
        monkeypatch.setitem(transport.config, "CLAMD_HOST", "127.0.0.1")
        monkeypatch.setitem(transport.config, "CLAMD_PORT", port)
        verified = api(
            p,
            "transporte",
            f"/api/v1/files/{document['id']}/verify",
            user="admin1",
            fmt=fmt,
        )
        assert verified["status"] == "VERIFIED" and scanned == [payload]
        api(
            p,
            "transporte",
            f"/api/v1/files/{document['id']}/download",
            user="admin1",
            fmt=fmt,
            method="GET",
        )
        api(
            p,
            "transporte",
            f"/api/v1/documents?subject_kind=ACCREDITATION&subject_id={accreditation['id']}",
            user="admin1",
            fmt=fmt,
            method="GET",
        )
        resource(p)
        for format in ("CSV", "PDF", "XLSX"):
            job = api(
                p,
                "transporte",
                "/api/v1/export-jobs",
                {
                    "report": "EXPIRY",
                    "format": format,
                    "from_at": iso(),
                    "until_at": iso(days=10),
                },
                "medical1",
                fmt,
            )
            assert job["status"] == "PENDING" and job["file_id"] is None
            assert (
                p.request(
                    "transporte",
                    "GET",
                    "/api/v1/export-jobs/" + job["id"],
                    user="medical2",
                ).status_code
                == 403
            )
            with transport.app_context():
                process()
            ready = api(
                p,
                "transporte",
                "/api/v1/export-jobs/" + job["id"],
                user="medical1",
                fmt=fmt,
                method="GET",
            )
            assert ready["status"] == "COMPLETE", ready
            api(
                p,
                "transporte",
                f"/api/v1/files/{ready['file_id']}/download",
                user="medical1",
                fmt=fmt,
                method="GET",
            )
            with p.owner("documentos") as conn:
                report_path = conn.execute(
                    "SELECT object_path FROM files WHERE id=%s", (ready["file_id"],)
                ).fetchone()[0]
            output = storage.objects[report_path][0]
            if format == "PDF":
                assert "Red House" in PdfReader(BytesIO(output)).pages[0].extract_text()
            elif format == "XLSX":
                with ZipFile(BytesIO(output)) as archive:
                    assert "xl/worksheets/sheet1.xml" in archive.namelist()
            else:
                assert "expires_at" in output.decode("utf-8-sig")
        api(
            p,
            "transporte",
            "/api/v1/export-jobs",
            user="medical1",
            fmt=fmt,
            method="GET",
        )
    assert len([path for path in storage.objects if path.startswith("documents/")]) == 1
    assert len([path for path in storage.objects if path.startswith("reports/")]) >= 3


def test_clamd_infected_unavailable_and_formula_injection(p, monkeypatch):
    from redhouse.malware import scan
    from redhouse.errors import APIError
    from redhouse.report_formats import render

    app = p.apps["documentos"]
    with clamd_receiver() as (port, received):
        monkeypatch.setitem(app.config, "CLAMD_HOST", "127.0.0.1")
        monkeypatch.setitem(app.config, "CLAMD_PORT", port)
        with app.app_context():
            assert scan(b"SYNTHETIC_MALWARE") == "INFECTED"
    with app.app_context(), pytest.raises(APIError, match="motor"):
        scan(b"valid")
    assert "'=SUM" in render([{"value": "=SUM(1,2)"}], "CSV").decode("utf-8-sig")
