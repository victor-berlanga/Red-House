"""Arranque/parada conjunta de la web y de su entorno MS; no opera bases ajenas."""

import argparse
import json
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.local import pid_matches, private_file


def save(directory, state):
    temporary = directory / "state-platform.tmp"
    if temporary.exists():
        raise RuntimeError(
            "Hay una configuración temporal previa; revisar antes de continuar."
        )
    private_file(temporary, json.dumps(state, indent=2))
    os.replace(temporary, directory / "state.json")


def session_worker(directory, state):
    pid = state.get("web_pids", {}).get("revocations")
    if pid and pid_matches(pid, directory):
        return
    web = ROOT.parent / "web-monolito01"
    python = web / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    with open(directory / "web-sessions.log", "ab") as log:
        process = subprocess.Popen(
            [
                str(python),
                str(web / "scripts/session_worker.py"),
                "--config",
                str(directory / "web-client.json"),
            ],
            cwd=web,
            stdout=log,
            stderr=log,
            start_new_session=True,
        )
    state.setdefault("web_pids", {})["revocations"] = process.pid
    save(directory, state)
    time.sleep(0.5)
    if process.poll() is not None:
        raise RuntimeError(
            "No inició el worker de revocaciones; revisa web-sessions.log."
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("start", "stop", "status", "restart-web"))
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--web-port", type=int, default=5050)
    args = parser.parse_args()
    restart_web_only = args.action == "restart-web"
    directory = args.directory.resolve()
    state = json.loads((directory / "state.json").read_text())
    if Path(state["directory"]).resolve() != directory:
        raise RuntimeError("Directorio no corresponde a este entorno.")
    command = [sys.executable, str(ROOT / "scripts/local.py")]
    if args.action == "restart-web":
        processes = list(state.get("web_pids", {}).values())
        for pid in processes:
            if pid_matches(pid, directory):
                os.kill(pid, signal.SIGTERM)
        until = time.monotonic() + 15
        while (
            any(pid_matches(pid, directory) for pid in processes)
            and time.monotonic() < until
        ):
            time.sleep(0.1)
        if any(pid_matches(pid, directory) for pid in processes):
            raise RuntimeError("Un proceso web no terminó; no se duplica el portal.")
        state["web_pids"] = {}
        save(directory, state)
        args.action = "start"
    if args.action == "start":
        active = [pid_matches(pid, directory) for pid in state["service_pids"].values()]
        workers = [
            pid_matches(pid, directory) for pid in state.get("worker_pids", {}).values()
        ]
        if not restart_web_only and (
            len(active) != 11
            or not all(active)
            or len(workers) != 11
            or not all(workers)
        ):
            if any(active):
                subprocess.run(
                    command + ["stop", "--directory", str(directory)], check=True
                )
            subprocess.run(
                command + ["start", "--directory", str(directory)], check=True
            )
            state = json.loads((directory / "state.json").read_text())
        portal_pid = state.get("web_pids", {}).get("portal")
        if portal_pid and pid_matches(portal_pid, directory):
            session_worker(directory, state)
            print("Portal ya iniciado:", state.get("web_url"))
            return
        test = socket.socket()
        try:
            if os.name != "nt":
                test.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            test.bind(("127.0.0.1", args.web_port))
        except OSError:
            raise RuntimeError(
                "El puerto web está ocupado. No se detuvo ningún proceso ajeno; indica --web-port."
            ) from None
        finally:
            test.close()
        web = ROOT.parent / "web-monolito01"
        python = (
            web / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        )
        if not python.exists():
            raise RuntimeError("Instala las dependencias de la web en su .venv propio.")
        if not (directory / "web-client.json").exists():
            raise RuntimeError(
                "Configura web-client.json antes del arranque integrado."
            )
        with open(directory / "web.log", "ab") as log:
            process = subprocess.Popen(
                [
                    str(python),
                    str(web / "scripts/run_web.py"),
                    "--config",
                    str(directory / "web-client.json"),
                    "--port",
                    str(args.web_port),
                ],
                cwd=web,
                stdout=log,
                stderr=log,
                start_new_session=True,
            )
        state.setdefault("web_pids", {})["portal"] = process.pid
        state["web_url"] = "http://127.0.0.1:" + str(args.web_port)
        save(directory, state)
        session_worker(directory, state)
        until = time.monotonic() + 20
        while time.monotonic() < until:
            if process.poll() is not None:
                raise RuntimeError("El portal no inició; revisa su log privado.")
            try:
                if (
                    requests.get(
                        state["web_url"] + "/health/live", timeout=1
                    ).status_code
                    == 200
                ):
                    print("Portal integrado iniciado:", state["web_url"])
                    return
            except requests.RequestException:
                pass
            time.sleep(0.2)
        raise RuntimeError(
            "El portal agotó el tiempo de inicio; revisa su estado antes de repetir."
        )
    if args.action == "stop":
        for pid in state.get("web_pids", {}).values():
            if pid_matches(pid, directory):
                try:
                    os.kill(pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
        subprocess.run(command + ["stop", "--directory", str(directory)], check=True)
        print("Portal y entorno propio detenidos; datos conservados.")
        return
    try:
        response = requests.get(
            state.get("web_url", "http://127.0.0.1:" + str(args.web_port))
            + "/health/live",
            timeout=2,
        )
        print("portal", response.status_code, state.get("web_url", "sin iniciar"))
    except requests.RequestException:
        print("portal down")
    subprocess.run(command + ["status", "--directory", str(directory)], check=True)


if __name__ == "__main__":
    main()
