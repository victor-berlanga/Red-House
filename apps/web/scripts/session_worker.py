"""Reintenta revocaciones remotas; nunca restaura cookies ni sesiones del navegador."""

import argparse
import logging
import signal
import sys
from pathlib import Path
from threading import Event

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import create_app
from src.integration.sessions import retry_revocations


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    app = create_app(
        {"BACKEND_MODE": "microservices", "MICROSERVICES_CONFIG": args.config}
    )
    stopped = Event()
    signal.signal(signal.SIGTERM, lambda *_: stopped.set())
    signal.signal(signal.SIGINT, lambda *_: stopped.set())
    while not stopped.is_set():
        try:
            with app.app_context():
                retry_revocations()
        except Exception as exc:
            logging.error("session_revocation_failure type=%s", type(exc).__name__)
        stopped.wait(30)


if __name__ == "__main__":
    main()
