"""Vínculo documental HLA sintético con ClamD real y archivos locales."""

import hashlib
import os
from io import BytesIO
from urllib.parse import urlsplit
from uuid import uuid4

import pytest
from PIL import Image

from .helpers import iso
from .test_cont01_hla_evaluation import CONFIRM, rejected
from .test_final_quality import api


@pytest.mark.skipif(
    not os.environ.get("REDHOUSE_TEST_CLAMD_PORT"),
    reason="Requiere ClamD real del laboratorio",
)
@pytest.mark.parametrize("fmt", ["json", "xml"])
def test_hla_document_cross_test_binding_and_versions(p, tmp_path, monkeypatch, fmt):
    owner = "medical2"
    app = p.apps["documentos"]
    root = tmp_path / "private-files"
    root.mkdir(mode=0o700)
    for key, value in {
        "STORAGE_PROVIDER": "local",
        "STORAGE_LOCAL_ROOT": str(root),
        "STORAGE_PUBLIC_BASE_URL": "https://example.test",
        "CLAMD_HOST": "127.0.0.1",
        "CLAMD_PORT": int(os.environ["REDHOUSE_TEST_CLAMD_PORT"]),
    }.items():
        monkeypatch.setitem(app.config, key, value)
    from redhouse.malware import scan

    eicar = b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
    with app.app_context():
        assert scan(eicar) == "INFECTED"
    recipient = api(
        p,
        "receptores",
        "/api/v1/recipients",
        {
            "folio": "HDOC-" + uuid4().hex[:10],
            "display_name": "Receptor sintético",
            "kind": "ORGAN",
            "blood_group": "A+",
            "organ_type": "KIDNEY",
            "studies": "Referencia ficticia",
        },
        user=owner,
        fmt=fmt,
    )
    profile = api(
        p,
        "compatibilidad",
        "/api/v1/laboratory/profiles",
        {
            "name": "Perfil documental sintético",
            "kind": "ORGAN",
            "component": "KIDNEY",
            "version": 1,
            "required_tests": ["HLA"],
            "required_loci": ["A"],
            "source": "Ensayo sin uso clínico",
            "policy": {"require_document": True},
            "synthetic": True,
            "effective_at": iso(),
        },
        user=owner,
        fmt=fmt,
    )
    sample = api(
        p,
        "compatibilidad",
        "/api/v1/laboratory/samples",
        {
            "recipient_id": recipient["id"],
            "profile_id": profile["id"],
            "identifier": "DOC-" + uuid4().hex[:12],
            "collected_at": iso(minutes=-5),
        },
        user=owner,
        fmt=fmt,
    )
    api(
        p,
        "compatibilidad",
        f"/api/v1/laboratory/samples/{sample['id']}/receive",
        dict(CONFIRM, version=1, decision="RECEIVED"),
        user=owner,
        fmt=fmt,
    )
    base = {
        "sample_id": sample["id"],
        "method": "Método ficticio",
        "laboratory": "Laboratorio sintético",
        "reference": "Documento ficticio",
        "measured_at": iso(minutes=-2),
        "result_state": "PENDING",
    }
    hla = api(
        p,
        "compatibilidad",
        "/api/v1/laboratory/results",
        dict(base, test_code="HLA"),
        user=owner,
        fmt=fmt,
    )
    abo = api(
        p,
        "compatibilidad",
        "/api/v1/laboratory/results",
        dict(base, test_code="ABO"),
        user=owner,
        fmt=fmt,
    )
    image = BytesIO()
    Image.new("RGB", (8, 8), "red").save(image, format="PNG")
    content = image.getvalue()
    digest = hashlib.sha256(content).hexdigest()

    def document(subject, supersedes=None):
        body = {
            "subject_kind": "RESULT",
            "subject_id": subject,
            "category": "LAB_RESULT",
            "mime_type": "image/png",
            "size": len(content),
            "sha256": digest,
            "policy_reference": "Evidencia sintética",
        }
        if supersedes:
            body["supersedes"] = supersedes
        created = api(p, "documentos", "/api/v1/documents", body, user=owner, fmt=fmt)
        uploaded = app.test_client().put(
            urlsplit(created["upload_url"]).path, data=content, content_type="image/png"
        )
        assert uploaded.status_code == 201
        verified = api(
            p,
            "documentos",
            f"/api/v1/files/{created['id']}/verify",
            {},
            user=owner,
            fmt=fmt,
        )
        assert verified["status"] == "VERIFIED"
        metadata = api(
            p,
            "documentos",
            f"/api/v1/documents/{created['id']}/verified",
            user=owner,
            fmt=fmt,
            method="GET",
        )
        assert metadata["analysis"] == "CLEAN" and metadata["sha256"] == digest
        assert metadata["subject_id"] == subject and metadata["generation"]
        return metadata

    wrong = document(abo["id"])
    data = dict(
        base,
        test_code="HLA",
        result_state="CORRECTED",
        supersedes=hla["id"],
        document_id=wrong["id"],
        issued_at=iso(minutes=-1),
        hla={
            "nomenclature": "HLA-colon-2010",
            "nomenclature_version": "2010",
            "resolution": "Dos campos",
            "loci": [{"locus": "A", "alleles": ["A*01:01"], "ambiguous": False}],
        },
    )
    error = rejected(
        p, "compatibilidad", "/api/v1/laboratory/results", data, owner, fmt
    )
    assert error["code"] == "evidence_mismatch"
    assert all(
        identifier not in str(error)
        for identifier in (wrong["id"], abo["id"], hla["id"])
    )
    with p.owner("compatibilidad") as conn:
        assert (
            conn.execute(
                "SELECT count(*) FROM lab_results WHERE sample_id=%s AND test_code='HLA'",
                (sample["id"],),
            ).fetchone()[0]
            == 1
        )
    # La implementación actual exige documento para cada resultado presente,
    # incluso si no figura entre las pruebas requeridas. El ABO auxiliar se
    # documenta y autoriza antes de comprobar completitud del HLA.
    abo_corrected = api(
        p,
        "compatibilidad",
        "/api/v1/laboratory/results",
        dict(
            base,
            test_code="ABO",
            result_state="CORRECTED",
            supersedes=abo["id"],
            document_id=wrong["id"],
            issued_at=iso(minutes=-1),
            value="A",
        ),
        user=owner,
        fmt=fmt,
    )
    api(
        p,
        "compatibilidad",
        f"/api/v1/laboratory/results/{abo_corrected['id']}/review",
        dict(CONFIRM, version=2, decision="AUTHORIZED"),
        user=owner,
        fmt=fmt,
    )
    first = document(hla["id"])
    second = document(hla["id"], first["id"])
    assert (
        first["version"] == 1
        and second["version"] == 2
        and second["supersedes"] == first["id"]
    )
    data["document_id"] = second["id"]
    corrected = api(
        p, "compatibilidad", "/api/v1/laboratory/results", data, user=owner, fmt=fmt
    )
    assert corrected["version"] == 2 and corrected["supersedes"] == hla["id"]
    assert corrected["document_snapshot"]["id"] == second["id"]
    assert corrected["document_snapshot"]["generation"] == second["generation"]
    assert corrected["document_snapshot"]["sha256"] == digest
    api(
        p,
        "compatibilidad",
        f"/api/v1/laboratory/results/{corrected['id']}/review",
        dict(CONFIRM, version=2, decision="AUTHORIZED"),
        user=owner,
        fmt=fmt,
    )
    check = api(
        p,
        "compatibilidad",
        f"/api/v1/laboratory/samples/{sample['id']}/completeness",
        user=owner,
        fmt=fmt,
        method="GET",
    )
    assert (
        check["complete"]
        and not check["clinical_approval"]
        and not check["clinical_enabled"]
    ), {
        k: check[k]
        for k in (
            "complete",
            "missing",
            "conflicts",
            "clinical_approval",
            "clinical_enabled",
        )
    }
    assert (
        p.request(
            "documentos",
            "GET",
            f"/api/v1/documents/{second['id']}/verified",
            user="medical1",
        ).status_code
        == 403
    )
    # La política existente permite reutilizar evidencia de la misma prueba y
    # muestra en otra versión. No se interpreta su suficiencia clínica.
    next_data = dict(data, supersedes=corrected["id"])
    later = api(
        p,
        "compatibilidad",
        "/api/v1/laboratory/results",
        next_data,
        user=owner,
        fmt=fmt,
    )
    assert later["version"] == 3 and later["supersedes"] == corrected["id"]
    assert later["document_snapshot"]["id"] == second["id"]
    assert later["document_snapshot"]["subject_id"] == hla["id"]
    pending_again = api(
        p,
        "compatibilidad",
        f"/api/v1/laboratory/samples/{sample['id']}/completeness",
        user=owner,
        fmt=fmt,
        method="GET",
    )
    assert not pending_again["complete"] and not pending_again["clinical_approval"]
