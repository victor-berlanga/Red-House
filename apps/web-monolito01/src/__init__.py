from datetime import datetime, timezone
from uuid import uuid4

import psycopg
from flask import Flask, g, redirect, render_template, request, url_for
from flask_wtf.csrf import CSRFError, CSRFProtect
from werkzeug.exceptions import HTTPException

from .business.access import BusinessError
from .business.services import auth
from .config.settings import settings


def create_app(overrides=None):
    app = Flask(__name__, template_folder="presentation/templates", static_folder="presentation/static")
    app.config.update(settings())
    app.config.update(overrides or {})
    for key in ("SECRET_KEY", "JWT_SECRET_KEY"):
        value = app.config.get(key)
        if not isinstance(value, str) or len(value) < 32:
            raise RuntimeError(f"Configura {key} con al menos 32 caracteres aleatorios en el entorno local.")
    if app.config["SECRET_KEY"] == app.config["JWT_SECRET_KEY"]:
        raise RuntimeError("SECRET_KEY y JWT_SECRET_KEY deben ser diferentes.")

    @app.before_request
    def identity():
        g.correlation_id, g.principal, g.session_id = uuid4(), None, None
        public = {"public.index", "public.login", "public.recovery", "public.live", "static"}
        if request.endpoint and request.endpoint not in public:
            g.principal, g.session_id = auth.authenticate(request.cookies.get(app.config["JWT_COOKIE_NAME"]))
            if not g.principal:
                response = redirect(url_for("public.login"))
                response.delete_cookie(app.config["JWT_COOKIE_NAME"], path="/")
                return response

    CSRFProtect(app)

    from .presentation.routes import admin, inventory, portal, public
    for blueprint in (public.bp, portal.bp, admin.bp, inventory.bp):
        app.register_blueprint(blueprint)
    from .cli import register
    register(app)

    @app.context_processor
    def common_context():
        from .presentation.views import NAV, FUTURE, TITLES
        from .data_access.repositories.inventory import STATUSES
        return {"principal": getattr(g, "principal", None), "navigation": NAV, "future_views": FUTURE,
                "titles": TITLES, "statuses": STATUSES, "utc_now": datetime.now(timezone.utc),
                "chart_enabled": app.config["HIGHCHARTS_ENABLED"]}

    @app.template_filter("datefmt")
    def datefmt(value):
        return value.astimezone(timezone.utc).strftime("%d/%m/%Y · %H:%M") if value else "—"

    @app.after_request
    def response_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; "
            "connect-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'")
        response.headers["X-Request-ID"] = str(getattr(g, "correlation_id", uuid4()))
        if request.endpoint != "static":
            response.headers["Cache-Control"] = "no-store"
        if app.config["PRODUCTION"]:
            response.headers["Strict-Transport-Security"] = "max-age=31536000"
        return response

    @app.errorhandler(BusinessError)
    def business_error(error):
        if error.status in (403, 404) and getattr(g, "principal", None):
            from .data_access.connection import transaction
            from .data_access.repositories.audit import record
            with transaction() as conn:
                record(conn, g.principal, "ACCESS", "ENDPOINT", request.endpoint or "UNKNOWN",
                       "Operación denegada", outcome="DENIED")
        return render_template("error.html", title="Operación no completada", message=error.message, code=error.status), error.status

    @app.errorhandler(CSRFError)
    def csrf_error(error):
        return render_template("error.html", title="Formulario vencido", code=400,
                               message="La protección del formulario venció. Regresa, recarga la página y vuelve a intentarlo."), 400

    @app.errorhandler(psycopg.IntegrityError)
    def integrity_error(error):
        return render_template("error.html", title="Revisa el registro", code=409,
                               message="El código o correo ya existe, o una referencia impide guardar el cambio. No se aplicó la operación."), 409

    @app.errorhandler(psycopg.Error)
    def database_error(error):
        app.logger.error("database_unavailable correlation=%s type=%s", getattr(g, "correlation_id", "none"), type(error).__name__)
        return render_template("error.html", title="Servicio temporalmente no disponible", code=503,
                               message="No se pudo completar la operación con PostgreSQL. No se confirmó ningún cambio; vuelve a intentarlo al restablecer el servicio."), 503

    @app.errorhandler(HTTPException)
    def http_error(error):
        return render_template("error.html", title="Página no disponible", code=error.code,
                               message="La página o la operación solicitada no está disponible."), error.code

    @app.errorhandler(Exception)
    def unexpected_error(error):
        if app.testing:
            raise error
        app.logger.error("request_failed correlation=%s type=%s", getattr(g, "correlation_id", "none"), type(error).__name__)
        return render_template("error.html", title="No fue posible completar la operación", code=500,
                               message="Ocurrió un error interno. Conserva el identificador de referencia y contacta al responsable del entorno."), 500

    return app
