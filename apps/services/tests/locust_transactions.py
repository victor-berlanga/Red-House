"""Citas e inventario sintéticos; un proceso, una cuenta preparada por usuario."""

import json
import os
import sys
import time
from pathlib import Path

from locust import HttpUser, between, task
from locust.exception import StopUser
from locust.runners import STATE_RUNNING, STATE_SPAWNING, WorkerRunner

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.load_client import LoadFailure, LoadSession
from scripts.load_workflows import appointment_cycle, inventory_cycle

from tests.load_cleanup import cleanup_for

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
        cleanup_for(self.environment).add(self.api, self.client)
        try:
            self.api.login(account["username"], state["password"])
            if self.api.user["role"] != self.role:
                raise ValueError("Perfil sintético inesperado.")
        except LoadFailure:
            raise StopUser() from None

    @task
    def business_cycle(self):
        if self.environment.runner.state not in (STATE_RUNNING, STATE_SPAWNING):
            # A queued task may reach this method while the runner is stopping.
            # Start no new transaction; an already-started one still reports failure
            # if it is interrupted below, including an uncertain write.
            raise StopUser()
        started = time.perf_counter()
        error = None
        try:
            self.workflow(self.api, self.campaign)
        except LoadFailure as exc:
            error = exc
        except BaseException as exc:
            # Keep the exception class, never its message or response contents.
            # Interruptions remain failures; shutdown must not hide partial writes.
            error = LoadFailure("workflow_interrupted_" + type(exc).__name__)
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
        # La limpieza de red ocurre en test_stop, fuera de esta greenlet.
        pass
