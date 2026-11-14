"""Pruebas sin motores del arnés sostenido y su frontera MFA."""

import errno
import importlib
import json
import signal
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from scripts.load_client import LoadSession
from scripts.load_guard import BudgetExceeded, CensusFailure

from scripts import sustained_read


def test_login_mfa_is_only_sent_in_request(monkeypatch):
    client = LoadSession(object(), {"identidad_acceso": "http://127.0.0.1:1234"})
    sent = {}

    def wire(*_args, **kwargs):
        sent.update(kwargs["body"])
        return {"user": {"username": "medical2", "active": True}}

    monkeypatch.setattr(client, "_wire", wire)
    monkeypatch.setattr(client, "_accept_tokens", lambda _data: None)
    client.login("medical2", "synthetic-password", otp="123456")
    assert sent == {
        "username": "medical2",
        "password": "synthetic-password",
        "otp": "123456",
    }
    assert not hasattr(client, "otp")


def test_warmup_failures_survive_stats_reset(tmp_path, monkeypatch):
    # This test invokes the controller directly and does not exercise gevent scheduling.
    monkeypatch.setenv("LOCUST_SKIP_MONKEY_PATCH", "1")
    tests_dir = Path(__file__).resolve().parent
    monkeypatch.syspath_prepend(str(tests_dir))
    module = importlib.import_module("locust_sustained")
    marker = tmp_path / "phase.json"
    monkeypatch.setenv("REDHOUSE_LOAD_MARKER", str(marker))
    times = iter((1.0, 31.0, 151.0))
    monkeypatch.setattr(module.time, "monotonic", lambda: next(times))
    monkeypatch.setattr(module, "observe_users", lambda _environment, _seconds: 6)
    monkeypatch.setattr(module, "_user_errors", 0)
    resets = []
    quits = []
    env = SimpleNamespace(
        stats=SimpleNamespace(
            entries={
                "one": SimpleNamespace(
                    num_requests=10,
                    num_failures=2,
                    method="GET",
                    name="synthetic",
                    avg_response_time=8,
                    median_response_time=9,
                    get_response_time_percentile=lambda q: 12 if q == 0.95 else 14,
                )
            },
            reset_all=lambda: resets.append(True),
        ),
        runner=SimpleNamespace(quit=lambda: quits.append(True)),
    )
    module.measured_cycle(env)
    result = json.loads(marker.read_text())
    assert result == {
        "stage": "finished",
        "started": 1.0,
        "measured": 31.0,
        "finished": 151.0,
        "warmup": {"requests": 10, "failures": 2},
        "warmup_min_users": 6,
        "measurement_min_users": 6,
        "user_errors": 0,
        "cache": {},
        "http": {},
        "measurement": [
            {
                "method": "GET",
                "name": "synthetic",
                "requests": 10,
                "failures": 2,
                "requests_per_second": 10 / 120,
                "mean_ms": 8,
                "median_ms": 9,
                "p95_ms": 12,
                "p99_ms": 14,
            }
        ],
    }
    assert resets == [True] and quits == [True]
    assert marker.stat().st_mode & 0o777 == 0o600


def test_all_sessions_arrive_before_measurement_and_cache_quota_observed(monkeypatch):
    monkeypatch.setenv("LOCUST_SKIP_MONKEY_PATCH", "1")
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parent))
    module = importlib.import_module("locust_sustained")
    ready = SimpleNamespace(set=lambda: calls.append("ready"))
    calls = []
    monkeypatch.setattr(module, "_ready", ready)
    monkeypatch.setattr(module, "_logged_in", 0)
    for _ in range(11):
        assert not module.mark_logged_in(12)
        assert not calls
    assert module.mark_logged_in(12)
    assert calls == ["ready"]
    with pytest.raises(ValueError):
        module.mark_logged_in(12)
    module._cache.clear()
    module._http.clear()
    module.observe_cache("HIT", 200)
    module.observe_cache("BYPASS", 429)
    assert module._cache == {"HIT": 1, "BYPASS": 1}
    assert module._http == {"quota_429": 1}


def test_mfa_waits_past_enrollment_and_each_previous_counter(monkeypatch):
    monkeypatch.setenv("LOCUST_SKIP_MONKEY_PATCH", "1")
    monkeypatch.setenv("REDHOUSE_LOAD_MFA_AFTER", "100")
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parent))
    module = importlib.import_module("locust_sustained")
    clock = [3000.0]
    monkeypatch.setattr(module.time, "time", lambda: clock[0])
    monkeypatch.setattr(
        module.gevent, "sleep", lambda _: clock.__setitem__(0, clock[0] + 30)
    )
    monkeypatch.setattr(module, "_mfa_last", {})
    assert module.next_mfa_counter("medical2") == 101
    assert module.next_mfa_counter("medical2") == 102


def test_user_error_during_final_drain_sets_failure_after_snapshot(monkeypatch):
    monkeypatch.setenv("LOCUST_SKIP_MONKEY_PATCH", "1")
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parent))
    module = importlib.import_module("locust_sustained")
    monkeypatch.setattr(module, "_user_errors", 0)
    snapshot_errors = module._user_errors
    environment = SimpleNamespace(
        runner=SimpleNamespace(stop=lambda: module.record_user_error()),
        process_exit_code=None,
    )
    module.enforce_final_user_errors(environment)
    assert snapshot_errors == 0
    assert environment.process_exit_code == 1


def test_phase_rejects_unbalanced_user_count_and_unsupported_duration(tmp_path):
    with pytest.raises(ValueError):
        sustained_read.run_phase(None, {}, tmp_path, None, users=7)
    with pytest.raises(ValueError):
        sustained_read.run_phase(None, {}, tmp_path, None, users=12, seconds=61)


def test_acceptance_requires_p95_error_rate_and_observed_cache_mode():
    rows = [{"method": "GET", "requests": 200, "p95_ms": 1999}]
    assert sustained_read.evaluate_measurement(
        rows, 1, {"HIT": 1}, no_cache=False, execution_valid=True
    )["measurement_accepted"]
    assert not sustained_read.evaluate_measurement(
        rows, 2, {"HIT": 1}, no_cache=False, execution_valid=True
    )["measurement_accepted"]
    assert not sustained_read.evaluate_measurement(
        rows, 0, {}, no_cache=False, execution_valid=True
    )["measurement_accepted"]
    assert not sustained_read.evaluate_measurement(
        rows, 0, {"MISS": 1, "BYPASS": 1000}, no_cache=False, execution_valid=True
    )["measurement_accepted"]
    assert not sustained_read.evaluate_measurement(
        rows, 0, {"HIT": 1, "BYPASS": 1}, no_cache=False, execution_valid=True
    )["measurement_accepted"]
    assert not sustained_read.evaluate_measurement(
        rows, 0, {"HIT": 1, "BYPASS": 1}, no_cache=True, execution_valid=True
    )["measurement_accepted"]
    rows[0]["p95_ms"] = 2000
    assert not sustained_read.evaluate_measurement(
        rows, 0, {"BYPASS": 1}, no_cache=True, execution_valid=True
    )["measurement_accepted"]


def test_cleanup_failure_invalidates_even_if_sessions_were_revoked():
    rows = [
        {"method": "GET", "name": "Lectura", "num_failures": 0},
        {"method": "CLEANUP", "name": "Cierre / sesiones", "num_failures": 1},
    ]
    reads = (
        "inventario / Disponibilidad regional",
        "inventario / Inventario propio",
        "priorizacion_geografia / Rutas",
        "auditoria / Bitácora",
        "donantes / Agenda propia",
        "transporte / Tareas propias",
    )
    result = {
        "runner_exit": 0,
        "stopped_by_guard": False,
        "session_revocation_verified": True,
        "session_count_verified": True,
        "cleanup_failures": sustained_read.cleanup_failures(rows),
        "counts": {"Identidad / revocación al salir": 6},
        "measurement_counts": {name: 1 for name in reads},
        "timing": {
            "stage": "finished",
            "warmup": {"requests": 1},
            "warmup_min_users": 6,
            "measurement_min_users": 6,
            "user_errors": 0,
            "started": 0,
            "measured": 30,
            "finished": 150,
        },
    }
    assert not sustained_read.phase_execution_valid(result, 6, 120)
    result["cleanup_failures"] = 0
    assert sustained_read.phase_execution_valid(result, 6, 120)
    execution_valid = False
    measured = [{"method": "GET", "requests": 100, "p95_ms": 100}]
    assert not sustained_read.evaluate_measurement(
        measured, 0, {"HIT": 1}, no_cache=False, execution_valid=execution_valid
    )["measurement_accepted"]


def test_invalid_phase_stops_series_but_unmet_performance_does_not():
    summary = {"phases": []}
    sustained_read.record_phase(
        summary, "24-active", {"execution_valid": True, "measurement_accepted": False}
    )
    with pytest.raises(RuntimeError):
        sustained_read.record_phase(
            summary,
            "6-recovery",
            {"execution_valid": False, "measurement_accepted": False},
        )
    assert [phase["name"] for phase in summary["phases"]] == ["24-active", "6-recovery"]


def test_process_sampling_includes_descendants_not_unrelated(monkeypatch):
    monkeypatch.setattr(
        sustained_read.subprocess,
        "run",
        lambda *_a, **_kw: SimpleNamespace(
            stdout="10 1 100 1.0\n11 10 50 2.0\n12 11 25 3.0\n20 1 200 4.0\n90 1 999 9.0\n"
        ),
    )
    env = SimpleNamespace(processes=[SimpleNamespace(pid=10, poll=lambda: None)])
    result = sustained_read.process_sample(env, SimpleNamespace(pid=20))
    assert result == {
        "rss_sum_kib": 375,
        "ps_cpu_percent_sum": 10.0,
        "sampled_processes": 4,
        "root_processes_missing": 0,
    }


@pytest.mark.parametrize(
    ("error", "category", "code", "expected_errno"),
    [
        (
            BudgetExceeded(
                "free_insufficient",
                {
                    "free_bytes": 1,
                    "owned_bytes": 2,
                    "minimum_free_bytes": 3,
                    "maximum_owned_bytes": 4,
                },
            ),
            "budget",
            "free_insufficient",
            None,
        ),
        (
            BudgetExceeded(
                "owned_limit_exceeded",
                {
                    "free_bytes": 3,
                    "owned_bytes": 5,
                    "minimum_free_bytes": 3,
                    "maximum_owned_bytes": 4,
                },
            ),
            "budget",
            "owned_limit_exceeded",
            None,
        ),
        (CensusFailure("unstable"), "census", "unstable", None),
        (CensusFailure("symlink"), "census", "symlink", None),
        (
            PermissionError(errno.EACCES, "secret", "/private/secret"),
            "filesystem_os",
            None,
            errno.EACCES,
        ),
        (OSError(9999, "secret"), "filesystem_os", None, None),
        (RuntimeError("secret"), "guard_unknown", None, None),
    ],
)
def test_guard_interruption_records_only_fixed_diagnostic(
    error, category, code, expected_errno
):
    def fail(_directory):
        raise error

    signals = []
    sample, interruption = sustained_read.sample_or_interrupt(
        fail,
        Path("/private/secret"),
        sustained_read.time.monotonic(),
        SimpleNamespace(send_signal=signals.append),
    )
    assert signals == [signal.SIGINT]
    assert sample is None
    assert interruption["category"] == category
    assert interruption.get("code") == code
    assert interruption.get("errno") == expected_errno
    assert interruption["utc"].endswith("+00:00")
    assert interruption["elapsed_seconds"] >= 0
    assert "secret" not in json.dumps(interruption)


def test_guard_success_samples_timestamp_and_elapsed():
    sample, interruption = sustained_read.check_budget(
        lambda _: {"free_bytes": 100, "owned_bytes": 20},
        Path("/ignored"),
        sustained_read.time.monotonic(),
    )
    assert interruption is None
    assert sample["free_bytes"] == 100 and sample["owned_bytes"] == 20
    assert sample["utc"].endswith("+00:00") and sample["elapsed_seconds"] >= 0


def test_guard_rejects_unknown_codes_and_non_numeric_samples():
    valid = {
        "free_bytes": 3,
        "owned_bytes": 2,
        "minimum_free_bytes": 1,
        "maximum_owned_bytes": 4,
    }
    with pytest.raises(ValueError):
        BudgetExceeded("secret", valid)
    with pytest.raises(ValueError):
        BudgetExceeded("free_insufficient", dict(valid, free_bytes="secret"))
    with pytest.raises(ValueError):
        CensusFailure("secret")


def test_runtime_topology_requires_owned_listener(tmp_path, monkeypatch):
    state = {"service_pids": {}, "worker_pids": {}, "urls": {}}
    processes = []
    for index, service in enumerate(sustained_read.SERVICES):
        api_pid, worker_pid, port = 1000 + index, 2000 + index, 5000 + index
        config = str(tmp_path / f"{service}.json")
        processes.extend(
            [
                SimpleNamespace(
                    pid=api_pid,
                    poll=lambda: None,
                    args=[
                        sys.executable,
                        str(sustained_read.ROOT / "run.py"),
                        service,
                        "--config",
                        config,
                    ],
                ),
                SimpleNamespace(
                    pid=worker_pid,
                    poll=lambda: None,
                    args=[
                        sys.executable,
                        str(sustained_read.ROOT / "worker.py"),
                        service,
                        "--config",
                        config,
                    ],
                ),
            ]
        )
        state["service_pids"][service] = api_pid
        state["worker_pids"][service] = worker_pid
        state["urls"][service] = f"http://127.0.0.1:{port}"
    env = SimpleNamespace(directory=tmp_path, processes=processes, state=state)

    def lsof(command, **_kwargs):
        pid = command[command.index("-p") + 1]
        port = command[command.index("-p") + 2].split(":")[1]
        return SimpleNamespace(stdout=f"p{pid}\nn127.0.0.1:{port}\n")

    monkeypatch.setattr(sustained_read.subprocess, "run", lsof)
    assert len(sustained_read.runtime_topology(env)) == len(sustained_read.SERVICES)
    monkeypatch.setattr(
        sustained_read.subprocess,
        "run",
        lambda *_a, **_kw: SimpleNamespace(stdout="p999\nn127.0.0.1:1\n"),
    )
    with pytest.raises(ValueError, match="Listener"):
        sustained_read.runtime_topology(env)
