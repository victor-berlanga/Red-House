import json
import logging
import time
from uuid import UUID, uuid4

from flask import Flask, Response, g, request
from werkzeug.exceptions import HTTPException

from .codec import representation, respond
from .config import MONGO_SERVICES, settings
from .db import transaction
from .errors import APIError
from .events import mongodb
from .security import redis_call

logger = logging.getLogger("redhouse.request")


def base_app(service, config=None):
    app = Flask(service, static_folder=None)
    app.config.update(settings(service, config))
    app.extensions["contracts"] = []

    @app.before_request
    def prepare():
        g.started = time.perf_counter()
        try:
            value = request.headers.get("X-Correlation-ID", "")
            g.correlation_id = str(UUID(value))
        except (ValueError, TypeError):
            g.correlation_id = str(uuid4())
        g.error_code = None
        if request.path.startswith(("/api/", "/internal/", "/health/")):
            representation()

    @app.after_request
    def finish(response):
        response.headers.update(
            {
                "X-Correlation-ID": g.correlation_id,
                "Cache-Control": "no-store",
                "X-Content-Type-Options": "nosniff",
                "Referrer-Policy": "no-referrer",
            }
        )
        if response.status_code == 429:
            response.headers["Retry-After"] = "60"
        if hasattr(g, "cache_status"):
            response.headers["X-Cache"] = g.cache_status
        # No se registran query strings, cuerpos, JWT, nombres ni estudios.
        logger.info(
            json.dumps(
                {
                    "service": service,
                    "correlation_id": g.correlation_id,
                    "method": request.method,
                    "route": request.url_rule.rule if request.url_rule else "unmatched",
                    "status": response.status_code,
                    "elapsed_ms": round((time.perf_counter() - g.started) * 1000, 3),
                    "error": g.error_code,
                }
            )
        )
        return response

    @app.errorhandler(APIError)
    def expected(exc):
        g.error_code = exc.code
        return respond(
            {
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                },
                "meta": {
                    "correlation_id": g.correlation_id,
                    "service": service,
                    "version": app.config["VERSION"],
                },
            },
            exc.status,
        )

    @app.errorhandler(Exception)
    def unexpected(exc):
        if isinstance(exc, HTTPException):
            return expected(
                APIError("http_error", "Petición no disponible o inválida.", exc.code)
            )
        # El tipo técnico es útil; no imprimir excepciones que contengan SQL/DSN/datos.
        logger.error(
            json.dumps(
                {
                    "service": service,
                    "correlation_id": g.correlation_id,
                    "exception_type": type(exc).__name__,
                }
            )
        )
        return expected(
            APIError("internal_error", "No se pudo completar la operación.", 500)
        )

    def probe(name):
        try:
            if name == "database":
                with transaction() as conn:
                    from .schema import service_path

                    required = max(
                        2,
                        *(
                            int(p.stem)
                            for p in (service_path(service) / "migrations").glob(
                                "*.sql"
                            )
                        ),
                    )
                    if not conn.execute(
                        "SELECT version FROM schema_version WHERE version=%s",
                        (required,),
                    ).fetchone():
                        raise RuntimeError("schema_not_ready")
            elif name == "redis":
                redis_call(lambda r: r.ping())
            elif name == "mongodb":
                if service not in MONGO_SERVICES:
                    return {"state": "not_applicable"}
                with mongodb() as client:
                    client.admin.command("ping")
            elif name == "storage":
                if service != "transporte":
                    return {"state": "not_applicable"}
                if not app.config.get("GCS_BUCKET"):
                    return {"state": "not_configured", "required": False}
                from .storage import bucket

                if not bucket().exists(timeout=2):
                    raise RuntimeError("bucket_unavailable")
                return {"state": "up", "required": True}
            elif name == "worker":
                if not app.config.get("WORKER_REQUIRED", False):
                    return {"state": "not_configured", "required": False}
                with transaction() as conn:
                    heartbeat = conn.execute(
                        "SELECT extract(epoch FROM now()-checked_at) AS age,last_error FROM worker_health WHERE id=1"
                    ).fetchone()
                    backlog = conn.execute(
                        "SELECT count(*) AS pending,coalesce(extract(epoch FROM now()-min(created_at)),0) AS oldest_seconds FROM outbox WHERE delivered_at IS NULL"
                    ).fetchone()
                healthy = (
                    heartbeat
                    and heartbeat["age"] < app.config.get("WORKER_TIMEOUT", 120)
                    and not heartbeat["last_error"]
                )
                delayed = backlog["pending"] and backlog[
                    "oldest_seconds"
                ] > app.config.get("OUTBOX_WARNING_SECONDS", 120)
                return {
                    "state": ("degraded" if delayed else "up") if healthy else "down",
                    "error": ("outbox_delayed" if delayed else None)
                    if healthy
                    else "worker_unavailable",
                    "pending": backlog["pending"],
                    "oldest_seconds": float(backlog["oldest_seconds"]),
                }
            return {"state": "up"}
        except Exception:
            return {"state": "down", "error": "dependency_unavailable"}

    @app.get("/health/live")
    def live():
        return respond(
            {
                "data": {
                    "state": "up",
                    "service": service,
                    "version": app.config["VERSION"],
                },
                "meta": {"correlation_id": g.correlation_id},
            }
        )

    @app.get("/health/ready")
    def ready():
        states = {
            name: probe(name)
            for name in ("database", "redis", "mongodb", "storage", "worker")
        }
        available = not any(s["state"] in ("down", "degraded") for s in states.values())
        return respond(
            {
                "data": {
                    "state": "up" if available else "degraded",
                    "dependencies": states,
                    "service": service,
                    "version": app.config["VERSION"],
                },
                "meta": {"correlation_id": g.correlation_id},
            },
            200 if available else 503,
        )

    for name in ("database", "redis", "mongodb", "storage", "worker"):

        def check(dependency=name):
            result = probe(dependency)
            return respond(
                {"data": result, "meta": {"correlation_id": g.correlation_id}},
                503 if result["state"] in ("down", "degraded") else 200,
            )

        app.add_url_rule("/health/" + name, endpoint="health_" + name, view_func=check)
    return app


def complete_app(app):
    from .openapi import install

    install(app)
    return app
