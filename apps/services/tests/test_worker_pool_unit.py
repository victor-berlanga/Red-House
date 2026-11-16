"""Ámbito y cierre del pool del proceso worker; no abre conexiones."""

import json
import signal
import sys
from contextlib import nullcontext
from types import SimpleNamespace

import pytest
import worker


def run_once(monkeypatch, tmp_path, configuration, *, failure=None):
    path = tmp_path / "worker.json"
    original = json.dumps(configuration)
    path.write_text(original)
    closed = []
    app = SimpleNamespace(
        config=dict(configuration),
        app_context=nullcontext,
        extensions={
            "database_pools": {
                "first": SimpleNamespace(close=lambda: closed.append("first")),
                "second": SimpleNamespace(close=lambda: closed.append("second")),
            }
        },
    )

    def load(service, supplied):
        assert service == "auditoria" and supplied == configuration
        return app

    def step(_app, next_poll):
        if failure:
            raise failure
        return next_poll, {"delivered": 0, "failed": 0}

    monkeypatch.setattr(worker, "load_app", load)
    monkeypatch.setattr(worker, "step", step)
    monkeypatch.setattr(worker, "heartbeat", lambda *_: None)
    monkeypatch.setattr(
        worker,
        "signal",
        SimpleNamespace(
            SIGTERM=signal.SIGTERM,
            SIGINT=signal.SIGINT,
            signal=lambda *_: None,
        ),
    )
    monkeypatch.setattr(
        sys, "argv", ["worker.py", "auditoria", "--config", str(path), "--once"]
    )
    try:
        worker.main()
    finally:
        assert closed == ["first", "second"]
        assert path.read_text() == original
    return app


@pytest.mark.parametrize("explicit,expected", [(None, 1), (0, 0), (3, 3)])
def test_worker_default_preserves_explicit_configuration(
    monkeypatch, tmp_path, explicit, expected
):
    configuration = {} if explicit is None else {"DATABASE_POOL_SIZE": explicit}
    app = run_once(monkeypatch, tmp_path, configuration)
    assert app.config["DATABASE_POOL_SIZE"] == expected
    assert configuration == (
        {} if explicit is None else {"DATABASE_POOL_SIZE": explicit}
    )


@pytest.mark.parametrize("failure", [RuntimeError("failure"), SystemExit(9)])
def test_worker_closes_pools_on_error_and_exit(monkeypatch, tmp_path, failure):
    if isinstance(failure, SystemExit):
        with pytest.raises(SystemExit) as error:
            run_once(monkeypatch, tmp_path, {}, failure=failure)
        assert error.value.code == 9
    else:
        run_once(monkeypatch, tmp_path, {}, failure=failure)


def test_shared_step_and_api_keep_unpooled_default(monkeypatch):
    # Real app construction, no request, storage or engine access.
    app = worker.load_app(
        "auditoria",
        {
            "DATABASE_URL": "postgresql://unused.invalid/red_house",
            "JWT_PUBLIC_KEY": "unused-public-key",
        },
    )
    assert app.config.get("DATABASE_POOL_SIZE", 0) == 0
    monkeypatch.setattr(worker, "dispatch", lambda: {"delivered": 0, "failed": 0})
    monkeypatch.setattr(worker, "heartbeat", lambda *_: None)
    worker.step(app)
    assert app.config.get("DATABASE_POOL_SIZE", 0) == 0
    assert "database_pools" not in app.extensions
