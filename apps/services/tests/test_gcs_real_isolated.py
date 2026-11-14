"""GCS real: solo objetos sintéticos nuevos; limpieza por generación exacta."""

import hashlib
import json
import os
from io import BytesIO
from urllib.parse import parse_qs, urlsplit
from uuid import uuid4

import jsonschema
import pytest
import requests
from google.api_core.exceptions import NotFound
from PIL import Image
from redhouse.examples import request_xml
from redhouse.output_schemas import result_schema
from redhouse.xml_response import validate_response

from .helpers import iso
from .test_final_operations import CONFIRM

BUCKET = "red-house-evidencias-sistemas-integracion-01"


@pytest.mark.skipif(
    os.environ.get("REDHOUSE_TEST_GCS_BUCKET") != BUCKET
    or not os.environ.get("REDHOUSE_TEST_CLAMD_PORT"),
    reason="Requiere bucket autorizado y ClamD real aislado",
)
@pytest.mark.parametrize("fmt", ["json", "xml"])
def test_new_private_gcs_document(p, monkeypatch, tmp_path, fmt):
    app = p.apps["documentos"]
    for key, value in {
        "STORAGE_PROVIDER": "gcs",
        "GCS_BUCKET": BUCKET,
        "GCS_PROJECT": "sistemas-integracion-01",
        "CLAMD_HOST": "127.0.0.1",
        "CLAMD_PORT": int(os.environ["REDHOUSE_TEST_CLAMD_PORT"]),
        "CLAMD_VERSION_TIMEZONE": "UTC",
        "CLAMD_SIGNATURE_MAX_AGE_SECONDS": 172800,
    }.items():
        monkeypatch.setitem(app.config, key, value)

    def call(method, path, *, data=None, key=None):
        headers = {
            "Accept": "application/" + fmt,
            "Authorization": "Bearer " + p.tokens["admin1"],
            "Idempotency-Key": key or uuid4().hex,
        }
        body = None
        if data is not None:
            headers["Content-Type"] = "application/" + fmt
            body = request_xml(data).encode() if fmt == "xml" else None
        response = requests.request(
            method,
            p.urls["documentos"] + path,
            headers=headers,
            data=body,
            json=data if fmt == "json" else None,
            timeout=30,
            allow_redirects=False,
        )
        assert response.status_code < 300
        name, _ = app.url_map.bind("localhost").match(path.split("?")[0], method=method)
        contract = next(
            item for item in app.extensions["contracts"] if item["name"] == name
        )
        schema = contract["result"] or result_schema("documentos", name)
        try:
            if fmt == "xml":
                value = validate_response(
                    response.content, {"type": "object", "properties": {"data": schema}}
                )["data"]
            else:
                value = response.json()["data"]
                jsonschema.validate(value, schema)
        except Exception:  # noqa: BLE001 - las URLs firmadas no deben aparecer en fallos
            pytest.fail(
                "Contrato público inválido; respuesta omitida por privacidad.",
                pytrace=False,
            )
        return value

    def transfer(method, url, **kwargs):
        try:
            return requests.request(
                method, url, timeout=30, allow_redirects=False, **kwargs
            )
        except requests.RequestException:
            raise RuntimeError(
                "Transferencia GCS incierta; detalles omitidos."
            ) from None

    subject = p.ok(
        "identidad_acceso",
        "POST",
        "/api/v1/accreditations",
        user="admin1",
        data=dict(
            CONFIRM,
            issuer="Ensayo GCS sintético",
            category="LICENSE",
            reference=uuid4().hex,
            valid_from=iso(days=-1),
            valid_until=iso(days=1),
        ),
    )
    image = BytesIO()
    Image.new("RGB", (4, 4), "red").save(image, format="PNG")
    content = image.getvalue()
    digest = hashlib.sha256(content).hexdigest()
    payload = {
        "subject_kind": "ACCREDITATION",
        "subject_id": subject["id"],
        "category": "ACCREDITATION",
        "mime_type": "image/png",
        "size": len(content),
        "sha256": digest,
        "policy_reference": "Ensayo sintético aislado",
    }
    key = uuid4().hex
    created = call("POST", "/api/v1/documents", data=payload, key=key)
    repeated = call("POST", "/api/v1/documents", data=payload, key=key)
    assert repeated["id"] == created["id"]
    with p.owner("documentos") as conn:
        row = conn.execute(
            "SELECT object_path,storage_provider FROM files WHERE id=%s",
            (created["id"],),
        ).fetchone()
    expected = f"documents/{p.env.state['tenants'][0]}/{created['id']}"
    assert row == (expected, "gcs")
    from redhouse.storage import bucket

    with app.app_context():
        blob = bucket().blob(expected)
    attempted = False
    outcome_known = False
    uploaded_by_test = False
    upload_generation = None
    cleaned = False
    journal = tmp_path / "gcs-cleanup.private.json"

    def check_target(url):
        try:
            parsed = urlsplit(url)
            valid = (
                parsed.scheme == "https"
                and parsed.hostname == "storage.googleapis.com"
                and parsed.port in (None, 443)
                and not parsed.username
                and not parsed.password
                and not parsed.fragment
                and parsed.path == f"/{BUCKET}/{expected}"
                and parse_qs(parsed.query).get("X-Goog-Expires") == ["300"]
            )
        except ValueError:
            valid = False
        if not valid:
            raise RuntimeError("Destino o TTL GCS inválido; capacidad omitida.")

    try:
        url = created["upload_url"]
        check_target(url)
        assert created["upload_headers"]["x-goog-if-generation-match"] == "0"
        descriptor = os.open(journal, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(descriptor, "w") as output:
            json.dump({"bucket": BUCKET, "object": expected, "sha256": digest}, output)
            output.flush()
            os.fsync(output.fileno())
        attempted = True
        uploaded = transfer("PUT", url, data=content, headers=created["upload_headers"])
        outcome_known = True
        uploaded_by_test = uploaded.status_code == 200
        assert uploaded.status_code == 200
        value = uploaded.headers.get("x-goog-generation", "")
        if value.isdigit() and int(value) > 0:
            upload_generation = int(value)
            next_journal = journal.with_name("gcs-cleanup.next.private.json")
            descriptor = os.open(
                next_journal, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600
            )
            with os.fdopen(descriptor, "w") as output:
                json.dump(
                    {
                        "bucket": BUCKET,
                        "object": expected,
                        "sha256": digest,
                        "generation": upload_generation,
                    },
                    output,
                )
                output.flush()
                os.fsync(output.fileno())
            os.replace(next_journal, journal)
        assert upload_generation is not None, "Carga sin generación confirmada."
        assert (
            transfer(
                "PUT", url, data=content, headers=created["upload_headers"]
            ).status_code
            == 412
        )
        verify_key = uuid4().hex
        verified = call(
            "POST", f"/api/v1/files/{created['id']}/verify", data={}, key=verify_key
        )
        assert verified["status"] == "VERIFIED" and verified["sha256"] == digest
        assert (
            call(
                "POST", f"/api/v1/files/{created['id']}/verify", data={}, key=verify_key
            )["id"]
            == created["id"]
        )
        metadata = call("GET", f"/api/v1/documents/{created['id']}/verified")
        assert metadata["analysis"] == "CLEAN" and metadata["sha256"] == digest
        with app.app_context():
            blob.reload(timeout=15, retry=None)
            generation = str(blob.generation)
        assert metadata["generation"] == generation
        assert blob.size == len(content) and blob.content_type == "image/png"
        assert (
            p.request(
                "documentos",
                "GET",
                f"/api/v1/files/{created['id']}/download",
                user="medical2",
            ).status_code
            == 403
        )
        access = call("GET", f"/api/v1/files/{created['id']}/download")
        assert access["expires_in"] == 300
        check_target(access["download_url"])
        downloaded = transfer("GET", access["download_url"])
        assert downloaded.status_code == 200 and downloaded.content == content
        assert hashlib.sha256(downloaded.content).hexdigest() == digest
        assert downloaded.headers["Content-Type"].split(";", 1)[0] == "image/png"
        with p.owner("documentos") as conn:
            status = conn.execute(
                "SELECT status,engine_version,signature_version,signature_at FROM file_scans WHERE file_id=%s ORDER BY created_at DESC LIMIT 1",
                (created["id"],),
            ).fetchone()
        assert status[0] == "CLEAN" and all(status[1:])
        assert (
            p.request(
                "identidad_acceso", "POST", "/api/v1/auth/logout", user="admin1"
            ).status_code
            == 200
        )
        assert (
            p.request(
                "documentos",
                "GET",
                f"/api/v1/files/{created['id']}/download",
                user="admin1",
            ).status_code
            == 401
        )
        # GCS valida la firma durante su TTL; logout impide URLs nuevas, pero
        # no revoca inmediatamente una capacidad que ya fue emitida.
        previous = transfer("GET", access["download_url"])
        assert previous.status_code == 200 and previous.content == content
    finally:
        if uploaded_by_test and upload_generation is not None:
            try:
                with app.app_context():
                    blob.reload(
                        if_generation_match=upload_generation, timeout=15, retry=None
                    )
                    actual = blob.download_as_bytes(
                        if_generation_match=upload_generation, timeout=15, retry=None
                    )
                    if hashlib.sha256(actual).hexdigest() != digest:
                        raise RuntimeError(
                            "El objeto sintético no coincide; no se elimina."
                        )
                    blob.delete(
                        if_generation_match=upload_generation, timeout=15, retry=None
                    )
                    try:
                        blob.reload(timeout=15, retry=None)
                    except NotFound:
                        cleaned = True
            except NotFound:
                cleaned = True
        elif not attempted or (outcome_known and not uploaded_by_test):
            cleaned = True
        assert cleaned, "No se confirmó la limpieza del objeto sintético."
        if journal.exists():
            journal.unlink()
        if (
            not p.tokens.get("admin1")
            or p.request(
                "identidad_acceso", "GET", "/api/v1/auth/me", user="admin1"
            ).status_code
            == 401
        ):
            login = p.ok(
                "identidad_acceso",
                "POST",
                "/api/v1/auth/login",
                user=None,
                data={"username": "admin1", "password": p.env.state["password"]},
            )
            p.tokens["admin1"] = login["access_token"]
