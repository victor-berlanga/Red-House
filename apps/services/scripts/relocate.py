"""Copia un entorno detenido a almacenamiento persistente; conserva el origen."""

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.local import pid_matches, infrastructure_pid


def relocate(source, destination):
    source, destination = Path(source).resolve(), Path(destination).resolve()
    if destination == source or source in destination.parents or destination.exists():
        raise RuntimeError("Usa un destino nuevo, fuera del directorio de origen.")
    state = json.loads((source / "state.json").read_text())
    if Path(state["directory"]).resolve() != source:
        raise RuntimeError("Entorno no coincide.")
    for group in ("service_pids", "worker_pids", "web_pids"):
        if any(pid_matches(pid, source) for pid in state.get(group, {}).values()):
            raise RuntimeError("Detén el entorno antes de copiarlo.")
    if any(infrastructure_pid(state, name) for name in state["infrastructure_pids"]):
        raise RuntimeError("Detén también las dependencias antes de copiar el entorno.")
    shutil.copytree(
        source,
        destination,
        ignore=shutil.ignore_patterns("*.sock", ".s.PGSQL.*", "postmaster.pid"),
    )
    os.chmod(destination, 0o700)
    # Solo configuración textual del lanzador. Nunca reemplazar bytes de las bases.
    for path in [
        *destination.glob("*.json"),
        destination / "redis.conf",
        destination / "redis.acl",
    ]:
        if path.exists():
            path.write_text(path.read_text().replace(str(source), str(destination)))
            os.chmod(path, 0o600)
    state = json.loads((destination / "state.json").read_text())
    state["service_pids"] = {}
    state["worker_pids"] = {}
    state["web_pids"] = {}
    (destination / "state.json").write_text(json.dumps(state, indent=2))
    print("Entorno copiado a", destination, "; origen conservado.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    relocate(args.source, args.destination)


if __name__ == "__main__":
    main()
