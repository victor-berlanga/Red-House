"""Añade ClamAV privado a una instalación GCP existente; conserva sus overrides."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile

IMAGE = "clamav/clamav@sha256:982e28f90061d0e66eb03276419f589a47c9fa601e985e472fc2f6c64b497ca0"
READINESS_SOURCE = Path(__file__).with_name("clamav_readiness.sh")


def configure(directory):
    directory = directory.resolve()
    path = directory / "gcs.compose.yaml"
    override = json.loads(path.read_text())
    config_path = directory / "apps/documentos.json"
    config = json.loads(config_path.read_text())
    config.update(CLAMD_HOST="clamav", CLAMD_PORT=3310)
    config.setdefault("CLAMD_VERSION_TIMEZONE", "UTC")
    config.setdefault("CLAMD_SIGNATURE_MAX_AGE_SECONDS", 172800)
    helper = directory / "clamav-readiness.sh"
    helper_bytes = READINESS_SOURCE.read_bytes()
    with tempfile.NamedTemporaryFile(dir=directory, delete=False) as temporary:
        temporary_path = Path(temporary.name)
        try:
            temporary.write(helper_bytes)
            temporary.flush()
            os.fchmod(temporary.fileno(), 0o444)
            os.replace(temporary_path, helper)
        finally:
            temporary_path.unlink(missing_ok=True)
    services = override.setdefault("services", {})
    services["clamav"] = {
        "image": IMAGE,
        "labels": {
            "org.redhouse.clamav-readiness.sha256": hashlib.sha256(
                helper_bytes
            ).hexdigest()
        },
        "environment": {
            "TZ": "UTC",
            "FRESHCLAM_CHECKS": "12",
            "CLAMD_CONF_ConcurrentDatabaseReload": "no",
            "CLAMD_SIGNATURE_MAX_AGE_SECONDS": str(
                config["CLAMD_SIGNATURE_MAX_AGE_SECONDS"]
            ),
        },
        "networks": ["data", "edge"],
        "volumes": [
            "clamav-signatures:/var/lib/clamav",
            {
                "type": "bind",
                "source": "${REDHOUSE_COMPOSE_DIR:-./.local/compose}/clamav-readiness.sh",
                "target": "/opt/redhouse/clamav-readiness.sh",
                "read_only": True,
            },
        ],
        "restart": "unless-stopped",
        "security_opt": ["no-new-privileges:true"],
        "mem_limit": "2g",
        "healthcheck": {
            "test": ["CMD", "/bin/sh", "/opt/redhouse/clamav-readiness.sh"],
            "interval": "30s",
            "timeout": "15s",
            "start_period": "240s",
            "retries": 3,
        },
    }
    override.setdefault("volumes", {})["clamav-signatures"] = {}
    for name in ("documentos-a", "documentos-b", "web"):
        services.setdefault(name, {}).setdefault("depends_on", {})["clamav"] = {
            "condition": "service_healthy"
        }
    path.write_text(json.dumps(override, indent=2) + "\n")
    config_path.write_text(json.dumps(config, indent=2) + "\n")
    print("ClamAV configurado en red Docker privada, sin puertos publicados.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=Path(".local/compose"))
    configure(parser.parse_args().directory)
