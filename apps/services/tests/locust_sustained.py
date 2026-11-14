"""Lecturas reales con MFA de laboratorio entregado solo por descriptor anónimo."""

import json
import os
import time
from collections import Counter
from pathlib import Path

import gevent
from gevent.event import Event
from gevent.lock import Semaphore
from locust import events
from locust.exception import StopUser
from locustfile import PROFILES, RegionalUser
from ms_identidad_acceso.strong_auth import totp
from scripts.load_client import LoadFailure, LoadSession

from tests.load_cleanup import cleanup_for

_secrets = None
_logged_in = 0
_user_errors = 0
_ready = Event()
_mfa_locks = {name: Semaphore() for name in ("medical2", "coordinator1")}
_mfa_last = {}
_cache = Counter()
_http = Counter()


def observe_cache(value, status):
    if value in ("HIT", "MISS", "BYPASS"):
        _cache[value] += 1
    if status == 429:
        _http["quota_429"] += 1


def mark_logged_in(total):
    global _logged_in
    if total not in (6, 12, 24, 36) or _logged_in >= total:
        raise ValueError("Barrera de sesiones inválida")
    _logged_in += 1
    if _logged_in == total:
        _ready.set()
        return True
    return False


def next_mfa_counter(profile):
    previous = max(
        _mfa_last.get(profile, -1), int(os.environ.get("REDHOUSE_LOAD_MFA_AFTER", "-1"))
    )
    while int(time.time()) // 30 <= previous:
        gevent.sleep(0.25)
    counter = int(time.time()) // 30
    _mfa_last[profile] = counter
    return counter


@events.user_error.add_listener
def record_user_error(**_kwargs):
    global _user_errors
    _user_errors += 1


@events.quitting.add_listener
def enforce_final_user_errors(environment, **_kwargs):
    # Locust calcula el código antes de su runner.quit final; detener primero
    # asegura que cualquier error durante el drenado también sea observable.
    if environment.runner:
        environment.runner.stop()
    if _user_errors:
        environment.process_exit_code = 1


def observe_users(environment, seconds):
    until = time.monotonic() + seconds
    minimum = environment.runner.user_count
    while time.monotonic() < until:
        gevent.sleep(min(1, max(0, until - time.monotonic())))
        minimum = min(minimum, environment.runner.user_count)
    return minimum


def snapshot_stats(environment, duration):
    return [
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
        }
        for entry in environment.stats.entries.values()
    ]


def write_marker(path, payload):
    temporary = path.with_suffix(".new")
    temporary.write_text(json.dumps(payload))
    temporary.chmod(0o600)
    os.replace(temporary, path)


def measured_cycle(environment):
    marker = Path(os.environ["REDHOUSE_LOAD_MARKER"])
    started = time.monotonic()
    write_marker(marker, {"stage": "warmup", "started": started})
    warmup_min_users = observe_users(environment, 30)
    warmup = {
        "requests": sum(
            entry.num_requests for entry in environment.stats.entries.values()
        ),
        "failures": sum(
            entry.num_failures for entry in environment.stats.entries.values()
        ),
    }
    environment.stats.reset_all()
    measured = time.monotonic()
    write_marker(
        marker,
        {
            "stage": "measuring",
            "started": started,
            "measured": measured,
            "warmup": warmup,
        },
    )
    _cache.clear()
    _http.clear()
    measurement_min_users = observe_users(
        environment, int(os.environ.get("REDHOUSE_LOAD_MEASURE_SECONDS", "120"))
    )
    finished = time.monotonic()
    measurement = snapshot_stats(environment, finished - measured)
    write_marker(
        marker,
        {
            "stage": "finished",
            "started": started,
            "measured": measured,
            "finished": finished,
            "warmup": warmup,
            "warmup_min_users": warmup_min_users,
            "measurement_min_users": measurement_min_users,
            "user_errors": _user_errors,
            "cache": dict(_cache),
            "http": dict(_http),
            "measurement": measurement,
        },
    )
    environment.runner.quit()


def ephemeral_factors():
    global _secrets
    if _secrets is None:
        descriptor = int(os.environ.pop("REDHOUSE_LOAD_MFA_FD"))
        with os.fdopen(descriptor, "r") as source:
            _secrets = json.load(source)
        if set(_secrets) != {"medical2", "coordinator1"}:
            raise ValueError("Factores sintéticos incompletos")
    return _secrets


class SustainedUser(RegionalUser):
    issued = 0

    def on_start(self):
        self.api = None
        if os.environ.get("REDHOUSE_LOAD_ISOLATED") != "1":
            raise ValueError("Laboratorio aislado requerido")
        path = Path(os.environ["REDHOUSE_LOAD_STATE"]).resolve()
        state = json.loads(path.read_text())
        if Path(state["directory"]).resolve() != path.parent:
            raise ValueError("Estado ajeno al laboratorio")
        self.profile = PROFILES[type(self).issued % len(PROFILES)]
        type(self).issued += 1
        self.client.trust_env = False
        self.api = LoadSession(
            self.client,
            state["urls"],
            mime="application/xml"
            if self.profile == "operator1"
            else "application/json",
            no_cache=os.environ.get("REDHOUSE_LOAD_NO_CACHE") == "1",
            cache_observer=observe_cache,
        )
        cleanup_for(self.environment).add(self.api, self.client)
        factors = ephemeral_factors()
        try:
            if self.profile in factors:
                with _mfa_locks[self.profile]:
                    counter = next_mfa_counter(self.profile)
                    self.api.login(
                        self.profile,
                        state["password"],
                        otp=totp(factors[self.profile], counter),
                    )
            else:
                self.api.login(self.profile, state["password"])
        except LoadFailure:
            raise StopUser() from None
        if mark_logged_in(int(os.environ.get("REDHOUSE_LOAD_USERS", "6"))):
            gevent.spawn(measured_cycle, self.environment)
        _ready.wait()
