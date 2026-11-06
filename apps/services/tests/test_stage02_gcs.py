"""Opt-in existing authorized GCS bucket; only fresh fictitious objects are touched."""

import hashlib
import json
import os
from io import BytesIO
from pathlib import Path
from uuid import uuid4

import pytest
import requests
from PIL import Image

from .final_receivers import clamd_receiver
from .helpers import iso
from .test_correction_backend import laboratory
from .test_final_quality import api


@pytest.mark.skipif(
    not os.environ.get("REDHOUSE_GCS_TEST_BUCKET"),
    reason="Existing authorized bucket must be selected explicitly",
)
def test_result_real_gcs_upload_verified_binding_private_download(p, monkeypatch):
    from redhouse.storage import bucket

    app = p.apps["documentos"]
    monkeypatch.setitem(
        app.config, "GCS_BUCKET", os.environ["REDHOUSE_GCS_TEST_BUCKET"]
    )
    monkeypatch.setitem(
        app.config, "GCS_PROJECT", os.environ.get("GOOGLE_CLOUD_PROJECT")
    )
    unit = api(
        p,
        "inventario",
        "/api/v1/resources",
        {
            "folio": "GCS02-" + uuid4().hex[:10],
            "kind": "BLOOD",
            "component": "RBC",
            "blood_group": "O-",
            "expires_at": iso(days=1),
        },
        user="operator1",
    )
    _, body, result = laboratory(p, unit, "json")
    content = BytesIO()
    Image.new("RGB", (8, 8), color="blue").save(content, format="PNG")
    payload = content.getvalue()
    digest = hashlib.sha256(payload).hexdigest()
    doc = api(
        p,
        "documentos",
        "/api/v1/documents",
        {
            "subject_kind": "RESULT",
            "subject_id": result["id"],
            "category": "LAB_RESULT",
            "mime_type": "image/png",
            "size": len(payload),
            "sha256": digest,
            "policy_reference": "Ensayo ficticio de integración etapa02; no dato clínico",
        },
    )
    with p.owner("documentos") as conn:
        object_path = conn.execute(
            "SELECT object_path FROM files WHERE id=%s", (doc["id"],)
        ).fetchone()[0]
    with app.app_context():
        blob = bucket().blob(object_path)
    generation = None
    try:
        response = requests.put(
            doc["upload_url"], data=payload, headers=doc["upload_headers"], timeout=20
        )
        assert response.status_code == 200, ("GCS upload", response.status_code)
        blob.reload(timeout=10, retry=None)
        generation = blob.generation
        assert (
            p.request(
                "documentos",
                "GET",
                "/api/v1/files/" + doc["id"] + "/download",
                user="medical1",
            ).status_code
            == 409
        )
        with clamd_receiver() as (port, scanned):
            monkeypatch.setitem(app.config, "CLAMD_HOST", "127.0.0.1")
            monkeypatch.setitem(app.config, "CLAMD_PORT", port)
            api(p, "documentos", "/api/v1/files/" + doc["id"] + "/verify")
            assert scanned
        informed = api(
            p,
            "compatibilidad",
            "/api/v1/laboratory/results",
            dict(
                body,
                supersedes=result["id"],
                result_state="CORRECTED",
                issued_at=iso(),
                document_id=doc["id"],
            ),
        )
        assert informed["document_snapshot"]["generation"] == str(generation)
        assert informed["document_snapshot"]["sha256"] == digest
        download = api(
            p,
            "documentos",
            "/api/v1/files/" + doc["id"] + "/download",
            method="GET",
            fmt="xml",
        )
        response = requests.get(download["download_url"], timeout=20)
        assert (
            response.status_code == 200
            and hashlib.sha256(response.content).hexdigest() == digest
        )
        assert (
            p.request(
                "documentos",
                "GET",
                "/api/v1/files/" + doc["id"] + "/download",
                user="medical2",
            ).status_code
            == 403
        )
        response = requests.get(
            "https://storage.googleapis.com/"
            + os.environ["REDHOUSE_GCS_TEST_BUCKET"]
            + "/"
            + object_path,
            timeout=20,
        )
        assert response.status_code == 403
        directory = os.environ.get("REDHOUSE_STAGE02_EVIDENCE")
        if directory:
            Path(directory, "gcs-result.json").write_text(
                json.dumps(
                    {
                        "storage": "REAL_GCS",
                        "signed_upload": "PASS",
                        "verified_generation": True,
                        "sha256_matches": True,
                        "authorized_download": "PASS",
                        "foreign_tenant": 403,
                        "anonymous": 403,
                        "scanner": "TCP ClamD protocol fixture; not certified malware engine",
                        "synthetic": True,
                    },
                    indent=2,
                )
            )
    finally:
        if generation:
            blob.delete(if_generation_match=generation, timeout=10, retry=None)
