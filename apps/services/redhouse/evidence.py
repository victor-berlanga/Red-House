"""Captura explícita de peticiones ejecutadas con datos ficticios, nunca por defecto."""

import base64
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from flask import current_app, g, request

PRIVATE = re.compile(
    r"password|secret|token|authorization|cookie|signature|private.key|upload_url|download_url",
    re.IGNORECASE,
)


def redact(value, key=""):
    if PRIVATE.search(key):
        return "[REDACTED]"
    if isinstance(value, dict):
        return {k: redact(v, k) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v) for v in value]
    if isinstance(value, str):
        value = re.sub(
            r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+",
            "[REDACTED JWT]",
            value,
        )
        if "X-Goog-Signature=" in value:
            url = urlsplit(value)
            return urlunsplit((url.scheme, url.netloc, url.path, "[REDACTED]", ""))
    return value


def body(raw, mime):
    if raw and not any(
        value in mime for value in ("json", "xml", "text", "javascript")
    ):
        return {"encoding": "base64", "content": base64.b64encode(raw).decode()}
    text = raw.decode("utf-8", errors="replace")
    if "json" in mime:
        try:
            return redact(json.loads(text))
        except ValueError:
            return (
                "[Invalid JSON omitted; sha256=" + hashlib.sha256(raw).hexdigest() + "]"
            )
    if "xml" in mime:
        from lxml import etree

        try:
            root = etree.fromstring(
                raw,
                etree.XMLParser(
                    resolve_entities=False, no_network=True, load_dtd=False
                ),
            )
            for node in root.iter():
                if isinstance(node.tag, str) and PRIVATE.search(
                    node.get("name", node.tag)
                ):
                    node.text = "[REDACTED]"
                    for child in list(node):
                        node.remove(child)
            return redact(etree.tostring(root, encoding="unicode"))
        except etree.XMLSyntaxError:
            return (
                "[Invalid XML omitted; sha256=" + hashlib.sha256(raw).hexdigest() + "]"
            )
    return redact(text)


def install(app, directory):
    directory = Path(directory) / app.config["SERVICE"]
    directory.mkdir(parents=True, exist_ok=True)
    from .schema import service_path

    digest = hashlib.sha256()
    source_files = list(Path(__file__).parent.glob("*.py")) + list(
        service_path(app.config["SERVICE"]).glob("*.py")
    )
    for source in sorted(source_files):
        digest.update(source.name.encode() + source.read_bytes())
    implementation_hash = digest.hexdigest()
    inventory = []
    for rule in app.url_map.iter_rules():
        for method in sorted(rule.methods - {"OPTIONS", "HEAD"}):
            contract = next(
                (c for c in app.extensions["contracts"] if c["name"] == rule.endpoint),
                {},
            )
            inventory.append(
                {
                    "method": method,
                    "route": rule.rule,
                    "endpoint": rule.endpoint,
                    "objective": contract.get(
                        "summary", "Infraestructura y documentación"
                    ),
                    "roles": list(contract.get("roles", ())),
                    "internal_callers": list(contract.get("internal", ())),
                    "version": app.config["VERSION"],
                }
            )
    (directory / "inventory.json").write_text(json.dumps(inventory, indent=2) + "\n")

    @app.after_request
    def record(response):
        if not request.url_rule:
            return response
        mime = response.mimetype or ""
        route = request.url_rule.rule
        # send_file responses stream by default. Evidence is opt-in and needs
        # the actual bytes, so materialize the stream before capturing it.
        if response.direct_passthrough:
            response.direct_passthrough = False
        transport = request.environ.get("redhouse.transport")
        if not transport:
            server = request.environ.get("SERVER_SOFTWARE", "").lower()
            transport = (
                "http"
                if "werkzeug.socket" in request.environ
                or server.startswith(("werkzeug", "waitress"))
                else "wsgi"
            )
        response_body = body(response.get_data(), mime)
        error = (
            response_body.get("error", {}).get("code", "")
            if isinstance(response_body, dict)
            else ""
        )
        identity = "|".join(
            (
                request.method,
                route,
                str(response.status_code),
                mime,
                error,
                request.content_type or "",
                transport,
            )
        )
        path = directory / (
            hashlib.sha256(identity.encode()).hexdigest()[:24] + ".json"
        )
        record = {
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "version": app.config["VERSION"],
            "source_revision": app.config.get("SOURCE_REVISION", "working-tree"),
            "implementation_sha256": implementation_hash,
            "transport": transport,
            "method": request.method,
            "route": route,
            "objective": next(
                (
                    c["summary"]
                    for c in app.extensions["contracts"]
                    if c["name"] == request.endpoint
                ),
                request.endpoint,
            ),
            "url": request.url,
            "parameters": dict(request.args),
            "path_parameters": request.view_args,
            "request_headers": redact(dict(request.headers)),
            "request_body": body(request.get_data(), request.content_type or ""),
            "status": response.status_code,
            "response_headers": redact(
                dict(
                    response.headers,
                    **{"X-Correlation-ID": str(getattr(g, "correlation_id", ""))},
                )
            ),
            "response_body": response_body,
            "correlation_id": str(getattr(g, "correlation_id", "")),
        }
        try:
            record["persistence"] = persistence(response)
        except Exception as exc:  # noqa: BLE001 - evidence must not change committed HTTP outcomes
            # Collection must never turn a committed operation into HTTP 500.
            # The catalogue exposes the missing proof for review/re-execution.
            record["persistence"] = {
                "effect": "verification_error",
                "type": type(exc).__name__,
            }
            app.logger.error(
                "http_persistence_evidence_failed type=%s", type(exc).__name__
            )
        try:
            with path.open("x") as stream:
                json.dump(record, stream, indent=2, default=str)
                stream.write("\n")
        except FileExistsError:
            pass
        except OSError:
            app.logger.error("http_evidence_write_failed")
        return response

    # Flask invokes response hooks in reverse registration order. Capture after
    # the standard security and correlation headers have been applied.
    app.after_request_funcs[None].insert(0, app.after_request_funcs[None].pop())


def payload(raw, mime):
    """Decode only trusted successful envelopes for read-only verification."""
    if "json" in mime:
        return json.loads(raw)
    from lxml import etree

    root = etree.fromstring(
        raw, etree.XMLParser(resolve_entities=False, no_network=True)
    )

    def unpack(node):
        if node.get("type") == "array":
            return [unpack(child) for child in node]
        return (
            {child.get("name", child.tag): unpack(child) for child in node}
            if len(node)
            else node.text
        )

    return unpack(root)


def persistence(response):
    if response.status_code >= 400:
        return {
            "effect": "controlled_error",
            "note": "No se infiere ausencia de efectos de un error; revisar correlación y estado de operación.",
        }
    if request.method == "GET":
        return {
            "effect": "read",
            "note": "Consulta; accesos protegidos generan auditoría local transaccional.",
        }
    actor = getattr(g, "actor", {})
    idem = request.headers.get("Idempotency-Key")
    from .db import transaction
    from .errors import APIError

    service = current_app.config["SERVICE"]
    data = payload(response.get_data(), response.mimetype).get("data", {})

    def proof(query, params):
        with transaction() as conn:
            row = conn.execute(query, params).fetchone()
        return {
            "effect": "committed" if row else "record_not_found",
            "store": "PostgreSQL red_house",
            "query": query,
            "parameters": redact(list(params)),
            "row": redact(row),
        }

    try:
        if service == "identidad_acceso" and request.path.startswith("/api/v1/auth/"):
            import jwt

            from .security import key, redis_call

            claims = getattr(g, "claims", None)
            if data.get("access_token"):
                claims = jwt.decode(
                    data["access_token"],
                    current_app.config["JWT_PUBLIC_KEY"],
                    algorithms=["RS256"],
                    issuer=current_app.config["JWT_ISSUER"],
                    audience=current_app.config["JWT_AUDIENCE"],
                )
            if claims:
                sid = claims["sid"]
            else:
                sid = payload(request.get_data(), request.mimetype)[
                    "refresh_token"
                ].split(".")[0]
            result = proof(
                "SELECT id,user_id,expires_at,revoked_at FROM sessions WHERE id=%s",
                (sid,),
            )
            result["redis"] = redis_call(
                lambda r: {
                    "session_exists": bool(r.exists(key("session:" + sid))),
                    "session_ttl": r.ttl(key("session:" + sid)),
                }
            )
            return result
        if request.path == "/internal/v1/events":
            event = payload(request.get_data(), request.mimetype)
            return proof(
                "SELECT event_id,fingerprint FROM inbox WHERE event_id=%s",
                (event["event_id"],),
            )
        if service == "receptores" and request.path.startswith("/internal/v1/holds"):
            return proof(
                "SELECT id,operation_id,request_id,resource_id,status FROM holds WHERE id=%s",
                (data["id"],),
            )
        if service == "inventario" and (
            request.path == "/api/v1/reservations" or request.path.endswith("/resume")
        ):
            return proof(
                "SELECT id,status,hold_id,error FROM operations WHERE id=%s",
                (data["operation_id"],),
            )
        if service == "inventario" and request.path.endswith("/claim"):
            return proof(
                "SELECT id,status,shipment_id FROM reservations WHERE id=%s",
                (request.view_args["identifier"],),
            )
        if service == "transporte" and request.path == "/api/v1/shipments":
            return proof(
                "SELECT id,reservation_id,status,inventory_pending FROM shipments WHERE id=%s",
                (data["id"],),
            )
    except APIError:
        return {"effect": "verification_unavailable"}
    if actor.get("id") and idem:
        try:
            with transaction() as conn:
                row = conn.execute(
                    "SELECT operation,fingerprint,result FROM idempotency WHERE user_id=%s AND key=%s",
                    (actor["id"], idem),
                ).fetchone()
            if row:
                return {
                    "effect": "committed",
                    "store": "PostgreSQL red_house",
                    "query": "SELECT operation,fingerprint,result FROM idempotency WHERE user_id=:actor AND key=:idempotency_key",
                    "row": redact(row),
                }
        except APIError:
            return {"effect": "verification_unavailable"}
    return {
        "effect": "requires_flow_evidence",
        "note": "Operación sin registro idempotente humano; revisar sesión Redis, inbox firmado o prueba de flujo relacionada.",
    }
