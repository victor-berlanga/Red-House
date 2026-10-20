"""Sesiones con Redis/PostgreSQL reales: expiración, permisos, concurrencia y recuperación."""

import secrets
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from unittest.mock import patch

import psycopg
import pytest
import redis

from .test_web_integration import login, form, create_app
from .test_web_integration import web as web
from src.integration import sessions
from src.access import BusinessError


def save_session(app, sid):
    with app.app_context():
        sessions.save(
            sid,
            {
                "access_token": "old-access",
                "refresh_token": "private-refresh",
                "expires_at": time.time() + 900,
                "session_expires": time.time() + 86400,
            },
        )


def test_logout_failure_clears_credentials_and_queues_encrypted_revocation(web):
    sid = secrets.token_urlsafe(32)
    save_session(web, sid)
    with (
        web.app_context(),
        patch.object(sessions, "call", side_effect=BusinessError("Unavailable", 503)),
    ):
        payload = sessions.redis_client().get(
            sessions.redis_key("session", sessions.key(sid))
        )
        assert sessions.logout(sid) is False
        assert sessions.load(sid) is None
        with sessions.database() as conn:
            stored = conn.execute(
                "SELECT payload FROM web_runtime.session_revocations WHERE id=%s",
                (sessions.key(sid),),
            ).fetchone()[0]
            assert b"private-refresh" not in stored and b"old-access" not in stored
    with (
        web.app_context(),
        patch.object(sessions, "call", return_value={"revoked": True}),
    ):
        assert sessions.retry_revocations() == 1
        assert sessions.load(sid) is None
        # Simular una copia obsoleta de Redis: el cierre durable sigue prevaleciendo.
        sessions.redis_client().set(
            sessions.redis_key("session", sessions.key(sid)), payload, ex=60
        )
        assert sessions.load(sid) is None


def test_network_renewal_does_not_lock_other_sessions_and_rejects_same_session(web):
    first, second = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    save_session(web, first)
    waiting, finish = Event(), Event()

    def remote(*args, **kwargs):
        waiting.set()
        assert finish.wait(5)
        return {
            "access_token": "new-access",
            "refresh_token": "new-refresh",
            "expires_in": 900,
        }

    def renew():
        with web.app_context():
            return sessions.renew(first)

    with (
        patch.object(sessions, "call", side_effect=remote),
        ThreadPoolExecutor(max_workers=2) as pool,
    ):
        pending = pool.submit(renew)
        assert waiting.wait(3)
        try:
            pool.submit(save_session, web, second).result(timeout=2)
            with web.app_context(), pytest.raises(BusinessError) as error:
                sessions.renew(first)
            assert error.value.status == 409
        finally:
            finish.set()
        pending.result(timeout=5)
    with web.app_context():
        assert sessions.load(first)["access_token"] == "new-access"


def test_logout_during_refresh_never_recreates_session(web):
    sid = secrets.token_urlsafe(32)
    save_session(web, sid)
    waiting, finish = Event(), Event()

    def remote(service, path, *args, **kwargs):
        if path.endswith("refresh"):
            waiting.set()
            assert finish.wait(5)
            return {
                "access_token": "new-access",
                "refresh_token": "new-refresh",
                "expires_in": 900,
            }
        return {"revoked": True}

    def renew():
        with web.app_context():
            return sessions.renew(sid)

    with (
        patch.object(sessions, "call", side_effect=remote),
        ThreadPoolExecutor(max_workers=1) as pool,
    ):
        pending = pool.submit(renew)
        assert waiting.wait(3)
        try:
            with web.app_context():
                assert sessions.logout(sid)
        finally:
            finish.set()
        with pytest.raises(BusinessError) as error:
            pending.result(timeout=5)
        assert error.value.status == 401
    with web.app_context():
        assert sessions.load(sid) is None
        assert (
            sessions.redis_client().get(
                sessions.redis_key("session", sessions.key(sid))
            )
            is None
        )


def test_redis_outage_logout_is_durable_and_revokes_after_recovery(web, p, monkeypatch):
    client = login(web, p, "medical1")
    csrf = form(client, "/solicitudes/nueva")["csrf_token"]
    cookie = client.get_cookie(web.config["JWT_COOKIE_NAME"]).value
    with web.app_context():
        value = sessions.load(cookie)
    with monkeypatch.context() as changes:
        changes.setitem(web.config, "WEB_REDIS_URL", "redis://127.0.0.1:1/0")
        assert client.get("/panel").status_code == 503
        assert client.post("/logout", data={"csrf_token": csrf}).status_code == 302
        assert client.get_cookie(web.config["JWT_COOKIE_NAME"]) is None
        with web.app_context():
            assert sessions.load(cookie) is None
            with sessions.database() as conn:
                row = conn.execute(
                    "SELECT payload,confirmed FROM web_runtime.session_revocations WHERE id=%s",
                    (sessions.key(cookie),),
                ).fetchone()
                assert row == (None, False)
    with web.app_context():
        assert sessions.load(cookie) is None
        assert sessions.retry_revocations() >= 1
    assert (
        p.request(
            "identidad_acceso",
            "GET",
            "/api/v1/auth/me",
            user=None,
            headers={"Authorization": "Bearer " + value["access_token"]},
        ).status_code
        == 401
    )


def test_postgres_outage_fails_closed_and_logout_removes_browser_cookie(
    web, p, monkeypatch
):
    client = login(web, p, "medical1")
    csrf = form(client, "/solicitudes/nueva")["csrf_token"]
    with monkeypatch.context() as changes:
        changes.setitem(
            web.config, "WEB_DATABASE_URL", "postgresql://127.0.0.1:1/unused"
        )
        result = client.get("/panel")
        assert result.status_code == 503 and b"postgresql://" not in result.data
        result = client.post("/logout", data={"csrf_token": csrf})
        assert result.status_code == 503
        assert client.get_cookie(web.config["JWT_COOKIE_NAME"]) is None
    assert client.get("/panel").status_code == 302


def test_encrypted_session_is_shared_between_web_instances_and_expires(web, p):
    client = login(web, p, "operator1")
    cookie = client.get_cookie(web.config["JWT_COOKIE_NAME"]).value
    other = create_app(dict(web.config))
    with other.app_context():
        assert sessions.authenticate(cookie)["role"] == "OPERATOR"
        value = sessions.load(cookie)
        name = sessions.redis_key("session", sessions.key(cookie))
        payload = sessions.redis_client().get(name)
        assert value["access_token"].encode() not in payload
        assert value["refresh_token"].encode() not in payload
        assert cookie.encode() not in payload
        assert 0 < sessions.redis_client().ttl(name) <= 86400
    admin = redis.Redis.from_url(p.env.state["redis_admin"])
    admin.expire(name, 0)
    with web.app_context():
        assert sessions.load(cookie) is None
        with pytest.raises(BusinessError) as error:
            sessions.renew(cookie)
        assert error.value.status == 401


def test_portal_credentials_cannot_read_identity_keys_or_domain_tables(web, p):
    with web.app_context():
        with pytest.raises(redis.exceptions.NoPermissionError):
            sessions.redis_client().get(
                p.apps["identidad_acceso"].config["REDIS_PREFIX"] + "session:any"
            )
        with pytest.raises(redis.exceptions.NoPermissionError):
            sessions.redis_client().execute_command("ACL", "LIST")
    with psycopg.connect(web.config["WEB_DATABASE_URL"]) as conn:
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            conn.execute("SELECT * FROM red_house.usuario LIMIT 1")


def test_storage_upgrade_is_repeatable_preserves_secret_and_pending_rows(web, p):
    from scripts.web_sessions import upgrade_local

    sid = secrets.token_urlsafe(32)
    with (
        web.app_context(),
        patch.object(sessions, "call", side_effect=BusinessError("Unavailable", 503)),
    ):
        save_session(web, sid)
        sessions.logout(sid)
    expected = dict(p.env.state["web_sessions"])
    assert upgrade_local(p.env.directory, p.env.state) == expected
    assert upgrade_local(p.env.directory, p.env.state) == expected
    with web.app_context():
        assert sessions.load(sid) is None
        with sessions.database() as conn:
            assert conn.execute(
                "SELECT payload IS NOT NULL FROM web_runtime.session_revocations WHERE id=%s",
                (sessions.key(sid),),
            ).fetchone()[0]
    with (
        web.app_context(),
        patch.object(sessions, "call", return_value={"revoked": True}),
    ):
        sessions.retry_revocations()


def test_undecipherable_revocation_remains_pending_until_key_is_restored(
    web, monkeypatch
):
    sid = secrets.token_urlsafe(32)
    save_session(web, sid)
    with (
        web.app_context(),
        patch.object(sessions, "call", return_value={"revoked": True}) as remote,
    ):
        with monkeypatch.context() as changes:
            changes.setitem(web.config, "SECRET_KEY", secrets.token_hex(32))
            assert sessions.load(sid) is None
            assert sessions.logout(sid) is False
            with sessions.database() as conn:
                assert conn.execute(
                    "SELECT confirmed,payload IS NOT NULL FROM web_runtime.session_revocations WHERE id=%s",
                    (sessions.key(sid),),
                ).fetchone() == (False, True)
            remote.assert_not_called()
        assert sessions.retry_revocations() >= 1
        remote.assert_called_once()
        assert sessions.load(sid) is None
