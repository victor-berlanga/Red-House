"""Carga y consulta de evidencia privada asociada a traslados autorizados."""

import hashlib
from uuid import uuid4

import requests
from flask import flash, g, redirect, render_template, request, url_for

from ...access import BusinessError
from ..client import call
from ..storage_client import storage_target, upload_object
from .common import regional

LIMIT = 10 * 1024 * 1024


@regional.route("/traslados/<uuid:identifier>/archivos", methods=["GET", "POST"])
def shipment_files(identifier):
    if g.principal.role_code not in ("TRANSPORT", "OPERATOR", "COORDINATOR"):
        raise BusinessError("Tu perfil no puede gestionar evidencias.", 403)
    path = "/api/v1/shipments/" + str(identifier)
    shipment = call("transporte", path)
    error, status, field_errors = None, 200, []
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
                    "Selecciona un JPEG, PNG o PDF no vacío de hasta 10 MiB.",
                    422,
                    field="evidence",
                )
            digest = hashlib.sha256(content).hexdigest()
            upload_key = hashlib.sha256((idem + digest + mime).encode()).hexdigest()
            prepared = call(
                "documentos",
                path + "/files",
                "POST",
                {
                    "mime_type": mime,
                    "size": len(content),
                    "sha256": digest,
                },
                idem=upload_key,
            )
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
                    "Carga sin confirmar. Consulta la evidencia pendiente y pulsa Verificar antes de repetirla.",
                    503,
                ) from None
            call(
                "documentos",
                "/api/v1/files/" + prepared["file"]["id"] + "/verify",
                "POST",
                idem=upload_key + "-verify",
            )
            flash("Evidencia cargada y verificada.", "success")
            return redirect(
                url_for("regional.shipment_files", identifier=identifier), code=303
            )
        except BusinessError as exc:
            error, status = str(exc), exc.status
            if exc.field == "evidence" or exc.status in (400, 413, 415, 422):
                field_errors = [
                    dict(
                        name="evidence",
                        label="Evidencia",
                        errors=[error + " Selecciona nuevamente el archivo."],
                    )
                ]
    files = call(
        "documentos",
        path + "/files",
        params={"page": request.args.get("page", 1), "page_size": 20},
    )
    return render_template(
        "integration/files.html",
        title="Evidencias del traslado",
        active="traslados",
        shipment=shipment,
        files=files,
        error=error,
        field_errors=field_errors,
        idempotency_key=idem,
        can_upload=shipment["status"] not in ("ACCEPTED", "CANCELLED", "REJECTED")
        and not shipment["inventory_pending"],
    ), status


@regional.post("/archivos/<uuid:identifier>/verificar")
def verify_file(identifier):
    row = call(
        "documentos",
        "/api/v1/files/" + str(identifier) + "/verify",
        "POST",
        idem=request.form.get("idempotency_key") or uuid4().hex,
    )
    flash("Evidencia verificada.", "success")
    return redirect(
        url_for("regional.shipment_files", identifier=row["shipment_id"]), code=303
    )


@regional.get("/archivos/<uuid:identifier>/descargar")
def download_file(identifier):
    data = call("documentos", "/api/v1/files/" + str(identifier) + "/download")
    storage_target(data["download_url"])
    return redirect(data["download_url"], code=303)
