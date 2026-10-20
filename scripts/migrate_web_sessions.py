"""Actualizar sesiones del portal a Redis/PostgreSQL, sin cambiar datos del dominio.

Ejecutar con el portal detenido. Las cookies anteriores dejan de ser válidas.
Los archivos privados anteriores se conservan como respaldo, sin leerlos al operar.
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps/services"))
from scripts.local import Environment, pid_matches
from scripts.web_sessions import upgrade_local


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=ROOT / ".local/runtime")
    args = parser.parse_args()
    directory = args.directory.resolve()
    state = json.loads((directory / "state.json").read_text())
    if Path(state["directory"]).resolve() != directory:
        raise RuntimeError("El directorio no corresponde al entorno registrado.")
    if state.get("database_layout") != "shared-v6":
        raise RuntimeError("Esta actualización requiere primero la base compartida v6.")
    for pid in state.get("web_pids", {}).values():
        if pid and pid_matches(pid, directory):
            raise RuntimeError("Detén el portal antes de actualizar sus sesiones.")
    env = Environment(directory)
    env.state = state
    try:
        env.ensure_infrastructure()
        upgrade_local(directory, env.state)
        print(
            "Sesiones Redis, cola PostgreSQL y permisos limitados preparados. Inicia sesión nuevamente."
        )
    finally:
        # Únicamente procesos iniciados por esta ejecución; conservar almacenes ya activos.
        env.stop()


if __name__ == "__main__":
    main()
