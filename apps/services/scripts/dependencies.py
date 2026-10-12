"""Localización y validación de binarios; no instala ni toca datos."""

import os
import re
import shutil
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
MONGO_VERSION = "8.0.17"
MONGO_SHA256 = {
    "x86_64": "daca542b413f4322cef3199bdceed9c06e0b9999a246f6d72c42afb463349805",
    "arm64": "e1ec5131b8d65f06d3a1a9f1a4bfe6f08a7d2f9c876436d33ab483d2e26840cb",
}


def pg_major(directory):
    version = Path(directory) / "pg/PG_VERSION"
    return version.read_text().strip() if version.exists() else "14"


def resolve_binary(name, directory, saved=None, explicit=None):
    """Conservar el major de PostgreSQL y la serie MongoDB de este entorno."""
    override = explicit or os.environ.get(
        {
            "mongod": "REDHOUSE_MONGOD",
            "redis-server": "REDHOUSE_REDIS",
            "postgres": "REDHOUSE_POSTGRES",
            "initdb": "REDHOUSE_INITDB",
        }[name]
    )
    candidates = [override] if override else [saved, shutil.which(name)]
    if not override:
        if name == "mongod":
            candidates.append(
                str(REPO / f".local/tools/mongodb-{MONGO_VERSION}/bin/mongod")
            )
        for prefix in ("/opt/homebrew", "/usr/local", "/home/linuxbrew/.linuxbrew"):
            package = {
                "postgres": "postgresql@" + pg_major(directory),
                "initdb": "postgresql@" + pg_major(directory),
                "mongod": "mongodb-community@8.0",
                "redis-server": "redis",
            }[name]
            candidates.append(f"{prefix}/opt/{package}/bin/{name}")
        if name in ("postgres", "initdb"):
            candidates.append(f"/usr/lib/postgresql/{pg_major(directory)}/bin/{name}")
    for candidate in dict.fromkeys(candidates):
        if (
            not candidate
            or not Path(candidate).is_file()
            or not os.access(candidate, os.X_OK)
        ):
            continue
        try:
            result = subprocess.run(
                [candidate, "--version"], capture_output=True, text=True, timeout=10
            )
        except (OSError, subprocess.TimeoutExpired):
            continue
        if result.returncode:
            continue
        output = result.stdout + result.stderr
        pattern = {
            "postgres": r"PostgreSQL\) (\d+)\.",
            "initdb": r"PostgreSQL\) (\d+)\.",
            "mongod": r"db version v(\d+\.\d+)\.",
            "redis-server": r"v=(\d+)\.",
        }[name]
        match = re.search(pattern, output)
        if not match:
            continue
        version = match.group(1)
        compatible = (
            version == pg_major(directory)
            if name in ("postgres", "initdb")
            else version == "8.0"
            if name == "mongod"
            else int(version) >= 7
        )
        if compatible:
            return str(Path(candidate).absolute())
    raise RuntimeError(
        f"No se encontró {name} compatible ({'PostgreSQL ' + pg_major(directory) if name in ('postgres', 'initdb') else 'MongoDB 8.0' if name == 'mongod' else 'Redis 7+'}). "
        "Ejecuta bash install.sh para preparar las dependencias."
    )
