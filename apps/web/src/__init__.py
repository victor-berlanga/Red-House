"""Portal Flask/Jinja con backend modular propio o transporte HTTP explícito."""

from flask import Flask
import json
from pathlib import Path
from .config.settings import settings


def create_app(overrides=None):
    app = Flask(
        __name__,
        template_folder="presentation/templates",
        static_folder="presentation/static",
    )
    app.config.update(settings())
    app.config.update(overrides or {})
    # Load mounted secrets before validating them; the file is the complete
    # runtime configuration in Docker, where no repository .env is present.
    config = app.config.get("MICROSERVICES_CONFIG")
    if isinstance(config, (str, Path)):
        config = json.loads(Path(config).read_text())
    if not isinstance(config, dict):
        raise RuntimeError("MICROSERVICES_CONFIG debe apuntar a configuración privada del cliente web.")
    app.config.update(config)
    app.config["MICROSERVICES_CONFIG"] = config
    for key in ("SECRET_KEY", "JWT_SECRET_KEY"):
        value = app.config.get(key)
        if not isinstance(value, str) or len(value) < 32:
            raise RuntimeError(
                f"Configura {key} con al menos 32 caracteres aleatorios en el entorno local."
            )
    if app.config["SECRET_KEY"] == app.config["JWT_SECRET_KEY"]:
        raise RuntimeError("SECRET_KEY y JWT_SECRET_KEY deben ser diferentes.")
    if app.config["BACKEND_MODE"] not in ("microservices", "monolith"):
        raise RuntimeError(
            "BACKEND_MODE debe ser monolith o microservices."
        )
    from .integration import configure

    return configure(app)
