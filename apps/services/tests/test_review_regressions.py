"""Casos reproducibles encontrados en la revisión del 8 de octubre."""

import json
from uuid import uuid4
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from flask import Flask, g
from lxml import etree as E
from redhouse.codec import parse, request_xsd
from redhouse.errors import APIError
from ms_transporte.routes import Transition
from ms_donantes.routes import DonorCreate
from .helpers import (
    resource,
    recipient_request,
    evaluation,
    reservation,
    plan,
    move,
    iso,
)

CONFIRM = {
    "human_confirmation": True,
    "reason": "Corrección ficticia con revisión humana",
}


def test_nested_evidence_json_xml_parity():
    app = Flask(__name__)
    identifier = str(uuid4())
    body = dict(
        CONFIRM, state="DELIVERED", version=1, evidence={"object_id": identifier}
    )
    xml = f"<request><human_confirmation>true</human_confirmation><reason>{CONFIRM['reason']}</reason><state>DELIVERED</state><version>1</version><evidence><object_id>{identifier}</object_id></evidence></request>"
    with app.test_request_context(
        "/", method="POST", data=json.dumps(body), content_type="application/json"
    ):
        expected = parse(Transition)
    with app.test_request_context(
        "/", method="POST", data=xml, content_type="application/xml"
    ):
        assert parse(Transition) == expected
    schema = E.XMLSchema(E.fromstring(request_xsd(DonorCreate)))
    assert not schema.validate(
        E.fromstring(
            b"<request><folio>!!!bad!!!</folio><display_name>Ficticio</display_name><blood_group>O-</blood_group><consent>true</consent></request>"
        )
    )


@pytest.mark.parametrize(
    "previous,target,user",
    [
        ("PLANNED", "PREPARED", "operator1"),
        ("PREPARED", "COLLECTED", "transport1"),
        ("COLLECTED", "IN_TRANSIT", "transport1"),
        ("DELIVERED", "ACCEPTED", "operator2"),
    ],
)
def test_expired_shipment_cannot_advance_or_fulfill(p, previous, target, user):
    # Reloj controlado: SQL conserva límites válidos; no altera restricciones.
    unit = resource(p)
    _, req = recipient_request(p)
    shipment = plan(p, reservation(p, evaluation(p, req, [unit]), unit)["reservation"])
    with p.owner("transporte") as conn:
        conn.execute(
            "UPDATE shipments SET status=%s WHERE id=%s", (previous, shipment["id"])
        )
    future = datetime.now(timezone.utc) + timedelta(days=10)
    with patch("ms_transporte.routes.datetime") as clock:
        clock.now.return_value = future
        response = p.request(
            "transporte",
            "POST",
            f"/api/v1/shipments/{shipment['id']}/transitions",
            user=user,
            data=dict(CONFIRM, state=target, version=shipment["version"]),
        )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "expired_resource"
    assert (
        p.ok("receptores", "GET", "/api/v1/requests/" + req["id"])["status"] != "CLOSED"
    )


def test_rate_limits_separate_users_behind_same_web_ip(p, monkeypatch):
    from redhouse.security import key, redis_client

    app = p.apps["identidad_acceso"]
    monkeypatch.setitem(app.config, "RATE_LIMIT", 2)
    with app.app_context():
        client = redis_client()
        # Solo los contadores de esta prueba; los usuarios de fixture tienen actividad previa.
        import hashlib, time

        for name in ("operator1", "medical1"):
            account = p.env.state["accounts"][name]
            scope = hashlib.sha256(
                (account["tenant_id"] + ":" + account["id"]).encode()
            ).hexdigest()[:24]
            client.delete(
                key(f"limit:identidad_acceso:user:{scope}:{int(time.time()) // 60}")
            )
    for _ in range(2):
        assert (
            p.request(
                "identidad_acceso", "GET", "/api/v1/auth/me", user="operator1"
            ).status_code
            == 200
        )
    assert (
        p.request(
            "identidad_acceso", "GET", "/api/v1/auth/me", user="operator1"
        ).status_code
        == 429
    )
    assert (
        p.request(
            "identidad_acceso", "GET", "/api/v1/auth/me", user="medical1"
        ).status_code
        == 200
    )


def test_permission_publication_recovers_after_sql_rollback(p):
    from redhouse.security import key, redis_client
    import ms_identidad_acceso.routes as identity

    username = "recover_" + uuid4().hex[:10]
    password = uuid4().hex
    user = p.ok(
        "identidad_acceso",
        "POST",
        "/api/v1/users",
        user="admin1",
        data={
            "username": username,
            "password": password,
            "role": "OPERATOR",
            "tenant_id": p.env.state["tenants"][0],
        },
    )
    with patch.object(
        identity, "emit", side_effect=APIError("injected", "Fallo de prueba", 503)
    ):
        response = p.request(
            "identidad_acceso",
            "PATCH",
            "/api/v1/users/" + user["id"],
            user="admin1",
            data={"active": False, "version": 1},
        )
    assert response.status_code == 503
    with p.owner("identidad_acceso") as conn:
        assert conn.execute(
            "SELECT version,active FROM users WHERE id=%s", (user["id"],)
        ).fetchone() == (1, True)
    p.ok(
        "identidad_acceso",
        "POST",
        "/api/v1/auth/login",
        user=None,
        data={"username": username, "password": password},
    )
    with p.apps["identidad_acceso"].app_context():
        assert redis_client().get(key("permission_version:" + user["id"])) == "1"


def test_onboarding_cannot_take_over_existing_or_other_institution(p):
    institution = p.ok(
        "identidad_acceso",
        "POST",
        "/api/v1/institutions",
        user="admin1",
        data={"name": "Hospital ficticio " + uuid4().hex[:6]},
    )
    data = dict(CONFIRM, username="new_admin_" + uuid4().hex[:8], password=uuid4().hex)
    path = "/api/v1/institutions/" + institution["id"] + "/administrator"
    assert (
        p.request(
            "identidad_acceso", "POST", path, user="admin2", data=data
        ).status_code
        == 403
    )
    created = p.ok("identidad_acceso", "POST", path, user="admin1", data=data)
    assert created["tenant_id"] == institution["id"] and created["role"] == "ADMIN"
    assert (
        p.request(
            "identidad_acceso", "POST", path, user="admin1", data=data
        ).status_code
        == 409
    )
    login = p.ok(
        "identidad_acceso",
        "POST",
        "/api/v1/auth/login",
        user=None,
        data={k: data[k] for k in ("username", "password")},
    )
    assert login["user"]["tenant_id"] == institution["id"]


def test_catalogues_scope_version_and_dependencies(p):
    site = p.ok(
        "identidad_acceso",
        "POST",
        "/api/v1/catalogues/sites",
        user="admin1",
        data={
            "name": "Sede " + uuid4().hex[:8],
            "municipality": "Monterrey",
            "address": "Dirección ficticia",
        },
    )
    location = p.ok(
        "identidad_acceso",
        "POST",
        "/api/v1/catalogues/locations",
        user="admin1",
        data={
            "name": "Refrigerador " + uuid4().hex[:6],
            "parent_id": site["id"],
            "description": "Ubicación demostrativa",
        },
    )
    path = "/api/v1/catalogues/sites/" + site["id"]
    assert p.request("identidad_acceso", "GET", path, user="admin2").status_code == 403
    data = dict(
        CONFIRM,
        name=site["name"],
        municipality="Monterrey",
        address="Dirección actualizada",
        active=False,
        version=site["version"],
    )
    assert (
        p.request(
            "identidad_acceso", "PATCH", path, user="admin1", data=data
        ).status_code
        == 409
    )
    data["active"] = True
    updated = p.ok("identidad_acceso", "PATCH", path, user="admin1", data=data)
    assert updated["version"] == 2
    assert (
        p.request(
            "identidad_acceso", "PATCH", path, user="admin1", data=data
        ).status_code
        == 409
    )


def test_request_cancellation_preserves_private_reason(p):
    _, req = recipient_request(p)
    p.ok(
        "receptores",
        "POST",
        "/api/v1/requests/" + req["id"] + "/cancel",
        data=dict(CONFIRM, version=req["version"]),
    )
    row = p.ok("receptores", "GET", "/api/v1/requests/" + req["id"])
    assert row["decisions"][-1]["reason"] == CONFIRM["reason"]
    assert (
        p.request(
            "receptores", "GET", "/api/v1/requests/" + req["id"], user="medical1"
        ).status_code
        == 403
    )


def test_edit_and_withdraw_preserve_history_and_version(p):
    raw = {
        "folio": "EDIT-" + uuid4().hex[:12],
        "kind": "BLOOD",
        "component": "RBC-DEMO",
        "blood_group": "O-",
        "expires_at": iso(days=2),
    }
    row = p.ok("inventario", "POST", "/api/v1/resources", user="operator1", data=raw)
    changed = p.ok(
        "inventario",
        "PATCH",
        "/api/v1/resources/" + row["id"],
        user="operator1",
        data=dict(raw, **CONFIRM, version=1, folio="EDIT-" + uuid4().hex[:12]),
    )
    assert changed["version"] == 2
    assert (
        p.request(
            "inventario",
            "PATCH",
            "/api/v1/resources/" + row["id"],
            user="operator1",
            data=dict(raw, **CONFIRM, version=1),
        ).status_code
        == 409
    )
    withdrawn = p.ok(
        "inventario",
        "POST",
        "/api/v1/resources/" + row["id"] + "/withdraw",
        user="operator1",
        data=dict(CONFIRM, version=2),
    )
    assert withdrawn["status"] == "WITHDRAWN"
    detail = p.ok(
        "inventario", "GET", "/api/v1/resources/" + row["id"], user="operator1"
    )
    assert [r["action"] for r in detail["decisions"]] == [
        "RESOURCE_UPDATED",
        "RESOURCE_WITHDRAWN",
    ]
    assert all(r["reason"] == CONFIRM["reason"] for r in detail["decisions"])
    regional = p.ok(
        "inventario", "GET", "/api/v1/resources/" + row["id"], user="coordinator1"
    )
    assert "decisions" not in regional

    assert (
        p.request(
            "inventario",
            "POST",
            "/api/v1/resources/" + row["id"] + "/release",
            user="medical1",
            data=dict(CONFIRM, version=3),
        ).status_code
        == 409
    )
    assert (
        p.ok(
            "inventario", "GET", "/api/v1/resources?status=IN_TRANSIT", user="operator1"
        )["total"]
        >= 0
    )


def test_worker_health_exposes_stopped_worker_and_recovery(p, monkeypatch):
    from worker import heartbeat

    app = p.apps["donantes"]
    monkeypatch.setitem(app.config, "WORKER_REQUIRED", True)
    assert p.request("donantes", "GET", "/health/worker", user=None).status_code == 503
    with app.app_context():
        heartbeat()
    assert p.request("donantes", "GET", "/health/worker", user=None).status_code == 200
    with p.owner("donantes") as conn:
        conn.execute(
            "UPDATE worker_health SET checked_at=now()-interval '5 minutes' WHERE id=1"
        )
    assert p.request("donantes", "GET", "/health/worker", user=None).status_code == 503
    assert p.request("donantes", "GET", "/health/live", user=None).status_code == 200


def test_configured_storage_health_does_not_report_unconfigured(p, monkeypatch):
    from unittest.mock import Mock

    monkeypatch.setitem(
        p.apps["transporte"].config, "GCS_BUCKET", "isolated-test-bucket"
    )
    target = Mock()
    with patch("redhouse.storage.bucket", return_value=target):
        target.exists.return_value = False
        assert (
            p.request("transporte", "GET", "/health/storage", user=None).status_code
            == 503
        )
        target.exists.return_value = True
        assert p.request("transporte", "GET", "/health/storage", user=None).json()[
            "data"
        ] == {"state": "up", "required": True}


def test_additive_migration_preserves_v1_data_and_is_repeatable(p):
    from redhouse.schema import COMMON, SCHEMAS
    from redhouse.migrations import migrate
    from psycopg import sql

    with p.owner("inventario") as conn:
        namespace = "upgrade_" + uuid4().hex
        conn.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(namespace)))
        conn.execute(
            sql.SQL("SET LOCAL search_path={},pg_catalog").format(
                sql.Identifier(namespace)
            )
        )
        conn.execute(COMMON + SCHEMAS["inventario"])
        conn.execute("INSERT INTO schema_version(version) VALUES(1)")
        identifier = str(uuid4())
        tenant = p.env.state["tenants"][0]
        conn.execute(
            "INSERT INTO resources(id,tenant_id,region_id,current_institution_id,folio,kind,component,blood_group,expires_at) VALUES(%s,%s,%s,%s,'OLD-0001','BLOOD','RBC-DEMO','O-',now()+interval '2 days')",
            (identifier, tenant, p.env.state["region_id"], tenant),
        )
        migrate(conn, "inventario")
        migrate(conn, "inventario")
        assert conn.execute(
            "SELECT id::text,folio,location_id,collected_at FROM resources"
        ).fetchall() == [(identifier, "OLD-0001", None, None)]
        assert conn.execute(
            "SELECT version FROM schema_version ORDER BY version"
        ).fetchall() == [(1,), (2,), (3,), (4,)]
        assert conn.execute("SELECT name,revision FROM cache_revision").fetchall() == [
            ("inventory", 0)
        ]
        conn.rollback()


def test_revoke_with_refresh_removes_session_even_after_access_expired(p):
    login = p.ok(
        "identidad_acceso",
        "POST",
        "/api/v1/auth/login",
        user=None,
        data={"username": "operator1", "password": p.env.state["password"]},
    )
    p.ok(
        "identidad_acceso",
        "POST",
        "/api/v1/auth/revoke",
        user=None,
        data={"refresh_token": login["refresh_token"]},
    )
    assert (
        p.request(
            "identidad_acceso",
            "GET",
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer " + login["access_token"]},
        ).status_code
        == 401
    )
    assert (
        p.request(
            "identidad_acceso",
            "POST",
            "/api/v1/auth/refresh",
            user=None,
            data={"refresh_token": login["refresh_token"]},
        ).status_code
        == 401
    )


def test_xml_output_matches_published_operation_dto(p):
    import requests
    from redhouse.xml_response import validate_response

    value = p.request(
        "inventario",
        "GET",
        "/api/v1/resources",
        user="operator1",
        headers={"Accept": "application/xml"},
    )
    schema = requests.get(
        p.urls["inventario"] + "/schemas/resources_list.response.json", timeout=5
    ).json()
    decoded = validate_response(value.content, schema)
    assert decoded["data"]["page_size"] == 20
