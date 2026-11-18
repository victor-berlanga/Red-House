"""Ensayo de la demostración de tolerancia a fallos que se puede pedir en vivo.

Uso, con el Python de la instalación (trae requests, psycopg, redis y pymongo), desde una
instalación local NUEVA y desechable ya arrancada con `bash start.sh`:

    <raíz>/apps/services/.venv/bin/python demo_fallos_en_vivo.py --repo <raíz> demo --out demo.json

Ayudantes para la presentación (misma instalación):

    ... --repo <raíz> caso c_redis [d_mongodb ...] # uno o más casos sueltos, con testigo propio
    ... --repo <raíz> estado                      # /health/ready de los 12 servicios
    ... --repo <raíz> detener-base redis|mongodb|postgres
    ... --repo <raíz> pausar identidad_acceso     # congela la API (SIGSTOP): tiempo agotado
    ... --repo <raíz> reanudar identidad_acceso   # SIGCONT

Las bases se reinician con el comando documentado `bash components.sh bases`, y los
microservicios con `bash components.sh detener|reiniciar <servicio>`; `components.sh` no
tiene un comando para detener una sola base, por eso existe `detener-base`. Solo señala
procesos cuyo PID y comando pertenecen a esta instalación (misma verificación que
`apps/services/scripts/local.py`). No usar sobre el laboratorio restaurado ni sobre la VM.

Lee las URL y la contraseña sintética de `.local/runtime/state.json` sin escribirlas en la
salida: la bitácora solo guarda hora, paso, código HTTP, código de error, tiempo, PID y
correlation_id. Cada caso termina comprobando que el registro testigo creado antes del
fallo sigue íntegro y que ningún alta quedó duplicada.
"""

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import requests

BASES = ("postgres", "redis", "mongodb")


def now():
    return datetime.now(timezone.utc)


def iso(**delta):
    return (now() + timedelta(**delta)).isoformat()


class Demo:
    def __init__(self, repo):
        self.repo = Path(repo).resolve()
        self.directory = self.repo / ".local/runtime"
        sys.path.insert(0, str(self.repo / "apps/services"))
        self.state = json.loads((self.directory / "state.json").read_text())
        self.urls = self.state["urls"]
        self.tokens, self.refresh, self.steps, self.traced = {}, {}, [], []
        self.revoked_token = None

    # ------------------------------------------------------------------ utilidades
    def log(self, step, **data):
        entry = {"at": now().isoformat(), "step": step, **data}
        self.steps.append(entry)
        print(json.dumps(entry, ensure_ascii=False), flush=True)
        return entry

    def login(self, user, keep=True):
        started = time.monotonic()
        try:
            response = requests.post(
                self.urls["identidad_acceso"] + "/api/v1/auth/login",
                json={"username": user, "password": self.state["password"]},
                timeout=6,
            )
        except requests.RequestException as exc:
            return {"status": None, "error": type(exc).__name__,
                    "seconds": round(time.monotonic() - started, 3)}
        body = response.json() if response.content else {}
        result = {
            "status": response.status_code,
            "code": (body.get("error") or {}).get("code"),
            "seconds": round(time.monotonic() - started, 3),
        }
        if response.status_code == 200 and keep:
            self.tokens[user] = body["data"]["access_token"]
            self.refresh[user] = body["data"]["refresh_token"]
        return result

    def call(self, service, method, path, user=None, data=None, token=None,
             trace=None, timeout=20, url=None):
        started = time.monotonic()
        correlation = str(uuid4())
        headers = {"Accept": "application/json", "X-Correlation-ID": correlation}
        bearer = token or (self.tokens.get(user) if user else None)
        if bearer:
            headers["Authorization"] = "Bearer " + bearer
        if method in ("POST", "PATCH", "PUT"):
            headers["Idempotency-Key"] = uuid4().hex
        try:
            response = requests.request(
                method, (url or self.urls[service]) + path, json=data,
                headers=headers, timeout=timeout,
            )
            try:
                body = response.json() if response.content else {}
            except ValueError:
                body = {}
            result = {
                "status": response.status_code,
                "code": (body.get("error") or {}).get("code"),
                "seconds": round(time.monotonic() - started, 3),
                "correlation_id": correlation,
            }
            if response.headers.get("Retry-After"):
                result["retry_after"] = response.headers["Retry-After"]
            payload = body.get("data")
        except requests.RequestException as exc:
            result = {
                "status": None,
                "error": type(exc).__name__,
                "seconds": round(time.monotonic() - started, 3),
                "correlation_id": correlation,
            }
            payload = None
        if trace:
            self.traced.append({"service": service, "label": trace, **result})
        return result, payload

    def health(self, service, kind="ready"):
        try:
            response = requests.get(self.urls[service] + "/health/" + kind, timeout=5)
            data = response.json().get("data", {})
            down = sorted(
                name for name, value in (data.get("dependencies") or {}).items()
                if value.get("state") in ("down", "degraded")
            )
            return {"status": response.status_code, "down": down} if down else response.status_code
        except requests.RequestException as exc:
            return type(exc).__name__

    def ready(self):
        return {service: self.health(service) for service in self.urls}

    def wait_all_ready(self, limit=120):
        started = time.monotonic()
        while time.monotonic() - started < limit:
            current = self.ready()
            if all(value == 200 for value in current.values()):
                return round(time.monotonic() - started, 2), current
            time.sleep(1)
        return None, self.ready()

    def components(self, *args):
        started = time.monotonic()
        run = subprocess.run(
            ["bash", "components.sh", *args], cwd=self.repo,
            capture_output=True, text=True, check=False,
        )
        lines = [line for line in run.stdout.strip().splitlines() if "/docs" not in line]
        self.log(
            "bash components.sh " + " ".join(args), exit=run.returncode,
            seconds=round(time.monotonic() - started, 2), output=lines[-2:],
        )
        assert run.returncode == 0, run.stderr[-500:]

    # ------------------------------------------------- control de bases y procesos
    def base_pid(self, name):
        from scripts.local import infrastructure_pid

        return infrastructure_pid(self.state, name)

    def stop_base(self, name):
        pid = self.base_pid(name)
        if not pid:
            raise SystemExit(f"{name} no está activo en esta instalación.")
        # PostgreSQL: apagado rápido (SIGINT); con SIGTERM esperaría a que los
        # servicios cierren sus conexiones del pool.
        os.kill(pid, signal.SIGINT if name == "postgres" else signal.SIGTERM)
        started = time.monotonic()
        while time.monotonic() - started < 30:
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                break
            time.sleep(0.2)
        else:
            raise SystemExit(f"{name} no terminó en 30 s.")
        return {"pid": pid, "seconds": round(time.monotonic() - started, 2)}

    def signal_service(self, service, sig):
        from scripts.local import pid_matches

        pid = self.state["service_pids"][service]
        if not pid_matches(pid, self.directory):
            raise SystemExit(f"El PID de {service} no pertenece a esta instalación.")
        os.kill(pid, sig)
        return pid

    # --------------------------------------------------------- integridad de datos
    def new_donor(self, label, user="operator1", trace=None):
        folio = "DEMO-" + label + "-" + uuid4().hex[:8]
        status, data = self.call(
            "donantes", "POST", "/api/v1/donors", user,
            {"folio": folio, "display_name": "Donante ficticio " + label,
             "blood_group": "O-", "consent": True},
            trace=trace,
        )
        return folio, status, data

    def count_folio(self, folio, user="operator1"):
        status, data = self.call(
            "donantes", "GET", f"/api/v1/donors?q={folio}&page_size=100", user
        )
        if status["status"] != 200:
            return None
        return sum(1 for item in data["items"] if item["folio"] == folio)

    def integrity(self, case, attempted=()):
        """El testigo no cambió y cada alta intentada existe 0 o 1 vez (nunca 2)."""
        status, data = self.call(
            "donantes", "GET", "/api/v1/donors/" + self.witness["id"], "operator1"
        )
        same = status["status"] == 200 and all(
            data.get(k) == self.witness[k] for k in ("folio", "display_name", "version", "status")
        )
        witness_count = self.count_folio(self.witness["folio"])
        counts = {label: self.count_folio(folio) for label, folio in attempted}
        ok = same and witness_count == 1 and all(c in (0, 1) for c in counts.values())
        self.log(
            f"{case}: integridad tras recuperar", ok=ok, testigo_igual=same,
            testigo_veces=witness_count, altas_intentadas=counts,
        )
        return ok, counts

    # ---------------------------------------------------------------------- casos
    def case_archivo_inexistente(self):
        missing = str(uuid4())
        meta, _ = self.call("documentos", "GET", "/api/v1/documents/" + missing,
                            "operator1", trace="documento inexistente")
        self.log("g. metadatos de documento inexistente", **meta)
        download, _ = self.call("documentos", "GET", f"/api/v1/files/{missing}/download",
                                "operator1", trace="descarga inexistente")
        self.log("g. descarga de archivo inexistente", **download)
        invalid, _ = self.call("documentos", "GET", "/api/v1/documents/no-es-uuid",
                               "operator1")
        self.log("g. identificador mal formado", **invalid)
        return (meta["status"], meta["code"]) == (404, "not_found") and download["status"] == 404

    def case_sin_permisos(self):
        other, _ = self.call("donantes", "GET", "/api/v1/donors/" + self.witness["id"],
                             "operator2", trace="otra institución")
        self.log("i. operator2 (Hospital 2) abre donante del Hospital 1", **other)
        role, _ = self.call(
            "inventario", "POST", "/api/v1/resources", "donor1",
            {"folio": "DEMO-PERM-" + uuid4().hex[:8], "kind": "BLOOD",
             "component": "RBC", "blood_group": "O-", "expires_at": iso(days=2)},
            trace="rol sin permiso",
        )
        self.log("i. donor1 (DONOR) intenta registrar inventario", **role)
        auditor, _ = self.call(
            "donantes", "POST", "/api/v1/donors", "auditor1",
            {"folio": "DEMO-PERM-" + uuid4().hex[:8], "display_name": "x",
             "blood_group": "O-", "consent": True},
        )
        self.log("i. auditor1 (solo lectura) intenta registrar donante", **auditor)
        anonymous, _ = self.call("donantes", "GET", "/api/v1/donors")
        self.log("i. petición sin token", **anonymous)
        time.sleep(6)
        audit, data = self.call(
            "auditoria", "GET",
            "/api/v1/events?categories=ALL&correlation_id=" + other["correlation_id"],
            "auditor1",
        )
        actions = [
            (item.get("action"), item.get("category"))
            for item in (data or {}).get("items", [])
        ]
        # El 403 entre instituciones se audita (REJECTED); el 403 por rol se rechaza
        # antes de identificar al actor y solo queda en el log del servicio.
        self.log("i. auditoría registra el rechazo entre instituciones por correlation_id",
                 **audit, acciones=actions)
        ok, _ = self.integrity("i")
        return (
            (other["status"], other["code"]) == (403, "forbidden")
            and role["status"] == 403 and auditor["status"] == 403
            and anonymous["status"] == 401 and ok
        )

    def case_revocar_token(self):
        # Sesión C: otra sesión del mismo usuario; no debe verse afectada.
        self.login("transport1")
        other = self.tokens["transport1"]
        self.login("transport1")
        access, refresh = self.tokens["transport1"], self.refresh["transport1"]
        before, _ = self.call("identidad_acceso", "GET", "/api/v1/auth/me", token=access)
        self.log("b. token vigente consulta su perfil", **before)
        revoke, _ = self.call("identidad_acceso", "POST", "/api/v1/auth/revoke",
                              data={"refresh_token": refresh})
        self.log("b. POST /auth/revoke con el token de renovación", **revoke)
        reuse, _ = self.call("identidad_acceso", "GET", "/api/v1/auth/me", token=access,
                             trace="token revocado")
        self.log("b. reutilizar el token de acceso revocado", **reuse)
        renewed, _ = self.call("identidad_acceso", "POST", "/api/v1/auth/refresh",
                               data={"refresh_token": refresh})
        self.log("b. renovar con la familia revocada", **renewed)
        still, _ = self.call("identidad_acceso", "GET", "/api/v1/auth/me", token=other)
        self.log("b. otra sesión del mismo usuario sigue vigente", **still)
        self.login("transport1")
        logout_token = self.tokens["transport1"]
        logout, _ = self.call("identidad_acceso", "POST", "/api/v1/auth/logout",
                              token=logout_token)
        self.log("b. POST /auth/logout", **logout)
        after, _ = self.call("identidad_acceso", "GET", "/api/v1/auth/me", token=logout_token)
        self.log("b. reutilizar el token tras cerrar sesión", **after)
        self.revoked_token = access
        return (
            before["status"] == 200 and revoke["status"] == 200
            and (reuse["status"], reuse["code"]) == (401, "unauthorized")
            and renewed["status"] == 401 and still["status"] == 200
            and logout["status"] == 200 and after["status"] == 401
        )

    def monitor_state(self, service, since):
        status, data = self.call("monitoreo", "GET", "/api/v1/status", "auditor1")
        if status["status"] != 200:
            return None
        for row in data["latest"]:
            if row["service"] == service and row["created_at"] >= since:
                return row
        return None

    def wait_monitor(self, service, since, want_up, limit=80):
        started = time.monotonic()
        while time.monotonic() - started < limit:
            row = self.monitor_state(service, since)
            if row and (row["state"] == "up") == want_up:
                return round(time.monotonic() - started, 1), row
            time.sleep(3)
        return None, None

    def case_microservicio(self):
        service = "inventario"
        stopped_at = now().isoformat()
        self.components("detener", service)
        self.log("a. inventario detenido: /health/ready", ready=self.ready())
        direct, _ = self.call(service, "GET", "/api/v1/resources", "operator1")
        self.log("a. API de inventario sin proceso", **direct)
        others, _ = self.call("donantes", "GET", "/api/v1/campaigns", "operator1")
        self.log("a. donantes sigue atendiendo", **others)
        self.log("a. portal web (monolito) /inventario con la API detenida",
                 **self.portal("/inventario"))
        seconds, row = self.wait_monitor(service, stopped_at, want_up=False)
        self.log(
            "a. monitoreo registra la caída", detected=row is not None,
            seconds=seconds, state=row and row["state"], error=row and row["last_error"],
            checked_at=row and row["created_at"], stopped_at=stopped_at,
        )
        restarted_at = now().isoformat()
        self.components("reiniciar", service)
        created, _ = self.call(
            service, "POST", "/api/v1/resources", "operator1",
            {"folio": "DEMO-INV-" + uuid4().hex[:8], "kind": "BLOOD", "component": "RBC",
             "blood_group": "O-", "expires_at": iso(days=2)},
        )
        self.log("a. inventario reiniciado registra una unidad", **created)
        up_seconds, up_row = self.wait_monitor(service, restarted_at, want_up=True)
        self.log("a. monitoreo registra la recuperación", recovered=up_row is not None,
                 seconds=up_seconds)
        ok, _ = self.integrity("a")
        return (
            direct["status"] is None and others["status"] == 200 and row is not None
            and created["status"] == 201 and up_row is not None and ok
        )

    def unit(self, folio, location=None, trace=None):
        data = {"folio": folio, "kind": "BLOOD", "component": "RBC", "blood_group": "O-",
                "expires_at": iso(days=2)}
        if location:
            data["location_id"] = location
        return self.call("inventario", "POST", "/api/v1/resources", "operator1", data,
                         trace=trace)[0]

    def count_units(self, folio):
        status, data = self.call(
            "inventario", "GET", f"/api/v1/resources?q={folio}&page_size=100", "operator1"
        )
        if status["status"] != 200:
            return None
        return sum(1 for item in data["items"] if item["folio"] == folio)

    def case_tiempo_agotado(self):
        location = str(uuid4())  # Ubicación ficticia: obliga a consultar Identidad.
        folio = "DEMO-TO-" + uuid4().hex[:8]
        pid = self.signal_service("identidad_acceso", signal.SIGSTOP)
        self.log("f. identidad_acceso congelado (SIGSTOP): acepta conexiones y no responde", pid=pid)
        try:
            login = self.login("operator2", keep=False)
            self.log("f. inicio de sesión directo con identidad congelado", **login)
            frozen = self.unit(folio, location, trace="tiempo agotado")
            self.log("f. inventario espera a identidad (lectura máx. 3 s)", **frozen)
            independent = self.unit("DEMO-TO-LIBRE-" + uuid4().hex[:6])
            self.log("f. alta sin ubicación no depende de identidad", **independent)
        finally:
            self.signal_service("identidad_acceso", signal.SIGCONT)
            self.log("f. identidad_acceso reanudado (SIGCONT)", pid=pid)
        again = self.unit(folio, location)
        self.log("f. misma alta tras reanudar (la ubicación ficticia no existe)", **again)
        units = self.count_units(folio)
        self.log("f. unidades con el folio del intento fallido", count=units)
        ok, _ = self.integrity("f")
        return (
            (frozen["status"], frozen.get("code")) == (503, "dependency_unavailable")
            and 2.5 <= frozen["seconds"] <= 8 and independent["status"] == 201
            and again["status"] == 404 and units == 0 and ok
        )

    def web_session(self, user):
        import re

        jar, web = {}, self.state["web_url"]

        def request(method, path, **kwargs):
            headers = {"Cookie": "; ".join(f"{k}={v}" for k, v in jar.items())}
            response = requests.request(method, web + path, headers=headers,
                                        allow_redirects=False, timeout=20, **kwargs)
            for cookie in response.raw.headers.getlist("Set-Cookie"):
                name, value = cookie.split(";")[0].split("=", 1)
                jar[name] = value
            return response

        page = request("GET", "/login")
        token = re.search(r'name="csrf_token" value="([^"]+)"', page.text).group(1)
        logged = request("POST", "/login", data={
            "csrf_token": token, "login_email": user,
            "password": self.state["password"], "_timezone": "America/Monterrey"})
        assert logged.status_code == 302, logged.status_code
        return request

    def portal(self, path):
        import re

        response = self.web("GET", path)
        title = re.findall(r"<title>([^<]*)", response.text)
        return {"status": response.status_code,
                "title": title[0].replace(" · Red House", "") if title else None}

    def case_archivos(self):
        web = self.web
        page = f"/documentos?subject_kind=DONOR&subject_id={self.witness['id']}"
        self.components("detener", "documentos")
        self.log("j. documentos detenido: /health/ready", ready=self.ready())
        direct, _ = self.call("documentos", "GET", "/api/v1/documents/" + str(uuid4()), "operator1")
        self.log("j. API de documentos sin proceso", **direct)
        portal = web("GET", page)
        self.log("j. portal (monolito) consulta los documentos del testigo",
                 status=portal.status_code)
        self.components("reiniciar", "documentos")
        # Almacén privado inaccesible: la API sigue arriba pero no puede escribir archivos.
        storage = self.directory / "private-files"
        storage.chmod(0o000)
        try:
            probe = requests.get(self.urls["documentos"] + "/health/storage", timeout=5)
            ready = self.health("documentos")
            self.log("j. almacén privado sin permisos: /health/storage",
                     status=probe.status_code, data=probe.json().get("data"), ready=ready)
        finally:
            storage.chmod(0o700)
        restored = requests.get(self.urls["documentos"] + "/health/storage", timeout=5)
        self.log("j. almacén restablecido (0700): /health/storage",
                 status=restored.status_code, data=restored.json().get("data"))
        after = web("GET", page)
        self.log("j. portal tras reiniciar documentos", status=after.status_code)
        ok, _ = self.integrity("j")
        return (
            direct["status"] is None and probe.status_code == 503
            and restored.status_code == 200 and after.status_code == 200 and ok
        )

    def worker_failures(self):
        return sum(
            path.read_text(errors="replace").count("worker_failure")
            for path in self.directory.glob("*-worker.log")
        )

    def hold(self, case, seconds=12):
        before = self.worker_failures()
        time.sleep(seconds)
        self.log(case + ". caída sostenida", seconds=seconds,
                 worker_failure_nuevos=self.worker_failures() - before)

    def case_redis(self):
        folio = None
        stop = self.stop_base("redis")
        self.log("c. Redis detenido", **stop)
        try:
            authenticated, _ = self.call("donantes", "GET", "/api/v1/campaigns", "operator1",
                                         trace="redis caído")
            self.log("c. petición autenticada con Redis caído", **authenticated)
            login = self.login("operator2", keep=False)
            self.log("c. inicio de sesión con Redis caído", **login)
            folio, write, _ = self.new_donor("REDIS")
            self.log("c. alta de donante con Redis caído", **write)
            self.log("c. donantes /health/live", status=self.health("donantes", "live"))
            self.log("c. Redis caído: /health/ready", ready=self.ready())
            self.log("c. portal web /panel durante la caída", **self.portal("/panel"))
            self.hold("c")
        finally:
            self.components("bases")
        seconds, ready = self.wait_all_ready()
        self.log("c. Redis reiniciado: /health/ready", seconds_to_ready=seconds, ready=ready)
        same, _ = self.call("donantes", "GET", "/api/v1/campaigns", "operator1")
        self.log("c. el mismo token vuelve a servir (sesiones persistidas en AOF)", **same)
        self.log("c. portal web /panel tras recuperar (misma sesión)", **self.portal("/panel"))
        if self.revoked_token:
            revoked, _ = self.call("identidad_acceso", "GET", "/api/v1/auth/me",
                                   token=self.revoked_token)
            self.log("c. el token revocado en (b) sigue revocado tras reiniciar Redis", **revoked)
        else:  # Caso suelto: no se ejecutó (b) antes.
            revoked = {"status": 401}
        ok, counts = self.integrity("c", [("alta durante la caída", folio)])
        return (
            (authenticated["status"], authenticated["code"]) == (503, "redis_unavailable")
            and authenticated["seconds"] < 5 and login["status"] == 503
            and write["status"] == 503 and seconds is not None and same["status"] == 200
            and revoked["status"] == 401 and counts["alta durante la caída"] == 0 and ok
        )

    def mongo_pending(self):
        import psycopg

        with psycopg.connect(self.state["database_owners"]["auditoria"], connect_timeout=3) as conn:
            return conn.execute(
                "SELECT count(*) FROM outbox WHERE target='mongodb' AND delivered_at IS NULL"
            ).fetchone()[0]

    def mongo_copies(self, resource_id):
        from pymongo import MongoClient

        with MongoClient(self.state["mongo_admin"], serverSelectionTimeoutMS=3000) as client:
            return client["rh_auditoria"].events.count_documents(
                {"resource_id": resource_id, "action": "DONOR_REGISTERED"}
            )

    def case_mongodb(self):
        _, before = self.call("auditoria", "GET", "/api/v1/documentary-events?page_size=1", "auditor1")
        total_before = (before or {}).get("total")
        stop = self.stop_base("mongodb")
        self.log("d. MongoDB detenido", **stop, pendientes_antes=self.mongo_pending())
        try:
            self.log("d. MongoDB caído: /health/ready", ready=self.ready())
            self.log("d. portal web /panel durante la caída", **self.portal("/panel"))
            folio, write, donor = self.new_donor("MONGO")
            self.log("d. alta de donante (negocio en PostgreSQL) con MongoDB caído", **write)
            pending, started = 0, time.monotonic()
            while time.monotonic() - started < 40 and not pending:
                time.sleep(2)
                pending = self.mongo_pending()
            self.log("d. auditoría retenida en bandeja de salida (outbox) hacia MongoDB",
                     pendientes=pending, seconds=round(time.monotonic() - started, 1))
            sql, _ = self.call("auditoria", "GET",
                               f"/api/v1/events?resource={donor['id']}", "auditor1")
            self.log("d. bitácora SQL de auditoría sigue consultable", **sql)
            documentary, _ = self.call("auditoria", "GET", "/api/v1/documentary-events",
                                       "auditor1", trace="mongodb caído")
            self.log("d. proyección documental (MongoDB) con MongoDB caído", **documentary)
        finally:
            self.components("bases")
        drained, started = None, time.monotonic()
        while time.monotonic() - started < 90:
            if self.mongo_pending() == 0:
                drained = round(time.monotonic() - started, 1)
                break
            time.sleep(2)
        self.log("d. MongoDB reiniciado: bandeja de salida vaciada", seconds=drained)
        seconds, ready = self.wait_all_ready()
        self.log("d. MongoDB reiniciado: /health/ready", seconds_to_ready=seconds, ready=ready)
        after, data = self.call("auditoria", "GET", "/api/v1/documentary-events?page_size=1", "auditor1")
        copies = self.mongo_copies(donor["id"])
        self.log("d. proyección documental tras recuperar", **after,
                 total_antes=total_before, total_despues=(data or {}).get("total"),
                 copias_del_evento=copies)
        ok, counts = self.integrity("d", [("alta durante la caída", folio)])
        return (
            write["status"] == 201 and pending > 0 and sql["status"] == 200
            and (documentary["status"], documentary["code"]) == (503, "mongodb_unavailable")
            and drained is not None and seconds is not None and after["status"] == 200
            and copies == 1 and counts["alta durante la caída"] == 1 and ok
        )

    def case_postgres(self):
        folio = None
        stop = self.stop_base("postgres")
        self.log("e. PostgreSQL detenido (apagado rápido)", **stop)
        try:
            self.log("e. donantes /health/live", status=self.health("donantes", "live"))
            database = requests.get(self.urls["donantes"] + "/health/database", timeout=5)
            self.log("e. donantes /health/database", status=database.status_code,
                     data=database.json().get("data"))
            self.log("e. PostgreSQL caído: /health/ready", ready=self.ready())
            self.log("e. portal web /panel durante la caída", **self.portal("/panel"))
            read, _ = self.call("donantes", "GET", "/api/v1/campaigns", "operator1",
                                trace="postgres caído")
            self.log("e. lectura autenticada con PostgreSQL caído", **read)
            folio, write, _ = self.new_donor("PG")
            self.log("e. alta de donante con PostgreSQL caído", **write)
            login = self.login("operator2", keep=False)
            self.log("e. inicio de sesión con PostgreSQL caído", **login)
            self.hold("e")
        finally:
            self.components("bases")
        seconds, ready = self.wait_all_ready()
        self.log("e. PostgreSQL reiniciado: /health/ready", seconds_to_ready=seconds, ready=ready)
        again, _ = self.call("donantes", "GET", "/api/v1/campaigns", "operator1")
        self.log("e. la misma lectura tras recuperar", **again)
        self.log("e. portal web /panel tras recuperar (misma sesión)", **self.portal("/panel"))
        ok, counts = self.integrity("e", [("alta durante la caída", folio)])
        return (
            database.status_code == 503 and (read["status"], read["code"]) == (503, "database_unavailable")
            and write["status"] == 503 and seconds is not None and again["status"] == 200
            and counts["alta durante la caída"] == 0 and ok
        )

    def case_sobrecarga(self, total=240, workers=24):
        def one(_):
            return self.call("donantes", "GET", "/api/v1/campaigns?page_size=1", "operator1",
                             timeout=30)[0]

        started = time.monotonic()
        with ThreadPoolExecutor(workers) as pool:
            futures = [pool.submit(one, i) for i in range(total)]
            time.sleep(0.3)  # En plena ráfaga: otra cuenta y la sonda de salud.
            other, _ = self.call("donantes", "GET", "/api/v1/campaigns", "operator2")
            ready = self.health("donantes")
            results = [future.result() for future in futures]
        elapsed = round(time.monotonic() - started, 2)
        codes = {}
        for result in results:
            codes[str(result["status"])] = codes.get(str(result["status"]), 0) + 1
        limited = [r for r in results if r["status"] == 429]
        if limited:
            self.traced.append({"service": "donantes", "label": "sobrecarga 429", **limited[0]})
        self.log(
            "h. ráfaga de operator1 contra donantes", peticiones=total, concurrencia=workers,
            seconds=elapsed, codigos=codes,
            codigo_error=limited[0]["code"] if limited else None,
            retry_after=limited[0].get("retry_after") if limited else None,
            p_max_seconds=max(r["seconds"] for r in results),
        )
        self.log("h. operator2 durante la ráfaga", **other)
        self.log("h. donantes /health/ready durante la ráfaga", status=ready)
        # La cuota es por cuenta y por minuto: al cambiar la ventana operator1 vuelve.
        waited, started = None, time.monotonic()
        while time.monotonic() - started < 75:
            status, _ = self.call("donantes", "GET", "/api/v1/campaigns?page_size=1", "operator1")
            if status["status"] == 200:
                waited = round(time.monotonic() - started, 1)
                break
            time.sleep(5)
        self.log("h. operator1 vuelve a ser atendido al cambiar la ventana", seconds=waited)
        ok, _ = self.integrity("h")
        return (
            len(limited) > 0 and codes.get("200", 0) >= 150 and other["status"] == 200
            and ready == 200 and waited is not None and ok
        )

    def case_logs(self):
        found = []
        for item in self.traced:
            path = self.directory / (item["service"] + ".log")
            line = next(
                (l for l in path.read_text(errors="replace").splitlines()
                 if item["correlation_id"] in l and '"route"' in l), None,
            )
            found.append({"label": item["label"], "log": str(path.relative_to(self.repo)),
                          "correlation_id": item["correlation_id"],
                          "line": json.loads(line) if line else None})
        for entry in found:
            self.log("k. línea de log por correlation_id", **entry)
        workers = []
        for name in ("donantes-worker.log", "auditoria-worker.log"):
            text = (self.directory / name).read_text(errors="replace").splitlines()
            workers.append({"log": name, "worker_failure": sum("worker_failure" in l for l in text)})
        self.log("k. errores registrados por los workers durante las caídas", workers=workers)
        return bool(found) and all(entry["line"] for entry in found)

    # ------------------------------------------------------------------- ejecución
    def cases(self):
        return (
            ("g_archivo_inexistente", self.case_archivo_inexistente),
            ("i_sin_permisos", self.case_sin_permisos),
            ("b_revocar_token", self.case_revocar_token),
            ("a_microservicio_detenido", self.case_microservicio),
            ("f_tiempo_agotado", self.case_tiempo_agotado),
            ("j_archivos_no_disponibles", self.case_archivos),
            ("c_redis", self.case_redis),
            ("d_mongodb", self.case_mongodb),
            ("e_postgresql", self.case_postgres),
            ("h_sobrecarga", self.case_sobrecarga),
            ("k_logs", self.case_logs),
        )

    def run(self, only=None):
        for user in ("donor1", "operator1", "operator2", "transport1", "auditor1"):
            assert self.login(user)["status"] == 200, user
        self.log("base: /health/ready", ready=self.ready())
        self.web = self.web_session("operator1")
        _, status, data = self.new_donor("TESTIGO")
        assert status["status"] == 201, status
        self.witness = {k: data[k] for k in ("id", "folio", "display_name", "version", "status")}
        self.log("testigo creado antes de los fallos", **status, testigo=self.witness["id"])
        result = {}
        for name, case in self.cases():
            if only and name not in only:
                continue
            started = time.monotonic()
            try:
                result[name] = bool(case())
            except Exception as exc:  # noqa: BLE001 - registrar y seguir con el resto
                result[name] = False
                self.log(name + ": excepción", error=type(exc).__name__, detail=str(exc)[:300])
            self.log(name + ": resultado", ok=result[name],
                     seconds=round(time.monotonic() - started, 1))
        seconds, ready = self.wait_all_ready()
        self.log("final: /health/ready", seconds_to_ready=seconds, ready=ready)
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", required=True)
    sub = parser.add_subparsers(dest="command", required=True)
    demo = sub.add_parser("demo")
    demo.add_argument("--out", required=True)
    single = sub.add_parser("caso", help="Un caso suelto (con testigo propio) para mostrarlo en vivo")
    single.add_argument("nombre", nargs="+", choices=[
        "g_archivo_inexistente", "i_sin_permisos", "b_revocar_token",
        "a_microservicio_detenido", "f_tiempo_agotado", "j_archivos_no_disponibles",
        "c_redis", "d_mongodb", "e_postgresql", "h_sobrecarga", "k_logs"])
    sub.add_parser("estado")
    base = sub.add_parser("detener-base")
    base.add_argument("base", choices=BASES)
    for name in ("pausar", "reanudar"):
        sub.add_parser(name).add_argument("servicio")
    args = parser.parse_args()
    runner = Demo(args.repo)
    if args.command == "estado":
        print(json.dumps(runner.ready(), indent=2))
    elif args.command == "detener-base":
        print(json.dumps(runner.stop_base(args.base)))
        print("Para restablecer: bash components.sh bases")
    elif args.command in ("pausar", "reanudar"):
        sig = signal.SIGSTOP if args.command == "pausar" else signal.SIGCONT
        print(args.command, args.servicio, "PID", runner.signal_service(args.servicio, sig))
    elif args.command == "caso":
        # k_logs solo tiene sentido después de otro caso: lo agrega siempre al final.
        result = runner.run(set(args.nombre) | {"k_logs"})
        print(json.dumps(result, indent=2))
        sys.exit(0 if all(result.values()) else 1)
    else:
        started = now().isoformat()
        result = runner.run()
        Path(args.out).write_text(json.dumps(
            {"started": started, "finished": now().isoformat(), "result": result,
             "steps": runner.steps}, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps(result, indent=2))
        sys.exit(0 if all(result.values()) else 1)


if __name__ == "__main__":
    main()
