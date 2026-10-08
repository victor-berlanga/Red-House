"""Modo integrado: Flask/Jinja presenta; las API son autoridad de negocio."""

import json
import time
from pathlib import Path
from uuid import UUID, uuid4

from flask import g, jsonify, redirect, render_template, request, url_for
from flask_wtf.csrf import CSRFError, CSRFProtect
from werkzeug.exceptions import HTTPException

from ..business.access import BusinessError, Principal
from ..presentation.timezones import (
    ZONES,
    datefmt,
    inputfmt,
    local_value,
    selected_zone,
)
from ..presentation.views import audit_label, regional_value
from . import sessions
from .client import call, validate_urls

ROLES = {
    "ADMIN": "Administrador",
    "OPERATOR": "Operador",
    "MEDICAL": "Médico",
    "COORDINATOR": "Coordinador",
    "TRANSPORT": "Personal de traslado",
    "AUDITOR": "Auditor",
    "DONOR": "Donante",
}
PERMISSIONS = {
    "dashboard": set(ROLES),
    "inventory.read": {"OPERATOR", "MEDICAL", "COORDINATOR"},
    "donor.write": {"OPERATOR", "MEDICAL", "DONOR"},
    "recipient.write": {"MEDICAL", "OPERATOR"},
    "requests.read": {"MEDICAL", "OPERATOR"},
    "matching.read": {"MEDICAL"},
    "donations.read": {"MEDICAL", "OPERATOR"},
    "campaigns.read": {"MEDICAL", "OPERATOR", "DONOR"},
    "appointments.read": {"OPERATOR", "DONOR"},
    "route.write": {"COORDINATOR", "MEDICAL", "OPERATOR", "TRANSPORT"},
    "logistics": {"COORDINATOR", "MEDICAL", "OPERATOR", "TRANSPORT"},
    "organ.read": {"COORDINATOR", "MEDICAL", "OPERATOR"},
    "audit.read": {"AUDITOR"},
    "administration": {"ADMIN"},
    "alerts.read": set(ROLES),
    "monitor.read": {"ADMIN", "COORDINATOR", "AUDITOR"},
}
NAV = [
    (
        "GENERAL",
        "dashboard",
        "Panel principal",
        "layout-grid",
        "portal.dashboard",
        {},
        "dashboard",
        False,
    ),
    (
        "BANCO DE SANGRE",
        "donantes",
        "Donantes",
        "droplet",
        "regional.people",
        {"kind": "donor"},
        "donor.write",
        False,
    ),
    (
        "BANCO DE SANGRE",
        "donaciones",
        "Donaciones y procesamiento",
        "layers",
        "regional.donations",
        {},
        "donations.read",
        False,
    ),
    (
        "BANCO DE SANGRE",
        "receptores",
        "Receptores",
        "users",
        "regional.people",
        {"kind": "recipient"},
        "recipient.write",
        False,
    ),
    (
        "BANCO DE SANGRE",
        "inventory",
        "Inventario sanguíneo",
        "package",
        "inventory.index",
        {},
        "inventory.read",
        False,
    ),
    (
        "BANCO DE SANGRE",
        "disponibilidad",
        "Disponibilidad regional",
        "map-pin",
        "inventory.availability",
        {},
        "inventory.read",
        False,
    ),
    (
        "BANCO DE SANGRE",
        "solicitudes",
        "Solicitudes y compatibilidad",
        "triangle-alert",
        "regional.requests",
        {},
        "requests.read",
        False,
    ),
    (
        "BANCO DE SANGRE",
        "propuestas",
        "Propuestas de cobertura",
        "layout-grid",
        "regional.proposals",
        {},
        "matching.read",
        False,
    ),
    (
        "BANCO DE SANGRE",
        "campanas",
        "Campañas",
        "calendar-days",
        "regional.campaigns",
        {},
        "campaigns.read",
        False,
    ),
    (
        "BANCO DE SANGRE",
        "citas",
        "Citas",
        "calendar-days",
        "regional.appointments",
        {},
        "appointments.read",
        False,
    ),
    (
        "LOGÍSTICA",
        "rutas",
        "Rutas y estimaciones",
        "map-pin",
        "regional.routes",
        {},
        "route.write",
        False,
    ),
    (
        "LOGÍSTICA",
        "traslados",
        "Traslados y custodia",
        "truck",
        "regional.allocations",
        {},
        "logistics",
        False,
    ),
    (
        "DONACIÓN / TRASPLANTE DE ÓRGANOS",
        "organos",
        "Órganos y HLA",
        "heart-pulse",
        "organs.index",
        {},
        "organ.read",
        False,
    ),
    (
        "SEGUIMIENTO",
        "alertas",
        "Notificaciones",
        "inbox",
        "portal.alerts",
        {},
        "alerts.read",
        False,
    ),
    (
        "SEGUIMIENTO",
        "audit",
        "Bitácora de auditoría",
        "scroll-text",
        "portal.audit",
        {},
        "audit.read",
        False,
    ),
    (
        "SEGUIMIENTO",
        "monitoreo",
        "Estado de la plataforma",
        "shield-check",
        "portal.monitor",
        {},
        "monitor.read",
        False,
    ),
    (
        "ADMINISTRACIÓN",
        "institutions",
        "Instituciones",
        "building-2",
        "admin.index",
        {"entity": "institutions"},
        "administration",
        False,
    ),
    (
        "ADMINISTRACIÓN",
        "users",
        "Usuarios",
        "user-round-cog",
        "admin.index",
        {"entity": "users"},
        "administration",
        False,
    ),
    (
        "ADMINISTRACIÓN",
        "components",
        "Catálogos",
        "settings-2",
        "admin.index",
        {"entity": "components"},
        "administration",
        False,
    ),
    (
        "ADMINISTRACIÓN",
        "settings",
        "Roles y parámetros",
        "sliders-horizontal",
        "admin.settings",
        {},
        "administration",
        False,
    ),
]


class RemotePrincipal(Principal):
    def can(self, action):
        return self.role_code in PERMISSIONS.get(action, set())


def configure(app):
    config = app.config.get("MICROSERVICES_CONFIG")
    if isinstance(config, (str, Path)):
        config = json.loads(Path(config).read_text())
    if not isinstance(config, dict):
        raise RuntimeError(
            "MICROSERVICES_CONFIG debe apuntar a configuración privada del cliente web."
        )
    app.config.update(config)
    app.config["DEFAULT_DISPLAY_TIMEZONE"] = "America/Monterrey"
    validate_urls(app.config.get("SERVICE_URLS"))
    if not app.config.get("WEB_SESSION_STORE"):
        raise RuntimeError("Configura almacenamiento privado de sesiones web.")

    @app.before_request
    def identify():
        g.correlation_id, g.principal, g.access_token = uuid4(), None, None
        public = {
            "public.index",
            "public.login",
            "public.recovery",
            "public.live",
            "public.logout",
            "public.renew_session",
            "static",
        }
        if not request.endpoint or request.endpoint in public:
            return
        sid = request.cookies.get(app.config["JWT_COOKIE_NAME"])
        try:
            user = sessions.authenticate(sid)
        except BusinessError as exc:
            if exc.status != 401:
                raise
            user = None
        if not user:
            if request.endpoint == "public.session_status":
                return jsonify(
                    message="Tu sesión terminó. Inicia sesión nuevamente."
                ), 401
            response = redirect(url_for("public.login"))
            response.delete_cookie(app.config["JWT_COOKIE_NAME"])
            return response
        cache = app.extensions.setdefault("institution_names", {})
        cached = cache.get(user["region_id"])
        if cached and cached["until"] > time.monotonic():
            g.institutions = cached["names"]
        else:
            names, page = {}, 1
            try:
                while True:
                    institutions = call(
                        "identidad_acceso",
                        "/api/v1/institutions",
                        params={"page_size": 100, "page": page},
                    )
                    names.update(
                        {row["id"]: row["name"] for row in institutions["items"]}
                    )
                    if page * 100 >= institutions["total"] or not institutions["items"]:
                        break
                    page += 1
                cache[user["region_id"]] = {
                    "until": time.monotonic() + 30,
                    "names": names,
                }
                g.institutions = names
            except BusinessError as exc:
                if exc.status != 503:
                    raise
                # Los nombres son etiquetas, nunca una fuente de permisos.
                g.institutions = cached["names"] if cached else {}
        g.principal = RemotePrincipal(
            UUID(user["id"]),
            user["username"],
            user["role"],
            ROLES[user["role"]],
            UUID(user["tenant_id"]),
            app.config.get("REGION_NAME", "Nuevo León"),
            g.institutions.get(user["tenant_id"], "Institución"),
        )

    CSRFProtect(app)

    @app.cli.command("retry-session-revocations")
    def retry_session_revocations():
        import click

        click.echo(f"Revocaciones confirmadas: {sessions.retry_revocations()}")

    from .routes import blueprints
    from .maintenance import bp as maintenance

    app.register_blueprint(maintenance)
    from .selectors import bp as selectors

    app.register_blueprint(selectors)
    for bp in blueprints():
        app.register_blueprint(bp)
    app.jinja_env.filters.update(
        datefmt=datefmt,
        inputfmt=inputfmt,
        regional_value=regional_value,
        audit_label=audit_label,
    )
    from .routes import display

    app.jinja_env.filters["portal_value"] = display

    @app.context_processor
    def context():
        from datetime import datetime, timezone

        return dict(
            principal=getattr(g, "principal", None),
            navigation=NAV,
            chart_enabled=app.config["HIGHCHARTS_ENABLED"],
            display_timezone=selected_zone(),
            timezone_choices=ZONES,
            local_now=local_value(datetime.now(timezone.utc)),
            detail_modal=False,
            filter_fragment=False,
            roles=ROLES,
            integration_mode=True,
        )

    @app.after_request
    def headers(response):
        response.headers.update(
            {
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY",
                "Referrer-Policy": "same-origin",
                "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
                "X-Request-ID": str(g.correlation_id),
            }
        )
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'"
        )
        if request.endpoint != "static":
            response.headers["Cache-Control"] = "no-store"
        if app.config["PRODUCTION"]:
            response.headers["Strict-Transport-Security"] = "max-age=31536000"
        return response

    @app.errorhandler(BusinessError)
    def business_error(exc):
        return render_template(
            "error.html",
            title="No fue posible completar la operación",
            code=exc.status,
            message=exc.message,
        ), exc.status

    @app.errorhandler(CSRFError)
    def csrf_error(exc):
        return render_template(
            "error.html",
            title="Formulario vencido",
            code=400,
            message="Recarga el formulario y vuelve a intentarlo.",
        ), 400

    @app.errorhandler(HTTPException)
    def http_error(exc):
        return render_template(
            "error.html",
            title="Página no disponible",
            code=exc.code,
            message="La página u operación no está disponible.",
        ), exc.code

    @app.errorhandler(Exception)
    def unexpected(exc):
        if app.testing:
            raise exc
        app.logger.error(
            "web_service_failure correlation=%s type=%s",
            g.correlation_id,
            type(exc).__name__,
        )
        return render_template(
            "error.html",
            title="Servicio temporalmente no disponible",
            code=503,
            message="No fue posible completar la operación. Conserva el identificador de referencia.",
        ), 503

    return app
