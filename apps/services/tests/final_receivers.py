"""Receptores TCP/HTTP de prueba; no simulan haber enviado correo o push reales."""

import json
import socketserver
import struct
import threading
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


@contextmanager
def smtp_receiver():
    messages = []

    class Handler(socketserver.StreamRequestHandler):
        def handle(self):
            self.wfile.write(b"220 localhost test receiver\r\n")
            while line := self.rfile.readline():
                command = line[:4].upper()
                if command == b"DATA":
                    self.wfile.write(b"354 send data\r\n")
                    payload = b""
                    while (part := self.rfile.readline()) != b".\r\n":
                        if not part:
                            return
                        payload += part
                    messages.append(payload)
                    self.wfile.write(b"250 accepted\r\n")
                elif command == b"QUIT":
                    self.wfile.write(b"221 bye\r\n")
                    break
                else:
                    self.wfile.write(b"250 OK\r\n")

    with socketserver.ThreadingTCPServer(("127.0.0.1", 0), Handler) as server:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield server.server_address[1], messages
        finally:
            server.shutdown()


@contextmanager
def clamd_receiver():
    received = []

    class Handler(socketserver.StreamRequestHandler):
        def handle(self):
            assert self.rfile.read(10) == b"zINSTREAM\0"
            body = b""
            while size := struct.unpack("!I", self.rfile.read(4))[0]:
                body += self.rfile.read(size)
            received.append(body)
            self.wfile.write(
                b"stream: Test-Signature FOUND\0"
                if b"SYNTHETIC_MALWARE" in body
                else b"stream: OK\0"
            )

    with socketserver.ThreadingTCPServer(("127.0.0.1", 0), Handler) as server:
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            yield server.server_address[1], received
        finally:
            server.shutdown()


@contextmanager
def push_receiver():
    received = []
    state = {"fail": False}

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            if not state["fail"]:
                received.append(body)
            self.send_response(503 if state["fail"] else 202)
            self.end_headers()

        def log_message(self, *_):
            pass

    with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            yield f"http://127.0.0.1:{server.server_port}/push", received, state
        finally:
            server.shutdown()
