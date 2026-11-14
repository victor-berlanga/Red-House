"""Citas e inventario sintéticos; un proceso, una cuenta preparada por usuario."""

import json
import os
from pathlib import Path
import sys
import time

from locust import HttpUser, between, task
from locust.exception import StopUser
from locust.runners import WorkerRunner

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.load_client import LoadFailure, LoadSession
from scripts.load_workflows import appointment_cycle, inventory_cycle

WORKFLOWS = {"DONOR": appointment_cycle, "OPERATOR": inventory_cycle}


class TransactionUser(HttpUser):
    wait_time = between(0.5, 1.5)
    issued = 0

    def on_start(self):
        self.api = None
        if os.environ.get("REDHOUSE_LOAD_ISOLATED") != "1" or isinstance(
            self.environment.runner, WorkerRunner
        ):
            raise ValueError(
                "Este arnés requiere laboratorio aislado y un único proceso."
            )
        path = Path(os.environ["REDHOUSE_LOAD_STATE"]).resolve()
        state = json.loads(path.read_text())
        if Path(state["directory"]).resolve() != path.parent:
            raise ValueError("Estado ajeno al directorio del laboratorio.")
        index = type(self).issued
        type(self).issued += 1
        if index >= len(state["load_accounts"]):
            raise ValueError("Faltan cuentas sintéticas independientes para la carga.")
        account = state["load_accounts"][index]
        self.role = account["role"]
        self.workflow = WORKFLOWS[self.role]
        self.campaign = state["load_campaign"]
        self.api = LoadSession(self.client, state["urls"], mime=account["mime"])
        try:
            self.api.login(account["username"], state["password"])
            if self.api.user["role"] != self.role:
                self.api.close()
                raise ValueError("Perfil sintético inesperado.")
        except LoadFailure:
            raise StopUser() from None

    @task
    def business_cycle(self):
        started = time.perf_counter()
        error = None
        try:
            self.workflow(self.api, self.campaign)
        except LoadFailure as exc:
            error = exc
        except BaseException:
            error = LoadFailure("workflow_interrupted_or_invalid")
            raise
        finally:
            self.environment.events.request.fire(
                request_type="TRANSACTION",
                name="Recorrido / " + self.role,
                response_time=(time.perf_counter() - started) * 1000,
                response_length=0,
                exception=error,
                context={},
            )
        if error:
            # No repeat with a new key after an uncertain write. Keep any
            # partially completed fixture records for reconciliation/reporting.
            raise StopUser() from None

    def on_stop(self):
        if self.api:
            try:
                self.api.close()
            except LoadFailure:
                pass
        self.client.close()
