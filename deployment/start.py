"""Arranque acotado del Compose: evita iniciar todos los intérpretes a la vez."""

import argparse
import json
import os
import subprocess
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
    "monitoreo",
)


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
        subprocess.run(
            compose + ["up", "-d", "--wait", *group],
            env=environment,
            cwd=ROOT,
            check=True,
        )


if __name__ == "__main__":
    main()
