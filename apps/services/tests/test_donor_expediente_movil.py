"""H1/H2 en móvil: DONOR solo consulta sus evaluaciones y sus documentos de consentimiento."""

import pytest

from .test_donor_personal import donor, isolated_donor_accounts  # noqa: F401


def review(
    p, row, decision="DEFERRED", reason="Dictamen sintético visible para el donante"
):
    return p.ok(
        "donantes",
        "POST",
        f"/api/v1/donors/{row['id']}/reviews",
        user="medical1",
        data={
            "version": row["version"],
            "decision": decision,
            "human_confirmation": True,
            "reason": reason,
        },
    )


def test_donor_reads_only_own_reviews_with_visible_fields(p):
    own = donor(p, "donor1")
    other = donor(p, "donor2")
    review(p, own)
    detail = p.ok("donantes", "GET", f"/api/v1/donors/{own['id']}", user="donor1")
    assert [r["decision"] for r in detail["reviews"]] == ["DEFERRED"]
    # Campos que consume el móvil (parseDonorReviews): fecha, resultado y nota.
    assert {"id", "decision", "reason", "created_at"} <= set(detail["reviews"][0])
    # Otro donante: 403 por ámbito de recurso (donor_access), con o sin evaluaciones.
    for target in (own, other):
        reader = "donor2" if target is own else "donor1"
        response = p.request(
            "donantes", "GET", f"/api/v1/donors/{target['id']}", user=reader
        )
        assert response.status_code == 403, response.text
    # El listado del donante contiene solo su expediente.
    items = p.ok("donantes", "GET", "/api/v1/donors", user="donor1")["items"]
    assert {i["id"] for i in items} == {own["id"]}
    # Quien dictamina no puede ser el donante (el POST de dictámenes es de MEDICAL).
    denied = p.request(
        "donantes",
        "POST",
        f"/api/v1/donors/{own['id']}/reviews",
        user="donor1",
        data={
            "version": 1,
            "decision": "ELIGIBLE",
            "human_confirmation": True,
            "reason": "Autoevaluación",
        },
    )
    assert denied.status_code == 403


def test_donor_consent_documents_are_scoped_to_own_record(p):
    own = donor(p, "donor1")
    query = f"?subject_kind=DONOR&subject_id={own['id']}&category=CONSENT"
    listed = p.ok("documentos", "GET", "/api/v1/documents" + query, user="donor1")
    assert listed["items"] == [] and listed["total"] == 0
    # Otro donante no lista ni prepara documentos sobre un expediente ajeno.
    assert (
        p.request(
            "documentos", "GET", "/api/v1/documents" + query, user="donor2"
        ).status_code
        == 403
    )
    prepare = p.request(
        "documentos",
        "POST",
        "/api/v1/documents",
        user="donor2",
        data={
            "subject_kind": "DONOR",
            "subject_id": own["id"],
            "category": "CONSENT",
            "policy_reference": "Consentimiento ajeno",
            "mime_type": "image/jpeg",
            "size": 3,
            "sha256": "0" * 64,
        },
    )
    assert prepare.status_code == 403, prepare.text
    # Una categoría que no corresponde al sujeto se rechaza antes de tocar el almacenamiento.
    wrong = p.request(
        "documentos",
        "POST",
        "/api/v1/documents",
        user="donor1",
        data={
            "subject_kind": "DONOR",
            "subject_id": own["id"],
            "category": "LAB_RESULT",
            "policy_reference": "Categoría incorrecta",
            "mime_type": "image/jpeg",
            "size": 3,
            "sha256": "0" * 64,
        },
    )
    assert wrong.status_code == 422, wrong.text
