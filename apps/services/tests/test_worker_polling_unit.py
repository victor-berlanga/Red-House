"""Cadencia del worker sin red, almacenamiento ni procesos secundarios."""

import signal
import sys
from contextlib import nullcontext
from types import SimpleNamespace

import pytest
import worker


def run_worker(
    monkeypatch, tmp_path, outcomes, *, once=False, stop_during=False, durations=None
):
    clock = [0.0]
    calls = []
    sleeps = []
    handlers = {}
    sequence = iter(outcomes)
    durations = iter(durations or [0.0] * len(outcomes))
    app = SimpleNamespace(config={}, app_context=nullcontext, extensions={})
    config = tmp_path / "worker.json"
    config.write_text("{}")
    monkeypatch.setattr(
        sys,
        "argv",
        ["worker.py", "donantes", "--config", str(config)]
        + (["--once"] if once else []),
    )
    monkeypatch.setattr(worker, "load_app", lambda *_: app)
    monkeypatch.setattr(
        worker,
        "signal",
        SimpleNamespace(
            SIGTERM=signal.SIGTERM,
            SIGINT=signal.SIGINT,
            signal=lambda key, fn: handlers.setdefault(key, fn),
        ),
    )

    def dispatch():
        calls.append(("dispatch", round(clock[0], 6)))
        outcome = next(sequence)
        clock[0] += next(durations)
        if stop_during:
            handlers[signal.SIGTERM]()
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    def heartbeat(error=None):
        calls.append(("heartbeat", error))

    def step(_app, next_poll):
        calls.append(("periodic", round(clock[0], 6)))
        result = dispatch()
        heartbeat()
        return next_poll, result

    def sleep(delay):
        sleeps.append(delay)
        clock[0] += delay
        if len(sleeps) >= len(outcomes):
            handlers[signal.SIGTERM]()

    monkeypatch.setattr(worker, "dispatch", dispatch)
    monkeypatch.setattr(worker, "heartbeat", heartbeat)
    monkeypatch.setattr(worker, "step", step)
    monkeypatch.setattr(
        worker, "time", SimpleNamespace(monotonic=lambda: clock[0], sleep=sleep)
    )
    worker.main()
    return calls, sleeps


@pytest.mark.parametrize(
    "outcome,delay",
    [
        ({"delivered": 100, "failed": 0}, 0.1),
        ({"delivered": 99, "failed": 1}, 0.1),
        ({"delivered": 0, "failed": 100}, 5.0),
        ({"delivered": 99, "failed": 0}, 5.0),
        ({"delivered": 0, "failed": 0}, 5.0),
        (RuntimeError("dependency unavailable"), 5.0),
    ],
)
def test_batch_progress_controls_polling(monkeypatch, tmp_path, outcome, delay):
    _, sleeps = run_worker(monkeypatch, tmp_path, [outcome])
    assert sleeps == [delay]


def test_drain_keeps_periodic_work_at_ordinary_cadence(monkeypatch, tmp_path):
    calls, sleeps = run_worker(
        monkeypatch, tmp_path, [{"delivered": 100, "failed": 0}] * 55
    )
    periodic = [stamp for kind, stamp in calls if kind == "periodic"]
    assert len(periodic) == 2
    assert periodic[0] == 0
    assert 5 <= periodic[1] <= 5.1
    assert len([kind for kind, _ in calls if kind == "dispatch"]) == 55
    assert len([kind for kind, _ in calls if kind == "heartbeat"]) == 55
    assert all(delay == 0.1 for delay in sleeps)


def test_error_during_fast_drain_restores_backoff_and_recovers(monkeypatch, tmp_path):
    calls, sleeps = run_worker(
        monkeypatch,
        tmp_path,
        [
            {"delivered": 100, "failed": 0},
            RuntimeError("dependency unavailable"),
            {"delivered": 0, "failed": 0},
        ],
    )
    assert sleeps == pytest.approx([0.1, 5, 5])
    assert [stamp for kind, stamp in calls if kind == "periodic"] == [0, 5.1]
    assert ("heartbeat", "RuntimeError") in calls


@pytest.mark.parametrize("once,stop_during", [(True, False), (False, True)])
def test_once_and_signal_stop_without_another_batch(
    monkeypatch, tmp_path, once, stop_during
):
    calls, sleeps = run_worker(
        monkeypatch,
        tmp_path,
        [{"delivered": 100, "failed": 0}],
        once=once,
        stop_during=stop_during,
    )
    assert sleeps == []
    assert len([kind for kind, _ in calls if kind == "dispatch"]) == 1


@pytest.mark.parametrize(
    "outcome",
    [
        {"delivered": 0, "failed": 100},
        {"delivered": 50, "failed": 0},
        {"delivered": 0, "failed": 0},
    ],
)
def test_slow_fast_batch_waits_full_interval_after_deadline(
    monkeypatch, tmp_path, outcome
):
    calls, sleeps = run_worker(
        monkeypatch,
        tmp_path,
        [{"delivered": 100, "failed": 0}, outcome, {"delivered": 0, "failed": 0}],
        durations=[0, 6, 0],
    )
    assert sleeps == pytest.approx([0.1, 5, 5])
    assert [stamp for kind, stamp in calls if kind == "periodic"] == [0, 11.1]
    assert [stamp for kind, stamp in calls if kind == "dispatch"] == [0, 0.1, 11.1]
