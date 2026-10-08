"""Contratos, autorización y persistencia de evidencias de traslados."""

import hashlib
from typing import Annotated, Literal
from uuid import uuid4
from flask import g
from pydantic import Field
from redhouse.api import atomic, endpoint
from redhouse.db import get, insert, transaction, update
from redhouse.errors import APIError
from redhouse.events import emit
from redhouse.models import Model
from redhouse.storage import bucket, signed_url


class Upload(Model):
    mime_type: Literal["image/jpeg", "image/png", "application/pdf"]
    size: Annotated[int, Field(ge=1, le=10485760)]
    sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]


def register_files(app, access):
    @endpoint(
        app,
        "/api/v1/shipments/<identifier>/files",
        "POST",
        model=Upload,
        roles=("TRANSPORT", "OPERATOR", "COORDINATOR"),
        status=201,
        summary="Preparar carga privada con URL firmada de cinco minutos",
    )
    def file_prepare(identifier, data):
        target = bucket()

        def work(conn):
            shipment = get(conn, "shipments", identifier, True)
            access(shipment)
            if (
                shipment["status"] in ("ACCEPTED", "CANCELLED", "REJECTED")
                or shipment["inventory_pending"]
            ):
                raise APIError(
                    "conflict",
                    "Traslado fuera del periodo autorizado para evidencia.",
                    409,
                )
            object_id = str(uuid4())
            object_path = f"evidence/{shipment['region_id']}/{identifier}/{object_id}"
            row = insert(
                conn,
                "files",
                dict(
                    id=object_id,
                    shipment_id=identifier,
                    owner_id=g.actor["id"],
                    object_path=object_path,
                    mime_type=data["mime_type"],
                    size=data["size"],
                    sha256=data["sha256"],
                ),
            )
            emit(conn, "FILE_PREPARED", object_id, shipment["origin_id"])
            return row

        row = atomic("file_prepare:" + identifier, data, work)
        return {
            "file": row,
            "upload_url": signed_url(
                target.blob(row["object_path"]), "PUT", row["mime_type"]
            ),
            "expires_in": 300,
        }

    @endpoint(
        app,
        "/api/v1/files/<identifier>/verify",
        "POST",
        roles=("TRANSPORT", "OPERATOR", "COORDINATOR"),
        summary="Verificar tamaño, MIME, firma de archivo y SHA-256 del objeto real",
    )
    def file_verify(identifier):
        with transaction() as conn:
            row = get(conn, "files", identifier)
            shipment = get(conn, "shipments", str(row["shipment_id"]))
            access(shipment)
        target = bucket()
        try:
            blob = target.blob(row["object_path"])
            blob.reload()
            if blob.size != row["size"] or blob.content_type != row["mime_type"]:
                raise APIError(
                    "file_validation",
                    "Tamaño o tipo de archivo diferente al declarado.",
                    422,
                )
            content = blob.download_as_bytes(if_generation_match=blob.generation)
            magic = {
                "image/jpeg": b"\xff\xd8\xff",
                "image/png": b"\x89PNG\r\n\x1a\n",
                "application/pdf": b"%PDF-",
            }[row["mime_type"]]
            if (
                not content.startswith(magic)
                or hashlib.sha256(content).hexdigest() != row["sha256"]
            ):
                raise APIError(
                    "file_validation", "Contenido o hash de archivo inválido.", 422
                )
        except APIError:
            raise
        except Exception:
            raise APIError(
                "storage_unavailable", "No se pudo verificar el objeto.", 503
            ) from None

        def work(conn):
            current = get(conn, "files", identifier, True)
            shipment = get(conn, "shipments", str(current["shipment_id"]), True)
            access(shipment)
            if shipment["status"] in ("ACCEPTED", "CANCELLED", "REJECTED"):
                raise APIError("conflict", "Periodo de evidencia finalizado.", 409)
            result = update(
                conn,
                "files",
                identifier,
                {"status": "VERIFIED", "generation": str(blob.generation)},
            )
            emit(conn, "FILE_VERIFIED", identifier, shipment["origin_id"])
            return result

        return atomic("file_verify:" + identifier, {}, work)

    @endpoint(
        app,
        "/api/v1/files/<identifier>/download",
        roles=("TRANSPORT", "OPERATOR", "COORDINATOR"),
        summary="Descargar evidencia verificada mediante acceso temporal privado",
    )
    def file_download(identifier):
        with transaction() as conn:
            row = get(conn, "files", identifier)
            access(get(conn, "shipments", str(row["shipment_id"])))
            if row["status"] != "VERIFIED":
                raise APIError("conflict", "Archivo pendiente de verificación.", 409)
        blob = bucket().blob(row["object_path"], generation=int(row["generation"]))
        return {"download_url": signed_url(blob, "GET"), "expires_in": 300}
