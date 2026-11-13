"""Reautenticación ligada a intención; usa PostgreSQL/Redis aislados en integración."""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4
from pathlib import Path

import psycopg
import pytest
import requests
from redhouse.examples import request_xml
from redhouse.xml_response import validate_response


def test_reservation_ledger_delete_revoked_for_runtime(p):
    script = (
        Path(__file__).resolve().parents[1] / "scripts/reauth_operations_retention.sql"
    ).read_text()
    with p.owner("inventario") as owner:
        owner.execute(script)
        owner.execute(script)
    with psycopg.connect(p.env.configs["inventario"]["DATABASE_URL"]) as runtime:
        privileges = runtime.execute(
            "SELECT has_table_privilege(current_user, 'access_inventario.operations', 'SELECT'), "
            "has_table_privilege(current_user, 'access_inventario.operations', 'INSERT'), "
            "has_table_privilege(current_user, 'access_inventario.operations', 'UPDATE'), "
            "has_table_privilege(current_user, 'access_inventario.operations', 'DELETE')"
        ).fetchone()
        assert privileges == (True, True, True, False)
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            runtime.execute("DELETE FROM operations WHERE false")
        runtime.rollback()


def body_response(response, fmt):
    if fmt == "json":
        return response.json()
    return validate_response(response.content, {"type": "object"})


@pytest.mark.parametrize("fmt", ["json", "xml"])
def test_user_role_challenge_and_proofless_replay(p, monkeypatch, fmt):
    target = p.ok(
        "identidad_acceso",
        "POST",
        "/api/v1/users",
        user="admin1",
        data={
            "username": "role_" + uuid4().hex[:12],
            "password": p.env.state["password"],
            "role": "OPERATOR",
            "tenant_id": p.env.state["tenants"][0],
        },
    )
    monkeypatch.setitem(
        p.apps["identidad_acceso"].config, "REAUTH_REQUIRED_OPERATIONS", ["user_role"]
    )
    path = "/api/v1/users/" + target["id"] + "/role"
    body = {
        "role": "MEDICAL",
        "version": target["version"],
        "reason": "Cambio autorizado",
        "human_confirmation": True,
    }
    headers = {
        "Authorization": "Bearer " + p.tokens["admin1"],
        "Accept": "application/" + fmt,
        "Content-Type": "application/" + fmt,
        "Idempotency-Key": uuid4().hex,
    }

    def send(route, payload, hdr):
        encoded = (
            request_xml(payload).encode()
            if fmt == "xml"
            else __import__("json").dumps(payload)
        )
        return requests.post(
            p.urls["identidad_acceso"] + route, headers=hdr, data=encoded, timeout=20
        )

    initial = send(path, body, headers)
    assert initial.status_code == 403, initial.text
    challenge = next(
        item["challenge"]
        for item in body_response(initial, fmt)["error"]["details"]
        if item["code"] == "challenge"
    )
    proof_response = send(
        "/api/v1/auth/reauthentication-proofs",
        {"password": p.env.state["password"], "challenge": challenge},
        headers,
    )
    assert proof_response.status_code == 200, proof_response.text
    proof = body_response(proof_response, fmt)["data"]
    assert proof["operation"] == "user_role" and proof["resource_id"] == target["id"]
    first = send(
        path, body, dict(headers, **{"X-Reauthentication-Proof": proof["proof"]})
    )
    replay = send(path, body, headers)
    assert first.status_code == replay.status_code == 200, (first.text, replay.text)
    assert body_response(first, fmt)["data"] == body_response(replay, fmt)["data"]
    with p.owner("identidad_acceso") as conn:
        assert (
            conn.execute(
                "SELECT count(*) FROM activity_events WHERE event->>'action'='USER_ROLE_CHANGED' AND event->>'resource_id'=%s",
                (target["id"],),
            ).fetchone()[0]
            == 1
        )


@pytest.mark.parametrize("fmt", ["json", "xml"])
def test_bound_proof_replay_and_scope(p, monkeypatch, fmt):
    user = "reauth_" + uuid4().hex[:12]
    created = p.ok(
        "identidad_acceso",
        "POST",
        "/api/v1/users",
        user="admin1",
        data={
            "username": user,
            "password": p.env.state["password"],
            "role": "OPERATOR",
            "tenant_id": p.env.state["tenants"][0],
        },
    )
    app = p.apps["identidad_acceso"]
    monkeypatch.setitem(
        app.config, "REAUTH_REQUIRED_OPERATIONS", ["user_state", "user_role"]
    )
    path = "/api/v1/users/" + created["id"]
    body = {"active": False, "version": created["version"]}
    key = uuid4().hex

    def send(method, route, data, *, idem=None, proof=None, token=None):
        headers = {
            "Authorization": "Bearer " + (token or p.tokens["admin1"]),
            "Accept": "application/" + fmt,
            "Content-Type": "application/" + fmt,
            "Idempotency-Key": idem or uuid4().hex,
        }
        if proof:
            headers["X-Reauthentication-Proof"] = proof
        return requests.request(
            method,
            p.urls["identidad_acceso"] + route,
            headers=headers,
            data=request_xml(data).encode()
            if fmt == "xml"
            else __import__("json").dumps(data),
            timeout=20,
        )

    def challenge_for(route=path, data=body, idem=key, token=None):
        response = send("PATCH", route, data, idem=idem, token=token)
        assert response.status_code == 403, response.text
        error = body_response(response, fmt)["error"]
        assert error["code"] == "reauthentication_required"
        return next(
            item["challenge"]
            for item in error["details"]
            if item["code"] == "challenge"
        )

    def proof_for(challenge, token=None):
        response = send(
            "POST",
            "/api/v1/auth/reauthentication-proofs",
            {"password": p.env.state["password"], "challenge": challenge},
            token=token,
        )
        assert response.status_code == 200, response.text
        value = body_response(response, fmt)["data"]
        assert (
            value["operation"] == "user_state" and value["resource_id"] == created["id"]
        )
        return value["proof"]

    challenge = challenge_for()
    proof = proof_for(challenge)
    wrong_body = send(
        "PATCH",
        path,
        {"active": True, "version": created["version"]},
        idem=key,
        proof=proof,
    )
    assert wrong_body.status_code == 403
    wrong_key = send("PATCH", path, body, idem=uuid4().hex, proof=proof)
    assert wrong_key.status_code == 403
    first = send("PATCH", path, body, idem=key, proof=proof)
    replay = send("PATCH", path, body, idem=key, proof=proof)
    assert first.status_code == replay.status_code == 200, (first.text, replay.text)
    assert body_response(first, fmt)["data"] == body_response(replay, fmt)["data"]
    recovered = send("PATCH", path, body, idem=key)
    assert recovered.status_code == 200
    assert body_response(recovered, fmt)["data"] == body_response(first, fmt)["data"]
    assert body_response(first, fmt)["data"]["active"] is False
    with p.owner("identidad_acceso") as conn:
        events = conn.execute(
            "SELECT count(*) FROM activity_events WHERE event->>'action'='USER_STATE_CHANGED' AND event->>'resource_id'=%s",
            (created["id"],),
        ).fetchone()[0]
    assert events == 1
    tampered = challenge[:-1] + ("A" if challenge[-1] != "A" else "B")
    assert (
        send(
            "POST",
            "/api/v1/auth/reauthentication-proofs",
            {"password": p.env.state["password"], "challenge": tampered},
        ).status_code
        == 403
    )
    other = p.ok(
        "identidad_acceso",
        "POST",
        "/api/v1/auth/login",
        user=None,
        data={"username": "admin1", "password": p.env.state["password"]},
    )["access_token"]
    assert (
        send(
            "POST",
            "/api/v1/auth/reauthentication-proofs",
            {"password": p.env.state["password"], "challenge": challenge},
            token=other,
        ).status_code
        == 403
    )
    cross = p.request(
        "identidad_acceso",
        "PATCH",
        "/api/v1/users/" + p.env.state["accounts"]["operator2"]["id"],
        user="admin1",
        data={"active": False, "version": 1},
    )
    assert cross.status_code == 403
    assert not any("challenge" in entry for entry in cross.json()["error"]["details"])


def test_same_proof_concurrent_keys_one_intention(p, monkeypatch):
    user = "race_" + uuid4().hex[:12]
    created = p.ok(
        "identidad_acceso",
        "POST",
        "/api/v1/users",
        user="admin1",
        data={
            "username": user,
            "password": p.env.state["password"],
            "role": "OPERATOR",
            "tenant_id": p.env.state["tenants"][0],
        },
    )
    monkeypatch.setitem(
        p.apps["identidad_acceso"].config, "REAUTH_REQUIRED_OPERATIONS", ["user_state"]
    )
    path = "/api/v1/users/" + created["id"]
    body = {"active": False, "version": created["version"]}
    key = uuid4().hex
    initial = p.request(
        "identidad_acceso", "PATCH", path, user="admin1", data=body, key=key
    )
    assert initial.status_code == 403
    challenge = initial.json()["error"]["details"][0]["challenge"]
    proof = p.ok(
        "identidad_acceso",
        "POST",
        "/api/v1/auth/reauthentication-proofs",
        user="admin1",
        data={"password": p.env.state["password"], "challenge": challenge},
    )["proof"]
    barrier = Barrier(2)

    def submit(idem):
        barrier.wait(timeout=10)
        return p.request(
            "identidad_acceso",
            "PATCH",
            path,
            user="admin1",
            data=body,
            key=idem,
            headers={"X-Reauthentication-Proof": proof},
        ).status_code

    with ThreadPoolExecutor(2) as executor:
        results = list(executor.map(submit, [key, uuid4().hex]))
    assert sorted(results) == [200, 403]
    with p.owner("identidad_acceso") as conn:
        events = conn.execute(
            "SELECT count(*) FROM activity_events WHERE event->>'action'='USER_STATE_CHANGED' AND event->>'resource_id'=%s",
            (created["id"],),
        ).fetchone()[0]
    assert events == 1


def test_signed_challenge_binds_actor_session_and_normalized_body(monkeypatch):
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from flask import Flask, g
    from redhouse.errors import APIError
    from redhouse.reauth import binding, challenge, verify_challenge

    private = Ed25519PrivateKey.generate()
    private_pem = private.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()
    public_pem = (
        private.public_key()
        .public_bytes(
            serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
        )
        .decode()
    )
    app = Flask(__name__)
    app.config.update(
        SERVICE="identidad_acceso",
        SERVICE_PRIVATE_KEY=private_pem,
        SERVICE_PUBLIC_KEYS={"identidad_acceso": public_pem},
    )
    actor = {"id": str(uuid4()), "tenant_id": str(uuid4()), "version": 7}
    sid, identifier = str(uuid4()), str(uuid4())
    with app.test_request_context(
        "/api/v1/users/" + identifier,
        method="PATCH",
        headers={"Idempotency-Key": "test-key-123"},
    ):
        g.actor, g.claims = actor, {"sid": sid}
        first = binding("user_state", identifier, {"active": False, "version": 1})
        same = binding("user_state", identifier, {"version": 1, "active": False})
        changed = binding("user_state", identifier, {"version": 2, "active": False})
        assert first == same and first["body_hash"] != changed["body_hash"]
        token = challenge(first)
        assert verify_challenge(token)["body_hash"] == first["body_hash"]
        g.claims = {"sid": str(uuid4())}
        with pytest.raises(APIError):
            verify_challenge(token)
        g.claims = {"sid": sid}
        monkeypatch.setattr("redhouse.reauth.time.time", lambda: 10_000_000_000)
        with pytest.raises(APIError):
            verify_challenge(token)


def test_critical_operations_cannot_be_disabled_in_production():
    from redhouse.config import settings

    config = settings(
        "documentos",
        {
            "DATABASE_URL": "unused",
            "JWT_PUBLIC_KEY": "unused",
            "TESTING": False,
            "REAUTH_REQUIRED_OPERATIONS": [],
        },
    )
    assert {"resource_release", "reservation_create", "user_state", "user_role"} <= set(
        config["REAUTH_REQUIRED_OPERATIONS"]
    )


def test_old_unbound_reauthentication_payload_is_rejected(p):
    response = p.request(
        "identidad_acceso",
        "POST",
        "/api/v1/auth/reauthenticate",
        user="admin1",
        data={
            "password": p.env.state["password"],
            "operation": "user_state",
            "resource_id": str(uuid4()),
        },
    )
    assert response.status_code == 410
    assert response.json()["error"]["code"] == "reauthentication_protocol_obsolete"
    unsupported = p.request(
        "identidad_acceso",
        "POST",
        "/api/v1/auth/reauthentication-proofs",
        user="admin1",
        data={
            "password": p.env.state["password"],
            "operation": "user_state",
            "resource_id": str(uuid4()),
        },
    )
    assert unsupported.status_code in (400, 422)


def test_proof_binding_rejects_new_key_or_changed_body_without_consuming(monkeypatch):
    import hashlib
    import json

    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from flask import Flask, g, request
    from redhouse.errors import APIError
    from redhouse.reauth import _check, binding, challenge, verify_challenge

    private = Ed25519PrivateKey.generate()
    private_pem = private.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()
    public_pem = (
        private.public_key()
        .public_bytes(
            serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
        )
        .decode()
    )
    app = Flask(__name__)
    app.config.update(
        SERVICE="identidad_acceso",
        SERVICE_PRIVATE_KEY=private_pem,
        SERVICE_PUBLIC_KEYS={"identidad_acceso": public_pem},
        REDIS_PREFIX="test:",
    )
    actor = {"id": str(uuid4()), "tenant_id": str(uuid4()), "version": 1}
    identifier = str(uuid4())
    proof = "P" * 64
    storage = {}

    class FakeRedis:
        def get(self, key):
            return storage.get(key)

    monkeypatch.setattr(
        "redhouse.reauth.authorize",
        lambda *_args, **_kwargs: {"tenant_id": actor["tenant_id"]},
    )
    monkeypatch.setattr("redhouse.reauth.redis_call", lambda fn: fn(FakeRedis()))
    with app.test_request_context(
        "/api/v1/users/" + identifier,
        method="PATCH",
        headers={"Idempotency-Key": "first-key-123", "X-Reauthentication-Proof": proof},
    ):
        g.actor, g.claims = actor, {"sid": str(uuid4())}
        body = {"active": False, "version": 1}
        descriptor = verify_challenge(
            challenge(binding("user_state", identifier, body))
        )
        storage["test:reauth:v1:" + hashlib.sha256(proof.encode()).hexdigest()] = (
            json.dumps(descriptor)
        )
        assert _check("user_state", identifier, body)["tenant_id"] == actor["tenant_id"]
        request.environ["HTTP_IDEMPOTENCY_KEY"] = "other-key-123"
        with pytest.raises(APIError):
            _check("user_state", identifier, body)
        request.environ["HTTP_IDEMPOTENCY_KEY"] = "first-key-123"
        with pytest.raises(APIError):
            _check("user_state", identifier, {"active": True, "version": 1})
        assert _check("user_state", identifier, body)["tenant_id"] == actor["tenant_id"]


def test_all_nine_critical_routes_have_explicit_owner_and_roles():
    import importlib

    from redhouse.reauth import SCOPES

    expected = {
        "resource_release",
        "lab_result_review",
        "evaluation_review",
        "rule_transition",
        "anomaly_resolve",
        "reservation_create",
        "resource_destination",
        "user_state",
        "user_role",
    }
    assert {operation for _, operation in SCOPES} == expected
    for service in {name for name, _ in SCOPES}:
        app = importlib.import_module("ms_" + service).create_app(
            {
                "DATABASE_URL": "unused",
                "JWT_PUBLIC_KEY": "unused",
                "JWT_PRIVATE_KEY": "unused",
                "SERVICE_PRIVATE_KEY": "unused",
                "TESTING": True,
            }
        )
        contracts = {
            contract["name"]: contract for contract in app.extensions["contracts"]
        }
        for owner, operation in SCOPES:
            if owner != service:
                continue
            assert operation in contracts
            contract = contracts[operation]
            assert (
                contract["method"] in ("POST", "PATCH")
                and contract["model"]
                and contract["roles"]
                and not contract["public"]
            )


def test_json_xml_normalize_to_same_bound_digest():
    import json

    from flask import Flask, g
    from ms_identidad_acceso.routes import UserState
    from redhouse.codec import parse
    from redhouse.reauth import binding

    app = Flask(__name__)
    app.config.update(
        SERVICE="identidad_acceso", SERVICE_PRIVATE_KEY="synthetic-owner-key"
    )
    actor = {"id": str(uuid4()), "tenant_id": str(uuid4()), "version": 2}
    sid, target = str(uuid4()), str(uuid4())
    data = {"active": False, "version": 1}
    descriptors = []
    for content_type, raw in [
        ("application/json", json.dumps(data).encode()),
        ("application/xml", request_xml(dict(reversed(list(data.items())))).encode()),
    ]:
        with app.test_request_context(
            "/api/v1/users/" + target,
            method="PATCH",
            data=raw,
            content_type=content_type,
            headers={"Idempotency-Key": "same-key-123"},
        ):
            g.actor, g.claims = actor, {"sid": sid}
            descriptors.append(binding("user_state", target, parse(UserState)))
    assert descriptors[0] == descriptors[1]
