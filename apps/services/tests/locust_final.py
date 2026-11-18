"""Carga final: una identidad sintética distinta por usuario Locust (INC-436).

Solo corre contra un laboratorio desechable creado por ``scripts/load_final.py``.
Dos modos (``REDHOUSE_LOAD_MODE``):

- ``reads``: repite las operaciones de lectura de la serie sostenida
  (``tests/locustfile.py``), pero cada usuario usa su propia cuenta del rol.
- ``mixed``: perfiles diferenciados (consulta web, móvil donante, móvil
  transportista, escritorio XML con reportes, panel de auditoría y monitoreo, y
  un proceso automático de sondeo de salud).

Las cuentas, la contraseña sintética del laboratorio y los factores MFA nunca se
escriben en las estadísticas; los secretos MFA llegan por un descriptor anónimo.
"""

import contextlib
import json
import os
import sys
import time
from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import gevent
from gevent.event import Event
from locust import HttpUser, between, constant, events, task
from locust.exception import StopUser
from locust.runners import STATE_RUNNING, STATE_SPAWNING

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from locustfile import OPERATIONS

from ms_identidad_acceso.strong_auth import totp
from scripts.load_client import LoadFailure, LoadSession
from scripts.load_workflows import appointment_cycle, inventory_cycle

READ_PROFILES = {
    "medical2": "MEDICAL",
    "operator1": "OPERATOR",
    "coordinator1": "COORDINATOR",
    "auditor1": "AUDITOR",
    "donor1": "DONOR",
    "transport1": "TRANSPORT",
}
READ_ORDER = tuple(READ_PROFILES)

_state = None
_fixture = None
_secrets = None
_taken = Counter()
_logged_in = 0
_login_failures = 0
_ready = Event()
_cache = Counter()
_http = Counter()
_user_errors = 0


def state():
    global _state, _fixture
    if _state is None:
        if os.environ.get("REDHOUSE_LOAD_ISOLATED") != "1":
            raise ValueError("Laboratorio aislado requerido")
        path = Path(os.environ["REDHOUSE_LOAD_STATE"]).resolve()
        value = json.loads(path.read_text())
        if Path(value["directory"]).resolve() != path.parent:
            raise ValueError("Estado ajeno al laboratorio")
        fixture = json.loads((path.parent / "final-fixture.json").read_text())
        if fixture["directory"] != value["directory"]:
            raise ValueError("Fixture ajena al laboratorio")
        _state, _fixture = value, fixture
    return _state, _fixture


def secrets():
    global _secrets
    if _secrets is None:
        descriptor = int(os.environ.pop("REDHOUSE_LOAD_MFA_FD"))
        with os.fdopen(descriptor, "r") as source:
            _secrets = json.load(source)
    return _secrets


def take(role):
    """Entrega la siguiente cuenta libre del rol; nunca comparte identidad."""
    _, fixture = state()
    pool = fixture["accounts"][role]
    index = _taken[role]
    if index >= len(pool):
        raise ValueError("Cuentas sintéticas insuficientes para " + role)
    _taken[role] += 1
    return pool[index]


def observe_cache(value, status):
    if value in ("HIT", "MISS", "BYPASS"):
        _cache[value] += 1
    _http[str(status)] += 1


@events.user_error.add_listener
def record_user_error(**_kwargs):
    global _user_errors
    _user_errors += 1


def arrive(environment, ok):
    global _logged_in, _login_failures
    if ok:
        _logged_in += 1
    else:
        _login_failures += 1
    if _logged_in + _login_failures >= int(os.environ["REDHOUSE_LOAD_USERS"]):
        _ready.set()


def snapshot(environment, duration):
    rows = []
    for entry in list(environment.stats.entries.values()) + [environment.stats.total]:
        rows.append(
            {
                "method": entry.method,
                "name": entry.name,
                "requests": entry.num_requests,
                "failures": entry.num_failures,
                "requests_per_second": entry.num_requests / duration,
                "mean_ms": entry.avg_response_time,
                "median_ms": entry.median_response_time,
                "p95_ms": entry.get_response_time_percentile(0.95),
                "p99_ms": entry.get_response_time_percentile(0.99),
                "max_ms": entry.max_response_time,
            }
        )
    errors = [
        {
            "method": e.method,
            "name": e.name,
            "error": str(e.error)[:120],
            "occurrences": e.occurrences,
        }
        for e in environment.stats.errors.values()
    ]
    return rows, errors


def write_marker(payload):
    path = Path(os.environ["REDHOUSE_LOAD_MARKER"])
    temporary = path.with_suffix(".new")
    temporary.write_text(json.dumps(payload, indent=2))
    temporary.chmod(0o600)
    os.replace(temporary, path)


def measured_cycle(environment):
    started = time.monotonic()
    users = int(os.environ["REDHOUSE_LOAD_USERS"])
    _ready.wait(timeout=150)
    barrier = time.monotonic()
    write_marker({"stage": "warmup", "logged_in": _logged_in})
    warmup = int(os.environ.get("REDHOUSE_LOAD_WARMUP_SECONDS", "30"))
    gevent.sleep(warmup)
    warm = environment.stats.total
    warmup_stats = {"requests": warm.num_requests, "failures": warm.num_failures}
    environment.stats.reset_all()
    _cache.clear()
    _http.clear()
    measured = time.monotonic()
    write_marker({"stage": "measuring", "logged_in": _logged_in})
    seconds = int(os.environ["REDHOUSE_LOAD_MEASURE_SECONDS"])
    minimum = environment.runner.user_count
    until = measured + seconds
    while time.monotonic() < until:
        gevent.sleep(min(1, max(0, until - time.monotonic())))
        minimum = min(minimum, environment.runner.user_count)
    finished = time.monotonic()
    rows, errors = snapshot(environment, finished - measured)
    write_marker(
        {
            "stage": "finished",
            "mode": os.environ["REDHOUSE_LOAD_MODE"],
            "users": users,
            "logged_in": _logged_in,
            "login_failures": _login_failures,
            "distinct_identities": sum(_taken.values()),
            "identities_by_role": dict(_taken),
            "barrier_seconds": round(barrier - started, 3),
            "warmup_seconds": warmup,
            "warmup": warmup_stats,
            "measurement_seconds": round(finished - measured, 3),
            "measurement_min_users": minimum,
            "user_errors": _user_errors,
            "cache": dict(_cache),
            "http_status": dict(_http),
            "measurement": rows,
            "errors": errors,
        }
    )
    environment.runner.quit()


@events.test_start.add_listener
def start_cycle(environment, **_kwargs):
    gevent.spawn(measured_cycle, environment)


class Identified(HttpUser):
    abstract = True
    role = None
    mime = "application/json"
    profile = ""

    def login(self):
        st, _ = state()
        self.account = take(self.role)
        self.client.trust_env = False
        self.api = LoadSession(
            self.client,
            st["urls"],
            mime=self.mime,
            no_cache=os.environ.get("REDHOUSE_LOAD_NO_CACHE") == "1",
            cache_observer=observe_cache,
        )
        username = self.account["username"]
        otp = None
        factors = secrets()
        if username in factors:
            # Contador futuro aceptado por la ventana ±1; siempre mayor que el
            # contador consumido en la confirmación o en la fase anterior.
            otp = totp(factors[username], int(time.time()) // 30 + 1)
        try:
            self.api.login(username, st["password"], otp=otp)
        except LoadFailure:
            arrive(self.environment, False)
            raise StopUser() from None
        arrive(self.environment, True)
        _ready.wait()

    def on_start(self):
        self.api = None
        self.login()

    def on_stop(self):
        if self.api is not None:
            # La revocación ocurre fuera de la ventana medida.
            with contextlib.suppress(Exception):
                self.api.close()

    def get(self, service, path, label, **kwargs):
        return self.api.request(service, path, self.profile + " | " + label, **kwargs)

    def guard(self):
        if self.environment.runner.state not in (STATE_RUNNING, STATE_SPAWNING):
            raise StopUser()


# --- Modo reads: misma carga que la serie sostenida, identidad propia ---------


class ReadUser(Identified):
    """Mismas operaciones y espera que tests/locustfile.py (RegionalUser)."""

    wait_time = between(0.5, 1.5)
    issued = 0

    def on_start(self):
        self.api = None
        self.read_profile = READ_ORDER[type(self).issued % len(READ_ORDER)]
        type(self).issued += 1
        self.role = READ_PROFILES[self.read_profile]
        self.mime = (
            "application/xml"
            if self.read_profile == "operator1"
            else "application/json"
        )
        self.login()

    @task
    def regional_workflow(self):
        self.guard()
        try:
            for service, path, name in OPERATIONS[self.read_profile]:
                query = "" if path == "/api/v1/status" else "?page_size=20"
                data = self.api.request(service, path + query, f"{service} / {name}")
                if service == "transporte" and data.get("items"):
                    self.api.request(
                        service,
                        "/api/v1/shipments/" + data["items"][0]["id"],
                        "transporte / Detalle autorizado desde listado",
                        canonical="/api/v1/shipments/{identifier}",
                    )
            if self.read_profile == "donor1":
                page = self.api.request(
                    "donantes",
                    "/api/v1/public/campaign-feed?page_size=20",
                    "donantes / Feed público",
                    protected=False,
                )
                if page["total"] > page["page_size"]:
                    self.api.request(
                        "donantes",
                        "/api/v1/public/campaign-feed?page=2&page_size=20",
                        "donantes / Feed público página siguiente",
                        protected=False,
                    )
        except LoadFailure as exc:
            if str(exc) in ("session_unavailable", "http_401"):
                raise StopUser() from None


# --- Modo mixed: perfiles diferenciados ---------------------------------------


class ConsultaWeb(Identified):
    """Personal médico consultando en el portal (JSON, MFA)."""

    weight = 2
    role = "MEDICAL"
    profile = "Consulta web (médico)"
    wait_time = between(1, 3)

    @task
    def consultar(self):
        self.guard()
        try:
            self.get(
                "inventario",
                "/api/v1/availability?page_size=20",
                "Disponibilidad regional",
            )
            self.get(
                "receptores", "/api/v1/requests?page_size=20", "Solicitudes propias"
            )
            self.get("inventario", "/api/v1/summary", "Indicadores de inventario")
        except LoadFailure:
            pass


class MovilDonante(Identified):
    """App móvil del donante (JSON): consulta y registra citas."""

    weight = 3
    role = "DONOR"
    profile = "Móvil donante"
    wait_time = between(2, 5)

    @task(3)
    def consultar(self):
        self.guard()
        try:
            self.get(
                "donantes", "/api/v1/appointments/agenda?page_size=20", "Agenda propia"
            )
            self.get("alertas", "/api/v1/alerts?page_size=20", "Avisos propios")
            self.get("donantes", "/api/v1/donors?page_size=20", "Expediente propio")
        except LoadFailure:
            pass

    @task(1)
    def registrar_cita(self):
        self.guard()
        _, fixture = state()
        try:
            appointment_cycle(self.api, fixture["campaign_title"])
        except LoadFailure:
            pass


class MovilTransportista(Identified):
    """App móvil del transportista (JSON): tareas y avisos."""

    weight = 1
    role = "TRANSPORT"
    profile = "Móvil transportista"
    wait_time = between(2, 5)

    @task
    def consultar(self):
        self.guard()
        try:
            data = self.get(
                "transporte", "/api/v1/shipments?page_size=20", "Tareas propias"
            )
            if data.get("items"):
                self.get(
                    "transporte",
                    "/api/v1/shipments/" + data["items"][0]["id"],
                    "Detalle de traslado",
                    canonical="/api/v1/shipments/{identifier}",
                )
            self.get("alertas", "/api/v1/alerts?page_size=20", "Avisos de traslado")
        except LoadFailure:
            pass


class EscritorioOperador(Identified):
    """Consola de escritorio del operador (XML): inventario, registro y reportes."""

    weight = 2
    role = "OPERATOR"
    mime = "application/xml"
    profile = "Escritorio XML (operador)"
    wait_time = between(1, 3)

    @task(3)
    def consultar(self):
        self.guard()
        try:
            self.get(
                "inventario", "/api/v1/resources?page_size=20", "Inventario propio"
            )
            self.get("donantes", "/api/v1/campaigns?page_size=20", "Campañas")
            self.get(
                "documentos", "/api/v1/export-jobs?page_size=20", "Reportes solicitados"
            )
        except LoadFailure:
            pass

    @task(1)
    def registrar_unidad(self):
        self.guard()
        try:
            inventory_cycle(self.api, None)
        except LoadFailure:
            pass

    @task(1)
    def solicitar_reporte(self):
        """A lo sumo un reporte cada 120 s por operador (ritmo de escritorio).

        La extracción en segundo plano de Documentos pagina Inventario de 100 en
        100 con la identidad delegada del operador; un ritmo mayor agota su
        cuota HTTP por minuto (hallazgo documentado en la evidencia final).
        """
        self.guard()
        now = datetime.now(UTC)
        if time.monotonic() - getattr(self, "last_report", -1e9) < 120:
            self.consultar()
            return
        self.last_report = time.monotonic()
        try:
            job = self.get(
                "documentos",
                "/api/v1/export-jobs",
                "Solicitar reporte de inventario",
                method="POST",
                expected=202,
                key=str(uuid4()),
                body={
                    "report": "INVENTORY",
                    "subject_id": None,
                    "format": "CSV",
                    "from_at": (now - timedelta(days=30)).isoformat(),
                    "until_at": (now + timedelta(days=1)).isoformat(),
                    "order": "ID_ASC",
                    "filters": {},
                    "timezone": "America/Monterrey",
                },
            )
            self.get(
                "documentos",
                "/api/v1/export-jobs/" + job["id"],
                "Estado del reporte",
                canonical="/api/v1/export-jobs/{identifier}",
            )
        except LoadFailure:
            pass


class PanelAuditoria(Identified):
    """Auditor revisando bitácora, proyección documental y monitoreo (JSON)."""

    weight = 1
    role = "AUDITOR"
    profile = "Panel auditor/monitoreo"
    wait_time = between(2, 4)

    @task
    def revisar(self):
        self.guard()
        try:
            self.get("auditoria", "/api/v1/events?page_size=20", "Bitácora")
            self.get(
                "auditoria",
                "/api/v1/documentary-events?page_size=20",
                "Proyección documental",
            )
            self.get("auditoria", "/api/v1/findings?page_size=20", "Hallazgos")
            self.get("monitoreo", "/api/v1/status", "Estado regional")
            self.get("monitoreo", "/api/v1/checks?page_size=20", "Chequeos")
        except LoadFailure:
            pass


class ProcesoAutomatico(HttpUser):
    """Sondeo automático de salud de los doce servicios (sin sesión)."""

    fixed_count = 1
    wait_time = constant(5)

    def on_start(self):
        st, _ = state()
        self.client.trust_env = False
        self.urls = dict(st["urls"])
        arrive(self.environment, True)
        _ready.wait()

    @task
    def sondear(self):
        if self.environment.runner.state not in (STATE_RUNNING, STATE_SPAWNING):
            raise StopUser()
        for service, base in sorted(self.urls.items()):
            with self.client.get(
                base.rstrip("/") + "/health/ready",
                name="Proceso automático | /health/ready",
                timeout=(5, 10),
                catch_response=True,
            ) as response:
                _http[str(response.status_code)] += 1
                if response.status_code != 200:
                    response.failure("http_" + str(response.status_code))
