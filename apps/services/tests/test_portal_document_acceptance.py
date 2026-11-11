"""Aceptación local dirigida: SQL/Redis reales, GCS y ClamD dobles explícitos.

No acredita GCS, firmas de malware reales ni recorridos Chrome integrados.
"""

import hashlib
from io import BytesIO
from uuid import uuid4

import pytest
from PIL import Image

from .final_receivers import clamd_receiver
from .helpers import iso
from .test_final_delivery_documents import TestBucket
from .test_final_operations import CONFIRM


class RecordingBucket(TestBucket):
    """Registra la generación que el propietario pide firmar; no firma en GCS."""

    def __init__(self):
        super().__init__()
        self.downloads = []
        self.unavailable = False

    def blob(self, path, generation=None):
        blob = super().blob(path, generation)
        original = blob.generate_signed_url
        reload = blob.reload

        def sign(**kwargs):
            if kwargs["method"] == "GET":
                self.downloads.append((path, generation))
            return original(**kwargs)

        def load(**kwargs):
            if self.unavailable:
                raise ConnectionError("Fallo sintético de almacenamiento")
            return reload(**kwargs)

        blob.generate_signed_url = sign
        blob.reload = load
        return blob


@pytest.fixture
def documents(p, monkeypatch):
    name = "doc-accept-" + uuid4().hex[:12]
    password = p.env.state["password"]
    p.ok(
        "identidad_acceso",
        "POST",
        "/api/v1/users",
        user="admin1",
        data={
            "username": name,
            "password": password,
            "role": "ADMIN",
            "tenant_id": p.env.state["tenants"][0],
        },
    )
    session = p.ok(
        "identidad_acceso",
        "POST",
        "/api/v1/auth/login",
        user=None,
        data={"username": name, "password": password},
    )
    p.tokens[name] = session["access_token"]
    app, storage = p.apps["documentos"], RecordingBucket()
    monkeypatch.setitem(app.config, "GCS_BUCKET", "explicit-test-double")
    monkeypatch.setitem(app.extensions, "gcs_client", storage)
    subject = p.ok(
        "identidad_acceso",
        "POST",
        "/api/v1/accreditations",
        user=name,
        data=dict(
            CONFIRM,
            issuer="Emisor ficticio",
            category="LICENSE",
            reference="SYN-" + uuid4().hex,
            valid_from=iso(days=-1),
            valid_until=iso(days=2),
        ),
    )
    image = BytesIO()
    Image.new("RGB", (4, 4), color="red").save(image, format="PNG")
    payload = image.getvalue()
    data = {
        "subject_kind": "ACCREDITATION",
        "subject_id": subject["id"],
        "category": "ACCREDITATION",
        "mime_type": "image/png",
        "size": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "policy_reference": "Política sintética de aceptación",
    }

    def prepare(**overrides):
        row = p.ok(
            "documentos",
            "POST",
            "/api/v1/documents",
            user=name,
            data=dict(data, **overrides),
        )
        with p.owner("documentos") as conn:
            path = conn.execute(
                "SELECT object_path FROM files WHERE id=%s", (row["id"],)
            ).fetchone()[0]
        storage.objects[path] = payload, "image/png"
        return row, path

    try:
        yield name, app, storage, data, prepare
    finally:
        p.tokens.pop(name, None)


def test_document_versions_conflict_and_hold_are_persistent(p, documents):
    name, _, _, data, prepare = documents
    first, _ = prepare()
    second, _ = prepare(supersedes=first["id"])
    assert second["metadata"]["version"] == 2
    assert second["metadata"]["supersedes"] == first["id"]
    assert (
        p.request(
            "documentos",
            "POST",
            "/api/v1/documents",
            user=name,
            data=dict(data, supersedes=first["id"]),
        ).status_code
        == 412
    )
    assert (
        p.request(
            "documentos",
            "POST",
            "/api/v1/documents",
            user="admin2",
            data=dict(data, supersedes=second["id"]),
        ).status_code
        == 403
    )
    path = f"/api/v1/documents/{first['id']}/conservation"
    policy = dict(
        CONFIRM,
        policy_version=1,
        retention_until=iso(days=7),
        legal_hold=True,
        policy_reference="Bloqueo sintético",
    )
    saved = p.ok("documentos", "POST", path, user=name, data=policy)
    assert saved["legal_hold"] and saved["policy_version"] == 2
    assert (
        p.request("documentos", "POST", path, user=name, data=policy).status_code == 412
    )
    assert (
        p.request(
            "documentos",
            "POST",
            path,
            user=name,
            data=dict(policy, policy_version=2, retention_until=None, legal_hold=False),
        ).status_code
        == 409
    )
    with p.owner("documentos") as conn:
        rows = conn.execute(
            "SELECT id::text,version,supersedes::text,legal_hold,policy_version "
            "FROM document_metadata WHERE subject_id=%s ORDER BY version",
            (data["subject_id"],),
        ).fetchall()
        assert rows == [
            (first["id"], 1, None, True, 2),
            # La migración 010 conserva bloqueo por defecto en cada versión.
            (second["id"], 2, first["id"], True, 1),
        ]
        assert (
            conn.execute(
                "SELECT count(*) FROM activity_events WHERE event->>'action'="
                "'DOCUMENT_CONSERVATION_CHANGED' AND event->>'resource_id'=%s",
                (first["id"],),
            ).fetchone()[0]
            == 1
        )


def test_document_exact_analysis_generation_and_revoked_download(
    p, documents, monkeypatch
):
    name, app, storage, data, prepare = documents
    doc, path = prepare()
    identifier = doc["id"]
    with clamd_receiver() as (port, scanned):
        monkeypatch.setitem(app.config, "CLAMD_HOST", "127.0.0.1")
        monkeypatch.setitem(app.config, "CLAMD_PORT", port)
        p.ok("documentos", "POST", f"/api/v1/files/{identifier}/verify", user=name)
        assert len(scanned) == 1
    url = f"/api/v1/files/{identifier}/download"
    p.ok("documentos", "GET", url, user=name)
    assert storage.downloads == [(path, 1)]
    # Simula desajuste persistido: el análisis de otra generación/hash no autoriza.
    for generation, digest in (("2", data["sha256"]), ("1", "0" * 64)):
        with p.owner("documentos") as conn:
            conn.execute(
                "UPDATE files SET generation=%s,sha256=%s WHERE id=%s",
                (generation, digest, identifier),
            )
        response = p.request("documentos", "GET", url, user=name)
        assert response.status_code == 409
        assert storage.downloads == [(path, 1)]
    with p.owner("documentos") as conn:
        conn.execute(
            "UPDATE files SET generation='1',sha256=%s WHERE id=%s",
            (data["sha256"], identifier),
        )
    assert p.request("documentos", "GET", url, user="admin2").status_code == 403
    p.ok("identidad_acceso", "POST", "/api/v1/auth/logout", user=name)
    assert p.request("documentos", "GET", url, user=name).status_code == 401
    assert storage.downloads == [(path, 1)]


@pytest.mark.parametrize("dependency", ["scanner", "storage"])
def test_document_dependency_failure_blocks_download_then_recovers(
    p, documents, monkeypatch, dependency
):
    name, app, storage, _, prepare = documents
    doc, _ = prepare()
    verify = f"/api/v1/files/{doc['id']}/verify"
    download = f"/api/v1/files/{doc['id']}/download"
    if dependency == "scanner":
        monkeypatch.setitem(app.config, "CLAMD_HOST", "")
    else:
        storage.unavailable = True
    assert p.request("documentos", "POST", verify, user=name).status_code == 503
    assert p.request("documentos", "GET", download, user=name).status_code == 409
    assert not storage.downloads
    with p.owner("documentos") as conn:
        assert (
            conn.execute(
                "SELECT status FROM files WHERE id=%s", (doc["id"],)
            ).fetchone()[0]
            != "VERIFIED"
        )
    storage.unavailable = False
    with clamd_receiver() as (port, _):
        monkeypatch.setitem(app.config, "CLAMD_HOST", "127.0.0.1")
        monkeypatch.setitem(app.config, "CLAMD_PORT", port)
        assert p.ok("documentos", "POST", verify, user=name)["status"] == "VERIFIED"
    p.ok("documentos", "GET", download, user=name)
    assert len(storage.downloads) == 1
