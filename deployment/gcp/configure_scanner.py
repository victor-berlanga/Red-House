"""Añade ClamAV privado a una instalación GCP existente; conserva sus overrides."""

import argparse
import json
from pathlib import Path

IMAGE = "clamav/clamav@sha256:982e28f90061d0e66eb03276419f589a47c9fa601e985e472fc2f6c64b497ca0"


def configure(directory):
    directory = directory.resolve()
    path = directory / "gcs.compose.yaml"
    override = json.loads(path.read_text())
    services = override.setdefault("services", {})
    services["clamav"] = {
        "image": IMAGE,
        "environment": {"TZ": "UTC"},
        "networks": ["data", "edge"],
        "volumes": ["clamav-signatures:/var/lib/clamav"],
        "restart": "unless-stopped",
        "security_opt": ["no-new-privileges:true"],
        "mem_limit": "2g",
        "healthcheck": {
            "test": ["CMD", "clamdcheck.sh"],
            "interval": "15s",
            "timeout": "10s",
            "start_period": "240s",
            "retries": 20,
        },
    }
    override.setdefault("volumes", {})["clamav-signatures"] = {}
    for name in ("documentos-a", "documentos-b", "web"):
        services.setdefault(name, {}).setdefault("depends_on", {})["clamav"] = {
            "condition": "service_healthy"
        }
    path.write_text(json.dumps(override, indent=2) + "\n")
    config_path = directory / "apps/documentos.json"
    config = json.loads(config_path.read_text())
    config.update(CLAMD_HOST="clamav", CLAMD_PORT=3310)
    config.setdefault("CLAMD_VERSION_TIMEZONE", "UTC")
    config.setdefault("CLAMD_SIGNATURE_MAX_AGE_SECONDS", 172800)
    config_path.write_text(json.dumps(config, indent=2) + "\n")
    print("ClamAV configurado en red Docker privada, sin puertos publicados.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=Path(".local/compose"))
    configure(parser.parse_args().directory)
