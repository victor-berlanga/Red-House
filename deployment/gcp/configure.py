"""Configura GCS con identidad adjunta a la VM, sin ADC personal ni claves JSON."""

import argparse
import json
from pathlib import Path


def configure(directory, project, bucket):
    directory = directory.resolve()
    path = directory / "apps/transporte.json"
    config = json.loads(path.read_text())
    config.update(GCS_BUCKET=bucket, GCS_PROJECT=project)
    path.write_text(json.dumps(config, indent=2) + "\n")
    override = {
        "services": {
            name: {"environment": {"GOOGLE_CLOUD_PROJECT": project}}
            for name in ("web", "transporte-a", "transporte-b")
        }
    }
    (directory / "gcs.compose.yaml").write_text(json.dumps(override, indent=2) + "\n")
    print("GCS configurado mediante identidad de Compute Engine.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", type=Path, default=Path(".local/compose"))
    parser.add_argument("--project", default="sistemas-integracion-01")
    parser.add_argument(
        "--bucket", default="red-house-evidencias-sistemas-integracion-01"
    )
    args = parser.parse_args()
    configure(args.directory, args.project, args.bucket)
