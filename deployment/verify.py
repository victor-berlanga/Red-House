"""Pruebas operativas sobre el Compose aislado; nunca sobre .local/runtime.

Ejecutar con el Python de apps/services/.venv. Conserva resultados sin secretos.
Las escrituras usan exclusivamente HTTP; psql se usa para comprobar persistencia.
"""

import argparse
import json
import os
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import requests
from lxml import etree
from psycopg import sql

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps/services"))
from redhouse.config import SERVICES
from redhouse.evidence import redact
from tests import helpers


class Deployment:
    def __init__(self, directory, output):
        self.directory, self.output = Path(directory).resolve(), Path(output)
        if (
            self.directory.name == "runtime"
            or not (self.directory / "installation.json").exists()
        ):
            raise ValueError("Se requiere un entorno creado por deployment/prepare.py.")
        self.env = SimpleNamespace(
            state=json.loads((self.directory / "state.json").read_text())
        )
        self.urls = {
            s: f"http://127.0.0.1:{port + 1000}" for s, port in SERVICES.items()
        }
        self.web_url = "http://127.0.0.1:6050"
        self.tokens, self.records, self.checks = {}, [], []
        self.result, self.stage = "running", "initialization"
        self.compose = ["docker", "compose", "-f", str(ROOT / "compose.yaml")]
        gcs = self.directory / "gcs.compose.yaml"
        if gcs.exists():
            self.compose += ["-f", str(gcs)]
        self.command_env = dict(os.environ, REDHOUSE_COMPOSE_DIR=str(self.directory))
        self.output.mkdir(parents=True, exist_ok=True)

    def phase(self, name):
        self.stage = name
        print(
            json.dumps({"stage": name, "date": datetime.now(timezone.utc).isoformat()}),
            flush=True,
        )
        self.save()

    def command(self, *args):
        process = subprocess.run(
            self.compose + list(args),
            cwd=ROOT,
            env=self.command_env,
            text=True,
            capture_output=True,
            check=False,
        )
        if process.returncode:
            raise RuntimeError(
                "Docker falló: " + " ".join(args[:3]) + "; " + process.stderr[-2000:]
            )
        return process.stdout

    def restore_replicas(self, replicas):
        # Bound cold starts; starting 22 Python/worker pairs simultaneously can
        # saturate a development host before its health deadlines are reached.
        from start import START_ORDER

        replicas = sorted(
            replicas, key=lambda name: (START_ORDER.index(name[:-2]), name)
        )
        for offset in range(0, len(replicas), 2):
            self.command(
                "up", "-d", "--wait", "--no-deps", *replicas[offset : offset + 2]
            )

    def query(self, service, query, params=()):
        assert query.lstrip().upper().startswith("SELECT ")
        pieces = query.split("%s")
        assert len(pieces) == len(params) + 1
        statement = pieces[0]
        for value, piece in zip(params, pieces[1:]):
            statement += sql.Literal(value).as_string() + piece
        statement = (
            "SET search_path=access_" + service + ",public; "
            "SELECT coalesce(json_agg(q),'[]') FROM (" + statement + ") q"
        )
        result = self.command(
            "exec",
            "-T",
            "postgres",
            "psql",
            "-U",
            "rh_bootstrap",
            "-d",
            "red_house",
            "-qAt",
            "-v",
            "ON_ERROR_STOP=1",
            "-c",
            statement,
        )
        return json.loads(result)

    def request(
        self,
        service,
        method,
        path,
        *,
        user="medical2",
        data=None,
        key=None,
        headers=None,
    ):
        hdr = {
            "Accept": "application/json",
            "Idempotency-Key": key or uuid4().hex,
            "X-Correlation-ID": str(uuid4()),
        }
        if user:
            hdr["Authorization"] = "Bearer " + self.tokens[user]
        hdr.update(headers or {})
        started = time.perf_counter()
        response = requests.request(
            method, self.urls[service] + path, json=data, headers=hdr, timeout=(2, 8)
        )
        self.records.append(
            redact(
                {
                    "captured_at": datetime.now(timezone.utc).isoformat(),
                    "service": service,
                    "method": method,
                    "url": response.url,
                    "request_headers": hdr,
                    "request_body": data,
                    "status": response.status_code,
                    "response_headers": dict(response.headers),
                    "response_body": response.json()
                    if "json" in response.headers.get("Content-Type", "")
                    else response.text,
                    "elapsed_ms": round(1000 * (time.perf_counter() - started), 3),
                }
            )
        )
        return response

    def ok(self, service, method, path, **kwargs):
        response = self.request(service, method, path, **kwargs)
        assert response.status_code < 300, (
            service,
            path,
            response.status_code,
            response.text[:500],
        )
        return response.json()["data"]

    def login(self):
        for username in self.env.state["accounts"]:
            data = self.ok(
                "identidad_acceso",
                "POST",
                "/api/v1/auth/login",
                user=None,
                data={"username": username, "password": self.env.state["password"]},
            )
            self.tokens[username] = data["access_token"]

    def wait(self, predicate, seconds=30):
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            if predicate():
                return
            time.sleep(0.5)
        raise AssertionError(
            "No se alcanzó el estado esperado en el plazo de convergencia."
        )

    def route(self):
        rows = self.ok(
            "priorizacion_geografia", "GET", "/api/v1/routes", user="coordinator1"
        )["items"]
        origin, destination = self.env.state["tenants"]
        for row in rows:
            if row["origin_id"] == origin and row["destination_id"] == destination:
                return row["id"]
        return self.ok(
            "priorizacion_geografia",
            "POST",
            "/api/v1/routes",
            user="coordinator1",
            data={
                "origin_id": origin,
                "destination_id": destination,
                "distance_km": 10,
                "travel_minutes": 15,
                "source": "Estimación ficticia de prueba Docker",
            },
        )["id"]

    def business_reads(self):
        paths = {
            "identidad_acceso": ("/api/v1/users", "admin1"),
            "donantes": ("/api/v1/campaigns", "operator1"),
            "receptores": ("/api/v1/requests", "medical2"),
            "inventario": ("/api/v1/resources", "operator1"),
            "compatibilidad": ("/api/v1/evaluations", "medical2"),
            "priorizacion_geografia": ("/api/v1/routes", "coordinator1"),
            "transporte": ("/api/v1/shipments", "coordinator1"),
            "custodia": ("/api/v1/chains/" + self.shipment["id"], "transport1"),
            "alertas": ("/api/v1/alerts", "operator1"),
            "auditoria": ("/api/v1/events", "auditor1"),
            "monitoreo": ("/api/v1/status", "admin1"),
        }
        for service, (path, user) in paths.items():
            for mime in ("application/json", "application/xml"):
                response = self.request(
                    service, "GET", path, user=user, headers={"Accept": mime}
                )
                assert response.status_code == 200, (
                    service,
                    response.status_code,
                    response.text[:300],
                )
                if mime.endswith("xml"):
                    assert etree.fromstring(response.content).tag

    def flow(self, kind="BLOOD", component="RBC"):
        unit = helpers.resource(
            self, kind, component, "O+" if kind == "ORGAN" else "O-"
        )
        _, req = helpers.recipient_request(
            self, kind, component, "O+" if kind == "ORGAN" else "A+"
        )
        ev = helpers.evaluation(self, req, [unit])
        self.ok(
            "priorizacion_geografia",
            "POST",
            "/api/v1/rankings",
            data={"evaluation_id": ev["id"]},
        )
        key = uuid4().hex
        allocation = helpers.reservation(self, ev, unit, key)
        repeated = helpers.reservation(self, ev, unit, key)
        assert allocation["reservation"]["id"] == repeated["reservation"]["id"]
        shipment = helpers.plan(self, allocation["reservation"])
        for state, user in [
            ("PREPARED", "operator1"),
            ("COLLECTED", "transport1"),
            ("IN_TRANSIT", "transport1"),
            ("DELIVERED", "transport1"),
            ("ACCEPTED", "operator2"),
        ]:
            shipment = helpers.move(self, shipment, state, user)
        self.wait(
            lambda: (
                self.query(
                    "receptores",
                    "SELECT status FROM requests WHERE id=%s",
                    (req["id"],),
                )[0]["status"]
                == "CLOSED"
            )
        )
        self.wait(
            lambda: (
                len(
                    self.ok(
                        "custodia",
                        "GET",
                        "/api/v1/chains/" + shipment["id"],
                        user="transport1",
                    )["events"]
                )
                == 6
            )
        )
        self.shipment = shipment
        self.checks.append(
            {
                "check": "flujo_" + kind,
                "status": "passed",
                "shipment_id": shipment["id"],
                "resource_id": unit["id"],
                "request_id": req["id"],
                "persistence": self.query(
                    "inventario",
                    "SELECT id,status,tenant_id FROM resources WHERE id=%s",
                    (unit["id"],),
                ),
            }
        )
        return unit

    def web_login(self, user):
        session = requests.Session()
        values = self.form(session, "/login")
        values.update(login_email=user, password=self.env.state["password"])
        result = session.post(
            self.web_url + "/login", data=values, allow_redirects=False, timeout=8
        )
        assert result.status_code == 302, ("web_login", result.status_code)
        return session

    def form(self, session, path):
        result = session.get(self.web_url + path, timeout=8)
        assert result.status_code == 200, (path, result.status_code)
        return {
            n.get("name"): n.get("value", "")
            for n in etree.HTML(result.content).xpath('//input[@type="hidden"]')
        }

    def web_post(self, session, path, data):
        values = self.form(session, path)
        values.update(data)
        result = session.post(
            self.web_url + path, data=values, allow_redirects=False, timeout=8
        )
        assert result.status_code == 302, (path, result.status_code, result.text[:200])
        return result.headers["Location"]

    def web_flow(self, kind, component):
        clients = {
            u: self.web_login(u)
            for u in (
                "operator1",
                "medical1",
                "medical2",
                "coordinator1",
                "transport1",
                "operator2",
            )
        }
        common = {
            "human_confirmation": "on",
            "reason": "Confirmación humana ficticia durante caída de API",
        }
        unit_url = self.web_post(
            clients["operator1"],
            "/inventario/nuevo?kind=" + kind,
            {
                "folio": "DOCKER-WEB-" + uuid4().hex[:12],
                "component": component,
                "blood_group": "O+" if kind == "ORGAN" else "O-",
                "expires_at": helpers.iso(days=2),
                "donation_id": "",
            },
        )
        unit = unit_url.rsplit("/", 1)[1]
        self.web_post(clients["medical1"], unit_url + "/liberar", common)
        recipient_url = self.web_post(
            clients["medical2"],
            "/donantes/recipient/nuevo",
            {
                "folio": "PAT-" + uuid4().hex[:12],
                "display_name": "Paciente ficticio Docker",
                "kind": kind,
                "blood_group": "O+" if kind == "ORGAN" else "A+",
                "organ_type": component if kind == "ORGAN" else "",
                "studies": "Estudios ficticios; autorización clínica externa",
            },
        )
        req_url = self.web_post(
            clients["medical2"],
            "/solicitudes/nueva",
            {
                "recipient_id": recipient_url.rsplit("/", 1)[1],
                "component": component,
                "quantity": "1",
                "urgency": "3",
            },
        )
        ev_url = self.web_post(clients["medical2"], req_url + "/evaluar", {})
        self.web_post(
            clients["medical2"],
            ev_url + "/dictamen/" + unit,
            dict(common, decision="FAVORABLE"),
        )
        self.web_post(clients["medical2"], ev_url + "/ordenar", {})
        op_url = self.web_post(
            clients["medical2"], ev_url + "/reservar/" + unit, common
        )
        allocation = self.query(
            "inventario",
            "SELECT id FROM reservations WHERE operation_id=%s",
            (op_url.rsplit("/", 1)[1],),
        )[0]
        shipment_url = self.web_post(
            clients["coordinator1"],
            "/traslados/nuevo",
            dict(
                common,
                reservation_id=allocation["id"],
                transport_user_id=self.env.state["accounts"]["transport1"]["id"],
                departure_at=helpers.iso(minutes=1),
                eta=helpers.iso(minutes=30),
            ),
        )
        for state, user in [
            ("PREPARED", "operator1"),
            ("COLLECTED", "transport1"),
            ("IN_TRANSIT", "transport1"),
            ("DELIVERED", "transport1"),
            ("ACCEPTED", "operator2"),
        ]:
            self.web_post(clients[user], shipment_url + "/paso/" + state, common)
        request_id, shipment_id = (
            req_url.rsplit("/", 1)[1],
            shipment_url.rsplit("/", 1)[1],
        )
        self.wait(
            lambda: (
                self.query(
                    "receptores",
                    "SELECT status FROM requests WHERE id=%s",
                    (request_id,),
                )[0]["status"]
                == "CLOSED"
            )
        )
        self.wait(
            lambda: bool(
                self.query(
                    "auditoria",
                    "SELECT id FROM audit_events WHERE event->>'resource_id'=%s AND action='SHIPMENT_ACCEPTED'",
                    (shipment_id,),
                )
            )
        )
        assert (
            "Aceptado"
            in clients["operator2"].get(self.web_url + shipment_url, timeout=8).text
        )
        self.checks.append(
            {
                "check": "web_sin_api_" + kind,
                "status": "passed",
                "shipment_id": shipment_id,
                "persistence": self.query(
                    "inventario", "SELECT id,status FROM resources WHERE id=%s", (unit,)
                ),
            }
        )
        return unit

    def save(self):
        (self.output / "docker-http.json").write_text(
            json.dumps(redact(self.records), indent=2, ensure_ascii=False) + "\n"
        )
        (self.output / "docker-results.json").write_text(
            json.dumps(
                {
                    "date": datetime.now(timezone.utc).isoformat(),
                    "result": self.result,
                    "stage": self.stage,
                    "checks": self.checks,
                },
                indent=2,
                ensure_ascii=False,
            )
            + "\n"
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", default=".local/compose")
    parser.add_argument(
        "--output", default="documentation/evidencias/segundo-parcial/docker"
    )
    parser.add_argument(
        "--phase",
        choices=["smoke", "failover", "web", "restart", "rolling", "all"],
        default="all",
    )
    args = parser.parse_args()
    p = Deployment(args.directory, args.output)
    helpers.route = lambda _: p.route()
    replicas_a = [s.replace("_", "-") + "-a" for s in SERVICES]
    replicas_b = [s.replace("_", "-") + "-b" for s in SERVICES]
    try:
        p.phase("baseline")
        p.login()
        p.route()
        unit = p.flow()
        p.business_reads()
        p.checks.append({"check": "once_servicios_json_xml", "status": "passed"})
        if args.phase in ("failover", "all"):
            p.phase("failover")
            p.command("stop", *replicas_a)
            try:
                p.login()  # Identity must also survive.
                p.flow("ORGAN", "KIDNEY")
                p.business_reads()
                p.checks.append(
                    {"check": "once_replicas_a_detenidas", "status": "passed"}
                )
            finally:
                p.phase("restore_failover")
                p.restore_replicas(replicas_a)
        if args.phase in ("web", "all"):
            p.phase("web_without_apis")
            p.command("stop", *(replicas_a + replicas_b))
            try:
                p.web_flow("BLOOD", "RBC")
                p.web_flow("ORGAN", "KIDNEY")
                down = requests.get(
                    p.urls["inventario"] + "/api/v1/resources", timeout=8
                )
                assert down.status_code in (502, 503, 504)
                p.checks.append(
                    {
                        "check": "api_sin_autoridad_no_promete_continuidad",
                        "status": "passed",
                        "http": down.status_code,
                    }
                )
            finally:
                p.phase("restore_web_apis")
                p.restore_replicas(replicas_a + replicas_b)
        if args.phase in ("rolling", "all"):
            p.phase("rolling_update")
            # Each phase authenticates a current client. Slow cold starts must
            # not turn this update test into an unrelated expired-token test.
            p.login()

            def image_id(replica):
                container = p.command("ps", "-q", replica).strip()
                return subprocess.check_output(
                    ["docker", "inspect", "--format", "{{.Image}}", container],
                    text=True,
                ).strip()

            previous_images = {
                replica: image_id(replica)
                for replica in ("inventario-a", "inventario-b")
            }
            p.command("build", "inventario-a")
            results, stop = [], threading.Event()

            def traffic():
                while not stop.is_set():
                    try:
                        result = p.request(
                            "inventario", "GET", "/api/v1/resources", user="operator1"
                        )
                        results.append(result.status_code)
                    except requests.RequestException:
                        results.append(0)
                    stop.wait(0.3)

            thread = threading.Thread(target=traffic)
            thread.start()
            try:
                for replica in ("inventario-a", "inventario-b"):
                    p.command(
                        "up", "-d", "--wait", "--no-deps", "--force-recreate", replica
                    )
                    created = p.ok(
                        "inventario",
                        "POST",
                        "/api/v1/resources",
                        user="operator1",
                        data={
                            "folio": "ROLLING-" + uuid4().hex[:12],
                            "kind": "BLOOD",
                            "component": "RBC",
                            "blood_group": "O+",
                            "expires_at": helpers.iso(days=2),
                        },
                    )
                    assert p.query(
                        "inventario",
                        "SELECT id FROM resources WHERE id=%s",
                        (created["id"],),
                    )
            finally:
                stop.set()
                thread.join()
            assert results and set(results) == {200}, results
            current_images = {replica: image_id(replica) for replica in previous_images}
            p.checks.append(
                {
                    "check": "actualizacion_secuencial_imagen_compatible"
                    if previous_images != current_images
                    else "recreacion_secuencial_imagen_compatible",
                    "status": "passed",
                    "requests": len(results),
                    "codes": sorted(set(results)),
                    "before_images": previous_images,
                    "after_images": current_images,
                }
            )
        if args.phase in ("restart", "all"):
            p.phase("restart_stores")
            before = p.query(
                "inventario",
                "SELECT id,folio,status,version FROM resources WHERE id=%s",
                (unit["id"],),
            )
            p.command("restart", "postgres", "redis", "mongodb")
            p.command("up", "-d", "--wait", "postgres", "redis", "mongodb")
            after = p.query(
                "inventario",
                "SELECT id,folio,status,version FROM resources WHERE id=%s",
                (unit["id"],),
            )
            assert before == after
            p.login()
            p.business_reads()
            p.checks.append(
                {
                    "check": "persistencia_reinicio",
                    "status": "passed",
                    "before": before,
                    "after": after,
                }
            )
        p.result, p.stage = "passed", "complete"
        print(json.dumps({"result": "passed", "checks": len(p.checks)}), flush=True)
    except Exception as exc:
        p.result = "failed"
        p.checks.append(
            {"check": "execution", "status": "failed", "error": redact(str(exc))}
        )
        raise
    finally:
        p.save()


if __name__ == "__main__":
    main()
