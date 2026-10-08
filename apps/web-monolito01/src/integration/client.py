"""Cliente HTTP del servidor web. Nunca importa código ni conecta a bases de los MS."""

import json
import atexit
from threading import local
import requests
from urllib.parse import urlencode, urlsplit
from uuid import uuid4

from flask import current_app, g

from ..business.access import BusinessError


_clients = local()


def http_client():
    if not hasattr(_clients, "session"):
        _clients.session = requests.Session()
        _clients.session.trust_env = False
        atexit.register(_clients.session.close)
    _clients.session.cookies.clear()
    return _clients.session


def call(service, path, method="GET", data=None, *, token=None, idem=None, params=None):
    urls = current_app.config["SERVICE_URLS"]
    if (
        service not in urls
        or not path.startswith("/api/v1/")
        or "?" in path
        or "#" in path
    ):
        raise BusinessError("Operación de servicio no configurada.", 503)
    url = urls[service].rstrip("/") + path
    if params:
        url += "?" + urlencode(
            {k: v for k, v in params.items() if v is not None and v != ""}
        )
    headers = {
        "Accept": "application/json",
        "X-Correlation-ID": str(getattr(g, "correlation_id", uuid4())),
    }
    token = token if token is not None else getattr(g, "access_token", None)
    if token:
        headers["Authorization"] = "Bearer " + token
    if method in ("POST", "PATCH", "PUT"):
        headers["Idempotency-Key"] = idem or uuid4().hex
    body = None
    if data is not None:
        body = json.dumps(data, allow_nan=False).encode()
        headers["Content-Type"] = "application/json"
    try:
        with http_client().request(
            method,
            url,
            data=body,
            headers=headers,
            timeout=(1, current_app.config.get("SERVICE_TIMEOUT", 8)),
            allow_redirects=False,
            stream=True,
        ) as response:
            status = response.status_code
            if (
                300 <= status < 400
                or response.headers.get("Content-Type", "").split(";")[0]
                != "application/json"
            ):
                raise ValueError()
            raw = bytearray()
            for chunk in response.iter_content(8192):
                raw.extend(chunk)
                if len(raw) > 8 * 1024 * 1024:
                    raise ValueError()
            value = json.loads(raw)
        if not isinstance(value, dict) or not isinstance(value.get("meta"), dict):
            raise ValueError()
    except (
        requests.RequestException,
        TimeoutError,
        OSError,
        ValueError,
        TypeError,
    ) as exc:
        current_app.logger.warning(
            "service_call_failed service=%s method=%s exception_type=%s correlation_id=%s",
            service,
            method,
            type(exc).__name__,
            headers["X-Correlation-ID"],
        )
        raise BusinessError(
            "Un servicio necesario no está disponible. Conserva el formulario y vuelve a intentarlo; si enviaste una reserva, consulta su estado antes de repetirla.",
            503,
        ) from None
    if status >= 400:
        error = value.get("error", {})
        message = error.get("message")
        if not isinstance(message, str) or len(message) > 1200:
            message = "El servicio no pudo completar la operación."
        raise BusinessError(
            message,
            status
            if status in (400, 401, 403, 404, 409, 413, 415, 422, 429, 503)
            else 503,
        )
    if "data" not in value:
        raise BusinessError("Un servicio devolvió una respuesta inválida.", 503)
    return value["data"]


def validate_urls(urls):
    if not isinstance(urls, dict):
        raise RuntimeError("Configura SERVICE_URLS.")
    for url in urls.values():
        part = urlsplit(url)
        if (
            part.username
            or part.password
            or part.query
            or part.fragment
            or part.path not in ("", "/")
            or (
                part.scheme != "https"
                and not (
                    part.scheme == "http"
                    and part.hostname in ("127.0.0.1", "localhost", "::1")
                )
            )
        ):
            raise RuntimeError(
                "URLs de servicios requieren HTTPS o loopback local, sin credenciales."
            )
