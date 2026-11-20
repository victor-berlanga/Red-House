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
from scripts.load_workflows import (
    TransactionTrace,
    appointment_cycle,
    coordinator_cycle,
    inventory_cycle,
    medical_cycle,
    transport_cycle,
)

# Register error/quitting listeners before Locust emits init/test_start.
from tests import locust_sustained as timing
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
    if os.environ.get("REDHOUSE_LOAD_FINITE_ROLES") == "1":
        result["preflight"] = [
            {
                "method": e.method,
                "name": e.name,
                "requests": e.num_requests,
                "failures": e.num_failures,
            }
            for e in environment.stats.entries.values()
        ]
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
            self.client,
            state["urls"],
            mime=account["mime"],
            cache_observer=observer,
            # Las cuentas creadas por la prueba no siguen el prefijo donor*/transport*.
            app_client="mobile" if self.role in ("DONOR", "TRANSPORT") else "web",
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


FINITE_PROFILES = {
    "medical2": "MEDICAL",
    "coordinator1": "COORDINATOR",
    "transport1": "TRANSPORT",
}
FINITE_WORKFLOWS = {
    "MEDICAL": medical_cycle,
    "COORDINATOR": coordinator_cycle,
    "TRANSPORT": transport_cycle,
}


def finite_manifest(state, manifest):
    """A finite, disjoint inventory prepared outside timing; never recycle a case."""
    if (
        manifest.get("directory") != state["directory"]
        or manifest.get("schema_version") != 22
        or manifest.get("kind") != "finite-three-roles-v1"
        or manifest.get("gps") is not False
        or manifest.get("preparation_complete") is not True
    ):
        raise ValueError("finite_fixture_invalid")
    rows = manifest.get("accounts", [])
    if len(rows) != 3 or {r["username"]: r["role"] for r in rows} != FINITE_PROFILES:
        raise ValueError("finite_accounts_invalid")
    ids, resources, case_ids = set(), set(), set()
    for row in rows:
        expected = state["accounts"][row["username"]]
        if (
            any(row[k] != expected[k] for k in ("id", "tenant_id", "role"))
            or row["id"] in ids
        ):
            raise ValueError("finite_identity_changed")
        ids.add(row["id"])
        if row["mime"] != (
            "application/json" if row["role"] == "TRANSPORT" else "application/xml"
        ):
            raise ValueError("finite_representation_invalid")
        cases = manifest["cases"][row["role"]]
        if len(cases) != 3:
            raise ValueError("finite_inventory_incomplete")
        for case in cases:
            if (
                case["case_id"] in case_ids
                or case["resource_id"] in resources
                or not case.get("approved_reason")
            ):
                raise ValueError("finite_inventory_not_disjoint")
            resources.add(case["resource_id"])
            case_ids.add(case["case_id"])
    return rows


class FiniteRoleUser(HttpUser):
    """Three connected identities, exactly two measured cases each; not capacity."""

    wait_time = between(3, 5)
    issued = 0

    def on_start(self):
        global _logged_in
        self.trace = None
        self.preflight_done = False
        self.next_case = 1
        self.exhausted = False
        if (
            os.environ.get("REDHOUSE_LOAD_FINITE_ROLES") != "1"
            or os.environ.get("REDHOUSE_LOAD_ISOLATED") != "1"
            or os.environ.get("REDHOUSE_LOAD_USERS") != "3"
            or os.environ.get("REDHOUSE_LOAD_MEASURE_SECONDS") != "120"
            or isinstance(self.environment.runner, WorkerRunner)
        ):
            raise ValueError("finite_scope_invalid")
        path = Path(os.environ["REDHOUSE_LOAD_STATE"]).resolve()
        state = json.loads(path.read_text())
        if Path(state["directory"]).resolve() != path.parent:
            raise ValueError("foreign_load_state")
        fixture = Path(os.environ["REDHOUSE_LOAD_FINITE_MANIFEST"]).resolve()
        if fixture.parent != path.parent:
            raise ValueError("foreign_finite_manifest")
        manifest = json.loads(fixture.read_text())
        accounts = finite_manifest(state, manifest)
        index = type(self).issued
        type(self).issued += 1
        if index >= 3:
            raise ValueError("finite_user_limit")
        self.account = account = accounts[index]
        self.role, self.profile = account["role"], account["username"]
        self.cases = manifest["cases"][self.role]
        self.client.trust_env = False
        self.api = LoadSession(
            self.client,
            state["urls"],
            mime=account["mime"],
            cache_observer=timing.observe_cache,
        )
        cleanup_for(self.environment).add(self.api, self.client)
        factors = timing.ephemeral_factors()

        # Closure holds secrets in memory only. TransactionTrace never receives this body/result.
        def reauthenticate(challenge, operation, resource_id):
            from ms_identidad_acceso.strong_auth import totp

            with timing._mfa_locks[self.profile]:
                started = time.monotonic()
                counter = timing.next_mfa_counter(self.profile)
                waiting = (time.monotonic() - started) * 1000
                data = self.api.request(
                    "identidad_acceso",
                    "/api/v1/auth/reauthentication-proofs",
                    "Seguridad / Confirmar acción",
                    method="POST",
                    body={
                        "password": state["password"],
                        "otp": totp(factors[self.profile], counter),
                        "challenge": challenge,
                    },
                    check=lambda r: (
                        r["operation"] == operation
                        and r["resource_id"] == resource_id
                        and r["expires_in"] > 0
                        and bool(r["proof"])
                    ),
                )
                return data["proof"], waiting

        try:
            if self.profile in factors:
                from ms_identidad_acceso.strong_auth import totp

                with timing._mfa_locks[self.profile]:
                    counter = timing.next_mfa_counter(self.profile)
                    self.api.login(
                        self.profile,
                        state["password"],
                        otp=totp(factors[self.profile], counter),
                    )
            else:
                self.api.login(self.profile, state["password"])
            if any(
                self.api.user[k] != account[k]
                for k in ("id", "tenant_id", "role", "username")
            ):
                raise LoadFailure("finite_login_identity")
            self.trace = TransactionTrace(
                self.api,
                Path(os.environ["REDHOUSE_LOAD_MARKER"]).parent
                / ("attempts-" + account["id"] + ".jsonl"),
                account,
                lambda: _stage if self.preflight_done else "preflight",
                reauthenticate,
            )
            self.trace.replay_remaining = 0
            self.run_case(self.cases[0])
            self.preflight_done = True
            self.trace.replay_remaining = 1
            _logged_in += 1
            if _logged_in == 3:
                gevent.spawn(measured_transactions, self.environment)
            _ready.wait()
        except BaseException as exc:
            self.environment.process_exit_code = 1
            # A failed startup still owns a session; compensate before stopping peers.
            self.environment._redhouse_load_cleanup.schedule_close(
                self.api, self.client
            )
            gevent.spawn(self.environment.runner.quit)
            if not isinstance(exc, Exception):
                raise
            raise StopUser() from None

    def run_case(self, case):
        global _active
        _active += 1
        begin = time.perf_counter()
        error = None
        try:
            self.trace.begin()
            self.trace.emit(
                "case_start", case_id=case["case_id"], resource_id=case["resource_id"]
            )
            FINITE_WORKFLOWS[self.role](self.trace, case)
        except BaseException as exc:  # noqa: BLE001 - interruption must retain trace and close owned sessions
            error = LoadFailure(
                "finite_cycle_"
                + (str(exc) if isinstance(exc, LoadFailure) else type(exc).__name__)
            )
            raise error from None
        finally:
            elapsed = (time.perf_counter() - begin) * 1000
            self.trace.emit(
                "case_timing",
                elapsed_ms=elapsed,
                mfa_wait_ms=self.trace.mfa_wait_ms,
                excluding_mfa_wait_ms=max(0, elapsed - self.trace.mfa_wait_ms),
            )
            self.trace.end(error)
            _active -= 1
            self.environment.events.request.fire(
                request_type="PREFLIGHT"
                if not self.preflight_done
                else "DRAIN"
                if _stage == "drain"
                else "TRANSACTION",
                name="Recorrido finito / " + self.role,
                response_time=elapsed,
                response_length=0,
                exception=error,
                context={},
            )

    @task
    def finite_case(self):
        global _active
        if self.environment.runner.state not in (STATE_RUNNING, STATE_SPAWNING):
            raise StopUser()
        _admit.wait()
        if _stage not in ("warmup", "measuring"):
            raise StopUser()
        if _stage == "warmup":
            case = self.cases[0]
            service, path, canonical = (
                (
                    "receptores",
                    "/api/v1/requests/" + case["request_id"],
                    "/api/v1/requests/{identifier}",
                )
                if self.role == "MEDICAL"
                else (
                    "inventario",
                    "/api/v1/reservations/" + case["reservation_id"],
                    "/api/v1/reservations/{identifier}",
                )
                if self.role == "COORDINATOR"
                else (
                    "transporte",
                    "/api/v1/shipments/" + case["shipment_id"],
                    "/api/v1/shipments/{identifier}",
                )
            )
            _active += 1
            try:
                self.api.request(
                    service,
                    path,
                    "Calentamiento finito / " + self.role,
                    canonical=canonical,
                )
            finally:
                _active -= 1
            return
        if self.next_case >= 3:
            if not self.exhausted:
                self.trace.emit("batch_exhausted", measured_cases=2)
                self.exhausted = True
            return
        case = self.cases[self.next_case]
        self.next_case += (
            1  # Any uncertain outcome ends this actor, never creates another command.
        )
        try:
            self.run_case(case)
        except LoadFailure:
            self.environment.process_exit_code = 1
            raise StopUser() from None

    def on_stop(self):
        diagnostic = getattr(
            getattr(self, "api", None), "last_challenge_diagnostic", None
        )
        if diagnostic and self.trace:
            self.trace.emit("challenge_contract_diagnostic", metadata=diagnostic)
            self.api.last_challenge_diagnostic = None
        cleanup = getattr(self.environment, "_redhouse_load_cleanup", None)
        if cleanup is not None and getattr(self, "api", None) is not None:
            cleanup.schedule_close(self.api, self.client)
        if self.trace:
            self.trace.close()
