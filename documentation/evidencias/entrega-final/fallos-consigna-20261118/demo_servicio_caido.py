"""Demostración en vivo: un microservicio cae y el resto sigue operando.

Uso, desde la raíz de una instalación local NUEVA y desechable ya arrancada (`bash start.sh`):

    python3 demo_servicio_caido.py --repo <raíz> --out <resultado.json>

Detiene y reinicia servicios solo con los comandos documentados (`components.sh detener` y
`components.sh reiniciar`). Lee las URL y la contraseña sintética de `.local/runtime/state.json`
sin escribirlas en la salida. No usar sobre el laboratorio restaurado ni sobre la VM.

Escenario 1 (asíncrono): Alertas cae. Donantes sigue aceptando citas; el aviso queda en la
bandeja de salida y se entrega al reiniciar Alertas.
Escenario 2 (síncrono): Identidad cae. Un token ya emitido sigue sirviendo en otros servicios
(sesión validada en Redis); el inicio de sesión falla y una operación que consulta Identidad
responde 503 `dependency_unavailable` sin quedarse colgada; lo que no depende de Identidad sigue
funcionando. Al reiniciar, la consulta vuelve a llegar a Identidad. Se usa `operator1` porque
la instalación operativa exige MFA a ADMIN, MEDICAL y COORDINATOR.
"""

import argparse
import json
import subprocess
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import requests


def now():
    return datetime.now(timezone.utc)


def iso(**delta):
    return (now() + timedelta(**delta)).isoformat()


class Demo:
    def __init__(self, repo):
        self.repo = Path(repo)
        state = json.loads((self.repo / ".local/runtime/state.json").read_text())
        self.urls, self.password, self.tenants = (
            state["urls"],
            state["password"],
            state["tenants"],
        )
        self.tokens = {}
        self.steps = []

    def log(self, step, **data):
        entry = {"at": now().isoformat(), "step": step, **data}
        self.steps.append(entry)
        print(json.dumps(entry, ensure_ascii=False))

    def login(self, user):
        response = requests.post(
            self.urls["identidad_acceso"] + "/api/v1/auth/login",
            json={"username": user, "password": self.password},
            timeout=10,
        )
        response.raise_for_status()
        self.tokens[user] = response.json()["data"]["access_token"]

    def call(self, service, method, path, user, data=None):
        started = time.monotonic()
        try:
            response = requests.request(
                method,
                self.urls[service] + path,
                json=data,
                headers={
                    "Accept": "application/json",
                    "Authorization": "Bearer " + self.tokens[user],
                    "Idempotency-Key": uuid4().hex,
                },
                timeout=20,
            )
            body = response.json() if response.content else {}
            return {
                "status": response.status_code,
                "code": (body.get("error") or {}).get("code"),
                "seconds": round(time.monotonic() - started, 3),
            }, body.get("data")
        except requests.RequestException as exc:
            return {
                "status": None,
                "error": type(exc).__name__,
                "seconds": round(time.monotonic() - started, 3),
            }, None

    def ready(self):
        result = {}
        for service, url in self.urls.items():
            try:
                result[service] = requests.get(url + "/health/ready", timeout=5).status_code
            except requests.RequestException as exc:
                result[service] = type(exc).__name__
        return result

    def components(self, action, service):
        started = time.monotonic()
        run = subprocess.run(
            ["bash", "components.sh", action, service],
            cwd=self.repo,
            capture_output=True,
            text=True,
            check=False,
        )
        self.log(
            f"components.sh {action} {service}",
            exit=run.returncode,
            seconds=round(time.monotonic() - started, 2),
            output=run.stdout.strip().splitlines()[-1:] if run.stdout else [],
        )
        assert run.returncode == 0, run.stderr

    def alertas(self):
        self.log("base: /health/ready", ready=self.ready())
        self.components("detener", "alertas")
        self.log("alertas detenido: /health/ready", ready=self.ready())
        status, donor = self.call(
            "donantes",
            "POST",
            "/api/v1/donors",
            "donor1",
            {
                "folio": "DEMO-" + uuid4().hex[:8],
                "display_name": "Donante ficticio de demostración",
                "blood_group": "O-",
                "consent": True,
            },
        )
        self.log("donantes registra donante con alertas caído", **status)
        status, campaign = self.call(
            "donantes",
            "POST",
            "/api/v1/campaigns",
            "operator1",
            {
                "title": "Campaña ficticia de demostración",
                "starts_at": iso(minutes=10),
                "ends_at": iso(days=1),
                "capacity": 5,
            },
        )
        self.log("donantes crea campaña con alertas caído", **status)
        status, appointment = self.call(
            "donantes",
            "POST",
            "/api/v1/appointments",
            "donor1",
            {"donor_id": donor["id"], "campaign_id": campaign["id"]},
        )
        self.log("donantes agenda cita con alertas caído", **status)
        status, _ = self.call("alertas", "GET", "/api/v1/alerts", "donor1")
        self.log("bandeja de avisos con alertas caído", **status)
        restarted = time.monotonic()
        self.components("reiniciar", "alertas")
        delivered = None
        while time.monotonic() - restarted < 120:
            status, data = self.call("alertas", "GET", "/api/v1/alerts?page_size=100", "donor1")
            if status["status"] == 200 and any(
                a["message_code"] == "APPOINTMENT_BOOKED"
                and a["resource_id"] == appointment["id"]
                for a in data["items"]
            ):
                delivered = round(time.monotonic() - restarted, 2)
                break
            time.sleep(2)
        self.log(
            "aviso APPOINTMENT_BOOKED entregado tras reiniciar alertas",
            delivered=delivered is not None,
            seconds_after_restart=delivered,
        )
        self.log("alertas reiniciado: /health/ready", ready=self.ready())
        return delivered is not None

    def identidad(self):
        def unit(location=None):
            data = {
                "folio": "DEMO-" + uuid4().hex[:12],
                "kind": "BLOOD",
                "component": "RBC",
                "blood_group": "O-",
                "expires_at": iso(days=2),
            }
            if location:
                data["location_id"] = location
            return self.call("inventario", "POST", "/api/v1/resources", "operator1", data)[0]

        # Ubicación ficticia inexistente: obliga a Inventario a consultar Identidad.
        location = str(uuid4())
        self.components("detener", "identidad_acceso")
        self.log("identidad detenido: /health/ready", ready=self.ready())
        try:
            requests.post(
                self.urls["identidad_acceso"] + "/api/v1/auth/login",
                json={"username": "operator2", "password": self.password},
                timeout=5,
            )
            login = "respondió"
        except requests.RequestException as exc:
            login = type(exc).__name__
        self.log("inicio de sesión con identidad caído", result=login)
        status, _ = self.call("donantes", "GET", "/api/v1/campaigns", "operator1")
        self.log("token ya emitido sigue sirviendo en donantes", **status)
        independent = unit()
        self.log("inventario registra unidad sin ubicación (no consulta identidad)", **independent)
        down = unit(location)
        self.log("inventario valida ubicación en identidad, con identidad caído", **down)
        self.components("reiniciar", "identidad_acceso")
        up = unit(location)
        self.log(
            "misma validación tras reiniciar identidad (la ubicación ficticia no existe)",
            **up,
        )
        self.log("identidad reiniciado: /health/ready", ready=self.ready())
        return (
            independent["status"] == 201
            and down.get("code") == "dependency_unavailable"
            and up["status"] not in (None, 503)
        )

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    demo = Demo(args.repo)
    for user in ("donor1", "operator1"):
        demo.login(user)
    result = {"alertas": demo.alertas(), "identidad": demo.identidad()}
    Path(args.out).write_text(
        json.dumps({"result": result, "steps": demo.steps}, ensure_ascii=False, indent=2)
        + "\n"
    )
    print(json.dumps(result))


if __name__ == "__main__":
    main()
