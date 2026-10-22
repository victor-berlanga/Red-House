import json
import time
import atexit
from threading import local
from uuid import uuid4

import requests
from flask import current_app, g, has_request_context, request

from .errors import APIError
from .security import internal_signature

_clients = local()


def http_client():
    if not hasattr(_clients, "session"):
        _clients.session = requests.Session()
        _clients.session.trust_env = False
        atexit.register(_clients.session.close)
    # Las credenciales siempre viajan en el encabezado de esta petición.
    _clients.session.cookies.clear()
    return _clients.session


def call(service, method, path, data=None, delegate=True):
    cfg = current_app.config
    url = cfg["SERVICE_URLS"].get(service)
    if not url:
        raise APIError(
            "dependency_unconfigured", "Servicio dependiente no configurado.", 503
        )
    body = (
        json.dumps(data, separators=(",", ":"), allow_nan=False).encode()
        if data is not None
        else b""
    )
    caller = cfg["SERVICE"]
    secret = cfg["SERVICE_PRIVATE_KEY"]
    if not secret:
        raise APIError("service_credentials", "Credencial interna no configurada.", 503)
    timestamp, nonce = str(int(time.time())), str(uuid4())
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Service": caller,
        "X-Service-Time": timestamp,
        "X-Service-Nonce": nonce,
        "X-Service-Signature": internal_signature(
            secret, method, path, timestamp, nonce, body
        ),
        "X-Correlation-ID": getattr(g, "correlation_id", str(uuid4())),
    }
    if delegate and has_request_context():
        headers["Authorization"] = request.headers.get("Authorization", "")
    try:
        local_dispatch = cfg.get("LOCAL_DISPATCH")
        if local_dispatch is not None:
            response = local_dispatch(service, method, path, data=body, headers=headers)
        else:
            response = http_client().request(
                method,
                url.rstrip("/") + path,
                data=body,
                headers=headers,
                timeout=(1, 3),
                allow_redirects=False,
            )
        result = response.json()
        if not isinstance(result, dict) or not isinstance(result.get("meta"), dict):
            raise ValueError()
        if response.status_code >= 400:
            error = result.get("error", {})
            raise APIError(
                error.get("code", "dependency_error"),
                error.get("message", "Dependencia rechazó la operación."),
                response.status_code,
                error.get("details", []),
            )
        if "data" not in result:
            raise ValueError()
        return result["data"]
    except (requests.RequestException, ValueError):
        raise APIError(
            "dependency_unavailable",
            "Dependencia inaccesible o respuesta inválida; consulta la operación antes de reintentar.",
            503,
        ) from None
