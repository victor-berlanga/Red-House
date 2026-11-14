"""Línea base de consultas por rol; solo laboratorio explícito de loopback."""

import json
import os
import sys
from pathlib import Path

from locust import HttpUser, between, task
from locust.exception import StopUser
from locust.runners import STATE_RUNNING, STATE_SPAWNING

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.load_client import LoadFailure, LoadSession

from tests.load_cleanup import cleanup_for

PROFILES = ("medical2", "operator1", "coordinator1", "auditor1", "donor1", "transport1")
OPERATIONS = {
    "medical2": [
        ("inventario", "/api/v1/availability", "Disponibilidad regional"),
        ("receptores", "/api/v1/requests", "Solicitudes propias"),
    ],
    "operator1": [
        ("inventario", "/api/v1/resources", "Inventario propio"),
        ("donantes", "/api/v1/campaigns", "Campañas"),
    ],
    "coordinator1": [
        ("priorizacion_geografia", "/api/v1/routes", "Rutas"),
        ("transporte", "/api/v1/shipments", "Traslados"),
        ("monitoreo", "/api/v1/status", "Estado regional"),
    ],
    "auditor1": [("auditoria", "/api/v1/events", "Bitácora")],
    "donor1": [
        ("donantes", "/api/v1/appointments/agenda", "Agenda propia"),
        ("alertas", "/api/v1/alerts", "Avisos propios"),
    ],
    "transport1": [
        ("transporte", "/api/v1/shipments", "Tareas propias"),
        ("alertas", "/api/v1/alerts", "Avisos de traslado"),
    ],
}


class RegionalUser(HttpUser):
    wait_time = between(0.5, 1.5)
    issued = 0

    def on_start(self):
        self.api = None
        if os.environ.get("REDHOUSE_LOAD_ISOLATED") != "1":
            raise ValueError("Indica REDHOUSE_LOAD_ISOLATED=1 para el laboratorio.")
        path = Path(os.environ["REDHOUSE_LOAD_STATE"]).resolve()
        state = json.loads(path.read_text())
        if Path(state["directory"]).resolve() != path.parent:
            raise ValueError("El estado no corresponde al directorio del laboratorio.")
        self.profile = PROFILES[type(self).issued % len(PROFILES)]
        type(self).issued += 1
        self.api = LoadSession(
            self.client,
            state["urls"],
            mime="application/xml"
            if self.profile == "operator1"
            else "application/json",
            no_cache=os.environ.get("REDHOUSE_LOAD_NO_CACHE") == "1",
        )
        cleanup_for(self.environment).add(self.api, self.client)
        try:
            self.api.login(self.profile, state["password"])
        except LoadFailure:
            raise StopUser() from None

    @task
    def regional_workflow(self):
        if self.environment.runner.state not in (STATE_RUNNING, STATE_SPAWNING):
            raise StopUser()
        try:
            for service, path, name in OPERATIONS[self.profile]:
                query = "" if path == "/api/v1/status" else "?page_size=20"
                data = self.api.request(service, path + query, f"{service} / {name}")
                if service == "transporte" and data.get("items"):
                    identifier = data["items"][0]["id"]
                    self.api.request(
                        service,
                        "/api/v1/shipments/" + identifier,
                        "transporte / Detalle autorizado desde listado",
                        canonical="/api/v1/shipments/{identifier}",
                    )
            if self.profile == "donor1":
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

    def on_stop(self):
        # La revocación ocurre en test_stop tras detener los usuarios.
        pass
