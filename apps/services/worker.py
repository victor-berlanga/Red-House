"""Proceso separado para outbox, recuperación de operaciones y sondeos."""

import argparse
import json
import logging
import signal
import time
from pathlib import Path

from run import load_app
from redhouse.events import dispatch
from redhouse.db import transaction


def heartbeat(error=None):
    with transaction() as conn:
        conn.execute(
            "INSERT INTO worker_health(id,checked_at,last_success,last_error) "
            "VALUES(1,now(),CASE WHEN %s::text IS NULL THEN now() ELSE NULL END,%s) "
            "ON CONFLICT(id) DO UPDATE SET checked_at=now(), "
            "last_success=coalesce(EXCLUDED.last_success,worker_health.last_success),last_error=EXCLUDED.last_error",
            (error, error),
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("service")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--interval", type=float, default=5)
    args = parser.parse_args()
    app = load_app(args.service, json.loads(args.config.read_text()))
    running = True

    def stop(*_):
        nonlocal running
        running = False

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    next_poll = 0
    while running:
        with app.app_context():
            try:
                if args.service == "inventario":
                    from ms_inventario.routes import recover_operations

                    recover_operations()
                if args.service == "transporte":
                    from ms_transporte.routes import recover_shipments

                    recover_shipments()
                if args.service == "monitoreo" and time.monotonic() >= next_poll:
                    from servicio_monitoreo.routes import poll

                    poll()
                    next_poll = time.monotonic() + 30
                dispatch()
                heartbeat()
            except Exception as exc:
                logging.error(
                    "worker_failure service=%s exception_type=%s",
                    args.service,
                    type(exc).__name__,
                )
                try:
                    heartbeat(type(exc).__name__)
                except Exception:
                    pass  # La ausencia de latido también degrada health/worker.
        if args.once:
            break
        time.sleep(max(0.1, args.interval))


if __name__ == "__main__":
    main()
