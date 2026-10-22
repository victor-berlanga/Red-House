"""Validación acotada de evidencias; no sustituye un análisis antimalware."""

import hashlib
import warnings
from io import BytesIO

from .errors import APIError

LIMIT = 10 * 1024 * 1024


def rejected(message):
    return APIError(
        "file_validation",
        message,
        422,
        [{"field": "evidence", "code": "invalid_file", "message": message}],
    )


def inspect_content(content, mime, expected_hash):
    if not content:
        raise rejected("El archivo está vacío. Selecciona un archivo con contenido.")
    if len(content) > LIMIT:
        raise rejected("El archivo supera 10 MiB. Selecciona uno de menor tamaño.")
    if hashlib.sha256(content).hexdigest() != expected_hash:
        raise rejected(
            "El archivo recibido cambió durante la carga. Selecciona el original y vuelve a cargarlo."
        )
    try:
        if mime in ("image/png", "image/jpeg"):
            magic = b"\x89PNG\r\n\x1a\n" if mime == "image/png" else b"\xff\xd8\xff"
            if not content.startswith(magic):
                raise rejected(
                    "El contenido no corresponde al formato de imagen indicado. Exporta una imagen JPEG o PNG válida."
                )
            from PIL import Image

            with warnings.catch_warnings():
                warnings.simplefilter("error", Image.DecompressionBombWarning)
                expected_format = "PNG" if mime == "image/png" else "JPEG"
                with Image.open(BytesIO(content), formats=[expected_format]) as picture:
                    if (
                        picture.format
                        != {"image/png": "PNG", "image/jpeg": "JPEG"}[mime]
                    ):
                        raise ValueError("mime_mismatch")
                    if picture.width * picture.height > 25_000_000:
                        raise rejected(
                            "La imagen supera 25 millones de píxeles. Reduce sus dimensiones y vuelve a cargarla."
                        )
                    picture.verify()
        elif mime == "application/pdf":
            from pypdf import PdfReader

            if not content.startswith(b"%PDF-"):
                raise rejected(
                    "El contenido no es un PDF válido. Exporta el documento como PDF y vuelve a cargarlo."
                )
            pdf = PdfReader(BytesIO(content), strict=True)
            if pdf.is_encrypted:
                raise rejected(
                    "El PDF está protegido. Selecciona una copia autorizada sin contraseña."
                )
            if not 0 < len(pdf.pages) <= 200:
                raise rejected(
                    "El PDF debe contener entre 1 y 200 páginas. Selecciona un documento dentro de ese límite."
                )
            root = pdf.trailer["/Root"]
            if any(key in root for key in ("/OpenAction", "/AA")) or any(
                key in root.get("/Names", {})
                for key in ("/JavaScript", "/EmbeddedFiles")
            ):
                raise rejected(
                    "El PDF contiene acciones automáticas o archivos incrustados. Exporta una copia sin esos elementos."
                )
        else:
            raise rejected("Selecciona un archivo JPEG, PNG o PDF.")
    except APIError:
        raise
    except Exception:  # noqa: BLE001 - untrusted parsers fail closed without leaking internals
        raise rejected(
            "No se pudo leer el archivo. Comprueba que abre correctamente y exporta una copia JPEG, PNG o PDF válida."
        ) from None
