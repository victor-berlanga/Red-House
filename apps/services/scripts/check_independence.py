"""Verifica reinicio selectivo y continuidad de inventario/portal en el entorno propia."""

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    directory = args.directory.resolve()
    before = json.loads((directory / "state.json").read_text())
    if Path(before["directory"]).resolve() != directory:
        raise RuntimeError("Entorno no corresponde.")
    with requests.Session() as http:
        http.trust_env = False
        login = http.post(
            before["urls"]["identidad_acceso"] + "/api/v1/auth/login",
            json={"username": "medical1", "password": before["password"]},
            timeout=10,
        )
        login.raise_for_status()
        token = login.json()["data"]["access_token"]
        process = subprocess.Popen(
            [
                sys.executable,
                str(ROOT / "scripts/local.py"),
                "restart-service",
                "--directory",
                str(directory),
                "--service",
                "donantes",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        observations = []
        until = time.monotonic() + 60
        while process.poll() is None and time.monotonic() < until:
            inventory = http.get(
                before["urls"]["inventario"] + "/api/v1/resources?page_size=1",
                headers={"Authorization": "Bearer " + token},
                timeout=5,
            )
            portal = http.get(before["web_url"] + "/health/live", timeout=5)
            observations.append(
                {"inventory": inventory.status_code, "portal": portal.status_code}
            )
            time.sleep(0.5)
        if process.poll() is None:
            process.terminate()
            raise RuntimeError("Reinicio excedió límite; revisar estado del servicio.")
        if process.returncode:
            raise RuntimeError(
                "Falló reinicio selectivo; consultar estado/log privado."
            )
        after = json.loads((directory / "state.json").read_text())
        preserved = {}
        for group in ("service_pids", "worker_pids", "web_pids"):
            expected = {k: v for k, v in before[group].items() if k != "donantes"}
            assert all(after[group][k] == v for k, v in expected.items()), group
            preserved[group] = len(expected)
        assert after["service_pids"]["donantes"] != before["service_pids"]["donantes"]
        assert after["worker_pids"]["donantes"] != before["worker_pids"]["donantes"]
        assert observations and all(
            r == {"inventory": 200, "portal": 200} for r in observations
        )
        ready = http.get(before["urls"]["donantes"] + "/health/ready", timeout=5)
        assert ready.status_code == 200
        report = {
            "date": datetime.now(timezone.utc).isoformat(),
            "result": "passed",
            "service": "donantes",
            "preserved_processes": preserved,
            "observations": observations,
            "donantes_ready": ready.status_code,
        }
        args.report.write_text(json.dumps(report, indent=2) + "\n")
        print(
            "Reinicio selectivo comprobado; inventario y portal disponibles; demás procesos conservados."
        )


if __name__ == "__main__":
    main()
