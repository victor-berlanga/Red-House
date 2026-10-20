"""Readiness de cada instancia: HTTP y latido de su propio proceso worker."""

import os
import socket
import sys
import time

is_web = len(sys.argv) > 1 and sys.argv[1] == "web"
path = "/tmp/web-worker-heartbeat" if is_web else "/tmp/worker-heartbeat"
try:
    age = time.time() - os.stat(path).st_mtime
except FileNotFoundError:
    raise SystemExit(1)
if age > 60:
    raise SystemExit(1)
# Pure standard-library startup with python -S. HEAD executes the same Flask
# health handler; there is no TLS/auth on this loopback-only probe.
endpoint = "/health/" + ("live" if is_web else "ready")
with socket.create_connection(("127.0.0.1", 8080), timeout=1) as connection:
    connection.settimeout(3)
    connection.sendall(
        (
            "HEAD "
            + endpoint
            + " HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n"
        ).encode()
    )
    line = b""
    while b"\r\n" not in line and len(line) < 512:
        received = connection.recv(512 - len(line))
        if not received:
            break
        line += received
    status = line.split(b"\r\n", 1)[0].split()
    if len(status) < 2 or status[1] != b"200":
        raise SystemExit(1)
