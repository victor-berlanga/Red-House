"""Genera secretos de una instalación Docker nueva sin tocar el entorno local."""

import argparse
import json
import os
import secrets
from pathlib import Path


def prepare(directory):
    directory.mkdir(parents=True, mode=0o700, exist_ok=True)
    os.chmod(directory, 0o700)
    marker = directory / "installation.json"
    if marker.exists():
        print("Configuración existente conservada:", directory)
        return
    if any(directory.iterdir()):
        raise RuntimeError(
            "Directorio no vacío sin marcador: revisar antes de continuar."
        )
    (directory / "apps").mkdir(mode=0o700)
    passwords = {
        name: secrets.token_urlsafe(32) for name in ("postgres", "redis", "mongo")
    }
    for name, password in passwords.items():
        (directory / (name + "-password")).write_text(password)
    (directory / "redis.acl").write_text(
        f"user default on >{passwords['redis']} ~* &* +@all\n"
    )
    (directory / "redis.conf").write_text(
        "bind 0.0.0.0\nprotected-mode yes\nport 6379\n"
        "aclfile /data/users.acl\ndir /data\nappendonly yes\n"
        "appendfsync always\nmaxmemory-policy noeviction\n"
    )
    marker.write_text(json.dumps({"schema": 1, "purpose": "isolated-compose"}) + "\n")
    print("Secretos creados fuera de imágenes/Git:", directory)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=Path(".local/compose"))
    prepare(parser.parse_args().directory.resolve())
