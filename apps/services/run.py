"""Ejecutar UNA unidad: python run.py inventario --config /ruta/privada.json."""

import sys

# Transporte usa un servidor compatible con Upgrade; los demás conservan Waitress.
if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "transporte":
    from gevent import monkey

    monkey.patch_all()

import argparse
import importlib
import json
import logging
from pathlib import Path

from waitress import serve

from redhouse.config import SERVICES
from redhouse.proxy import waitress_proxy_options


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
    if args.service == "transporte":
        from gevent.pool import Pool
        from gevent.pywsgi import WSGIServer

        tls = {}
        if app.config.get("TRACKING_TLS_CERT"):
            tls = {
                "certfile": app.config["TRACKING_TLS_CERT"],
                "keyfile": app.config["TRACKING_TLS_KEY"],
            }
        WSGIServer(
            (args.host, args.port or app.config["PORT"]),
            app,
            spawn=Pool(96),
            log=None,
            **tls,
        ).serve_forever()
        return
    # Waitress limita cuerpos también; debug y recarga siempre desactivados.
    serve(
        app,
        host=args.host,
        port=args.port or app.config["PORT"],
        threads=8,
        # Documentos acepta binarios; Flask mantiene el límite de metadatos.
        max_request_body_size=10 * 1024 * 1024 if args.service == "documentos" else 262144,
        **waitress_proxy_options(app.config),
    )


if __name__ == "__main__":
    main()
