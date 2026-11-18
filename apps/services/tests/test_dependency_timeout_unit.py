"""Fallas de una dependencia interna: tiempo agotado y respuestas inválidas.

Sin laboratorio: cada caso levanta un servidor HTTP real en 127.0.0.1 que simula la
dependencia (no responde, responde HTML, JSON sin envoltura o se cierra) y comprueba que
`redhouse.client.call` lo convierte en un 503 `dependency_unavailable` controlado, sin
propagar la excepción ni esperar más que el límite configurado (conexión 1 s, lectura 3 s).
"""

import json
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
from flask import Flask

from redhouse.client import call
from redhouse.errors import APIError

READ_TIMEOUT = 3


def private_pem():
    return (
        ed25519.Ed25519PrivateKey.generate()
        .private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
        .decode()
    )


def serve(behaviour):
    release = threading.Event()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            behaviour(self, release)

        do_POST = do_GET

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, release


def reply(handler, status, body, content_type="application/json"):
    payload = body.encode()
    handler.send_response(status)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(payload)))
    handler.end_headers()
    handler.wfile.write(payload)


def app_for(url):
    app = Flask(__name__)
    app.config.update(
        SERVICE="donantes",
        SERVICE_PRIVATE_KEY=private_pem(),
        SERVICE_URLS={"alertas": url},
    )
    return app


def invoke(url):
    app = app_for(url)
    with app.test_request_context("/"):
        started = time.monotonic()
        with pytest.raises(APIError) as caught:
            call("alertas", "GET", "/internal/v1/probe")
        return caught.value, time.monotonic() - started


def assert_dependency_unavailable(error):
    assert error.status == 503
    assert error.code == "dependency_unavailable"


def test_read_timeout_is_bounded_and_controlled():
    def hang(handler, release):
        release.wait(READ_TIMEOUT + 5)

    server, release = serve(hang)
    try:
        error, elapsed = invoke(f"http://127.0.0.1:{server.server_port}")
    finally:
        release.set()
        server.shutdown()
    assert_dependency_unavailable(error)
    # Respeta el límite de lectura: ni responde antes de tiempo ni se queda colgado.
    assert READ_TIMEOUT - 0.5 <= elapsed < READ_TIMEOUT + 2, elapsed


def test_connection_refused_is_controlled():
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    error, elapsed = invoke(f"http://127.0.0.1:{port}")
    assert_dependency_unavailable(error)
    assert elapsed < 2, elapsed


@pytest.mark.parametrize(
    "status,body,content_type",
    [
        (200, "<html>proxy</html>", "text/html"),
        (502, "<html>Bad Gateway</html>", "text/html"),
        (200, json.dumps([1, 2, 3]), "application/json"),
        (200, json.dumps({"data": {"ok": True}}), "application/json"),
        (200, json.dumps({"meta": {}}), "application/json"),
        (200, '{"meta": {}, "data": ', "application/json"),
    ],
    ids=["html", "html-502", "lista", "sin-meta", "sin-data", "truncado"],
)
def test_invalid_response_is_controlled(status, body, content_type):
    server, _ = serve(lambda handler, release: reply(handler, status, body, content_type))
    try:
        error, _ = invoke(f"http://127.0.0.1:{server.server_port}")
    finally:
        server.shutdown()
    assert_dependency_unavailable(error)


def test_connection_closed_without_response_is_controlled():
    def close(handler, release):
        handler.connection.shutdown(socket.SHUT_RDWR)
        handler.close_connection = True

    server, _ = serve(close)
    try:
        error, _ = invoke(f"http://127.0.0.1:{server.server_port}")
    finally:
        server.shutdown()
    assert_dependency_unavailable(error)


def test_dependency_error_keeps_its_code():
    # Contraste: un error válido de la dependencia no se disfraza de indisponibilidad.
    envelope = {"meta": {}, "error": {"code": "conflict", "message": "Versión distinta."}}
    server, _ = serve(lambda handler, release: reply(handler, 409, json.dumps(envelope)))
    try:
        error, _ = invoke(f"http://127.0.0.1:{server.server_port}")
    finally:
        server.shutdown()
    assert error.status == 409 and error.code == "conflict"


def test_valid_response_returns_data():
    envelope = {"meta": {"request_id": "x"}, "data": {"ok": True}}
    server, _ = serve(lambda handler, release: reply(handler, 200, json.dumps(envelope)))
    try:
        app = app_for(f"http://127.0.0.1:{server.server_port}")
        with app.test_request_context("/"):
            assert call("alertas", "GET", "/internal/v1/probe") == {"ok": True}
    finally:
        server.shutdown()
