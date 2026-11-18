"""La «Referencia» que muestra la página de error del portal queda en el log."""

import logging
import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "web"))
from src import create_app
from src.access import BusinessError

SERVICES = (
    "identidad_acceso donantes receptores inventario compatibilidad "
    "priorizacion_geografia transporte custodia alertas auditoria monitoreo documentos"
).split()


def portal():
    app = create_app(
        {
            "BACKEND_MODE": "microservices",
            "TESTING": True,
            "MICROSERVICES_CONFIG": {
                "SECRET_KEY": secrets.token_urlsafe(32),
                "JWT_SECRET_KEY": secrets.token_urlsafe(32),
                "SERVICE_URLS": {name: "http://127.0.0.1:9" for name in SERVICES},
                # Sin conexiones reales: la ruta de prueba no usa sesión ni base.
                "WEB_REDIS_URL": "redis://127.0.0.1:9/0",
                "WEB_REDIS_PREFIX": "rh-prueba",
                "WEB_DATABASE_URL": "postgresql://prueba@127.0.0.1:9/prueba",
            },
        }
    )

    def negocio():
        raise BusinessError("Tu perfil no tiene permiso para esta operación.", 403)

    # Ruta pública existente: no requiere sesión ni servicios.
    app.view_functions["public.live"] = negocio
    return app


def test_business_error_reference_is_logged(caplog):
    app = portal()
    with caplog.at_level(logging.WARNING, logger=app.logger.name):
        with app.test_request_context():
            from flask import url_for

            path = url_for("public.live")
        response = app.test_client().get(path)
    assert response.status_code == 403
    page = response.get_data(as_text=True)
    reference = page.split("Referencia: <code>", 1)[1].split("</code>", 1)[0]
    assert reference and reference != "no-disponible"
    lines = [
        r.getMessage() for r in caplog.records if "web_business_error" in r.getMessage()
    ]
    assert lines == [
        f"web_business_error correlation={reference} status=403 code=- endpoint=public.live"
    ]
    # El mensaje mostrado al usuario no se copia al log.
    assert "permiso" not in lines[0]
