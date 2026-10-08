import json
import time
from uuid import uuid4

import jwt
import psycopg
import pytest
import redis
import requests
from lxml import etree as E
from openapi_spec_validator import validate

from redhouse.codec import request_xsd
from redhouse.config import SERVICES
from redhouse.security import internal_signature
from ms_donantes.routes import DonorCreate

from .helpers import evaluation, recipient_request, resource, route


@pytest.mark.parametrize("service", list(SERVICES))
def test_health_swagger_and_openapi_all_services(p, service):
    for path in (
        "/health/live",
        "/health/ready",
        "/health/database",
        "/health/redis",
        "/health/mongodb",
        "/health/storage",
    ):
        response = p.request(service, "GET", path, user=None)
        assert response.status_code == 200, response.text
    schema = requests.get(p.urls[service] + "/openapi.json", timeout=5).json()
    validate(schema)
    docs = requests.get(p.urls[service] + "/docs", timeout=5)
    assert docs.status_code == 200 and "SwaggerUIBundle" in docs.text
    assert (
        requests.get(p.urls[service] + "/docs/swagger.json", timeout=5).json()[
            "openapi"
        ]
        == "3.1.0"
    )
    assert all(
        "application/xml" in op["responses"][str(c["status"])]["content"]
        for c in p.apps[service].extensions["contracts"]
        for op in [
            schema["paths"][__import__("re").sub(r"<([^>]+)>", r"{\1}", c["path"])][
                c["method"].lower()
            ]
        ]
    )


@pytest.mark.parametrize(
    "case",
    [
        "none",
        "hs256",
        "expired",
        "audience",
        "issuer",
        "missing",
        "refresh_use",
        "numeric_sub",
    ],
)
def test_jwt_rejects_invalid_variants_before_domain(p, case):
    cfg = p.apps["identidad_acceso"].config
    claims = jwt.decode(
        p.tokens["medical2"],
        cfg["JWT_PUBLIC_KEY"],
        algorithms=["RS256"],
        audience=cfg["JWT_AUDIENCE"],
        issuer=cfg["JWT_ISSUER"],
    )
    if case == "none":
        token = jwt.encode(claims, key=None, algorithm="none")
    elif case == "hs256":
        token = jwt.encode(claims, "x" * 40, algorithm="HS256")
    else:
        if case == "expired":
            claims["exp"] = int(time.time()) - 1
        elif case == "audience":
            claims["aud"] = "other"
        elif case == "issuer":
            claims["iss"] = "other"
        elif case == "missing":
            del claims["sid"]
        elif case == "refresh_use":
            claims["token_use"] = "refresh"
        else:
            claims["sub"] = 12
        token = jwt.encode(claims, cfg["JWT_PRIVATE_KEY"], algorithm="RS256")
    result = p.request(
        "receptores",
        "GET",
        "/api/v1/recipients",
        headers={"Authorization": "Bearer " + token},
    )
    assert result.status_code == 401


def test_session_rotation_replay_and_logout(p):
    credentials = {"username": "medical2", "password": p.env.state["password"]}
    first = p.ok(
        "identidad_acceso", "POST", "/api/v1/auth/login", user=None, data=credentials
    )
    rotated = p.ok(
        "identidad_acceso",
        "POST",
        "/api/v1/auth/refresh",
        user=None,
        data={"refresh_token": first["refresh_token"]},
    )
    assert rotated["refresh_token"] != first["refresh_token"]
    repeated = p.request(
        "identidad_acceso",
        "POST",
        "/api/v1/auth/refresh",
        user=None,
        data={"refresh_token": first["refresh_token"]},
    )
    assert repeated.status_code == 401
    denied = p.request(
        "receptores",
        "GET",
        "/api/v1/recipients",
        headers={"Authorization": "Bearer " + rotated["access_token"]},
    )
    assert denied.status_code == 401
    new = p.ok(
        "identidad_acceso", "POST", "/api/v1/auth/login", user=None, data=credentials
    )
    p.ok(
        "identidad_acceso",
        "POST",
        "/api/v1/auth/logout",
        headers={"Authorization": "Bearer " + new["access_token"]},
    )
    assert (
        p.request(
            "receptores",
            "GET",
            "/api/v1/recipients",
            headers={"Authorization": "Bearer " + new["access_token"]},
        ).status_code
        == 401
    )


def test_account_deactivation_fences_permissions_and_preserves_password(p):
    from ms_identidad_acceso.routes import permissions
    from redhouse.errors import APIError

    username = "fenced_" + uuid4().hex[:12]
    password = "  " + uuid4().hex + "  "
    created = p.ok(
        "identidad_acceso",
        "POST",
        "/api/v1/users",
        user="admin2",
        data={
            "username": username,
            "password": password,
            "tenant_id": p.env.state["tenants"][1],
            "role": "MEDICAL",
        },
    )
    login = p.ok(
        "identidad_acceso",
        "POST",
        "/api/v1/auth/login",
        user=None,
        data={"username": username, "password": password},
    )
    assert (
        p.request(
            "identidad_acceso",
            "POST",
            "/api/v1/auth/login",
            user=None,
            data={"username": username, "password": password.strip()},
        ).status_code
        == 401
    )
    p.ok(
        "identidad_acceso",
        "PATCH",
        "/api/v1/users/" + created["id"],
        user="admin2",
        data={"active": False, "version": 1},
    )
    assert (
        p.request(
            "receptores",
            "GET",
            "/api/v1/recipients",
            headers={"Authorization": "Bearer " + login["access_token"]},
        ).status_code
        == 401
    )
    with p.apps["identidad_acceso"].app_context():
        with pytest.raises(APIError):
            permissions(created)
    p.ok(
        "identidad_acceso",
        "PATCH",
        "/api/v1/users/" + created["id"],
        user="admin2",
        data={"active": True, "version": 2},
    )
    assert (
        p.request(
            "receptores",
            "GET",
            "/api/v1/recipients",
            headers={"Authorization": "Bearer " + login["access_token"]},
        ).status_code
        == 401
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("display_name", None),
        ("display_name", "   "),
        ("display_name", "Nombre\x00inválido"),
        ("consent", None),
        ("consent", 1),
        ("blood_group", "X+"),
        ("unknown", "injection"),
    ],
)
def test_strict_inputs(p, field, value):
    data = {
        "folio": "DONOR-" + uuid4().hex[:10],
        "display_name": "Ficticio",
        "blood_group": "O-",
        "consent": True,
    }
    data[field] = value
    response = p.request(
        "donantes", "POST", "/api/v1/donors", user="operator1", data=data
    )
    assert response.status_code in (400, 422)


def test_xml_schema_json_parity_errors_and_xxe(p):
    xml = f"<request><folio>XML-{uuid4().hex[:10]}</folio><display_name>Ficticio XML</display_name><blood_group>O-</blood_group><consent>true</consent></request>"
    E.XMLSchema(E.fromstring(request_xsd(DonorCreate))).assertValid(
        E.fromstring(xml.encode())
    )
    headers = {
        "Authorization": "Bearer " + p.tokens["operator1"],
        "Idempotency-Key": uuid4().hex,
        "Accept": "application/xml",
        "Content-Type": "application/xml",
    }
    response = requests.post(
        p.urls["donantes"] + "/api/v1/donors",
        data=xml.encode(),
        headers=headers,
        timeout=5,
    )
    assert response.status_code == 201, response.text
    response_schema = E.XMLSchema(
        E.parse(
            str(
                __import__("pathlib").Path(__file__).resolve().parents[1]
                / "redhouse/response.xsd"
            )
        )
    )
    response_schema.assertValid(E.fromstring(response.content))
    identifier = E.fromstring(response.content).xpath(
        "string(field[@name='data']/field[@name='id'])"
    )
    detail = p.ok("donantes", "GET", "/api/v1/donors/" + identifier, user="operator1")
    assert detail["display_name"] == "Ficticio XML"
    malicious = b'<!DOCTYPE request [<!ENTITY leak SYSTEM "file:///etc/passwd">]><request><folio>&leak;</folio></request>'
    result = requests.post(
        p.urls["donantes"] + "/api/v1/donors",
        data=malicious,
        headers=headers,
        timeout=5,
    )
    assert result.status_code == 400 and result.headers["Content-Type"].startswith(
        "application/xml"
    )
    assert b"root:" not in result.content
    response_schema.assertValid(E.fromstring(result.content))
    missing = p.request(
        "donantes",
        "GET",
        "/api/v1/donors/" + str(uuid4()),
        user="operator1",
        headers={"Accept": "application/xml"},
    )
    assert missing.status_code == 404
    response_schema.assertValid(E.fromstring(missing.content))


def test_duplicate_json_keys_nonfinite_and_wrong_media(p):
    headers = {
        "Authorization": "Bearer " + p.tokens["operator1"],
        "Content-Type": "application/json",
    }
    for body in ('{"folio":"a","folio":"b"}', '{"latitude":NaN}', "[]", "{broken"):
        result = requests.post(
            p.urls["donantes"] + "/api/v1/donors", data=body, headers=headers, timeout=5
        )
        assert result.status_code == 400
    headers["Content-Type"] = "text/plain"
    assert (
        requests.post(
            p.urls["donantes"] + "/api/v1/donors",
            data="hello",
            headers=headers,
            timeout=5,
        ).status_code
        == 415
    )
    assert (
        p.request(
            "donantes",
            "GET",
            "/api/v1/donors",
            user="operator1",
            headers={"Accept": "text/html"},
        ).status_code
        == 406
    )


def test_institution_role_and_assignment_authorization(p):
    patient, _ = recipient_request(p)
    assert (
        p.request(
            "receptores", "GET", "/api/v1/recipients/" + patient["id"], user="medical1"
        ).status_code
        == 403
    )
    assert (
        p.request(
            "receptores", "GET", "/api/v1/recipients/" + patient["id"], user="admin2"
        ).status_code
        == 403
    )
    assert (
        p.request(
            "receptores",
            "GET",
            "/api/v1/recipients/" + patient["id"],
            user="coordinator2",
        ).status_code
        == 403
    )
    assert (
        p.request("auditoria", "GET", "/api/v1/events", user="medical2").status_code
        == 403
    )


def test_internal_signature_delegation_replay_and_wrong_caller(p):
    path = "/internal/v1/available-resources"
    cfg = p.apps["compatibilidad"].config
    timestamp, nonce = str(int(time.time())), str(uuid4())
    headers = {
        "X-Service": "compatibilidad",
        "X-Service-Time": timestamp,
        "X-Service-Nonce": nonce,
        "X-Service-Signature": internal_signature(
            cfg["SERVICE_PRIVATE_KEY"], "GET", path, timestamp, nonce, b""
        ),
    }
    success = p.request("inventario", "GET", path, headers=headers)
    assert success.status_code == 200
    assert p.request("inventario", "GET", path, headers=headers).status_code == 401
    assert p.request("inventario", "GET", path).status_code == 401
    headers["X-Service"] = "transporte"
    assert p.request("inventario", "GET", path, headers=headers).status_code == 401


def test_database_and_redis_privileges_are_separate(p):
    cfg = p.apps["inventario"].config
    with psycopg.connect(cfg["DATABASE_URL"]) as conn:
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            conn.execute("CREATE TABLE forbidden(id integer)")
    url = cfg["DATABASE_URL"].replace("/rh_inventario?", "/rh_receptores?")
    with pytest.raises(psycopg.OperationalError):
        psycopg.connect(url)
    client = redis.Redis.from_url(cfg["REDIS_URL"], decode_responses=True)
    with pytest.raises(redis.exceptions.NoPermissionError):
        client.set(
            cfg["REDIS_PREFIX"]
            + "permissions:"
            + p.env.state["accounts"]["medical2"]["id"],
            '{"role":"ADMIN"}',
        )


def test_rate_limit(p):
    app = p.apps["donantes"]
    old = app.config["RATE_LIMIT"]
    app.config["RATE_LIMIT"] = 1
    try:
        result = p.request("donantes", "GET", "/api/v1/donors", user="operator1")
        assert result.status_code == 429 and result.headers["Retry-After"] == "60"
    finally:
        app.config["RATE_LIMIT"] = old
