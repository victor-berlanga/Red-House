"""Validación acotada de evidencias; no sustituye un análisis antimalware."""

import hashlib
import warnings
from io import BytesIO

from .errors import APIError

LIMIT = 10 * 1024 * 1024


def inspect_content(content, mime, expected_hash):
    if (
        not 0 < len(content) <= LIMIT
        or hashlib.sha256(content).hexdigest() != expected_hash
    ):
        raise APIError("file_validation", "Tamaño o hash de archivo inválido.", 422)
    try:
        if mime in ("image/png", "image/jpeg"):
            magic = b"\x89PNG\r\n\x1a\n" if mime == "image/png" else b"\xff\xd8\xff"
            if not content.startswith(magic):
                raise ValueError("image_header")
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
                        raise ValueError("image_too_large")
                    picture.verify()
        elif mime == "application/pdf":
            from pypdf import PdfReader

            if not content.startswith(b"%PDF-"):
                raise ValueError("pdf_header")
            pdf = PdfReader(BytesIO(content), strict=True)
            if pdf.is_encrypted or not 0 < len(pdf.pages) <= 200:
                raise ValueError("pdf_limits")
            root = pdf.trailer["/Root"]
            if any(key in root for key in ("/OpenAction", "/AA")) or any(
                key in root.get("/Names", {})
                for key in ("/JavaScript", "/EmbeddedFiles")
            ):
                raise ValueError("active_pdf")
        else:
            raise ValueError("unsupported_mime")
    except Exception:  # noqa: BLE001 - untrusted parsers fail closed without leaking internals
        raise APIError(
            "file_validation",
            "Archivo ilegible, contenido activo o tipo diferente al declarado.",
            422,
        ) from None
