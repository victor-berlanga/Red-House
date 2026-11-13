"""Cuatro familias críticas: autorización, reto, efecto y repetición duradera."""

import json
from uuid import uuid4

import pytest
import psycopg
import requests
from psycopg.types.json import Jsonb
from redhouse.examples import request_xml
from redhouse.xml_response import validate_response

from .helpers import iso, recipient_request, resource, route

CONFIRM = {"human_confirmation": True, "reason": "Prueba sintética autorizada"}


def payload(response, fmt):
    return (
        response.json()
        if fmt == "json"
        else validate_response(response.content, {"type": "object"})
    )


@pytest.mark.parametrize("fmt", ["json", "xml"])
@pytest.mark.parametrize(
    "family",
    ["resource_destination", "evaluation_review", "rule_transition", "anomaly_resolve"],
)
def test_protected_family_challenge_scope_and_replay(p, monkeypatch, family, fmt):
    user = "medical1"
    other = "medical2"
    if family == "resource_destination":
        unit = resource(p)
        service, identifier = "inventario", unit["id"]
        path = f"/api/v1/resources/{identifier}/destination"
        body = dict(
            CONFIRM,
            version=unit["version"],
            destination="DISCARDED",
            reference="Acta sintética",
            occurred_at=iso(),
        )
        table, column = "resource_destinations", "resource_id"
    elif family == "evaluation_review":
        unit = resource(p)
        _, request = recipient_request(p)
        route(p)
        ev = p.ok(
            "compatibilidad",
            "POST",
            "/api/v1/evaluations",
            data={"request_id": request["id"]},
        )
        assert any(c["resource_id"] == unit["id"] for c in ev["candidates"])
        user, other = "medical2", "medical1"
        service, identifier = "compatibilidad", ev["id"]
        path = f"/api/v1/evaluations/{identifier}/reviews"
        body = dict(CONFIRM, resource_id=unit["id"], decision="FAVORABLE")
        table, column = "reviews", "evaluation_id"
    elif family == "rule_transition":
        profile = p.ok(
            "compatibilidad",
            "POST",
            "/api/v1/laboratory/profiles",
            user="medical1",
            data={
                "name": "Perfil sintético",
                "kind": "BLOOD",
                "component": "RBC",
                "version": 1,
                "required_tests": ["ABO"],
                "source": "Prueba sintética",
                "synthetic": True,
                "effective_at": iso(),
            },
        )
        service, identifier = "compatibilidad", profile["id"]
        with psycopg.connect(p.apps[service].config["DATABASE_URL"]) as runtime:
            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                runtime.execute(
                    "SELECT * FROM lab_profiles WHERE id=%s FOR UPDATE", (identifier,)
                )
            runtime.rollback()
        with p.owner(service) as owner:
            with pytest.raises(
                psycopg.errors.CheckViolation,
                match="Historical records are append-only",
            ):
                owner.execute(
                    "UPDATE lab_profiles SET name=name WHERE id=%s", (identifier,)
                )
            owner.rollback()
        path = f"/api/v1/laboratory/profiles/{identifier}/actions"
        body = dict(CONFIRM, sequence=1, state="IN_REVIEW")
        table, column = "rule_actions", "profile_id"
    else:
        service, identifier, user, other = (
            "auditoria",
            str(uuid4()),
            "auditor1",
            "medical1",
        )
        tenant = p.env.state["tenants"][0]
        with p.owner("identidad_acceso") as conn:
            region = conn.execute(
                "SELECT region_id FROM institutions WHERE id=%s", (tenant,)
            ).fetchone()[0]
        with p.owner("auditoria") as conn:
            conn.execute(
                "INSERT INTO anomaly_reviews(id,tenant_id,region_id,source,source_run_id,deduplication_key,evidence,correlation_id,responsible_id) VALUES(%s,%s,%s,'priorizacion_geografia',%s,%s,%s,%s,%s)",
                (
                    identifier,
                    tenant,
                    region,
                    str(uuid4()),
                    uuid4().hex,
                    Jsonb({}),
                    uuid4().hex,
                    p.env.state["accounts"][user]["id"],
                ),
            )
        path = f"/api/v1/anomaly-reviews/{identifier}/resolve"
        body = dict(CONFIRM, version=1, state="DISMISSED")
        table, column = "anomaly_actions", "review_id"
    monkeypatch.setitem(p.apps[service].config, "REAUTH_REQUIRED_OPERATIONS", [family])
    headers = {
        "Accept": "application/" + fmt,
        "Content-Type": "application/" + fmt,
        "Authorization": "Bearer " + p.tokens[user],
        "Idempotency-Key": uuid4().hex,
    }
    encoded = json.dumps(body) if fmt == "json" else request_xml(body).encode()

    def send(hdr):
        return requests.post(
            p.urls[service] + path, data=encoded, headers=hdr, timeout=20
        )

    denied = send(dict(headers, Authorization="Bearer " + p.tokens[other]))
    assert denied.status_code == 403, denied.text
    first = send(headers)
    assert first.status_code == 403, first.text
    error = payload(first, fmt)["error"]
    assert error["code"] == "reauthentication_required"
    challenge = next(
        item["challenge"] for item in error["details"] if item["code"] == "challenge"
    )
    with p.owner(service) as conn:
        assert (
            conn.execute(
                f"SELECT count(*) FROM {table} WHERE {column}=%s", (identifier,)
            ).fetchone()[0]
            == 0
        )
    auth = p.ok(
        "identidad_acceso",
        "POST",
        "/api/v1/auth/reauthentication-proofs",
        user=user,
        data={"password": p.env.state["password"], "challenge": challenge},
    )
    assert auth["operation"] == family and auth["resource_id"] == identifier
    done = send(dict(headers, **{"X-Reauthentication-Proof": auth["proof"]}))
    replay = send(headers)
    assert done.status_code in (200, 201), done.text
    assert replay.status_code == done.status_code, replay.text
    assert payload(done, fmt)["data"] == payload(replay, fmt)["data"]
    with p.owner(service) as conn:
        assert (
            conn.execute(
                f"SELECT count(*) FROM {table} WHERE {column}=%s", (identifier,)
            ).fetchone()[0]
            == 1
        )
