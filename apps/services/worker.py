"""Proceso separado para outbox, recuperación de operaciones y sondeos."""

import argparse
import json
import logging
import signal
import time
from pathlib import Path

from run import load_app
from redhouse.events import OUTBOX_BATCH_SIZE, dispatch
from redhouse.db import transaction


def heartbeat(error=None):
    with transaction() as conn:
        from flask import current_app

        conn.execute(
            "SELECT pg_advisory_xact_lock(hashtextextended(%s,53))",
            (current_app.config["SERVICE"],),
        )
        if conn.execute("SELECT id FROM worker_health WHERE id=1").fetchone():
            conn.execute(
                "UPDATE worker_health SET checked_at=now(),last_success=CASE WHEN %s::text IS NULL THEN now() ELSE last_success END,last_error=%s WHERE id=1",
                (error, error),
            )
        else:
            conn.execute(
                "INSERT INTO worker_health(id,checked_at,last_success,last_error) VALUES(1,now(),CASE WHEN %s::text IS NULL THEN now() ELSE NULL END,%s)",
                (error, error),
            )


def step(app, next_poll=0):
    """Un ciclo reutilizado por workers de API y del backend web autónomo."""
    with app.app_context():
        service = app.config["SERVICE"]
        if service == "donantes":
            from ms_donantes.agenda import reminders

            reminders()
        if service == "identidad_acceso":
            from ms_identidad_acceso.strong_auth import deliver_pending

            deliver_pending()
        if service == "alertas":
            from ms_alertas.delivery import process

            process()
        if service == "inventario":
            from ms_inventario.routes import recover_operations

            recover_operations()
            from ms_inventario.quality import scan_quality

            scan_quality()
        if service == "transporte":
            from ms_transporte.routes import recover_shipments

            recover_shipments()
        if service == "documentos":
            from ms_documentos.reports import process as exports

            exports()
        if service == "monitoreo" and time.monotonic() >= next_poll:
            from servicio_monitoreo.routes import poll

            poll()
            next_poll = time.monotonic() + 30
        result = dispatch()
        heartbeat()
        return next_poll, result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("service")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--interval", type=float, default=5)
    args = parser.parse_args()
    app = load_app(args.service, json.loads(args.config.read_text()))
    # Solo el proceso worker reutiliza una conexión por defecto. Un valor
    # explícito (incluido 0) conserva el comportamiento configurado.
    app.config.setdefault("DATABASE_POOL_SIZE", 1)
    running = True

    def stop(*_):
        nonlocal running
        running = False

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    next_poll = 0
    interval = max(0.1, args.interval)
    next_work = 0
    try:
        while running:
            result = None
            with app.app_context():
                try:
                    if time.monotonic() >= next_work:
                        next_poll, result = step(app, next_poll)
                        next_work = time.monotonic() + interval
                    else:
                        # Un lote lleno no adelanta recordatorios, recuperación ni sondeos.
                        result = dispatch()
                        heartbeat()
                    if app.config.get("WORKER_HEARTBEAT_FILE"):
                        Path(app.config["WORKER_HEARTBEAT_FILE"]).touch()
                except Exception as exc:
                    result = None
                    next_work = time.monotonic() + interval
                    logging.error(
                        "worker_failure service=%s exception_type=%s",
                        args.service,
                        type(exc).__name__,
                    )
                    try:
                        heartbeat(type(exc).__name__)
                    except Exception:
                        pass  # La ausencia de latido también degrada health/worker.
            if args.once or not running:
                break
            progressing = (
                result is not None
                and result["delivered"] > 0
                and result["delivered"] + result["failed"] >= OUTBOX_BATCH_SIZE
            )
            # Sin progreso o tras un error, conservar la espera ordinaria.
            delay = 0.1 if progressing else interval
            time.sleep(delay)
    finally:
        for pool in app.extensions.get("database_pools", {}).values():
            pool.close()


if __name__ == "__main__":
    main()
