"""Comprobación explícita de ClamAV real; el timeout usa un receptor TCP sin respuesta."""

import argparse
import json
import socket
import threading
import time
from pathlib import Path

from flask import Flask
from redhouse.errors import APIError
from redhouse.malware import scan


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=33310)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = {"environment": "real-clamd-official-signatures", "checks": []}
    with socket.create_connection((args.host, args.port), timeout=5) as connection:
        connection.sendall(b"zVERSION\0")
        result["engine"] = connection.recv(1024).decode().strip("\0\n")
    app = Flask(__name__)
    app.config.update(CLAMD_HOST=args.host, CLAMD_PORT=args.port)
    with app.app_context():
        assert scan(b"Synthetic clean file for Red House") == "CLEAN"
        assert (
            scan(
                b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
            )
            == "INFECTED"
        )
        result["checks"] += ["clean real engine", "EICAR rejected with real signatures"]
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            listener.listen()

            def no_reply():
                connection, _ = listener.accept()
                with connection:
                    time.sleep(9)

            thread = threading.Thread(target=no_reply)
            thread.start()
            app.config["CLAMD_PORT"] = listener.getsockname()[1]
            started = time.monotonic()
            try:
                scan(b"Synthetic timeout")
            except APIError as error:
                assert error.code == "scanner_unavailable"
            else:
                raise AssertionError("timeout accepted")
            result["timeout_seconds"] = round(time.monotonic() - started, 3)
            thread.join(10)
        app.config["CLAMD_PORT"] = args.port
        assert scan(b"Recovered real scanner") == "CLEAN"
        result["checks"] += [
            "TCP timeout fails closed (controlled transport)",
            "real engine recovers",
        ]
    result["passed"] = True
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
