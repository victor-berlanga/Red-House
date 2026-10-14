"""Portal Flask/Jinja; toda operación de negocio pasa por las API."""

from flask import Flask
from .config.settings import settings


def create_app(overrides=None):
    app = Flask(
        __name__,
        template_folder="presentation/templates",
        static_folder="presentation/static",
    )
    app.config.update(settings())
    app.config.update(overrides or {})
    for key in ("SECRET_KEY", "JWT_SECRET_KEY"):
        value = app.config.get(key)
        if not isinstance(value, str) or len(value) < 32:
            raise RuntimeError(
                f"Configura {key} con al menos 32 caracteres aleatorios en el entorno local."
            )
    if app.config["SECRET_KEY"] == app.config["JWT_SECRET_KEY"]:
        raise RuntimeError("SECRET_KEY y JWT_SECRET_KEY deben ser diferentes.")
    if app.config["BACKEND_MODE"] != "microservices":
        raise RuntimeError(
            "El portal utiliza BACKEND_MODE=microservices. Consulta documentation/markdowns/Instalacion_y_operacion.md."
        )
    from .integration import configure

    return configure(app)
