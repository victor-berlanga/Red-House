"""Arranque acotado del Compose: evita iniciar todos los intérpretes a la vez."""

import argparse
import json
import os
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
START_ORDER = (
    "auditoria",
    "alertas",
    "custodia",
    "identidad-acceso",
    "donantes",
    "receptores",
    "compatibilidad",
    "priorizacion-geografia",
    "inventario",
    "transporte",
    "documentos",
    "monitoreo",
)


def scanner_health(compose, environment):
    container = subprocess.run(
        compose + ["ps", "-q", "clamav"],
        env=environment,
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    if not container:
        return "missing"
    return subprocess.run(
        ["docker", "inspect", "-f", "{{.State.Health.Status}}", container],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def ensure_scanner(compose, environment, timeout=480):
    """Deja ClamAV sano antes de Documentos.

    Al encender la VM después de horas apagada, FreshClam descarga firmas nuevas
    mientras ClamD carga las anteriores. FreshClam no puede avisar a ClamD porque
    su socket aún no existe, y el healthcheck queda en «version mismatch» hasta la
    siguiente actualización publicada (horas). Pedimos a ClamD que recargue las
    firmas del disco; el healthcheck sigue decidiendo si el escáner está vigente.
    """
    configured = subprocess.run(
        compose + ["config", "--services"],
        env=environment,
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    if "clamav" not in configured:
        return
    subprocess.run(compose + ["up", "-d", "clamav"], env=environment, cwd=ROOT, check=True)
    deadline = time.monotonic() + timeout
    reloaded_at = None
    while time.monotonic() < deadline:
        status = scanner_health(compose, environment)
        if status == "healthy":
            return
        if status == "unhealthy" and (
            reloaded_at is None or time.monotonic() - reloaded_at > 180
        ):
            subprocess.run(
                compose
                + [
                    "exec",
                    "-T",
                    "clamav",
                    "sh",
                    "-c",
                    "printf 'RELOAD\\n' | nc -w 5 localhost 3310",
                ],
                env=environment,
                cwd=ROOT,
                check=False,
            )
            reloaded_at = time.monotonic()
        time.sleep(10)
    raise RuntimeError("ClamAV no quedó sano; Documentos no se inicia sin escáner vigente.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", type=Path, default=ROOT / ".local/compose")
    args = parser.parse_args()
    directory = args.directory.resolve()
    if not (directory / "installation.json").exists():
        raise RuntimeError("Ejecuta prepare.py y bootstrap antes del arranque.")
    compose = ["docker", "compose", "-f", str(ROOT / "compose.yaml")]
    for name in ("gcs.compose.yaml", "public.compose.yaml"):
        if (directory / name).exists():
            compose += ["-f", str(directory / name)]
    environment = dict(os.environ, REDHOUSE_COMPOSE_DIR=str(directory))
    services = json.loads((ROOT / "compose.yaml").read_text())["services"]
    groups = [["postgres", "redis", "mongodb"], ["gateway"]]
    assert {name + "-a" for name in START_ORDER} == {
        name for name in services if name.endswith("-a")
    }
    # Start event sinks before producers so old outbox entries can drain during
    # recovery, without requiring all authorities to cold-start simultaneously.
    groups += [[name + "-a", name + "-b"] for name in START_ORDER]
    groups += [["web"]]
    for group in groups:
        if group == ["documentos-a", "documentos-b"]:
            ensure_scanner(compose, environment)
        subprocess.run(
            compose + ["up", "-d", "--wait", *group],
            env=environment,
            cwd=ROOT,
            check=True,
        )


if __name__ == "__main__":
    main()
