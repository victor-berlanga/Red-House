"""Local disk plus isolated PostgreSQL/Redis; ClamD is an explicit test receiver."""

import hashlib
from io import BytesIO
from urllib.parse import urlsplit
from uuid import uuid4

from PIL import Image

from .final_receivers import clamd_receiver
from .helpers import iso
from .test_final_operations import CONFIRM


def test_local_document_session_integrity_and_replay(p, tmp_path, monkeypatch):
    app = p.apps["documentos"]
    monkeypatch.setitem(app.config, "STORAGE_PROVIDER", "local")
    monkeypatch.setitem(app.config, "STORAGE_LOCAL_ROOT", str(tmp_path))
    monkeypatch.setitem(app.config, "STORAGE_PUBLIC_BASE_URL", "https://example.test")
    subject = p.ok(
        "identidad_acceso",
        "POST",
        "/api/v1/accreditations",
        user="admin1",
        data=dict(
            CONFIRM,
            issuer="Prueba",
            category="LICENSE",
            reference=uuid4().hex,
            valid_from=iso(days=-1),
            valid_until=iso(days=2),
        ),
    )
    image = BytesIO()
    Image.new("RGB", (4, 4), "red").save(image, format="PNG")
    content = image.getvalue()
    payload = dict(
        subject_kind="ACCREDITATION",
        subject_id=subject["id"],
        category="ACCREDITATION",
        mime_type="image/png",
        size=len(content),
        sha256=hashlib.sha256(content).hexdigest(),
        policy_reference="Prueba local",
    )
    idem = uuid4().hex
    item = p.ok(
        "documentos", "POST", "/api/v1/documents", user="admin1", data=payload, key=idem
    )
    # Un resultado idempotente anterior a 019 no tiene este campo interno.
    with p.owner("documentos") as conn:
        conn.execute(
            "UPDATE idempotency SET result=jsonb_set(result, '{row}', (result->'row')-'storage_provider') WHERE key=%s",
            (idem,),
        )
    repeated = p.ok(
        "documentos", "POST", "/api/v1/documents", user="admin1", data=payload, key=idem
    )
    assert repeated["id"] == item["id"]
    path = urlsplit(repeated["upload_url"]).path
    client = app.test_client()
    assert (
        client.put(path, data=b"x" * len(content), content_type="image/png").status_code
        == 422
    )
    assert (
        client.put(path, data=content, content_type="application/pdf").status_code
        == 422
    )
    assert client.put(path, data=content, content_type="image/png").status_code == 201
    assert client.put(path, data=content, content_type="image/png").status_code == 412
    with clamd_receiver() as (port, scanned):
        monkeypatch.setitem(app.config, "CLAMD_HOST", "127.0.0.1")
        monkeypatch.setitem(app.config, "CLAMD_PORT", port)
        verified = p.request(
            "documentos",
            "POST",
            "/api/v1/files/" + item["id"] + "/verify",
            user="admin1",
        )
        assert verified.status_code == 200, verified.text
    assert scanned == [content]
    download = p.ok(
        "documentos", "GET", "/api/v1/files/" + item["id"] + "/download", user="admin1"
    )
    download_path = urlsplit(download["download_url"]).path
    assert client.get(download_path).data == content
    object_path = tmp_path / item["id"]
    original = object_path.read_bytes()
    object_path.write_bytes(original[:-1] + bytes([original[-1] ^ 1]))
    assert client.get(download_path).status_code == 409
    object_path.write_bytes(original)
    assert client.get(download_path).data == content
    oversized = p.request(
        "documentos",
        "POST",
        "/api/v1/documents",
        user="admin1",
        data={"padding": "x" * 262145},
    )
    assert oversized.status_code == 413
    assert (
        p.request(
            "documentos",
            "GET",
            "/api/v1/files/" + item["id"] + "/download",
            user="admin2",
        ).status_code
        == 403
    )
    logout = p.request("identidad_acceso", "POST", "/api/v1/auth/logout", user="admin1")
    assert logout.status_code == 200
    assert client.get(download_path).status_code == 401
    renewed = p.ok(
        "identidad_acceso",
        "POST",
        "/api/v1/auth/login",
        user=None,
        data={"username": "admin1", "password": p.env.state["password"]},
    )
    p.tokens["admin1"] = renewed["access_token"]


def test_local_immutable_object_and_symlink(tmp_path):
    import pytest
    from flask import Flask
    from google.api_core.exceptions import PreconditionFailed
    from redhouse.errors import APIError
    from redhouse.storage import LocalBucket

    app = Flask(__name__)
    app.config["STORAGE_LOCAL_ROOT"] = str(tmp_path)
    identifier = str(uuid4())
    with app.app_context():
        blob = LocalBucket().blob("documents/" + identifier)
        blob.upload_from_string(
            b"datos", content_type="application/pdf", if_generation_match=0
        )
        generation = blob.generation
        assert blob.download_as_bytes(if_generation_match=generation) == b"datos"
        with pytest.raises(PreconditionFailed):
            blob.upload_from_string(
                b"otros", content_type="application/pdf", if_generation_match=0
            )
        with pytest.raises(APIError):
            blob.download_as_bytes(if_generation_match=generation + 1)
        assert blob.download_as_bytes(if_generation_match=generation) == b"datos"
        import os

        leftover = tmp_path / ("." + "a" * 48)
        os.link(tmp_path / identifier, leftover)
        assert blob.download_as_bytes(if_generation_match=generation) == b"datos"
        assert leftover.exists()
        linked = str(uuid4())
        (tmp_path / linked).symlink_to(tmp_path / identifier)
        with pytest.raises(APIError):
            LocalBucket().blob(linked).reload()
        with pytest.raises(APIError):
            LocalBucket().blob("../../invalid")
        fifo = str(uuid4())
        os.mkfifo(tmp_path / fifo)
        with pytest.raises(APIError):
            LocalBucket().blob(fifo).reload()
        folder = str(uuid4())
        (tmp_path / folder).mkdir()
        with pytest.raises(APIError):
            LocalBucket().blob(folder).reload()
        tmp_path.chmod(0o755)
        with pytest.raises(APIError):
            blob.reload()
        tmp_path.chmod(0o700)


def test_gateway_rejects_unsafe_binary_requests():
    from flask import Flask
    from src.integration.storage_gateway import install
    from werkzeug.test import Client, EnvironBuilder
    from werkzeug.wrappers import Response

    app = Flask(__name__)
    app.config["SERVICE_URLS"] = {"documentos": "http://127.0.0.1:1"}
    install(app)
    client = Client(app, Response)
    assert client.post("/storage/v1/objects/token").status_code == 405
    assert (
        client.put(
            "/storage/v1/objects/token", data=b"x" * (10 * 1024 * 1024 + 1)
        ).status_code
        == 413
    )
    builder = EnvironBuilder(path="/storage/v1/objects/token", method="PUT")
    environ = builder.get_environ()
    environ.pop("CONTENT_LENGTH", None)
    response = Response.from_app(app, environ)
    assert response.status_code == 411


def test_upgrade_v18_preserves_historical_gcs(p):
    from pathlib import Path

    import psycopg
    import pytest
    from psycopg import sql

    dbname = "migration_" + uuid4().hex
    admin_url = p.env.state["database_admin"]
    root = Path(__file__).resolve().parents[3]
    with psycopg.connect(admin_url, autocommit=True) as admin:
        admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(dbname)))
    try:
        with psycopg.connect(
            admin_url.rsplit("/", 1)[0] + "/" + dbname, autocommit=True
        ) as conn:
            conn.execute((root / "data/database/schema.sql").read_text())
            file_id, owner_id, job_id = uuid4(), uuid4(), uuid4()
            conn.execute("SET session_replication_role=replica")
            conn.execute(
                "INSERT INTO red_house.stored_file(file_id,owner_id,object_path,mime_type,size_bytes,sha256,current_status,generation) VALUES (%s,%s,'historical/path','image/png',3,%s,'VERIFIED','123')",
                (file_id, owner_id, "a" * 64),
            )
            conn.execute(
                "INSERT INTO red_house.export_jobs(id,tenant_id,user_id,report,format,rows) VALUES (%s,%s,%s,'INVENTORY','CSV','[]'::jsonb)",
                (job_id, uuid4(), owner_id),
            )
            conn.execute("SET session_replication_role=origin")
            conn.execute(
                (root / "apps/services/redhouse/shared_migrations/019.sql").read_text()
            )
            row = conn.execute(
                "SELECT object_path,generation,sha256,storage_provider FROM red_house.stored_file WHERE file_id=%s",
                (file_id,),
            ).fetchone()
            assert row == ("historical/path", "123", "a" * 64, "gcs")
            assert (
                conn.execute(
                    "SELECT storage_provider FROM red_house.export_jobs WHERE id=%s",
                    (job_id,),
                ).fetchone()[0]
                == "gcs"
            )
            with pytest.raises(psycopg.errors.RaiseException):
                conn.execute(
                    "UPDATE red_house.export_jobs SET storage_provider='local' WHERE id=%s",
                    (job_id,),
                )
            with pytest.raises(psycopg.errors.RaiseException):
                conn.execute(
                    "UPDATE red_house.stored_file SET storage_provider='local' WHERE file_id=%s",
                    (file_id,),
                )
            with pytest.raises(psycopg.errors.RaiseException):
                conn.execute(
                    "UPDATE red_house.stored_file SET object_path='changed' WHERE file_id=%s",
                    (file_id,),
                )
    finally:
        with psycopg.connect(admin_url, autocommit=True) as admin:
            admin.execute(sql.SQL("DROP DATABASE {}").format(sql.Identifier(dbname)))


def test_local_disk_write_failure_is_sanitized(tmp_path, monkeypatch):
    import errno
    import os

    import pytest
    from flask import Flask
    from redhouse.errors import APIError
    from redhouse.storage import LocalBucket, local_health

    app = Flask(__name__)
    app.config["STORAGE_LOCAL_ROOT"] = str(tmp_path)
    original = os.open

    def open_with_full_disk(path, *args, **kwargs):
        if isinstance(path, str) and path.startswith("."):
            raise OSError(errno.ENOSPC, "sensitive path")
        return original(path, *args, **kwargs)

    with app.app_context():
        monkeypatch.setattr(os, "open", open_with_full_disk)
        with pytest.raises(APIError) as failure:
            LocalBucket().blob(str(uuid4())).upload_from_string(
                b"data", content_type="application/pdf"
            )
        assert failure.value.status == 503
        assert "sensitive path" not in failure.value.message
        with pytest.raises(APIError) as health:
            local_health()
        assert health.value.status == 503


def test_health_checks_active_local_provider(tmp_path):
    from redhouse.app import base_app

    app = base_app(
        "documentos",
        {
            "DATABASE_URL": "unused",
            "JWT_PUBLIC_KEY": "unused",
            "STORAGE_PROVIDER": "local",
            "STORAGE_LOCAL_ROOT": str(tmp_path),
            "TESTING": True,
        },
    )
    client = app.test_client()
    assert client.get("/health/storage").status_code == 200
    tmp_path.chmod(0o755)
    assert client.get("/health/storage").status_code == 503
    tmp_path.chmod(0o700)
    assert client.get("/health/storage").status_code == 200


def test_interrupted_after_link_keeps_object_readable(tmp_path, monkeypatch):
    import errno
    import os

    import pytest
    from flask import Flask
    from google.api_core.exceptions import PreconditionFailed
    from redhouse.errors import APIError
    from redhouse.storage import LocalBucket

    app = Flask(__name__)
    app.config["STORAGE_LOCAL_ROOT"] = str(tmp_path)
    blob = LocalBucket().blob(str(uuid4()))
    original = os.unlink

    def fail_temporary(name, *args, **kwargs):
        if isinstance(name, str) and name.startswith("."):
            raise OSError(errno.EIO, "interrupted unlink")
        return original(name, *args, **kwargs)

    with app.app_context():
        with monkeypatch.context() as changes:
            changes.setattr(os, "unlink", fail_temporary)
            with pytest.raises(APIError):
                blob.upload_from_string(b"data", content_type="application/pdf")
        blob.reload()
        assert blob.download_as_bytes(if_generation_match=blob.generation) == b"data"
        assert len(list(tmp_path.glob(".*"))) == 1
        with pytest.raises(PreconditionFailed):
            blob.upload_from_string(b"data", content_type="application/pdf")


def test_local_document_xml_contract(p, tmp_path, monkeypatch):
    from .test_final_quality import api

    app = p.apps["documentos"]
    monkeypatch.setitem(app.config, "STORAGE_PROVIDER", "local")
    monkeypatch.setitem(app.config, "STORAGE_LOCAL_ROOT", str(tmp_path))
    monkeypatch.setitem(app.config, "STORAGE_PUBLIC_BASE_URL", "https://example.test")
    subject = p.ok(
        "identidad_acceso",
        "POST",
        "/api/v1/accreditations",
        user="admin1",
        data=dict(
            CONFIRM,
            issuer="Prueba XML",
            category="LICENSE",
            reference=uuid4().hex,
            valid_from=iso(days=-1),
            valid_until=iso(days=2),
        ),
    )
    image = BytesIO()
    Image.new("RGB", (4, 4), "red").save(image, format="PNG")
    content = image.getvalue()
    prepared = api(
        p,
        "documentos",
        "/api/v1/documents",
        {
            "subject_kind": "ACCREDITATION",
            "subject_id": subject["id"],
            "category": "ACCREDITATION",
            "mime_type": "image/png",
            "size": len(content),
            "sha256": hashlib.sha256(content).hexdigest(),
            "policy_reference": "Política XML",
        },
        user="admin1",
        fmt="xml",
    )
    client = app.test_client()
    assert (
        client.put(
            urlsplit(prepared["upload_url"]).path,
            data=content,
            content_type="image/png",
        ).status_code
        == 201
    )
    with clamd_receiver() as (port, scanned):
        monkeypatch.setitem(app.config, "CLAMD_HOST", "127.0.0.1")
        monkeypatch.setitem(app.config, "CLAMD_PORT", port)
        row = api(
            p,
            "documentos",
            "/api/v1/files/" + prepared["id"] + "/verify",
            user="admin1",
            fmt="xml",
        )
        assert row["status"] == "VERIFIED" and scanned == [content]
    download = api(
        p,
        "documentos",
        "/api/v1/files/" + prepared["id"] + "/download",
        user="admin1",
        fmt="xml",
        method="GET",
    )
    assert client.get(urlsplit(download["download_url"]).path).data == content


def test_configure_local_preserves_existing_gcs(tmp_path):
    import json
    import sys

    import pytest

    sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[3]))
    from deployment.configure_local_storage import configure

    config = tmp_path / "documentos.json"
    config.write_text(
        json.dumps(
            {
                "GCS_BUCKET": "historical",
                "GCS_PROJECT": "project",
                "SERVICE_PRIVATE_KEY": "unchanged",
            }
        )
    )
    directory = tmp_path / "objects"
    configure(config, directory, "https://example.test")
    data = json.loads(config.read_text())
    assert (
        data["GCS_BUCKET"] == "historical"
        and data["SERVICE_PRIVATE_KEY"] == "unchanged"
    )
    assert data["STORAGE_PROVIDER"] == "local" and data["STORAGE_LOCAL_ROOT"] == str(
        directory
    )
    with pytest.raises(ValueError):
        configure(config, directory, "http://example.test")
    directory.chmod(0o755)
    with pytest.raises(ValueError):
        configure(config, directory, "https://example.test")
    directory.chmod(0o700)
