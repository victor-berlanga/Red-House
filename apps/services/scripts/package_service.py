"""Construye una entrega independiente con un solo dominio y utilidades comunes."""

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from redhouse.config import SERVICES


def package(service, destination):
    module = "servicio_monitoreo" if service == "monitoreo" else "ms_" + service
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    ignore = shutil.ignore_patterns("__pycache__", ".venv", ".env", "*.pyc")
    for folder in ("redhouse", module):
        shutil.copytree(ROOT / folder, destination / folder, ignore=ignore)
    for name in (
        "run.py",
        "worker.py",
        "requirements.txt",
        "requirements-storage.txt",
        "pyproject.toml",
    ):
        shutil.copy2(ROOT / name, destination / name)
    manifest = {
        str(p.relative_to(destination)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in destination.rglob("*")
        if p.is_file()
    }
    (destination / "MANIFEST.json").write_text(
        json.dumps({"service": service, "files": manifest}, indent=2) + "\n"
    )
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("service", choices=SERVICES)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(package(args.service, args.output))


if __name__ == "__main__":
    main()
