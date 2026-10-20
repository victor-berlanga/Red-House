"""Entrada independiente del portal integrado; configuración de cliente sin claves de MS."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "services"))
from src import create_app
from waitress import serve


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--port", type=int, default=5050)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()
    app = create_app(
        {"BACKEND_MODE": "microservices", "MICROSERVICES_CONFIG": args.config}
    )
    serve(
        app,
        host=args.host,
        port=args.port,
        # El despliegue público recibe exclusivamente HTTPS desde Nginx.
        # Configuración explícita: no aceptar cabeceras de proxy del cliente.
        url_scheme=app.config.get("PREFERRED_URL_SCHEME", "http"),
        threads=8,
        max_request_body_size=11 * 1024 * 1024,
    )


if __name__ == "__main__":
    main()
