"""Prueba real del lanzador en un entorno NUEVO; nunca reinicializa la DEMO."""

import argparse
import fcntl
import hashlib
import json
import os
import signal
import socket
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.local import free_port, infrastructure_pid, pid_matches

REPO = ROOT.parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    directory = Path(tempfile.mkdtemp(prefix="rh-launcher-", dir="/tmp")).resolve()
    port = free_port()
    results = []

    def command(*parts, success=True):
        result = subprocess.run(
            [
                "bash",
                str(
                    REPO / ("install.sh" if parts[0] == "preparar" else "components.sh")
                ),
                *(parts[1:] if parts[0] == "preparar" else parts),
                "--directory",
                str(directory),
                "--web-port",
                str(port),
                *(["--no-install"] if parts[0] == "preparar" else []),
            ],
            cwd="/tmp",
            capture_output=True,
            text=True,
            timeout=180,
        )
        assert (result.returncode == 0) == success, result.stdout + result.stderr
        return result

    def state():
        return json.loads((directory / "state.json").read_text())

    def record(name):
        results.append(name)
        print("PASS", name, flush=True)

    def pids(value):
        return {
            key: value.get(key, {})
            for key in (
                "service_pids",
                "worker_pids",
                "web_pids",
                "infrastructure_pids",
            )
        }

    def stable_config():
        # Comparar en memoria; nunca incluir hashes/credenciales en el reporte.
        files = sorted(directory.glob("*.json"))
        payload = []
        for path in files:
            if path.name == "state.json":
                data = json.loads(path.read_text())
                for key in (*pids(data), "web_url"):
                    data.pop(key, None)
                payload.append(json.dumps(data, sort_keys=True).encode())
            else:
                payload.append(path.read_bytes())
        return hashlib.sha256(b"".join(payload)).hexdigest()

    try:
        command("todo", success=False)
        assert not (directory / "state.json").exists()
        record("start_requires_prepared_environment")
        command("preparar")
        assert not state()["service_pids"]
        assert not any(
            infrastructure_pid(state(), name)
            for name in ("postgres", "redis", "mongodb")
        )
        record("installer_prepares_without_leaving_processes_running")
        command("bases")
        assert not state()["service_pids"]
        assert all(
            infrastructure_pid(state(), name)
            for name in ("postgres", "redis", "mongodb")
        )
        record("fresh_environment_databases_only")
        command("donantes")
        first = state()
        assert set(first["service_pids"]) == {"donantes"}
        record("single_service_and_worker")
        command("ms")
        current = state()
        assert len(current["service_pids"]) == 11
        assert current["service_pids"]["donantes"] == first["service_pids"]["donantes"]
        assert current["worker_pids"]["donantes"] == first["worker_pids"]["donantes"]
        assert not current.get("web_pids")
        record("all_services_preserve_existing_service")
        command("web")
        current = state()
        assert len(current["web_pids"]) == 2
        assert requests.get(current["web_url"] + "/login", timeout=5).status_code == 200
        record("web_and_session_worker")
        unchanged = pids(current)
        fingerprint = stable_config()
        command("preparar")
        assert pids(state()) == unchanged
        assert stable_config() == fingerprint
        record("installer_preserves_running_environment")
        command("todo")
        assert pids(state()) == unchanged
        record("repeat_start_preserves_all_pids")
        worker = current["worker_pids"]["donantes"]
        os.kill(worker, signal.SIGTERM)
        until = time.monotonic() + 15
        while pid_matches(worker, directory) and time.monotonic() < until:
            time.sleep(0.1)
        assert not pid_matches(worker, directory)
        command("ms")
        current = state()
        assert current["worker_pids"]["donantes"] != worker
        assert current["service_pids"] == unchanged["service_pids"]
        assert current["web_pids"] == unchanged["web_pids"]
        record("missing_worker_recovered_without_api_restart")
        previous = state()
        command("reiniciar", "donantes")
        current = state()
        assert (
            current["service_pids"]["donantes"] != previous["service_pids"]["donantes"]
        )
        for group in ("service_pids", "worker_pids"):
            assert {k: v for k, v in current[group].items() if k != "donantes"} == {
                k: v for k, v in previous[group].items() if k != "donantes"
            }
        assert current["web_pids"] == previous["web_pids"]
        record("restart_one_service_preserves_other_processes")
        command("detener", "web")
        assert all(
            pid_matches(pid, directory) for pid in state()["service_pids"].values()
        )
        with socket.socket() as occupied:
            occupied.bind(("127.0.0.1", port))
            occupied.listen()
            command("web", success=False)
            assert occupied.getsockname()[1] == port
        record("occupied_web_port_rejected_without_killing_owner")
        command("web")
        web_pids = state()["web_pids"]
        command("detener", "ms")
        assert all(pid_matches(pid, directory) for pid in web_pids.values())
        assert not any(
            pid_matches(pid, directory) for pid in state()["service_pids"].values()
        )
        command("ms")
        assert state()["web_pids"] == web_pids
        record("stop_and_start_services_preserve_web")
        with (REPO / ".local/launcher.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            result = command("estado", success=False)
            assert "Otro lanzador" in result.stderr
        record("concurrent_launcher_rejected")
        command("detener", "todo")
        assert not any(
            infrastructure_pid(state(), name)
            for name in ("postgres", "redis", "mongodb")
        )
        command("todo")
        assert stable_config() == fingerprint
        current = state()
        with requests.Session() as session:
            response = session.post(
                current["urls"]["identidad_acceso"] + "/api/v1/auth/login",
                json={"username": "admin1", "password": current["password"]},
                timeout=10,
            )
            assert response.status_code == 200
            response = session.get(
                current["urls"]["identidad_acceso"] + "/api/v1/institutions",
                headers={
                    "Authorization": "Bearer " + response.json()["data"]["access_token"]
                },
                timeout=10,
            )
            assert response.status_code == 200 and response.json()["data"]["total"] == 2
        record("cold_restart_preserves_configuration_and_accounts")
    finally:
        if (directory / "state.json").exists():
            command("detener", "todo")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(
            {
                "date": datetime.now(timezone.utc).isoformat(),
                "result": "passed",
                "checks": results,
                "environment": "new isolated local cluster; stopped after verification",
                "platform": sys.platform,
            },
            indent=2,
        )
        + "\n"
    )
    print("Entorno de prueba detenido; datos privados conservados en", directory)


if __name__ == "__main__":
    main()
