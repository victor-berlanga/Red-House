"""H1/H2 en móvil: DONOR solo consulta sus evaluaciones y sus documentos de consentimiento."""

import hashlib
from io import BytesIO
from urllib.parse import urlsplit
from uuid import uuid4

from PIL import Image

from .final_receivers import clamd_receiver
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


def same_tenant_donor(p):
    """Segundo usuario DONOR en la misma institución que donor1: el ámbito de recurso es por usuario."""
    owner = p.ok("identidad_acceso", "GET", "/api/v1/auth/me", user="admin1")
    username = "otro-" + uuid4().hex[:16] + "@redhouse.test"
    p.ok(
        "identidad_acceso",
        "POST",
        "/api/v1/users",
        user="admin1",
        data={
            "username": username,
            "password": p.env.state["password"],
            "role": "DONOR",
            "tenant_id": owner["tenant_id"],
        },
    )
    token = p.ok(
        "identidad_acceso",
        "POST",
        "/api/v1/auth/login",
        user=None,
        data={"username": username, "password": p.env.state["password"]},
    )["access_token"]
    p.tokens["donor_mismo_tenant"] = token
    return "donor_mismo_tenant"


def test_donor_scope_inside_same_institution_and_replacement(p, tmp_path, monkeypatch):
    """donor1 y donor2 son de instituciones distintas; aquí el intruso es de la MISMA institución."""
    app = p.apps["documentos"]
    monkeypatch.setitem(app.config, "STORAGE_PROVIDER", "local")
    monkeypatch.setitem(app.config, "STORAGE_LOCAL_ROOT", str(tmp_path))
    monkeypatch.setitem(app.config, "STORAGE_PUBLIC_BASE_URL", "https://example.test")
    own = donor(p, "donor1")
    review(p, own)
    intruder = same_tenant_donor(p)
    try:
        theirs = donor(p, intruder)
        # H1: el compañero de institución no lee las evaluaciones ajenas; las propias, sí.
        assert (
            p.request(
                "donantes", "GET", f"/api/v1/donors/{own['id']}", user=intruder
            ).status_code
            == 403
        )
        assert (
            p.ok("donantes", "GET", f"/api/v1/donors/{theirs['id']}", user=intruder)[
                "reviews"
            ]
            == []
        )
        # H2: flujo completo del móvil (preparar, PUT firmado, verificar) como donor1.
        image = BytesIO()
        Image.new("RGB", (4, 4), "white").save(image, format="JPEG")
        content = image.getvalue()

        def prepare(user, subject, supersedes=None, key=None):
            body = {
                "subject_kind": "DONOR",
                "subject_id": subject["id"],
                "category": "CONSENT",
                "policy_reference": "Consentimiento firmado cargado desde la app móvil",
                "mime_type": "image/jpeg",
                "size": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
            }
            if supersedes:
                body["supersedes"] = supersedes
            return p.request(
                "documentos", "POST", "/api/v1/documents", user=user, data=body, key=key
            )

        key = uuid4().hex
        first = prepare("donor1", own, key=key)
        assert first.status_code == 201, first.text
        item = first.json()["data"]
        # Cabeceras exactas que el móvil acepta del PUT firmado en almacenamiento local.
        assert item["upload_headers"] == {"Content-Type": "image/jpeg"}
        # Reintento con la misma clave y cuerpo: mismo documento (no duplica).
        assert prepare("donor1", own, key=key).json()["data"]["id"] == item["id"]
        # La misma clave con `supersedes` distinto es otro cuerpo: 409 (el móvil lo guarda en el diario).
        assert prepare("donor1", own, item["id"], key=key).status_code == 409
        path = urlsplit(item["upload_url"]).path
        client = app.test_client()
        assert (
            client.put(path, data=content, content_type="image/jpeg").status_code == 201
        )
        with clamd_receiver() as (port, scanned):
            monkeypatch.setitem(app.config, "CLAMD_HOST", "127.0.0.1")
            monkeypatch.setitem(app.config, "CLAMD_PORT", port)
            verified = p.request(
                "documentos",
                "POST",
                f"/api/v1/files/{item['id']}/verify",
                user="donor1",
            )
            assert verified.status_code == 200, verified.text
        status = p.ok(
            "documentos", "GET", f"/api/v1/documents/{item['id']}/status", user="donor1"
        )
        assert (status["file_status"], status["analysis"]) == ("VERIFIED", "CLEAN")
        # Un compañero de institución no ve, consulta, verifica ni descarga el documento ajeno.
        for method, route in (
            ("GET", f"/api/v1/documents/{item['id']}"),
            ("GET", f"/api/v1/documents/{item['id']}/status"),
            ("POST", f"/api/v1/files/{item['id']}/verify"),
            ("GET", f"/api/v1/files/{item['id']}/download"),
            (
                "GET",
                f"/api/v1/documents?subject_kind=DONOR&subject_id={own['id']}&category=CONSENT",
            ),
        ):
            denied = p.request("documentos", method, route, user=intruder)
            assert denied.status_code == 403, (route, denied.status_code)
        assert prepare(intruder, own).status_code == 403
        # Ni siquiera sobre su propio expediente puede sustituir un documento ajeno.
        assert prepare(intruder, theirs, item["id"]).status_code == 412
        # El propio donante sí puede sustituir su documento VERIFIED; una sola vez por versión.
        second = prepare("donor1", own, item["id"])
        assert second.status_code == 201, second.text
        assert second.json()["data"]["metadata"]["version"] == 2
        assert prepare("donor1", own, item["id"]).status_code == 412
    finally:
        p.tokens.pop(intruder, None)
