"""Conecta ADC impersonada local al entorno Docker; no crea recursos ni cambia IAM."""

import argparse
import json
import os
from pathlib import Path


def configure(directory, adc, bucket, project):
    directory = directory.resolve()
    credentials = json.loads(adc.read_text())
    if credentials.get("type") != "impersonated_service_account":
        raise RuntimeError(
            "Se requiere ADC impersonada, sin clave privada de servicio."
        )
    target = directory / "gcs-adc.json"
    if not target.exists():
        fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w") as stream:
            json.dump(credentials, stream)
        target.chmod(
            0o644
        )  # Host parent is 0700; bind secret must be readable by UID 10001.
    config_path = directory / "apps/transporte.json"
    config = json.loads(config_path.read_text())
    config.update(GCS_BUCKET=bucket, GCS_PROJECT=project)
    config_path.write_text(json.dumps(config, indent=2) + "\n")
    override = {"services": {}, "secrets": {"gcs_adc": {"file": str(target)}}}
    for name in ("web", "transporte-a", "transporte-b"):
        override["services"][name] = {
            "environment": {
                "GOOGLE_APPLICATION_CREDENTIALS": "/run/secrets/gcs_adc",
                "GOOGLE_CLOUD_PROJECT": project,
            },
            "secrets": [{"source": "gcs_adc", "target": "gcs_adc"}],
        }
    path = directory / "gcs.compose.yaml"
    path.write_text(json.dumps(override, indent=2) + "\n")
    print("Configuración privada GCS preparada. Usar -f compose.yaml -f", path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=Path(".local/compose"))
    parser.add_argument("--adc", type=Path, required=True)
    parser.add_argument("--bucket", required=True)
    parser.add_argument("--project", required=True)
    args = parser.parse_args()
    configure(args.directory, args.adc, args.bucket, args.project)
