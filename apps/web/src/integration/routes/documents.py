"""Documentos privados por sujeto autorizado; almacenamiento siempre mediante Documentos."""

import hashlib
from uuid import uuid4
import requests
from .common import (
    BusinessError,
    call,
    confirmations,
    detail,
    field,
    g,
    local_date,
    regional,
    render_template,
    request,
    redirect,
    rows,
    submit,
    url_for,
    flash,
)
from ..storage_client import upload_object
from .files import LIMIT

SUBJECTS = {
    "DONOR": (
        "Donante",
        "donantes",
        "/api/v1/donors",
        "CONSENT",
        ("DONOR", "OPERATOR", "MEDICAL"),
    ),
    "RESULT": (
        "Resultado de laboratorio",
        "compatibilidad",
        "/api/v1/laboratory/results",
        "LAB_RESULT",
        ("OPERATOR", "MEDICAL"),
    ),
    "RULE": (
        "Perfil de laboratorio",
        "compatibilidad",
        "/api/v1/laboratory/profiles",
        "RULE_APPROVAL",
        ("OPERATOR", "MEDICAL"),
    ),
    "ACCREDITATION": (
        "Acreditación",
        "identidad_acceso",
        "/api/v1/accreditations",
        "ACCREDITATION",
        ("ADMIN",),
    ),
    "REQUEST": (
        "Solicitud",
        "receptores",
        "/api/v1/requests",
        "AUTHORIZATION",
        ("MEDICAL",),
    ),
}


def subject(kind, identifier=None):
    if kind not in SUBJECTS or g.principal.role_code not in SUBJECTS[kind][4]:
        raise BusinessError("Sujeto documental no autorizado para este perfil.", 403)
    label, service, path, category, _ = SUBJECTS[kind]
    return call(service, path + "/" + identifier) if identifier else rows(service, path)


@regional.get("/documentos")
def document_center():
    kinds = [(k, v[0]) for k, v in SUBJECTS.items() if g.principal.role_code in v[4]]
    kind = request.args.get("subject_kind", kinds[0][0] if kinds else "")
    subjects = subject(kind) if kind else []
    identifier = request.args.get("subject_id", "")
    documents = None
    if identifier:
        subject(kind, identifier)
        documents = call(
            "documentos",
            "/api/v1/documents",
            params={
                "subject_kind": kind,
                "subject_id": identifier,
                "page": request.args.get("page", 1),
                "page_size": 20,
            },
        )
    return render_template(
        "integration/documents.html",
        title="Documentos privados",
        active="documentos",
        kinds=kinds,
        kind=kind,
        subjects=subjects,
        identifier=identifier,
        documents=documents,
    )


@regional.route("/documentos/nuevo", methods=["GET", "POST"])
def document_new():
    kind, identifier = (
        request.values.get("subject_kind", ""),
        request.values.get("subject_id", ""),
    )
    subject(kind, identifier)
    previous = request.values.get("supersedes") or None
    if previous:
        old = call("documentos", "/api/v1/documents/" + previous)
        if old["subject_kind"] != kind or old["subject_id"] != identifier:
            raise BusinessError("La versión anterior pertenece a otro expediente.", 403)
    error, status, prepared_id = None, 200, None
    idem = request.form.get("idempotency_key") or uuid4().hex
    if request.method == "POST":
        try:
            uploaded = request.files.get("evidence")
            content = uploaded.read(LIMIT + 1) if uploaded else b""
            mime = uploaded.mimetype if uploaded else ""
            if not 0 < len(content) <= LIMIT or mime not in (
                "image/jpeg",
                "image/png",
                "application/pdf",
            ):
                raise BusinessError(
                    "Selecciona JPEG, PNG o PDF no vacío de hasta 10 MiB.", 422
                )
            data = dict(
                subject_kind=kind,
                subject_id=identifier,
                category=SUBJECTS[kind][3],
                supersedes=previous,
                policy_reference=request.form.get("policy_reference", "").strip(),
                retention_until=local_date(request.form["retention_until"])
                if request.form.get("retention_until")
                else None,
                mime_type=mime,
                size=len(content),
                sha256=hashlib.sha256(content).hexdigest(),
            )
            prepared = call("documentos", "/api/v1/documents", "POST", data, idem=idem)
            prepared_id = prepared["id"]
            try:
                upload_status = upload_object(
                    prepared["upload_url"],
                    content=content,
                    headers=prepared["upload_headers"],
                )
                if upload_status not in (200, 201, 412):
                    raise requests.RequestException()
            except requests.RequestException:
                raise BusinessError(
                    "Carga sin confirmar. Consulta el documento preparado antes de repetir la carga.",
                    503,
                ) from None
            call(
                "documentos",
                f"/api/v1/files/{prepared_id}/verify",
                "POST",
                idem=idem + "-verify",
            )
            flash("Documento cargado, analizado y verificado.", "success")
            return redirect(
                url_for("regional.document_detail", identifier=prepared_id), code=303
            )
        except BusinessError as exc:
            error, status = exc.message, exc.status
    return render_template(
        "integration/document_upload.html",
        title="Nueva versión documental" if previous else "Cargar documento privado",
        active="documentos",
        kind=kind,
        identifier=identifier,
        previous=previous,
        error=error,
        prepared_id=prepared_id,
        idempotency_key=idem,
    ), status


@regional.get("/documentos/<uuid:identifier>")
def document_detail(identifier):
    row = call("documentos", f"/api/v1/documents/{identifier}/status")
    actions = [
        (
            "Analizar y verificar",
            url_for("regional.document_verify", identifier=identifier),
        ),
        (
            "Nueva versión",
            url_for(
                "regional.document_new",
                subject_kind=row["subject_kind"],
                subject_id=row["subject_id"],
                supersedes=identifier,
            ),
        ),
    ]
    if row["file_status"] == "VERIFIED" and row["analysis"] == "CLEAN":
        actions.append(
            (
                "Descargar objeto verificado",
                url_for("regional.download_file", identifier=identifier),
            )
        )
    if g.principal.role_code in ("ADMIN", "MEDICAL"):
        actions.append(
            (
                "Conservación y bloqueo",
                url_for("regional.document_conservation", identifier=identifier),
            )
        )
    return detail(
        "Documento privado",
        "documentos",
        row,
        actions,
        note="La descarga revalida permisos y el análisis de la generación actual. Un archivo pendiente o rechazado permanece bloqueado.",
    )


@regional.route("/documentos/<uuid:identifier>/verificar", methods=["GET", "POST"])
def document_verify(identifier):
    call("documentos", f"/api/v1/documents/{identifier}/status")
    return submit(
        "documentos",
        f"/api/v1/files/{identifier}/verify",
        [],
        title="Analizar y verificar documento",
        active="documentos",
        back=url_for("regional.document_detail", identifier=identifier),
        prompt="Analizar la generación cargada antes de permitir acceso.",
    )


@regional.route("/documentos/<uuid:identifier>/conservacion", methods=["GET", "POST"])
def document_conservation(identifier):
    from .conservation import permit

    permit("ADMIN", "MEDICAL")
    row = call("documentos", f"/api/v1/documents/{identifier}/status")
    return submit(
        "documentos",
        f"/api/v1/documents/{identifier}/conservation",
        [
            field(
                "policy_version",
                "Versión de política",
                "hidden",
                default=row["policy_version"],
            ),
            field(
                "retention_until",
                "Conservación hasta",
                "datetime-local",
                required=False,
            ),
            field(
                "legal_hold",
                "Mantener bloqueo de eliminación",
                "checkbox",
                default=row["legal_hold"],
                required=False,
            ),
            field(
                "policy_reference",
                "Referencia de política autorizada",
                default=row["policy_reference"],
            ),
        ]
        + confirmations(),
        transform=lambda d: dict(d, legal_hold=d.get("legal_hold", False)),
        title="Actualizar conservación documental",
        active="documentos",
        back=url_for("regional.document_detail", identifier=identifier),
        note="No se aplica un plazo legal supuesto. Debe proceder de la política autorizada de la institución.",
    )
