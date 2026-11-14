"""Citas e inventario sintéticos; un proceso, una cuenta preparada por usuario."""

import json
import os
import sys
import time
from pathlib import Path

import gevent
from gevent.event import Event
from locust import HttpUser, between, task
from locust.exception import StopUser
from locust.runners import STATE_RUNNING, STATE_SPAWNING, WorkerRunner

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.load_client import LoadFailure, LoadSession
from scripts.load_workflows import TransactionTrace, appointment_cycle, inventory_cycle

from tests.load_cleanup import cleanup_for

WORKFLOWS = {"DONOR": appointment_cycle, "OPERATOR": inventory_cycle}
_ready = Event()
_admit = Event()
_logged_in = 0
_active = 0
_stage = "starting"


def drain_cycles(timeout=30):
    deadline = time.monotonic() + timeout
    while _active:
        if time.monotonic() >= deadline:
            raise RuntimeError("transaction_drain_timeout")
        gevent.sleep(0.05)


def measured_transactions(environment):
    """Misma temporización/estadísticas; frontera de ciclos para separar escrituras."""
    from tests import locust_sustained as timing

    global _stage
    path = Path(os.environ["REDHOUSE_LOAD_MARKER"])
    result = {"stage": "warmup"}
    try:
        environment.stats.reset_all()
        started = time.monotonic()
        result["started"] = started
        _stage = "warmup"
        _admit.set()
        _ready.set()
        timing.write_marker(path, result)
        result["warmup_min_users"] = timing.observe_users(environment, 30)
        _admit.clear()
        _stage = "warmup_drain"
        drain_cycles()
        result["warmup"] = {
            "requests": sum(e.num_requests for e in environment.stats.entries.values()),
            "failures": sum(e.num_failures for e in environment.stats.entries.values()),
        }
        environment.stats.reset_all()
        timing._cache.clear()
        timing._http.clear()
        measured = time.monotonic()
        result.update(stage="measuring", measured=measured)
        timing.write_marker(path, result)
        _stage = "measuring"
        _admit.set()
        result["measurement_min_users"] = timing.observe_users(
            environment, int(os.environ["REDHOUSE_LOAD_MEASURE_SECONDS"])
        )
        _admit.clear()
        _stage = "drain"
        finished = time.monotonic()
        result.update(
            finished=finished,
            measurement=timing.snapshot_stats(environment, finished - measured),
            cache=dict(timing._cache),
            http=dict(timing._http),
        )
        # Snapshot precedes drain: its HTTP and completed transactions are excluded.
        drain_cycles()
        result.update(
            stage="finished", drained=time.monotonic(), user_errors=timing._user_errors
        )
    except BaseException as error:  # noqa: BLE001 - interruption must preserve marker and close sessions
        result.update(stage="interrupted", error_type=type(error).__name__)
        environment.process_exit_code = 1
    finally:
        _admit.clear()
        _stage = "finished"
        timing.write_marker(path, result)
        environment.runner.quit()


class TransactionUser(HttpUser):
    wait_time = between(0.5, 1.5)
    issued = 0

    def on_start(self):
        global _logged_in
        self.api = None
        self.trace = None
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
        self.sustained = os.environ.get("REDHOUSE_LOAD_TRANSACTIONAL") == "1"
        self.profile_id = state.get("load_profile") if self.sustained else None
        observer = None
        if self.sustained:
            from tests import locust_sustained as timing

            observer = timing.observe_cache
            if len(state["load_accounts"]) != 12 or not self.profile_id:
                raise ValueError("Fixture sostenida incompleta")
            self.wait_time = between(4, 6).__get__(self, type(self))
        self.client.trust_env = False
        self.api = LoadSession(
            self.client, state["urls"], mime=account["mime"], cache_observer=observer
        )
        cleanup_for(self.environment).add(self.api, self.client)
        try:
            self.api.login(account["username"], state["password"])
            if self.api.user["role"] != self.role:
                raise ValueError("Perfil sintético inesperado.")
            if self.sustained:
                if any(
                    self.api.user[k] != account[k]
                    for k in ("id", "tenant_id", "username")
                ):
                    raise ValueError("Identidad sintética ajena")
                self.trace = TransactionTrace(
                    self.api,
                    Path(os.environ["REDHOUSE_LOAD_MARKER"]).parent
                    / ("attempts-" + account["id"] + ".jsonl"),
                    account,
                    lambda: _stage,
                )
                _logged_in += 1
                if _logged_in == 12:
                    gevent.spawn(measured_transactions, self.environment)
                _ready.wait()
        except LoadFailure:
            raise StopUser() from None

    @task
    def business_cycle(self):
        global _active
        if self.environment.runner.state not in (STATE_RUNNING, STATE_SPAWNING):
            # A queued task may reach this method while the runner is stopping.
            # Start no new transaction; an already-started one still reports failure
            # if it is interrupted below, including an uncertain write.
            raise StopUser()
        if self.sustained:
            _admit.wait()
            if _stage not in ("warmup", "measuring"):
                raise StopUser()
        _active += 1
        started = time.perf_counter()
        error = None
        try:
            if self.trace:
                self.trace.begin()
            api = self.trace or self.api
            if self.role == "OPERATOR":
                inventory_cycle(api, self.campaign, profile_id=self.profile_id)
            else:
                self.workflow(api, self.campaign)
        except LoadFailure as exc:
            error = exc
        except BaseException as exc:
            # Keep the exception class, never its message or response contents.
            # Interruptions remain failures; shutdown must not hide partial writes.
            error = LoadFailure("workflow_interrupted_" + type(exc).__name__)
            raise
        finally:
            try:
                if self.trace:
                    self.trace.end(error)
            finally:
                _active -= 1
            self.environment.events.request.fire(
                request_type="DRAIN"
                if self.sustained and _stage in ("drain", "warmup_drain")
                else "TRANSACTION",
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
        if self.trace:
            self.trace.close()
