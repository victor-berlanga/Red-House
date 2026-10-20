"""Supervisor mínimo: API y worker terminan juntos si uno de los procesos falla."""

import signal
import subprocess
import sys
import time


def main():
    service = sys.argv[1]
    if service == "web":
        commands = [
            [
                sys.executable,
                "/app/apps/web/scripts/run_web.py",
                "--config",
                "/run/secrets/config",
                "--host",
                "0.0.0.0",
                "--port",
                "8080",
            ],
            [
                sys.executable,
                "/app/apps/web/scripts/session_worker.py",
                "--config",
                "/run/secrets/config",
            ],
        ]
    else:
        commands = [
            [
                sys.executable,
                "/app/apps/services/run.py",
                service,
                "--config",
                "/run/secrets/config",
                "--host",
                "0.0.0.0",
                "--port",
                "8080",
            ],
            [
                sys.executable,
                "/app/apps/services/worker.py",
                service,
                "--config",
                "/run/secrets/config",
                "--interval",
                "2",
            ],
        ]
    children = [subprocess.Popen(command) for command in commands]
    stopping = False

    def stop(*_):
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        while not stopping and all(child.poll() is None for child in children):
            time.sleep(0.2)
    finally:
        for child in children:
            if child.poll() is None:
                child.terminate()
        deadline = time.monotonic() + 15
        for child in children:
            try:
                child.wait(timeout=max(0.1, deadline - time.monotonic()))
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()
    if not stopping:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
