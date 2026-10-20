"""Backend modular del monolito, compartido con las entregas independientes.

El adaptador WSGI invoca los mismos controladores, reglas, transacciones y
autorizaciones sin sockets HTTP. No cambia de backend después de una escritura.
Cada módulo mantiene su conexión con privilegios limitados. No usa test_client.
"""

import importlib
import json
from pathlib import Path

from requests import Response
from werkzeug.test import EnvironBuilder
from werkzeug.wrappers import Response as WSGIResponse

from .config import SERVICES

APPLICATION_VERSION = "0.3.0"


class ApplicationKernel:
    def __init__(self, configs):
        if isinstance(configs, (str, Path)):
            configs = {
                name: json.loads((Path(configs) / (name + ".json")).read_text())
                for name in SERVICES
            }
        if set(configs) != set(SERVICES):
            raise ValueError(
                "El backend autónomo requiere todos sus módulos configurados."
            )
        self.apps = {}
        for name in SERVICES:
            module = "servicio_monitoreo" if name == "monitoreo" else "ms_" + name
            config = dict(configs[name], LOCAL_DISPATCH=self.request)
            self.apps[name] = importlib.import_module(module).create_app(config)

    def request(self, service, method, path, *, data=None, headers=None):
        if service not in self.apps or not path.startswith(
            ("/api/v1/", "/internal/v1/", "/health/")
        ):
            raise ValueError("Operación interna no registrada.")
        builder = EnvironBuilder(
            path=path,
            method=method,
            data=data,
            headers=headers,
            environ_base={"REMOTE_ADDR": "127.0.0.1", "redhouse.transport": "embedded"},
        )
        try:
            with WSGIResponse.from_app(
                self.apps[service], builder.get_environ()
            ) as result:
                response = Response()
                response.status_code = result.status_code
                response.headers.update(result.headers)
                response._content = result.get_data()
                response._content_consumed = True
                response.url = "embedded://" + service + path
                return response
        finally:
            builder.close()

    def drain(self, limit=100):
        from .events import dispatch

        return {
            name: self._dispatch(app, dispatch, limit)
            for name, app in self.apps.items()
        }

    @staticmethod
    def _dispatch(app, dispatch, limit):
        with app.app_context():
            return dispatch(limit)
