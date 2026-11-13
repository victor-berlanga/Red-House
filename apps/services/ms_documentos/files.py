"""Contratos, autorización y persistencia de evidencias de traslados."""

from uuid import uuid4

from flask import g
from redhouse.api import atomic, endpoint
from redhouse.db import get, insert, transaction, update
from redhouse.errors import APIError
from redhouse.events import emit
from redhouse.file_validation import inspect_content
from redhouse.storage import access_url, object_bucket, provider, upload_headers


def public_file(row):
    return {key: value for key, value in row.items() if key != "storage_provider"}


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
        selected = provider()
        object_bucket(selected)
        access(identifier)

        def work(conn):
            conn.execute(
                "SELECT pg_advisory_xact_lock(hashtextextended(%s,83))",
                ("shipment-evidence:" + identifier,),
            )
            shipment = access(identifier)
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
                    storage_provider=selected,
                    mime_type=data["mime_type"],
                    size=data["size"],
                    sha256=data["sha256"],
                ),
            )
            emit(conn, "FILE_PREPARED", object_id, shipment["origin_id"])
            return row

        row = atomic("file_prepare:" + identifier, data, work)
        # Idempotencias anteriores a la migración no incluyen el proveedor.
        with transaction() as conn:
            row = get(conn, "files", row["id"])
        return {
            "file": public_file(row),
            "upload_url": access_url(row, "PUT"),
            "expires_in": 300,
            "upload_headers": upload_headers(row),
        }

    @endpoint(
        app,
        "/api/v1/files/<identifier>/verify",
        "POST",
        roles=(
            "TRANSPORT",
            "OPERATOR",
            "COORDINATOR",
            "MEDICAL",
            "ADMIN",
            "DONOR",
            "AUDITOR",
        ),
        summary="Verificar tamaño, MIME, firma de archivo y SHA-256 del objeto real",
    )
    def file_verify(identifier):
        from .documents import file_access, require_clean

        with transaction() as conn:
            row = get(conn, "files", identifier)
            shipment = file_access(conn, row, access)
            if row["status"] == "VERIFIED":
                try:
                    require_clean(conn, row)
                    return public_file(row)
                except APIError:
                    pass  # Un archivo histórico se analiza antes de habilitar descarga.
        target = object_bucket(row["storage_provider"])
        try:
            blob = target.blob(row["object_path"])
            blob.reload(timeout=8, retry=None)
            if blob.size != row["size"] or blob.content_type != row["mime_type"]:
                raise APIError(
                    "file_validation",
                    "Tamaño o tipo de archivo diferente al declarado.",
                    422,
                )
            content = blob.download_as_bytes(
                if_generation_match=blob.generation, timeout=8, retry=None
            )
            inspect_content(content, row["mime_type"], row["sha256"])
            from redhouse.malware import scan

            scan_status = "ERROR"
            scan_metadata = {}
            try:
                result = scan(content)
                scan_metadata = result.metadata
                scan_status = result
            finally:
                with transaction() as conn:
                    insert(
                        conn,
                        "file_scans",
                        {
                            "id": str(uuid4()),
                            "file_id": identifier,
                            "generation": str(blob.generation),
                            "sha256": row["sha256"],
                            "status": str(scan_status),
                            "engine": "CLAMD_INSTREAM",
                            **scan_metadata,
                        },
                    )
            if scan_status != "CLEAN":
                raise APIError(
                    "malware_detected", "El análisis rechazó el documento.", 422
                )
        except APIError as exc:
            file_failure(
                identifier,
                shipment,
                "ERROR" if exc.status >= 500 else "REJECTED",
                exc.code,
            )
            raise
        except Exception as exc:
            from google.api_core.exceptions import NotFound

            if isinstance(exc, NotFound):
                file_failure(identifier, shipment, "MISSING", "object_missing")
                raise APIError(
                    "object_missing",
                    "El objeto aún no existe en el almacenamiento privado.",
                    404,
                ) from None
            file_failure(identifier, shipment, "ERROR", "storage_unavailable")
            raise APIError(
                "storage_unavailable", "No se pudo verificar el objeto.", 503
            ) from None

        def work(conn):
            current = get(conn, "files", identifier, True)
            shipment = file_access(conn, current, access)
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

        return public_file(atomic("file_verify:" + identifier, {}, work))

    @endpoint(
        app,
        "/api/v1/files/<identifier>/download",
        roles=(
            "TRANSPORT",
            "OPERATOR",
            "COORDINATOR",
            "MEDICAL",
            "ADMIN",
            "DONOR",
            "AUDITOR",
        ),
        summary="Descargar evidencia verificada mediante acceso temporal privado",
    )
    def file_download(identifier):
        from .documents import file_access, require_clean

        with transaction() as conn:
            row = get(conn, "files", identifier)
            file_access(conn, row, access)
            if row["status"] != "VERIFIED":
                raise APIError("conflict", "Archivo pendiente de verificación.", 409)
            require_clean(conn, row)
        return {"download_url": access_url(row, "GET"), "expires_in": 300}

    @endpoint(
        app,
        "/api/v1/shipments/<identifier>/files",
        roles=("TRANSPORT", "OPERATOR", "COORDINATOR"),
        paginated=True,
        summary="Evidencias del traslado y estado persistente de validación",
        query=("q", "from_at", "until_at", "date_field", "sort"),
    )
    def file_list(identifier):
        from redhouse.api import listing

        with transaction() as conn:
            access(identifier)
            result = listing(conn, "files", "shipment_id=%s", (identifier,))
            result["items"] = [public_file(row) for row in result["items"]]
            return result


def file_failure(identifier, shipment, state, code):
    with transaction() as conn:
        row = get(conn, "files", identifier, True)
        if row["status"] != "VERIFIED":
            update(conn, "files", identifier, {"status": state})
            emit(
                conn,
                "FILE_" + state,
                identifier,
                shipment["origin_id"],
                metadata={"code": code},
            )


# DTO compartido con el adaptador v1; no contiene acceso a datos.
from redhouse.document_contracts import Upload
