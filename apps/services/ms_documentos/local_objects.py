"""Transferencia de capacidades privadas, con autorización vigente en cada acceso."""

import base64
import hashlib
import json

from cryptography.fernet import Fernet, InvalidToken
from flask import Response, current_app, g, request
from google.api_core.exceptions import NotFound, PreconditionFailed
from redhouse.db import get, transaction
from redhouse.errors import APIError
from redhouse.security import authenticate, rate_limit
from redhouse.storage import LOCAL_LIMIT, object_bucket


def install(app):
    @app.route("/storage/v1/objects/<token>", methods=["GET", "PUT"])
    def local_object(token):
        from .documents import file_access, require_clean, shipment_access

        secret = current_app.config.get("SERVICE_PRIVATE_KEY", "")
        try:
            key = base64.urlsafe_b64encode(
                hashlib.sha256(("private-storage-v1:" + secret).encode()).digest()
            )
            data = json.loads(Fernet(key).decrypt(token.encode(), ttl=300))
            if data["method"] != request.method or not secret:
                raise ValueError()
            request.environ["HTTP_AUTHORIZATION"] = data["authorization"]
        except (InvalidToken, ValueError, KeyError, TypeError):
            raise APIError(
                "unauthorized", "Acceso temporal inválido o vencido.", 401
            ) from None
        authenticate(
            (
                "TRANSPORT",
                "OPERATOR",
                "COORDINATOR",
                "MEDICAL",
                "ADMIN",
                "DONOR",
                "AUDITOR",
            )
        )
        rate_limit("user", g.actor["tenant_id"] + ":" + g.actor["id"])
        with transaction() as conn:
            row = get(conn, "files", data["id"])
            shipment = file_access(conn, row, shipment_access)
            if row["storage_provider"] != "local":
                raise APIError("forbidden", "Acceso temporal inválido.", 403)
            blob = object_bucket("local").blob(
                row["object_path"],
                generation=row["generation"] if request.method == "GET" else None,
            )
            if request.method == "GET":
                if (
                    row["status"] != "VERIFIED"
                    or data["generation"] != row["generation"]
                ):
                    raise APIError(
                        "conflict", "Archivo pendiente de verificación.", 409
                    )
                require_clean(conn, row)
                try:
                    content = blob.download_as_bytes(
                        if_generation_match=row["generation"]
                    )
                except NotFound:
                    raise APIError(
                        "storage_unavailable",
                        "El objeto privado no está disponible.",
                        503,
                    ) from None
                if (
                    hashlib.sha256(content).hexdigest() != row["sha256"]
                    or blob.content_type != row["mime_type"]
                ):
                    raise APIError(
                        "file_validation",
                        "El objeto no coincide con la generación verificada.",
                        409,
                    )
                response = Response(content, content_type=row["mime_type"])
                response.headers["Content-Disposition"] = "attachment"
                return response
            if row["status"] not in ("PENDING", "MISSING") or str(row["owner_id"]) != g.actor["id"]:
                raise APIError("conflict", "Carga no disponible.", 409)
            if shipment["status"] in (
                "ACCEPTED",
                "CANCELLED",
                "REJECTED",
            ) or shipment.get("inventory_pending"):
                raise APIError("conflict", "Periodo de evidencia finalizado.", 409)
            request.max_content_length = LOCAL_LIMIT
            if (
                request.content_type != row["mime_type"]
                or request.content_length != row["size"]
            ):
                raise APIError(
                    "file_validation",
                    "Tamaño o tipo de archivo diferente al declarado.",
                    422,
                )
            content = request.get_data(cache=False)
            if (
                len(content) != row["size"]
                or hashlib.sha256(content).hexdigest() != row["sha256"]
            ):
                raise APIError(
                    "file_validation", "El contenido no coincide con el declarado.", 422
                )
            try:
                blob.upload_from_string(
                    content, content_type=row["mime_type"], if_generation_match=0
                )
            except PreconditionFailed:
                raise APIError("conflict", "El objeto ya existe.", 412) from None
        return Response(status=201)
