"""Entrada independiente del portal integrado; configuración de cliente sin claves de MS."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "services"))
from src import create_app
from waitress import serve
from redhouse.proxy import waitress_proxy_options


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
        # Solo el gateway configurado puede declarar dirección y protocolo.
        url_scheme=app.config.get("PREFERRED_URL_SCHEME", "http"),
        threads=8,
        max_request_body_size=11 * 1024 * 1024,
        **waitress_proxy_options(app.config),
    )


if __name__ == "__main__":
    main()
