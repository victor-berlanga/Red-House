"""Private binary transfers to the configured origin or the existing GCS host."""

import re
from urllib.parse import urlsplit

from flask import current_app

from ..access import BusinessError
from .client import http_client


def storage_target(url):
    """Return whether a validated URL belongs to the local storage gateway."""
    try:
        target = urlsplit(url)
        if (
            target.scheme != "https"
            or target.username
            or target.password
            or target.fragment
            or not target.hostname
        ):
            raise ValueError()
        if target.hostname == "storage.googleapis.com" and target.port in (None, 443):
            return False
        kernel = current_app.extensions.get("application_kernel")
        configured = current_app.config.get("STORAGE_PUBLIC_BASE_URL", "")
        if not configured and kernel is not None:
            configured = kernel.apps["documentos"].config.get(
                "STORAGE_PUBLIC_BASE_URL", ""
            )
        base = urlsplit(configured)
        if (
            base.scheme != "https"
            or not base.hostname
            or base.username
            or base.password
            or base.query
            or base.fragment
            or base.path not in ("", "/")
            or (target.hostname, target.port or 443)
            != (base.hostname, base.port or 443)
            or target.query
            or not re.fullmatch(
                r"/(?:portal-)?storage/v1/objects/[A-Za-z0-9_-]+=*", target.path
            )
        ):
            raise ValueError()
        return True
    except (TypeError, ValueError):
        raise BusinessError("Destino de almacenamiento no autorizado.", 503) from None


def upload_object(url, content, headers):
    local = storage_target(url)
    kernel = current_app.extensions.get("application_kernel")
    if local and kernel is not None:
        path = urlsplit(url).path
        if path.startswith("/portal-storage/v1/objects/"):
            path = "/storage/v1/objects/" + path.removeprefix(
                "/portal-storage/v1/objects/"
            )
        response = kernel.request(
            "documentos", "PUT", path, data=content, headers=headers
        )
    else:
        response = http_client().put(
            url, data=content, headers=headers, timeout=(2, 15), allow_redirects=False
        )
    with response:
        return response.status_code
