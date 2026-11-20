"""Acceso por aplicación: portal, escritorio y móvil (requisito 19-nov-2026).

Distribución: portal = ADMIN, OPERATOR, MEDICAL, COORDINATOR, AUDITOR;
escritorio = OPERATOR, MEDICAL, COORDINATOR; móvil = DONOR, TRANSPORT.
El servidor rechaza el login fuera de la aplicación del perfil (403
`client_not_allowed`), guarda la aplicación en la sesión y el JWT, y rechaza
las sesiones que no la tienen o cuyo perfil ya no corresponde.
"""

import json

import jwt
import pytest
import requests

from redhouse.security import CLIENT_ROLES

from .helpers import resource
from .test_web_integration import form, web as web  # noqa: F401

LOGIN = "/api/v1/auth/login"
ACCOUNTS = {
    "ADMIN": "admin1",
    "OPERATOR": "operator1",
    "MEDICAL": "medical1",
    "COORDINATOR": "coordinator1",
    "AUDITOR": "auditor1",
    "TRANSPORT": "transport1",
    "DONOR": "donor1",
}
APP_NAME = {
    "web": "el portal web",
    "desktop": "la consola de escritorio",
    "mobile": "la aplicación móvil",
}


def login(p, username, client, **extra):
    headers = {"Accept": "application/json"}
    if client is not None:
        headers["X-RedHouse-Client"] = client
    return requests.post(
        p.urls["identidad_acceso"] + LOGIN,
        json={"username": username, "password": p.env.state["password"], **extra},
        headers=headers,
        timeout=10,
    )


def authed(p, token, path="/api/v1/auth/me", service="identidad_acceso"):
    return requests.get(
        p.urls[service] + path,
        headers={"Authorization": "Bearer " + token, "Accept": "application/json"},
        timeout=10,
    )


def redis_access(p):
    """Cliente Redis y prefijo de Identidad, con contexto de aplicación."""
    from redhouse.security import key, redis_client

    app = p.apps["identidad_acceso"]
    ctx = app.app_context()
    ctx.push()
    return redis_client(), key, ctx


@pytest.mark.parametrize("client", ["web", "desktop", "mobile"])
@pytest.mark.parametrize("role", list(ACCOUNTS))
def test_login_by_role_and_client_matrix(p, role, client):
    response = login(p, ACCOUNTS[role], client)
    if role in CLIENT_ROLES[client]:
        assert response.status_code == 200, response.text
        data = response.json()["data"]
        claims = jwt.decode(data["access_token"], options={"verify_signature": False})
        assert claims["client"] == client
        # La sesión recién emitida opera con normalidad en su aplicación.
        assert authed(p, data["access_token"]).status_code == 200
    else:
        assert response.status_code == 403, response.text
        error = response.json()["error"]
        assert error["code"] == "client_not_allowed"
        # El mensaje nombra la aplicación rechazada y dónde sí entrar.
        assert APP_NAME[client] in error["message"]
        allowed = [a for c, a in APP_NAME.items() if role in CLIENT_ROLES[c]]
        assert all(a in error["message"] for a in allowed)
        assert "access_token" not in response.text


def test_matrix_matches_the_requested_distribution():
    assert CLIENT_ROLES["web"] == {
        "ADMIN",
        "OPERATOR",
        "MEDICAL",
        "COORDINATOR",
        "AUDITOR",
    }
    assert CLIENT_ROLES["desktop"] == {"OPERATOR", "MEDICAL", "COORDINATOR"}
    assert CLIENT_ROLES["mobile"] == {"DONOR", "TRANSPORT"}


@pytest.mark.parametrize("value", [None, "", "Web", "tablet", "web,desktop", "x" * 300])
def test_login_without_or_with_unknown_client_fails_closed(p, value):
    response = login(p, "operator1", value)
    assert response.status_code == 400, response.text
    assert response.json()["error"]["code"] == "client_required"
    assert "access_token" not in response.text


def test_wrong_application_does_not_count_as_failed_attempt(p):
    for _ in range(7):
        assert login(p, "transport2", "web").status_code == 403
    assert login(p, "transport2", "mobile").status_code == 200


def test_client_is_stored_in_sql_and_redis_session(p):
    token = login(p, "medical1", "desktop").json()["data"]["access_token"]
    claims = jwt.decode(token, options={"verify_signature": False})
    with p.owner("identidad_acceso") as conn:
        conn.execute("SET search_path=access_identidad_acceso,pg_catalog")
        stored = conn.execute(
            "SELECT client FROM sessions WHERE id=%s", (claims["sid"],)
        ).fetchone()[0]
    assert stored == "desktop"
    r, key, ctx = redis_access(p)
    try:
        state = json.loads(r.get(key("session:" + claims["sid"])))
    finally:
        ctx.pop()
    assert state["client"] == "desktop"


def test_refresh_keeps_client_and_revalidates_role(p):
    data = login(p, "operator1", "desktop").json()["data"]
    claims = jwt.decode(data["access_token"], options={"verify_signature": False})
    refreshed = requests.post(
        p.urls["identidad_acceso"] + "/api/v1/auth/refresh",
        json={"refresh_token": data["refresh_token"]},
        headers={"Accept": "application/json"},
        timeout=10,
    )
    assert refreshed.status_code == 200, refreshed.text
    new = refreshed.json()["data"]
    new_claims = jwt.decode(new["access_token"], options={"verify_signature": False})
    assert new_claims["client"] == "desktop" and new_claims["sid"] == claims["sid"]
    assert authed(p, new["access_token"]).status_code == 200
    # Si el perfil deja de corresponder a la aplicación, el refresh es 403.
    account = p.env.state["accounts"]["operator1"]["id"]
    with p.owner("identidad_acceso") as conn:
        conn.execute("SET search_path=access_identidad_acceso,pg_catalog")
        conn.execute("UPDATE users SET role='DONOR' WHERE id=%s", (account,))
        conn.commit()
    try:
        blocked = requests.post(
            p.urls["identidad_acceso"] + "/api/v1/auth/refresh",
            json={"refresh_token": new["refresh_token"]},
            headers={"Accept": "application/json"},
            timeout=10,
        )
        assert blocked.status_code == 403
        assert blocked.json()["error"]["code"] == "client_not_allowed"
    finally:
        with p.owner("identidad_acceso") as conn:
            conn.execute("SET search_path=access_identidad_acceso,pg_catalog")
            conn.execute("UPDATE users SET role='OPERATOR' WHERE id=%s", (account,))
            conn.commit()


def test_active_session_is_rejected_when_current_role_no_longer_fits_the_client(p):
    token = login(p, "coordinator2", "desktop").json()["data"]["access_token"]
    claims = jwt.decode(token, options={"verify_signature": False})
    r, key, ctx = redis_access(p)
    try:
        name = key("permissions:" + claims["sub"])
        original = r.get(name)
        changed = dict(json.loads(original), role="DONOR")
        r.set(name, json.dumps(changed))
        try:
            response = authed(p, token)
            assert response.status_code == 403
            assert response.json()["error"]["code"] == "client_not_allowed"
        finally:
            r.set(name, original)
        assert authed(p, token).status_code == 200
    finally:
        ctx.pop()


def test_session_issued_before_the_change_is_rejected_and_the_script_revokes_it(p):
    from scripts.revocar_sesiones_sin_cliente import revocar, sesiones_sin_cliente

    data = login(p, "auditor2", "web").json()["data"]
    claims = jwt.decode(data["access_token"], options={"verify_signature": False})
    sid = claims["sid"]
    r, key, ctx = redis_access(p)
    try:
        # Se simula una sesión de antes del cambio: sin cliente en SQL ni en Redis.
        state = json.loads(r.get(key("session:" + sid)))
        state.pop("client")
        r.set(key("session:" + sid), json.dumps(state), ex=600)
        with p.owner("identidad_acceso") as conn:
            conn.execute("SET search_path=access_identidad_acceso,pg_catalog")
            conn.execute("UPDATE sessions SET client=NULL WHERE id=%s", (sid,))
            conn.commit()
            # El token vigente ya no sirve (falla cerrada, 401) ni se puede renovar.
            rejected = authed(p, data["access_token"])
            assert rejected.status_code == 401
            assert "inicia sesión de nuevo" in rejected.json()["error"]["message"]
            refreshed = requests.post(
                p.urls["identidad_acceso"] + "/api/v1/auth/refresh",
                json={"refresh_token": data["refresh_token"]},
                headers={"Accept": "application/json"},
                timeout=10,
            )
            assert refreshed.status_code == 401
            # El script en seco cuenta sin cambiar; aplicado revoca; repetido no encuentra nada.
            pending = sesiones_sin_cliente(conn)
            assert sid in pending
            assert (
                conn.execute(
                    "SELECT revoked_at FROM sessions WHERE id=%s", (sid,)
                ).fetchone()[0]
                is None
            )
            changed = revocar(
                conn, r, p.apps["identidad_acceso"].config["REDIS_PREFIX"], pending
            )
            conn.commit()
            assert changed == len(pending)
            assert (
                conn.execute(
                    "SELECT revoked_at FROM sessions WHERE id=%s", (sid,)
                ).fetchone()[0]
                is not None
            )
            assert sesiones_sin_cliente(conn) == []
        assert r.get(key("session:" + sid)) is None
    finally:
        ctx.pop()
    # La persona puede iniciar sesión de nuevo con normalidad.
    assert login(p, "auditor2", "web").status_code == 200


def test_script_requires_a_directory_and_rejects_conflicting_modes(tmp_path):
    from scripts import revocar_sesiones_sin_cliente as script

    with pytest.raises(SystemExit):
        script.main(["--aplicar", "--dry-run", "--directory", str(tmp_path)])
    with pytest.raises(SystemExit):
        script.main([])


def test_mobile_device_registration_is_exclusive_to_mobile_profiles(p):
    body = {
        "id": "3f2b1d52-8f0e-4f6e-9a39-2b9d0f6f7a11",
        "source": "ANDROID",
        "label": "Teléfono de prueba",
    }
    for user in ("operator1", "medical1", "coordinator1", "admin1", "auditor1"):
        response = p.request(
            "identidad_acceso", "POST", "/api/v1/mobile/devices", user=user, data=body
        )
        assert response.status_code == 403, (user, response.text)
    assert (
        p.request(
            "identidad_acceso",
            "POST",
            "/api/v1/mobile/devices",
            user="transport2",
            data=dict(body, id="3f2b1d52-8f0e-4f6e-9a39-2b9d0f6f7a12"),
        ).status_code
        < 300
    )


@pytest.mark.parametrize("role", ["DONOR", "TRANSPORT"])
def test_portal_login_refuses_mobile_profiles_with_a_clear_message(web, p, role):
    client = web.test_client()
    values = form(client, "/login")
    values.update(
        login_email=ACCOUNTS[role].replace("1", "2"), password=p.env.state["password"]
    )
    response = client.post("/login", data=values)
    assert response.status_code == 403
    assert "aplicación móvil".encode() in response.data
    assert client.get_cookie(web.config["JWT_COOKIE_NAME"]) is None


@pytest.mark.parametrize(
    "path",
    [
        "/panel",
        "/donantes/donor",
        "/campanas",
        "/citas",
        "/traslados",
        "/notificaciones",
        "/donantes/donor/00000000-0000-4000-8000-000000000001/mis-datos",
    ],
)
def test_direct_access_to_private_sections_with_a_donor_never_opens_them(web, p, path):
    client = web.test_client()
    values = form(client, "/login")
    values.update(login_email="donor2", password=p.env.state["password"])
    assert client.post("/login", data=values).status_code == 403
    response = client.get(path)
    assert response.status_code == 302 and response.location.endswith("/login")


def test_portal_permissions_exclude_mobile_profiles():
    from src.integration import PERMISSIONS, PORTAL_ROLES
    from src.integration.presentation import TASKS

    assert PORTAL_ROLES == CLIENT_ROLES["web"]
    for action, roles in PERMISSIONS.items():
        assert not roles & {"DONOR", "TRANSPORT"}, action
    assert not set(TASKS) & {"DONOR", "TRANSPORT"}


def test_resource_outside_the_scope_stays_denied_with_a_desktop_session(p):
    unit = resource(p)  # operator1, institución 1
    other = login(p, "operator2", "desktop").json()["data"]["access_token"]
    own = login(p, "operator1", "desktop").json()["data"]["access_token"]
    path = "/api/v1/resources/" + unit["id"]
    assert authed(p, own, path, "inventario").status_code == 200
    assert authed(p, other, path, "inventario").status_code in (403, 404)
