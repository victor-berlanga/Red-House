"""Adaptador técnico GCS; las operaciones de evidencia pertenecen a Transporte."""

from datetime import timedelta
from flask import current_app
from .errors import APIError


def bucket():
    if not current_app.config.get("GCS_BUCKET"):
        raise APIError(
            "storage_unconfigured",
            "Bucket privado y credenciales GCS pendientes de configuración.",
            503,
        )
    try:
        from google.cloud import storage

        return storage.Client().bucket(current_app.config["GCS_BUCKET"])
    except Exception:
        raise APIError(
            "storage_unavailable", "Almacenamiento de archivos inaccesible.", 503
        ) from None


def signed_url(blob, method, mime=None):
    try:
        return blob.generate_signed_url(
            version="v4",
            expiration=timedelta(minutes=5),
            method=method,
            content_type=mime,
        )
    except Exception:
        raise APIError(
            "storage_unavailable", "No se pudo generar acceso temporal al archivo.", 503
        ) from None
