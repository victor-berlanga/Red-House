"""Varios perfiles y consultas reales. Credenciales únicamente en state.json privado."""

import json
import os
import random
from pathlib import Path

from locust import HttpUser, between, task


class RegionalUser(HttpUser):
    wait_time = between(0.5, 1.5)
    issued = 0

    def on_start(self):
        state = json.loads(Path(os.environ["REDHOUSE_LOAD_STATE"]).read_text())
        self.urls = state["urls"]
        profiles = ["medical2", "operator1", "coordinator1", "auditor1", "donor1"]
        self.profile = profiles[type(self).issued % len(profiles)]
        type(self).issued += 1
        with self.client.post(
            self.urls["identidad_acceso"] + "/api/v1/auth/login",
            name="Identidad / login",
            json={"username": self.profile, "password": state["password"]},
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure("login_rejected")
                return
            self.token = response.json()["data"]["access_token"]

    @task
    def regional_workflow(self):
        if not hasattr(self, "token"):
            return
        operations = {
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
                ("donantes", "/api/v1/campaigns", "Campañas donante"),
                ("donantes", "/api/v1/appointments", "Citas propias"),
                ("alertas", "/api/v1/alerts", "Avisos propios"),
            ],
        }
        headers = {
            "Authorization": "Bearer " + self.token,
            "Accept": "application/xml"
            if self.profile == "operator1"
            else "application/json",
        }
        if os.environ.get("REDHOUSE_LOAD_NO_CACHE") == "1":
            headers["Cache-Control"] = "no-cache"
        for service, path, name in operations[self.profile]:
            self.client.get(
                self.urls[service] + path, name=f"{service} / {name}", headers=headers
            )
