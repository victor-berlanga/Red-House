"""Pure candidate checks; no services, databases, users, sockets or credentials."""

import json
import os
from types import SimpleNamespace

import pytest
from lxml import etree

os.environ["LOCUST_SKIP_MONKEY_PATCH"] = "1"
from redhouse.codec import xml_value
from tests import load_finite_support as support
from tests import locust_transactions as locust

from scripts import load_client as client
from scripts import load_workflows as flows
from scripts import sustained_read as phase

ID = "00000000-0000-4000-8000-000000000001"


class Reply:
    def __init__(
        self,
        mime="application/json",
        code="reauthentication_required",
        owner="compatibilidad",
    ):
        self.payload = {
            "meta": {"correlation_id": ID, "service": owner, "version": "0.4.4"},
            "error": {
                "code": code,
                "message": "Confirmación requerida",
                "details": [
                    {
                        "field": "reauthentication",
                        "code": "challenge",
                        "challenge": "x" * 60,
                    }
                ],
            },
        }
        self.headers = {"Content-Type": mime}
        self.status_code = 403
        self.failed = []
        self.passed = False
        if mime == "application/xml":
            root = etree.Element("response")
            xml_value(root, self.payload)
            self.content = etree.tostring(root)
        else:
            self.content = json.dumps(self.payload).encode()

    def json(self):
        return self.payload

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def failure(self, e):
        self.failed.append(e)

    def success(self):
        self.passed = True


@pytest.mark.parametrize("mime", ["application/json", "application/xml"])
def test_challenge_is_validated_in_both_representations(mime):
    r = Reply(mime)
    assert client.reauthentication_challenge(r, "compatibilidad", mime) == "x" * 60


@pytest.mark.parametrize(
    "code,owner",
    [("forbidden", "compatibilidad"), ("reauthentication_required", "inventario")],
)
def test_denial_or_wrong_owner_never_becomes_challenge(code, owner):
    with pytest.raises(ValueError):
        client.reauthentication_challenge(
            Reply(code=code, owner=owner), "compatibilidad", "application/json"
        )


def test_expected_403_is_opt_in_and_not_a_failed_business_request():
    reply = Reply()
    http = SimpleNamespace(request=lambda *_a, **_k: reply)
    api = client.LoadSession(http, {"compatibilidad": "http://127.0.0.1:19111"})
    api.access = "synthetic"
    api.renew_at = float("inf")
    with pytest.raises(client.ReauthenticationRequired) as err:
        api.request(
            "compatibilidad",
            "/api/v1/evaluations",
            "Eval",
            method="POST",
            expected=201,
            body={"request_id": ID},
            allow_reauthentication=True,
        )
    assert reply.passed and not reply.failed and "x" * 60 not in str(err.value)
    with pytest.raises(client.LoadFailure, match="http_403"):
        api.request(
            "compatibilidad",
            "/api/v1/evaluations",
            "Eval",
            method="POST",
            expected=201,
            body={"request_id": ID},
        )


def account():
    return {"id": ID, "tenant_id": ID, "role": "MEDICAL"}


def test_trace_fsync_before_send_same_key_body_proof_only_in_memory(tmp_path):
    p = tmp_path / "trace"
    calls = []
    challenge = "challenge-private-" * 4
    proof = "proof-private"

    def request(service, path, label, **kw):
        saved = [json.loads(line) for line in p.read_text().splitlines()]
        assert any(x["kind"] == "intent" and x["key"] == kw["key"] for x in saved)
        calls.append(kw.copy())
        if len(calls) == 1:
            raise client.ReauthenticationRequired(challenge)
        return {"id": ID}

    def reauth(value, op, resource):
        assert (value, op, resource) == (challenge, "evaluation_review", ID)
        return proof, 30000

    trace = flows.TransactionTrace(
        SimpleNamespace(request=request), p, account(), lambda: "measuring", reauth
    )
    trace.begin()
    trace.request(
        "compatibilidad",
        "/api/v1/evaluations/" + ID + "/reviews",
        "Review",
        method="POST",
        key="same-key",
        body={"resource_id": ID},
        critical=("evaluation_review", ID),
    )
    trace.end(None)
    trace.close()
    assert len(calls) == 3 and all(
        x["key"] == "same-key" and x["body"] == {"resource_id": ID} for x in calls
    )
    assert calls[1]["proof"] == proof and "proof" not in calls[2]
    assert challenge not in p.read_text() and proof not in p.read_text()
    assert trace.mfa_wait_ms == 30000


@pytest.mark.parametrize(
    "body",
    [
        {"password": "private"},
        {"custody": {"proof": "private"}},
        {"list": [{"otp": "private"}]},
    ],
)
def test_trace_refuses_security_values_before_writing_or_network(tmp_path, body):
    p = tmp_path / "trace"
    calls = []
    trace = flows.TransactionTrace(
        SimpleNamespace(request=lambda *_a, **_k: calls.append(1)),
        p,
        account(),
        lambda: "measuring",
    )
    with pytest.raises(client.LoadFailure, match="secret_must_not_enter_trace"):
        trace.request(
            "compatibilidad",
            "/api/v1/evaluations",
            "Eval",
            method="POST",
            key="same-key",
            body=body,
        )
    trace.close()
    assert not calls and not p.read_text()


def test_lost_write_stays_one_attempt_without_automatic_replacement(tmp_path):
    p = tmp_path / "trace"
    calls = []

    def lost(*_a, **_k):
        calls.append(1)
        raise client.LoadFailure("http_0")

    trace = flows.TransactionTrace(
        SimpleNamespace(request=lost), p, account(), lambda: "measuring"
    )
    trace.begin()
    with pytest.raises(client.LoadFailure, match="http_0"):
        trace.request(
            "transporte",
            "/api/v1/shipments",
            "Plan",
            method="POST",
            key="same-key",
            body={"reservation_id": ID},
        )
    trace.close()
    rows = [json.loads(x) for x in p.read_text().splitlines()]
    assert (
        len(calls) == 1
        and sum(r["kind"] == "intent" for r in rows) == 1
        and not any(r["kind"] == "response" for r in rows)
    )


def test_finite_inventory_cannot_share_units_across_actors():
    rows = [
        {
            "username": n,
            "id": n,
            "tenant_id": "tenant",
            "role": r,
            "mime": "application/json" if r == "TRANSPORT" else "application/xml",
        }
        for n, r in locust.FINITE_PROFILES.items()
    ]
    state = {
        "directory": "/private/tmp/fixture",
        "accounts": {r["username"]: r for r in rows},
    }
    m = {
        "directory": state["directory"],
        "schema_version": 22,
        "kind": "finite-three-roles-v1",
        "gps": False,
        "preparation_complete": True,
        "accounts": rows,
        "cases": {
            r: [
                {
                    "case_id": f"{r}{i}",
                    "resource_id": f"{r}{i}",
                    "approved_reason": "Sintético",
                }
                for i in range(3)
            ]
            for r in locust.FINITE_WORKFLOWS
        },
    }
    assert locust.finite_manifest(state, m) == rows
    m["cases"]["TRANSPORT"][1]["resource_id"] = m["cases"]["MEDICAL"][0]["resource_id"]
    with pytest.raises(ValueError, match="finite_inventory_not_disjoint"):
        locust.finite_manifest(state, m)


def test_transport_has_exact_states_scans_versions_and_no_gps():
    calls = []
    events = []
    current = {
        "id": "shipment",
        "reservation_id": "reservation",
        "transport_user_id": ID,
        "status": "PREPARED",
        "version": 2,
        "inventory_pending": False,
    }
    context = {
        "shipment_id": "shipment",
        "shipment_version": 2,
        "origin": {"operators": [{"id": "origin"}]},
        "destination": {"operators": [{"id": "destination"}]},
    }

    def request(service, path, label, **kw):
        calls.append((path, kw))
        if path.endswith("operational-context"):
            answer = context
        elif path.endswith("/scan"):
            answer = {
                "shipment_id": "shipment",
                "resource_id": "unit",
                "verified": True,
                "version": current["version"],
            }
        elif path.endswith("/transitions"):
            body = kw["body"]
            assert body["version"] == current["version"]
            current.update(status=body["state"], version=current["version"] + 1)
            answer = current.copy()
        else:
            answer = current.copy()
        assert kw.get("check", lambda _: True)(answer)
        return answer

    api = SimpleNamespace(
        account=account(),
        request=request,
        emit=lambda kind, **kw: events.append((kind, kw)),
    )
    flows.transport_cycle(
        api,
        {
            "case_id": "case",
            "shipment_id": "shipment",
            "resource_id": "unit",
            "reservation_id": "reservation",
            "origin_operator_id": "origin",
            "destination_operator_id": "destination",
            "seal": "synthetic",
            "approved_reason": "Ensayo sintético",
        },
    )
    assert [kw["body"]["state"] for p, kw in calls if p.endswith("/transitions")] == [
        "COLLECTED",
        "IN_TRANSIT",
        "DELIVERED",
    ]
    assert len([p for p, _ in calls if p.endswith("/scan")]) == 2
    assert (
        events[0][1]["gps_in_this_increment"] is False
        and events[0][1]["accepted_by_destination"] is False
    )


@pytest.mark.parametrize(
    "service,path,body,expected",
    [
        (
            "compatibilidad",
            "/api/v1/evaluations",
            {"request_id": ID},
            "evaluation_create",
        ),
        (
            "compatibilidad",
            "/api/v1/evaluations/{identifier}/reviews",
            {
                "resource_id": ID,
                "decision": "FAVORABLE",
                "human_confirmation": True,
                "reason": "Ensayo sintético autorizado",
            },
            "evaluation_review:" + ID,
        ),
        (
            "inventario",
            "/api/v1/reservations",
            {
                "evaluation_id": ID,
                "resource_id": ID,
                "human_confirmation": True,
                "reason": "Ensayo sintético autorizado",
            },
            "reservation_create",
        ),
        (
            "transporte",
            "/api/v1/shipments",
            {
                "reservation_id": ID,
                "transport_user_id": ID,
                "departure_at": "2026-11-17T10:00:00+00:00",
                "eta": "2026-11-17T11:00:00+00:00",
                "human_confirmation": True,
                "reason": "Ensayo sintético autorizado",
            },
            "shipment_create",
        ),
        (
            "transporte",
            "/api/v1/shipments/{identifier}/scan",
            {"scanned_resource_id": ID},
            "shipment_scan:" + ID,
        ),
        (
            "transporte",
            "/api/v1/shipments/{identifier}/transitions",
            {
                "state": "IN_TRANSIT",
                "version": 2,
                "human_confirmation": True,
                "reason": "Ensayo sintético autorizado",
            },
            "shipment_transition:" + ID,
        ),
    ],
)
def test_oracle_normalizes_using_real_owner_models(service, path, body, expected):
    name, normalized, fingerprint = support.normalized_intent(
        {
            "service": service,
            "canonical": path,
            "path": path.replace("{identifier}", ID),
            "body": body,
        }
    )
    assert name == expected
    assert fingerprint == support.digest(
        normalized
        if name == "reservation_create"
        else {"operation": name, "input": normalized}
    )
    if name.startswith("shipment_transition:"):
        assert normalized["custody"] is None


def trace_fixture():
    accounts = [
        {"id": str(i), "tenant_id": "tenant", "role": role}
        for i, role in enumerate(support.PROFILES.values())
    ]
    events = []
    after = {"atomic": {}, "sagas": {}}
    for a in accounts:
        for cycle in range(1, 4):
            key = "key-" + str(cycle)
            base = {
                "user_id": a["id"],
                "tenant_id": a["tenant_id"],
                "role": a["role"],
                "cycle": cycle,
                "stage": "preflight" if cycle == 1 else "measuring",
                "at": cycle * 10,
            }
            intent = dict(
                base,
                kind="intent",
                key=key,
                service="compatibilidad",
                canonical="/api/v1/evaluations",
                path="/api/v1/evaluations",
                body={"request_id": ID},
            )
            operation, _body, fingerprint = support.normalized_intent(intent)
            result = {"id": "r" + str(cycle)}
            after["atomic"]["|".join(("compatibilidad", a["id"], key))] = {
                "operation": operation,
                "fingerprint": fingerprint,
                "result": result,
            }
            events.extend(
                [
                    dict(base, kind="cycle_start"),
                    intent,
                    dict(base, kind="response", key=key, result=result),
                    dict(base, kind="case_result", case_id=a["id"] + str(cycle)),
                    dict(base, kind="cycle_end", success=True, at=cycle * 10 + 5),
                ]
            )
            if cycle == 2:
                events.extend(
                    [
                        dict(base, kind="replay_intent", key=key),
                        dict(base, kind="replay_response", key=key, result=result),
                    ]
                )
    return accounts, events, after


def test_oracle_preserves_failed_replay_and_detects_omitted_actor_cycle():
    accounts, events, after = trace_fixture()
    empty = {"atomic": {}, "sagas": {}}
    good = support.reconcile_finite_trace(events, empty, after, accounts)
    assert (
        good["errors"] == []
        and good["active_cycle_peak"] == 3
        and good["active_cycle_seconds"] == 10
    )
    damaged = [
        r
        for r in events
        if not (
            r["user_id"] == "0"
            and (
                r["kind"] == "replay_response"
                or r["kind"] == "cycle_end"
                and r["cycle"] == 3
            )
        )
    ]
    bad = support.reconcile_finite_trace(damaged, empty, after, accounts)
    assert bad["unconfirmed_replays"] == 1 and bad["incomplete_cycles"] == 1
    assert "unconfirmed_replay" in bad["errors"]


def test_oracle_reconciles_lost_response_and_untracked_commit():
    accounts, events, after = trace_fixture()
    empty = {"atomic": {}, "sagas": {}}
    events = [
        r
        for r in events
        if not (r["user_id"] == "0" and r["cycle"] == 3 and r["kind"] == "response")
    ]
    after["atomic"]["unknown"] = {"operation": "unexpected"}
    bad = support.reconcile_finite_trace(events, empty, after, accounts)
    assert bad["response_lost_committed"] == 1 and "untracked_commit" in bad["errors"]


def result_fixture():
    rows = [
        {
            "method": "TRANSACTION",
            "name": "Recorrido finito / " + role,
            "requests": 2,
            "failures": 0,
            "p95_ms": 60000,
        }
        for role in support.PROFILES.values()
    ]
    rows.append(
        {
            "method": "GET",
            "name": "Consulta",
            "requests": 9,
            "failures": 0,
            "p95_ms": 100,
        }
    )
    return {
        "runner_exit": 0,
        "session_revocation_verified": True,
        "session_count_verified": True,
        "cleanup_failures": 0,
        "failures": 0,
        "counts": {"Identidad / revocación al salir": 3},
        "timing": {
            "measurement": rows,
            "started": 0,
            "measured": 30,
            "finished": 150,
            "stage": "finished",
            "user_errors": 0,
            "warmup_min_users": 3,
            "measurement_min_users": 3,
            "warmup": {"requests": 9, "failures": 0},
        },
        "business": {
            "persistence_verified": True,
            "not_committed": 0,
            "response_lost_committed": 0,
            "incomplete_cycles": 0,
            "replays": 3,
            "unconfirmed_replays": 0,
            "measured_completed": {r: 2 for r in support.PROFILES.values()},
        },
    }


def test_finite_acceptance_does_not_treat_totp_as_capacity_but_requires_read_target():
    result = result_fixture()
    accepted = phase.evaluate_finite_transactions(result)
    assert (
        accepted["execution_valid"]
        and accepted["measurement_accepted"]
        and not accepted["capacity_estimate"]
    )
    result["timing"]["measurement"][-1]["p95_ms"] = 2000
    rejected = phase.evaluate_finite_transactions(result)
    assert rejected["execution_valid"] and not rejected["measurement_accepted"]


@pytest.mark.parametrize(
    "field", ["session_revocation_verified", "session_count_verified"]
)
def test_finite_missing_closure_never_accepted(field):
    result = result_fixture()
    result[field] = False
    assert not phase.evaluate_finite_transactions(result)["execution_valid"]


@pytest.mark.parametrize("resource_case", ["valid", "foreign", "expired"])
def test_coordinator_reads_expiry_from_public_resource_dto(resource_case):
    from datetime import datetime, timedelta, timezone

    from jsonschema import Draft202012Validator, FormatChecker

    reservation = {
        "id": ID,
        "resource_id": ID,
        "status": "RESERVED",
        "shipment_id": None,
        "route_id": ID,
        "route_version": 1,
        "origin_id": ID,
    }
    schema = json.loads(
        (
            client.ROOT / "ms_inventario/contracts/reservation_detail.response.json"
        ).read_text()
    )["properties"]["data"]
    assert "expires_at" not in reservation
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(reservation)
    expires = datetime.now(timezone.utc) + timedelta(
        hours=-1 if resource_case == "expired" else 4
    )
    resource = {
        "id": "00000000-0000-4000-8000-000000000002"
        if resource_case == "foreign"
        else ID,
        "status": "RESERVED",
        "expires_at": expires.isoformat(),
    }
    resource_schema = json.loads(
        (
            client.ROOT / "ms_inventario/contracts/resource_detail.response.json"
        ).read_text()
    )["properties"]["data"]
    Draft202012Validator(resource_schema, format_checker=FormatChecker()).validate(
        resource
    )
    calls, events = [], []

    def request(service, path, label, **kw):
        calls.append((path, kw))
        if path.startswith("/api/v1/reservations/"):
            answer = reservation
        elif path.startswith("/api/v1/resources/"):
            answer = resource
        elif path.startswith("/api/v1/routes/"):
            answer = {"id": ID, "version": 1, "travel_minutes": 15}
        elif path.startswith("/api/v1/users?"):
            answer = {
                "items": [
                    {"id": ID, "role": "TRANSPORT", "active": True, "tenant_id": ID}
                ]
            }
        else:
            assert path in ("/api/v1/shipments", "/api/v1/shipments/" + ID)
            answer = {
                "id": ID,
                "reservation_id": ID,
                "transport_user_id": ID,
                "status": "PLANNED",
                "inventory_pending": False,
            }
        if not kw.get("check", lambda _: True)(answer):
            raise client.LoadFailure("response_correlation")
        return answer

    api = SimpleNamespace(request=request, emit=lambda *a, **k: events.append(k))
    case = {
        "case_id": ID,
        "reservation_id": ID,
        "resource_id": ID,
        "transport_user_id": ID,
        "transport_username": "transport1",
        "approved_reason": "Preparación sintética autorizada",
    }
    if resource_case == "valid":
        flows.coordinator_cycle(api, case)
        assert len(events) == 1 and events[0]["status"] == "PLANNED"
        mutation = [kw for _, kw in calls if kw.get("method") == "POST"]
        assert len(mutation) == 1
        assert datetime.fromisoformat(mutation[0]["body"]["eta"]) < expires
    else:
        with pytest.raises(
            client.LoadFailure,
            match=(
                "response_correlation"
                if resource_case == "foreign"
                else "prepared_reservation_expiring"
            ),
        ):
            flows.coordinator_cycle(api, case)
        assert not events and not any(kw.get("method") == "POST" for _, kw in calls)
    assert sum(path == "/api/v1/resources/" + ID for path, _ in calls) == 1


def test_medical_accepts_public_review_without_operation_scope():
    from jsonschema import Draft202012Validator, FormatChecker

    review = {
        "id": ID,
        "evaluation_id": ID,
        "resource_id": ID,
        "decision": "FAVORABLE",
        "actor_id": ID,
        "tenant_id": ID,
        "reason": "Ensayo académico sintético",
        "created_at": "2026-11-17T00:00:00Z",
    }
    schema = json.loads(
        (
            client.ROOT / "ms_compatibilidad/contracts/evaluation_review.response.json"
        ).read_text()
    )["properties"]["data"]
    assert (
        "operation_scope" not in review
        and "operation_scope" not in schema["properties"]
    )
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(review)
    events, critical = [], []

    def request(service, path, label, **kw):
        if path.startswith("/api/v1/requests/"):
            answer = {"id": ID, "status": "OPEN"}
        elif path == "/api/v1/evaluations":
            answer = {"id": ID, "request_id": ID, "candidates": [{"resource_id": ID}]}
        elif path.endswith("/reviews"):
            answer = review
        elif path == "/api/v1/reservations":
            answer = {"operation_id": ID}
        else:
            assert path == "/api/v1/operations/" + ID
            answer = {
                "operation_id": ID,
                "status": "COMPLETED",
                "reservation": {
                    "id": ID,
                    "resource_id": ID,
                    "request_id": ID,
                    "status": "RESERVED",
                },
            }
        assert kw.get("check", lambda _: True)(answer)
        if kw.get("critical"):
            critical.append(kw["critical"])
        return answer

    flows.medical_cycle(
        SimpleNamespace(request=request, emit=lambda *a, **k: events.append(k)),
        {
            "case_id": ID,
            "request_id": ID,
            "resource_id": ID,
            "approved_reason": "Ensayo académico sintético",
        },
    )
    assert critical == [("evaluation_review", ID), ("reservation_create", ID)]
    assert len(events) == 1 and events[0]["status"] == "RESERVED"
