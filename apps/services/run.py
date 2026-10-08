"""Ejecutar UNA unidad: python run.py inventario --config /ruta/privada.json."""

import argparse
import importlib
import json
import logging
from pathlib import Path

from waitress import serve

from redhouse.config import SERVICES


def load_app(service, config=None):
    module = "servicio_monitoreo" if service == "monitoreo" else "ms_" + service
    return importlib.import_module(module).create_app(config)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("service", choices=SERVICES)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int)
    args = parser.parse_args()
    config = json.loads(args.config.read_text()) if args.config else None
    app = load_app(args.service, config)
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    # Waitress limita cuerpos también; debug y recarga siempre desactivados.
    serve(
        app,
        host=args.host,
        port=args.port or app.config["PORT"],
        threads=8,
        max_request_body_size=262144,
    )


if __name__ == "__main__":
    main()
