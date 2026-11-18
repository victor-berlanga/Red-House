"""Cliente del arnés de carga aislado; nunca guarda tokens ni respuestas."""

import ipaddress
import json
import time
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlsplit

from jsonschema import Draft202012Validator, FormatChecker
from lxml import etree
from redhouse.xml_response import validate_response

ROOT = Path(__file__).resolve().parents[1]


class LoadFailure(Exception):
    """Solo códigos fijos, aptos para estadísticas sin datos de respuesta."""


class ReauthenticationRequired(LoadFailure):
    """Expected, validated challenge; the secret is never part of exception text."""

    def __init__(self, challenge):
        super().__init__("reauthentication_required")
        self.challenge = challenge


@lru_cache(maxsize=16)
def error_contract(service):
    module = "servicio_monitoreo" if service == "monitoreo" else "ms_" + service
    spec = json.loads((ROOT / module / "contracts/openapi.json").read_text())
    definition = {
        "$ref": "#/components/schemas/Error",
        "components": spec["components"],
    }
    return definition, Draft202012Validator(definition, format_checker=FormatChecker())


@lru_cache(maxsize=16)
def service_version(service):
    module = "servicio_monitoreo" if service == "monitoreo" else "ms_" + service
    return json.loads((ROOT / module / "contracts/openapi.json").read_text())["info"][
        "version"
    ]


def reauthentication_challenge(response, service, mime, *, diagnostic=None):
    """Accept only the declared 403 challenge; other denials remain failures."""
    schema, validator = error_contract(service)
    if diagnostic is not None:
        diagnostic.update(
            status=response.status_code,
            expected_service=service,
            expected_version=service_version(service),
            mime_matches=response.headers.get("Content-Type", "").split(";", 1)[0]
            == mime,
            response_bytes=len(response.content),
        )
    if (
        response.headers.get("Content-Type", "").split(";", 1)[0] != mime
        or len(response.content) > 65536
    ):
        raise ValueError("invalid_challenge_contract")
    if mime == "application/xml":
        payload = validate_response(response.content, schema)
    else:
        payload = response.json()
        validator.validate(payload)
    if diagnostic is not None:
        diagnostic.update(
            owner_matches=payload["meta"]["service"] == service,
            version_matches=payload["meta"]["version"] == service_version(service),
            correlation_id=payload["meta"]["correlation_id"],
            reauthentication_required=payload["error"]["code"]
            == "reauthentication_required",
            details=[
                {
                    "reauthentication_field": d.get("field") == "reauthentication",
                    "challenge_code": d.get("code") == "challenge",
                    "challenge_type": type(d.get("challenge")).__name__,
                    "challenge_length": len(d["challenge"])
                    if isinstance(d.get("challenge"), str)
                    else None,
                }
                for d in payload["error"].get("details", [])
            ],
        )
    if payload["meta"]["service"] != service or payload["meta"][
        "version"
    ] != service_version(service):
        raise ValueError("invalid_challenge_owner")
    error = payload["error"]
    if error["code"] != "reauthentication_required":
        raise ValueError("unexpected_denial")
    matches = [
        item.get("challenge")
        for item in error.get("details", [])
        if item.get("field") == "reauthentication" and item.get("code") == "challenge"
    ]
    if (
        len(matches) != 1
        or not isinstance(matches[0], str)
        or not 40 <= len(matches[0]) <= 4096
    ):
        raise ValueError("invalid_challenge")
    return matches[0]


def isolated_urls(urls):
    if not isinstance(urls, dict) or not urls:
        raise ValueError("Faltan destinos de laboratorio.")
    for url in urls.values():
        parsed = urlsplit(url)
        try:
            local = ipaddress.ip_address(parsed.hostname).is_loopback
            port = parsed.port
        except (ValueError, TypeError):
            local = False
            port = None
        if (
            not local
            or not port
            or parsed.scheme not in ("http", "https")
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
            or parsed.path not in ("", "/")
        ):
            raise ValueError("La carga requiere destinos IP de loopback explícitos.")
    return {key: value.rstrip("/") for key, value in urls.items()}


@lru_cache(maxsize=128)
def response_contract(service, path, method):
    module = "servicio_monitoreo" if service == "monitoreo" else "ms_" + service
    directory = ROOT / module / "contracts"
    spec = json.loads((directory / "openapi.json").read_text())
    operation = spec["paths"][path][method.lower()]["operationId"]
    schema = json.loads((directory / (operation + ".response.json")).read_text())
    return schema, Draft202012Validator(schema, format_checker=FormatChecker())


def request_xml(body):
    def write(parent, values):
        for name, value in values.items():
            node = etree.SubElement(parent, name)
            if isinstance(value, dict):
                write(node, value)
            elif isinstance(value, list):
                for item in value:
                    write(node, {"item": item})
            elif value is None:
                node.set("{http://www.w3.org/2001/XMLSchema-instance}nil", "true")
            else:
                node.text = (
                    str(value).lower() if isinstance(value, bool) else str(value)
                )

    root = etree.Element("request")
    write(root, body)
    return etree.tostring(root, encoding="UTF-8", xml_declaration=True)


class LoadSession:
    """Una identidad por usuario Locust; renovación secuencial, sin reintento."""

    def __init__(
        self,
        client,
        urls,
        *,
        clock=time.monotonic,
        no_cache=False,
        mime="application/json",
        cache_observer=None,
    ):
        self.client = client
        self.urls = isolated_urls(urls)
        self.clock = clock
        self.no_cache = no_cache
        self.cache_observer = cache_observer
        if mime not in ("application/json", "application/xml"):
            raise ValueError("Formato del arnés no admitido.")
        self.mime = mime
        self.access = self.refresh = None
        self.renew_at = 0
        self.user = None
        self.last_challenge_diagnostic = None

    def _wire(
        self,
        service,
        path,
        label,
        *,
        method="GET",
        body=None,
        mime=None,
        protected=True,
        canonical=None,
        key=None,
        expected=200,
        check=None,
        allow_reauthentication=False,
        proof=None,
    ):
        if not path.startswith("/api/v1/") or "://" in path or "#" in path:
            raise ValueError("Ruta no permitida en el arnés.")
        schema, validator = response_contract(
            service, canonical or path.split("?", 1)[0], method
        )
        mime = mime or self.mime
        headers = {"Accept": mime}
        if protected:
            if not self.access:
                raise LoadFailure("session_unavailable")
            headers["Authorization"] = "Bearer " + self.access
        if self.no_cache and method == "GET":
            headers["Cache-Control"] = "no-cache"
        if key:
            headers["Idempotency-Key"] = key
        if proof:
            headers["X-Reauthentication-Proof"] = proof
        request_body = {}
        if body is not None:
            if mime == "application/xml":
                headers["Content-Type"] = mime
                request_body["data"] = request_xml(body)
            else:
                request_body["json"] = body
        error = None
        payload = None
        challenge = None
        with self.client.request(
            method,
            self.urls[service] + path,
            name=label,
            headers=headers,
            timeout=(5, 20),
            allow_redirects=False,
            catch_response=True,
            **request_body,
        ) as response:
            if self.cache_observer:
                self.cache_observer(
                    response.headers.get("X-Cache"), response.status_code
                )
            if response.status_code == 403 and allow_reauthentication and proof is None:
                diagnostic = {}
                try:
                    challenge = reauthentication_challenge(
                        response, service, mime, diagnostic=diagnostic
                    )
                    response.success()
                except Exception as exc:  # noqa: BLE001 - keep hostile response bodies out of statistics
                    diagnostic["parser_exception"] = type(exc).__name__
                    self.last_challenge_diagnostic = diagnostic
                    error = "reauthentication_contract"
            elif response.status_code != expected:
                error = "http_" + str(response.status_code)
            else:
                try:
                    content_type = response.headers.get("Content-Type", "").split(
                        ";", 1
                    )[0]
                    if content_type != mime or len(response.content) > 8 * 1024 * 1024:
                        raise ValueError()
                    if mime == "application/xml":
                        payload = validate_response(response.content, schema)
                    else:
                        payload = response.json()
                        validator.validate(payload)
                    if check and not check(payload["data"]):
                        raise ValueError()
                except Exception:  # noqa: BLE001 - redact contract details from load statistics
                    error = "response_contract"
            if error:
                response.failure(error)
        if error:
            raise LoadFailure(error)
        if challenge is not None:
            raise ReauthenticationRequired(challenge)
        return payload["data"]

    def _accept_tokens(self, data):
        # A failed renewal never retries the consumed refresh token or logs in
        # again silently: its outcome remains an observed load-test failure.
        self.access = data["access_token"]
        self.refresh = data["refresh_token"]
        lifetime = data["expires_in"]
        if lifetime <= 0:
            raise LoadFailure("invalid_token_lifetime")
        self.renew_at = self.clock() + max(0.1, lifetime - min(30, lifetime / 2))

    def login(self, username, password, otp=None):
        body = {"username": username, "password": password}
        if otp is not None:
            body["otp"] = otp
        data = self._wire(
            "identidad_acceso",
            "/api/v1/auth/login",
            "Identidad / login",
            method="POST",
            body=body,
            protected=False,
            check=lambda data: (
                data["expires_in"] > 0
                and data["user"]["username"] == username
                and data["user"]["active"]
            ),
        )
        self._accept_tokens(data)
        self.user = data["user"]
        if self.user["username"] != username or not self.user["active"]:
            raise LoadFailure("identity_mismatch")

    def renew(self):
        if not self.access or not self.refresh:
            raise LoadFailure("session_unavailable")
        try:
            data = self._wire(
                "identidad_acceso",
                "/api/v1/auth/refresh",
                "Identidad / renovación",
                method="POST",
                body={"refresh_token": self.refresh},
                protected=False,
                check=lambda value: (
                    value["expires_in"] > 0 and value["refresh_token"] != self.refresh
                ),
            )
        except LoadFailure:
            self.access = None
            self.renew_at = float("inf")
            raise
        self._accept_tokens(data)

    def request(self, service, path, label, **kwargs):
        if kwargs.get("protected", True) and not self.access:
            raise LoadFailure("session_unavailable")
        if kwargs.get("protected", True) and self.clock() >= self.renew_at:
            self.renew()
        return self._wire(service, path, label, **kwargs)

    def close(self):
        try:
            if self.refresh:
                self._wire(
                    "identidad_acceso",
                    "/api/v1/auth/revoke",
                    "Identidad / revocación al salir",
                    method="POST",
                    body={"refresh_token": self.refresh},
                    protected=False,
                )
        finally:
            self.access = self.refresh = self.user = None
            self.renew_at = 0
