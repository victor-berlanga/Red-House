"""Configura explícitamente Documentos para un directorio local privado persistente."""

import argparse
import json
import os
import stat
import tempfile
from pathlib import Path
from urllib.parse import urlsplit


def configure(config_path, directory, origin):
    config_path = Path(config_path)
    directory = Path(directory)
    parsed = urlsplit(origin)
    if (
        not directory.is_absolute()
        or parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.path not in ("", "/")
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError(
            "Se requiere directorio absoluto y origen HTTPS sin ruta ni credenciales."
        )
    if directory.is_symlink():
        raise ValueError("El directorio no puede ser enlace simbólico.")
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    info = directory.stat()
    if (
        not stat.S_ISDIR(info.st_mode)
        or info.st_uid != os.geteuid()
        or stat.S_IMODE(info.st_mode) & 0o077
    ):
        raise ValueError(
            "El directorio debe pertenecer al usuario y ser privado (0700)."
        )
    info = config_path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid():
        raise ValueError("La configuración debe ser archivo regular propio.")
    config = json.loads(config_path.read_text())
    config.update(
        STORAGE_PROVIDER="local",
        STORAGE_LOCAL_ROOT=str(directory),
        STORAGE_PUBLIC_BASE_URL=origin.rstrip("/"),
    )
    fd, name = tempfile.mkstemp(prefix=".storage-config-", dir=config_path.parent)
    try:
        os.fchmod(fd, stat.S_IMODE(info.st_mode))
        with os.fdopen(fd, "w") as output:
            json.dump(config, output, ensure_ascii=False, indent=2)
            output.write("\n")
            output.flush()
            os.fsync(output.fileno())
        os.replace(name, config_path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, help="JSON privado de Documentos")
    parser.add_argument(
        "--directory", required=True, help="Directorio absoluto persistente privado"
    )
    parser.add_argument(
        "--origin", required=True, help="Origen público HTTPS, sin ruta"
    )
    args = parser.parse_args()
    configure(args.config, args.directory, args.origin)
    print(
        "Proveedor local configurado; reinicie web, Documentos y worker. GCS histórico se conserva."
    )


if __name__ == "__main__":
    main()
