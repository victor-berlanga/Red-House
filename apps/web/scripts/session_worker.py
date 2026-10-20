"""Reintenta revocaciones remotas; nunca restaura cookies ni sesiones del navegador."""

import argparse
import logging
import signal
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "services"))
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
    kernel = app.extensions.get("application_kernel")
    polls = {}
    next_revocation = 0
    pool = ThreadPoolExecutor(max_workers=11)

    def cycle(name, module):
        from worker import step

        polls[name], _ = step(module, polls.get(name, 0))

    while not stopped.is_set():
        try:
            if time.monotonic() >= next_revocation:
                with app.app_context():
                    retry_revocations()
                next_revocation = time.monotonic() + 30
            if kernel:
                jobs = [
                    pool.submit(cycle, name, module)
                    for name, module in kernel.apps.items()
                ]
                for job in jobs:
                    job.result()
            if app.config.get("WORKER_HEARTBEAT_FILE"):
                Path(app.config["WORKER_HEARTBEAT_FILE"]).touch()
        except Exception as exc:
            logging.error("session_revocation_failure type=%s", type(exc).__name__)
        stopped.wait(2 if kernel else 30)
    pool.shutdown(wait=True)


if __name__ == "__main__":
    main()
