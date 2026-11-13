"""Portal: reto, CSRF y recuperación del resultado idempotente."""

from uuid import uuid4

from .test_web_integration import form, login, web  # noqa: F401


def test_web_user_state_reauth_and_replay_without_otp(p, web, monkeypatch):
    target = p.ok(
        "identidad_acceso",
        "POST",
        "/api/v1/users",
        user="admin1",
        data={
            "username": "webreauth_" + uuid4().hex[:12],
            "password": p.env.state["password"],
            "role": "OPERATOR",
            "tenant_id": p.env.state["tenants"][0],
        },
    )
    monkeypatch.setitem(
        p.apps["identidad_acceso"].config,
        "REAUTH_REQUIRED_OPERATIONS",
        ["user_state", "user_role"],
    )
    client = login(web, p, "admin1")
    path = "/administracion/usuarios/" + target["id"] + "/estado?active=false"
    values = form(client, path)
    assert client.post(path, data={"version": target["version"]}).status_code == 400
    values["reauth_password"] = p.env.state["password"]
    first = client.post(path, data=values)
    assert first.status_code == 302, first.data[:1000]
    values.pop("reauth_password")
    replay = client.post(path, data=values)
    assert replay.status_code == 302, replay.data[:1000]
    with p.owner("identidad_acceso") as conn:
        row = conn.execute(
            "SELECT active,version FROM users WHERE id=%s", (target["id"],)
        ).fetchone()
        assert row == (False, target["version"] + 1)
        count = conn.execute(
            "SELECT count(*) FROM activity_events WHERE event->>'action'='USER_STATE_CHANGED' AND event->>'resource_id'=%s",
            (target["id"],),
        ).fetchone()[0]
        assert count == 1
