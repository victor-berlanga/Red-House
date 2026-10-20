"""Comprobar HTTP y GCS real en la VM, usando datos ficticios y evidencia redactada."""

import argparse
import hashlib
import json
import sys
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "deployment"))
from verify import Deployment, helpers


class CloudDeployment(Deployment):
    def form(self, session, path):
        values = super().form(session, path)
        # Un navegador envía Referer; Flask-WTF lo exige cuando hay HTTPS.
        session.headers["Referer"] = self.web_url + path
        return values


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--origin")
    args = parser.parse_args()
    metadata = ROOT / ".local/compose/public.json"
    origin = args.origin or (
        json.loads(metadata.read_text())["origin"] if metadata.exists() else None
    )
    output = ROOT / (
        "documentation/evidencias/gcp/public/http"
        if origin
        else "documentation/evidencias/gcp/http"
    )
    p = CloudDeployment(ROOT / ".local/compose", output)
    if origin:
        p.web_url = origin.rstrip("/")
        p.urls = {
            name: p.web_url + "/services/" + name.replace("_", "-") for name in p.urls
        }
    helpers.route = lambda _: p.route()
    try:
        p.phase("gcp_baseline")
        p.login()
        p.flow()
        p.business_reads()
        p.checks.append(
            {"check": "sangre_y_once_servicios_json_xml", "status": "passed"}
        )
        if origin:
            p.phase("gcp_public_web_flow")
            p.web_flow("BLOOD", "RBC")
            # El helper también se usa para ensayos de caída, pero esta prueba
            # mantiene las API encendidas y no acredita una caída nueva.
            p.checks[-1]["check"] = "sangre_web_https"
            p.checks[-1]["apis_running"] = True
        p.phase("gcp_web_files")
        unit = helpers.resource(p)
        _, req = helpers.recipient_request(p)
        ev = helpers.evaluation(p, req, [unit])
        shipment = helpers.plan(p, helpers.reservation(p, ev, unit)["reservation"])
        client = p.web_login("operator1")
        page = "/traslados/" + shipment["id"] + "/archivos"
        content = BytesIO()
        Image.new("RGB", (4, 4), color="red").save(content, format="PNG")
        payload = content.getvalue()
        response = client.post(
            p.web_url + page,
            data=p.form(client, page),
            files={"evidence": ("evidencia-gcp-ficticia.png", payload, "image/png")},
            allow_redirects=False,
            timeout=15,
        )
        assert response.status_code == 303, ("upload", response.status_code)
        rows = p.ok(
            "transporte",
            "GET",
            "/api/v1/shipments/" + shipment["id"] + "/files",
            user="operator1",
        )["items"]
        row = rows[0]
        assert row["status"] == "VERIFIED"
        assert row["sha256"] == hashlib.sha256(payload).hexdigest()
        response = client.get(
            p.web_url + "/archivos/" + row["id"] + "/descargar",
            allow_redirects=False,
            timeout=8,
        )
        assert response.status_code == 303
        downloaded = requests.get(response.headers["Location"], timeout=10)
        assert downloaded.status_code == 200 and downloaded.content == payload
        anonymous = requests.get(
            "https://storage.googleapis.com/red-house-evidencias-sistemas-integracion-01/"
            + row["object_path"],
            timeout=10,
        )
        assert anonymous.status_code in (401, 403)
        assert (
            p.request(
                "transporte",
                "GET",
                "/api/v1/files/" + row["id"] + "/download",
                user="transport2",
            ).status_code
            == 403
        )
        p.checks.append(
            {
                "check": "gcs_web_identidad_vm",
                "status": "passed",
                "file_id": row["id"],
                "shipment_id": shipment["id"],
                "sha256": row["sha256"],
                "anonymous_status": anonymous.status_code,
                "download_hash_matches": True,
            }
        )
        p.result = "passed"
    except Exception:
        p.result = "failed"
        raise
    finally:
        p.save()
    print(json.dumps({"result": p.result, "checks": p.checks}, indent=2))


if __name__ == "__main__":
    main()
