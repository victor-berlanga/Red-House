"""Prueba real del adaptador de firma con ADC local o identidad adjunta a una VM."""

import hashlib
import json
import sys
from pathlib import Path
from uuid import uuid4

import requests
from flask import Flask

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "apps/services"))
from redhouse.storage import bucket, signed_url


def main():
    app = Flask(__name__)
    app.config.update(
        GCS_PROJECT="sistemas-integracion-01",
        GCS_BUCKET="red-house-evidencias-sistemas-integracion-01",
    )
    payload = b"Red House: comprobacion ficticia de despliegue.\n"
    with app.app_context():
        blob = bucket().blob("_deployment-checks/" + uuid4().hex + ".txt")
        uploaded = False
        try:
            response = requests.put(
                signed_url(blob, "PUT", "text/plain"),
                data=payload,
                headers={
                    "Content-Type": "text/plain",
                    "x-goog-if-generation-match": "0",
                },
                timeout=10,
            )
            assert response.status_code == 200, ("upload", response.status_code)
            uploaded = True
            downloaded = requests.get(signed_url(blob, "GET"), timeout=10)
            assert downloaded.status_code == 200 and downloaded.content == payload
            anonymous = requests.get(blob.public_url, timeout=10)
            assert anonymous.status_code in (401, 403)
            credential_type = type(app.extensions["gcs_client"]._credentials).__module__
            result = {
                "result": "passed",
                "credential_type": credential_type,
                "signed_upload": 200,
                "signed_download": 200,
                "anonymous_status": anonymous.status_code,
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        finally:
            if uploaded:
                blob.delete(timeout=(1, 2), retry=None)
        result["temporary_object_deleted"] = True
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
