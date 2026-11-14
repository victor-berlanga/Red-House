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
        "measurement": [
            {
                "method": "GET",
                "name": "synthetic",
                "requests": 10,
                "failures": 2,
                "requests_per_second": 10 / 120,
                "mean_ms": 8,
                "p95_ms": 12,
                "p99_ms": 14,
            }
        ],
    }
    assert resets == [True] and quits == [True]
    assert marker.stat().st_mode & 0o777 == 0o600


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
