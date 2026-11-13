"""Recibo mínimo de alta de usuario, con ámbito propio y sesión vigente."""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from uuid import uuid4

import pytest


def test_evidence_redacts_receipt_key():
    from redhouse.evidence import redact

    assert redact({"Idempotency-Key": "synthetic-secret"}) == {
        "Idempotency-Key": "[REDACTED]"
    }


def make_user(p, admin, role):
    actor = p.ok("identidad_acceso", "GET", "/api/v1/auth/me", user=admin)
    name = "receipt-" + uuid4().hex[:12]
    user = p.ok(
        "identidad_acceso",
        "POST",
        "/api/v1/users",
        user=admin,
        data={
            "username": name,
            "password": p.env.state["password"],
            "tenant_id": actor["tenant_id"],
            "role": role,
        },
    )
    return name, user


@pytest.mark.parametrize("representation", ["application/json", "application/xml"])
def test_receipt_scope_and_session(p, representation):
    name, admin = make_user(p, "admin1", "ADMIN")
    login = p.ok(
        "identidad_acceso",
        "POST",
        "/api/v1/auth/login",
        user=None,
        data={"username": name, "password": p.env.state["password"]},
    )
    p.tokens[name] = login["access_token"]
    key = uuid4().hex
    created_name = "created-" + uuid4().hex[:12]
    body = {
        "username": created_name,
        "password": p.env.state["password"],
        "tenant_id": admin["tenant_id"],
        "role": "OPERATOR",
    }
    created = p.ok(
        "identidad_acceso", "POST", "/api/v1/users", user=name, key=key, data=body
    )

    def receipt(user, idem=key):
        return p.request(
            "identidad_acceso",
            "GET",
            "/api/v1/user-creation-receipt",
            user=user,
            headers={"Accept": representation, "Idempotency-Key": idem},
        )

    response = receipt(name)
    assert response.status_code == 200
    if representation == "application/xml":
        from redhouse.xml_response import validate_response

        schema = json.loads(
            (
                Path(__file__).parents[1]
                / "ms_identidad_acceso/contracts/user_creation_receipt.response.json"
            ).read_text()
        )
        data = validate_response(response.content, schema)["data"]
    else:
        data = response.json()["data"]
    assert data == {"id": created["id"], "username": created_name, "role": "OPERATOR"}
    assert (
        p.ok(
            "identidad_acceso", "POST", "/api/v1/users", user=name, key=key, data=body
        )["id"]
        == created["id"]
    )
    assert receipt("admin1").status_code == 404
    assert receipt("admin2").status_code == 404
    assert receipt("operator1").status_code == 403
    assert receipt(name, "not-valid").status_code == 404
    assert receipt(name, "x").status_code == 400
    assert receipt(name, key + "," + key).status_code == 400
    other_key = uuid4().hex
    p.ok(
        "identidad_acceso",
        "POST",
        "/api/v1/devices",
        user=name,
        key=other_key,
        data={
            "id": str(uuid4()),
            "user_id": p.env.state["accounts"]["transport1"]["id"],
            "source": "SIMULATOR",
            "label": "Dispositivo sintético",
            "expires_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
        },
    )
    assert receipt(name, other_key).status_code == 404
    assert (
        p.request(
            "identidad_acceso",
            "POST",
            "/api/v1/users",
            user=name,
            key=key,
            data=dict(body, password="different-synthetic-password"),
        ).status_code
        == 409
    )
    p.ok(
        "identidad_acceso",
        "POST",
        "/api/v1/auth/revoke",
        user=name,
        data={"refresh_token": login["refresh_token"]},
    )
    assert receipt(name).status_code == 401


def test_receipt_during_uncommitted_creation_is_not_final(p, monkeypatch):
    import ms_identidad_acceso.routes as routes

    actor = p.ok("identidad_acceso", "GET", "/api/v1/auth/me", user="admin1")
    name = "concurrent-" + uuid4().hex[:12]
    body = {
        "username": name,
        "password": p.env.state["password"],
        "tenant_id": actor["tenant_id"],
        "role": "OPERATOR",
    }
    key = uuid4().hex
    inserted = Event()
    release = Event()
    original = routes.insert

    def delayed(conn, table, fields):
        row = original(conn, table, fields)
        if table == "users" and fields.get("username") == name:
            inserted.set()
            assert release.wait(15)
        return row

    monkeypatch.setattr(routes, "insert", delayed)
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(
            p.request,
            "identidad_acceso",
            "POST",
            "/api/v1/users",
            user="admin1",
            key=key,
            data=body,
        )
        try:
            assert inserted.wait(15)
            response = p.request(
                "identidad_acceso",
                "GET",
                "/api/v1/user-creation-receipt",
                user="admin1",
                headers={"Idempotency-Key": key},
            )
            assert response.status_code == 404
        finally:
            release.set()
        assert future.result().status_code == 201
    assert (
        p.request(
            "identidad_acceso",
            "GET",
            "/api/v1/user-creation-receipt",
            user="admin1",
            headers={"Idempotency-Key": key},
        ).status_code
        == 200
    )


def test_receipt_rejects_changed_role(p):
    name, admin = make_user(p, "admin1", "ADMIN")
    login = p.ok(
        "identidad_acceso",
        "POST",
        "/api/v1/auth/login",
        user=None,
        data={"username": name, "password": p.env.state["password"]},
    )
    p.tokens[name] = login["access_token"]
    key = uuid4().hex
    p.ok(
        "identidad_acceso",
        "POST",
        "/api/v1/users",
        user=name,
        key=key,
        data={
            "username": "created-" + uuid4().hex[:12],
            "password": p.env.state["password"],
            "tenant_id": admin["tenant_id"],
            "role": "OPERATOR",
        },
    )
    # La API impide cambiar el rol ADMIN; se simula una divergencia de caché
    # directamente en el almacén aislado, solo para comprobar el cierre seguro.
    with p.owner("identidad_acceso") as conn:
        conn.execute("UPDATE users SET role='OPERATOR' WHERE id=%s", (admin["id"],))
    assert p.request(
        "identidad_acceso",
        "GET",
        "/api/v1/user-creation-receipt",
        user=name,
        headers={"Idempotency-Key": key},
    ).status_code in (401, 403)


@pytest.mark.parametrize("change", ["inactive", "tenant", "version"])
def test_receipt_rechecks_sql_when_cache_is_stale(p, change):
    name, admin = make_user(p, "admin1", "ADMIN")
    login = p.ok(
        "identidad_acceso",
        "POST",
        "/api/v1/auth/login",
        user=None,
        data={"username": name, "password": p.env.state["password"]},
    )
    p.tokens[name] = login["access_token"]
    idem = uuid4().hex
    p.ok(
        "identidad_acceso",
        "POST",
        "/api/v1/users",
        user=name,
        key=idem,
        data={
            "username": "created-" + uuid4().hex[:12],
            "password": p.env.state["password"],
            "tenant_id": admin["tenant_id"],
            "role": "OPERATOR",
        },
    )
    if change == "tenant":
        other = p.ok("identidad_acceso", "GET", "/api/v1/auth/me", user="admin2")[
            "tenant_id"
        ]
    with p.owner("identidad_acceso") as conn:
        if change == "inactive":
            conn.execute("UPDATE users SET active=false WHERE id=%s", (admin["id"],))
        elif change == "version":
            conn.execute(
                "UPDATE users SET version=version+1 WHERE id=%s", (admin["id"],)
            )
        else:
            conn.execute(
                "UPDATE users SET tenant_id=%s WHERE id=%s", (other, admin["id"])
            )
    assert (
        p.request(
            "identidad_acceso",
            "GET",
            "/api/v1/user-creation-receipt",
            user=name,
            headers={"Idempotency-Key": idem},
        ).status_code
        == 401
    )
