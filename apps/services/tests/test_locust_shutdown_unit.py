"""Cierre del arnés de carga; sin servicios de dominio ni credenciales reales."""

import os
from types import SimpleNamespace

import gevent
import pytest
from gevent import GreenletExit

# Pytest ya importó ssl; Locust no debe monkey-patchear el proceso de pruebas.
_previous_patch = os.environ.get("LOCUST_SKIP_MONKEY_PATCH")
os.environ["LOCUST_SKIP_MONKEY_PATCH"] = "1"
try:
    from locust import User, task
    from locust.env import Environment
    from locust.exception import StopUser
    from locust.runners import STATE_CLEANUP, STATE_RUNNING

    from tests.load_cleanup import SessionCleanup, cleanup_for
    from tests.load_support import verify_new_sessions
    from tests.locust_transactions import TransactionUser
    from tests.locustfile import RegionalUser
finally:
    if _previous_patch is None:
        del os.environ["LOCUST_SKIP_MONKEY_PATCH"]
    else:
        os.environ["LOCUST_SKIP_MONKEY_PATCH"] = _previous_patch


class Event:
    def __init__(self):
        self.calls = []
        self.listeners = []

    def fire(self, **kwargs):
        self.calls.append(kwargs)

    def add_listener(self, listener):
        self.listeners.append(listener)


class Users:
    def __init__(self, drained=True):
        self.drained = drained
        self.killed = False

    def join(self, timeout):
        return self.drained

    def kill(self, block, timeout):
        self.killed = True
        self.drained = True

    def __len__(self):
        return 0 if self.drained else 1


def environment(drained=True):
    return SimpleNamespace(
        runner=SimpleNamespace(state=STATE_RUNNING, user_greenlets=Users(drained)),
        events=SimpleNamespace(request=Event(), test_stop=Event()),
    )


def test_cleanup_uses_latest_refresh_only_after_users_drain():
    env = environment()
    registry = cleanup_for(env)
    calls = []

    class Api:
        user = "synthetic"
        refresh = "old"

        def close(self):
            calls.append(("revoke", self.refresh))
            self.refresh = None

    api = Api()
    client = SimpleNamespace(close=lambda: calls.append(("client", None)))
    registry.add(api, client)
    api.refresh = "rotated"
    assert not calls
    assert len(env.events.test_stop.listeners) == 1
    assert cleanup_for(env) is registry
    registry.finish()
    registry.finish()
    assert calls == [("revoke", "rotated"), ("client", None)]
    assert not env.events.request.calls
    assert cleanup_for(env) is registry
    assert len(env.events.test_stop.listeners) == 1


def test_failed_revocation_is_recorded_and_does_not_skip_other_sessions():
    env = environment()
    registry = SessionCleanup(env)
    calls = []

    class Api:
        user = "synthetic"
        refresh = "synthetic-refresh"

        def __init__(self, fail):
            self.fail = fail

        def close(self):
            if self.fail:
                raise RuntimeError("private response must never be recorded")
            calls.append("revoked")

    registry.add(Api(True), SimpleNamespace(close=lambda: calls.append("closed-1")))
    registry.add(Api(False), SimpleNamespace(close=lambda: calls.append("closed-2")))
    registry.finish()
    assert calls == ["closed-1", "revoked", "closed-2"]
    event = env.events.request.calls[0]
    assert event["request_type"] == "CLEANUP"
    assert str(event["exception"]) == "cleanup_RuntimeError"
    assert "private response" not in str(event)


def test_undrained_user_is_recorded_as_failure_before_cleanup():
    env = environment(drained=False)
    registry = SessionCleanup(env)
    registry.finish()
    assert env.runner.user_greenlets.killed
    assert str(env.events.request.calls[0]["exception"]) == "users_not_drained"


def test_drain_error_is_sanitized_and_never_runs_revocation_concurrently():
    env = environment()

    def fail_drain(timeout):
        raise RuntimeError("private detail")

    env.runner.user_greenlets.join = fail_drain
    cleanup = SessionCleanup(env)
    calls = []
    api = SimpleNamespace(
        user="synthetic", refresh="synthetic", close=lambda: calls.append(1)
    )
    cleanup.add(api, SimpleNamespace(close=lambda: calls.append(2)))
    cleanup.finish()
    assert not calls
    assert str(env.events.request.calls[0]["exception"]) == "drain_RuntimeError"
    assert "private detail" not in str(env.events.request.calls[0])


def test_missing_refresh_is_a_cleanup_failure():
    env = environment()
    cleanup = SessionCleanup(env)
    closed = []
    api = SimpleNamespace(user="synthetic", refresh=None, close=lambda: None)
    cleanup.add(api, SimpleNamespace(close=lambda: closed.append(True)))
    cleanup.finish()
    assert closed == [True]
    assert str(env.events.request.calls[0]["exception"]) == "cleanup_LoadFailure"


def test_session_verification_ignores_existing_and_rejects_active_or_extra():
    class RedisDouble:
        def __init__(self, values):
            self.values = values
            self.keys = None

        def mget(self, keys):
            self.keys = keys
            return self.values

    previous = [("old", "user", None)]
    new = [("new", "user", "revoked")]
    client = RedisDouble([None])
    verify_new_sessions({"old"}, previous + new, ["user"], "fixture:", client)
    assert client.keys == ["fixture:session:new"]
    with pytest.raises(ValueError):
        verify_new_sessions(
            {"old"}, previous + [("new", "user", None)], ["user"], "fixture:", client
        )
    with pytest.raises(ValueError):
        verify_new_sessions(
            {"old"},
            previous + new + [("extra", "user", "revoked")],
            ["user"],
            "fixture:",
            client,
        )
    with pytest.raises(ValueError):
        verify_new_sessions(
            {"old"}, previous + new, ["user"], "fixture:", RedisDouble([b"active"])
        )


def test_session_verification_requires_distinct_families_per_identity():
    class RedisDouble:
        def mget(self, keys):
            return [None] * len(keys)

    rows = [
        ("a1", "a", "revoked"),
        ("a2", "a", "revoked"),
        ("b1", "b", "revoked"),
        ("b2", "b", "revoked"),
    ]
    verify_new_sessions(
        set(), rows, ["a", "b"], "fixture:", RedisDouble(), multiplicity=2
    )
    with pytest.raises(ValueError):
        verify_new_sessions(
            set(),
            rows[:-1] + [("a3", "a", "revoked")],
            ["a", "b"],
            "fixture:",
            RedisDouble(),
            multiplicity=2,
        )
    with pytest.raises(ValueError):
        verify_new_sessions(
            set(),
            rows[:-1] + [("a1", "b", "revoked")],
            ["a", "b"],
            "fixture:",
            RedisDouble(),
            multiplicity=2,
        )


def test_real_locust_test_stop_records_revocation_before_final_stats():
    env = Environment(user_classes=[])
    runner = env.create_local_runner()

    class Api:
        user = "synthetic"
        refresh = "synthetic"

        def close(self):
            env.events.request.fire(
                request_type="POST",
                name="Identidad / revocación al salir",
                response_time=1,
                response_length=0,
                exception=None,
                context={},
            )

    cleanup_for(env).add(Api(), SimpleNamespace(close=lambda: None))
    try:
        runner.stop()
        assert (
            runner.stats.get("Identidad / revocación al salir", "POST").num_requests
            == 1
        )
    finally:
        runner.quit()


def test_real_locust_runner_drains_and_revokes_each_registered_session():
    revoked = []

    class Api:
        user = "synthetic"
        refresh = "synthetic"

        def __init__(self, number):
            self.number = number

        def close(self):
            revoked.append(self.number)

    class Probe(User):
        counter = 0

        def on_start(self):
            number = type(self).counter
            type(self).counter += 1
            cleanup_for(self.environment).add(
                Api(number), SimpleNamespace(close=lambda: None)
            )

        @task
        def brief_task(self):
            gevent.sleep(0.01)

    env = Environment(user_classes=[Probe], stop_timeout=1)
    runner = env.create_local_runner()
    try:
        runner.start(user_count=4, spawn_rate=100)
        gevent.sleep(0.15)
        assert runner.user_count == 4
        runner.stop()
        assert sorted(revoked) == [0, 1, 2, 3]
        assert runner.stats.total.num_failures == 0
    finally:
        runner.quit()


def test_interrupted_transaction_is_failure_and_queued_shutdown_starts_none():
    env = environment()

    def interrupted(_api, _campaign):
        raise GreenletExit()

    user = SimpleNamespace(
        environment=env,
        role="DONOR",
        workflow=interrupted,
        api=None,
        campaign="synthetic",
    )
    with pytest.raises(GreenletExit):
        TransactionUser.business_cycle(user)
    assert (
        str(env.events.request.calls[0]["exception"])
        == "workflow_interrupted_GreenletExit"
    )
    env.runner.state = STATE_CLEANUP
    with pytest.raises(StopUser):
        TransactionUser.business_cycle(user)
    assert len(env.events.request.calls) == 1
    with pytest.raises(StopUser):
        RegionalUser.regional_workflow(user)
    assert len(env.events.request.calls) == 1
