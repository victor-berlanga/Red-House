"""Comprueba la imagen Documentos con almacenes temporales y su entrypoint real.

Uso: REDHOUSE_TEST_MONGOD=/ruta/mongod python tests/check_document_image.py
     --output /ruta/evidencia.json
Requiere Docker disponible y redhouse/documentos:0.4.1 construida previamente.
No utiliza la configuración ni los volúmenes de la instalación habitual.
"""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from uuid import uuid4

import requests
from lxml import etree

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tests.conftest import platform


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--image", default="redhouse/documentos:0.4.1")
    args = parser.parse_args()
    fixture = platform.__wrapped__()
    p = next(fixture)
    name = "redhouse-document-proof-" + uuid4().hex[:10]
    started = False
    result = {
        "date": datetime.now(timezone.utc).isoformat(),
        "image": args.image,
        "scope": "Entrypoint, API y worker reales con almacenes aislados; TESTING=True. No acredita producción ni readiness GCS.",
    }
    try:
        # El listener documental del fixture deja de existir antes del arranque.
        p.servers["documentos"].shutdown()
        p.servers["documentos"].server_close()
        with tempfile.TemporaryDirectory(prefix="rh-doc-image-", dir="/tmp") as folder:
            config = dict(
                p.env.configs["documentos"],
                TESTING=True,
                SERVICE_URLS=p.urls,
                WORKER_REQUIRED=True,
            )
            config_path = Path(folder) / "config.json"
            config_path.write_text(
                json.dumps(config).replace("127.0.0.1", "host.docker.internal")
            )
            # El padre es 0700; el UID 10001 del contenedor necesita leer el mount.
            config_path.chmod(0o644)
            subprocess.run(
                [
                    "docker",
                    "run",
                    "--detach",
                    "--rm",
                    "--name",
                    name,
                    "--publish",
                    "127.0.0.1::8080",
                    "--mount",
                    f"type=bind,source={config_path},target=/run/secrets/config,readonly",
                    args.image,
                ],
                check=True,
                capture_output=True,
                timeout=90,
            )
            started = True
            published = subprocess.check_output(
                ["docker", "port", name, "8080"], text=True
            ).strip()
            base = "http://127.0.0.1:" + published.rsplit(":", 1)[1]
            deadline = time.monotonic() + 90
            while time.monotonic() < deadline:
                try:
                    response = requests.get(base + "/health/live", timeout=3)
                    if response.status_code == 200:
                        break
                except requests.RequestException:
                    pass
                time.sleep(0.5)
            else:
                raise AssertionError("La API de la imagen no inició")
            result["health"] = {}
            for endpoint in ("live", "database", "redis", "worker"):
                while time.monotonic() < deadline:
                    response = requests.get(base + "/health/" + endpoint, timeout=10)
                    if response.status_code == 200:
                        break
                    time.sleep(0.5)
                assert response.status_code == 200, endpoint
                result["health"][endpoint] = response.status_code
            result["authenticated_reads"] = []
            for mime in ("application/json", "application/xml"):
                response = requests.get(
                    base + "/api/v1/export-jobs",
                    headers={
                        "Authorization": "Bearer " + p.tokens["medical2"],
                        "Accept": mime,
                    },
                    timeout=15,
                )
                assert response.status_code == 200, mime
                if mime.endswith("json"):
                    assert response.json()["meta"]["version"] == "0.4.1"
                else:
                    assert etree.fromstring(response.content).tag
                result["authenticated_reads"].append(
                    {"representation": mime, "status": response.status_code}
                )
            with p.owner("documentos") as conn:
                row = conn.execute(
                    "SELECT last_success,last_error FROM worker_health WHERE id=1"
                ).fetchone()
                assert row and row[0] and not row[1]
                result["worker_last_success"] = row[0].isoformat()
            inspect = json.loads(
                subprocess.check_output(["docker", "inspect", name], text=True)
            )[0]
            result["image_id"] = inspect["Image"]
            result["entrypoint"] = inspect["Config"]["Entrypoint"]
            assert result["entrypoint"] == [
                "python",
                "/app/deployment/container.py",
                "documentos",
            ]
            result["fixture_document_api_stopped"] = True
            result["passed"] = True
    finally:
        if started:
            subprocess.run(
                ["docker", "stop", "--time", "20", name],
                capture_output=True,
                timeout=40,
            )
        fixture.close()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(
        "Imagen Documentos: API autenticada JSON/XML y worker con PostgreSQL/Redis reales aprobados."
    )


if __name__ == "__main__":
    main()
