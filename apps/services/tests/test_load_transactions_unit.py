"""Oráculos transaccionales puros: no bases, servidores, sockets ni procesos."""

import importlib
import json
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest
from scripts.load_client import LoadFailure
from scripts.load_workflows import TransactionTrace
from scripts.sustained_read import evaluate_transactions

from tests.load_support import reconcile_transaction_log


def account():
    return {
        "id": str(uuid4()),
        "tenant_id": str(uuid4()),
        "role": "OPERATOR",
        "donor_id": None,
    }


def event(owner, kind, **kwargs):
    return {
        "kind": kind,
        "cycle": 1,
        "user_id": owner["id"],
        "tenant_id": owner["tenant_id"],
        "role": owner["role"],
        "stage": "measuring",
        "at": 1,
        **kwargs,
    }


def inventory_intent(owner):
    key, identifier = str(uuid4()), str(uuid4())
    intent = event(
        owner,
        "intent",
        service="inventario",
        key=key,
        path="/api/v1/resources",
        body={"folio": "LOAD-UNIT"},
    )
    result = {
        "id": identifier,
        "tenant_id": owner["tenant_id"],
        "folio": "LOAD-UNIT",
        "status": "QUARANTINE",
    }
    commit = {
        ("inventario", owner["id"], key): {
            "operation": "resource_create",
            "result": result,
        }
    }
    return intent, result, commit


def test_lost_response_stays_durable_and_never_uses_a_new_key(tmp_path):
    owner = account()
    calls = []

    def request(*args, **kwargs):
        calls.append(kwargs["key"])
        raise LoadFailure("http_0")

    path = tmp_path / "attempts.jsonl"
    trace = TransactionTrace(
        SimpleNamespace(request=request), path, owner, lambda: "measuring"
    )
    trace.begin()
    key = str(uuid4())
    with pytest.raises(LoadFailure):
        trace.request(
            "inventario",
            "/api/v1/resources",
            "Registrar",
            method="POST",
            key=key,
            body={"folio": "LOAD-UNIT"},
        )
    trace.end(LoadFailure("http_0"))
    trace.close()
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    assert [r["kind"] for r in rows] == ["cycle_start", "intent", "cycle_end"]
    assert calls == [key] and rows[1]["key"] == key
    assert path.stat().st_mode & 0o777 == 0o600


def test_replay_uses_identical_body_key_and_records_one_logical_intent(tmp_path):
    owner = account()
    calls = []

    def request(*args, **kwargs):
        calls.append(kwargs)
        return {"id": "same"}

    path = tmp_path / "attempts.jsonl"
    trace = TransactionTrace(
        SimpleNamespace(request=request), path, owner, lambda: "warmup"
    )
    trace.begin()
    trace.request(
        "inventario",
        "/api/v1/resources",
        "Registrar",
        method="POST",
        key=str(uuid4()),
        body={"folio": "LOAD-UNIT"},
    )
    trace.close()
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    assert calls[0] == calls[1]
    assert sum(r["kind"] == "intent" for r in rows) == 1
    assert sum(r["kind"] == "replay_response" for r in rows) == 1


def test_oracle_reconciles_committed_response_loss_and_retains_partial_cycle():
    owner = account()
    intent, result, commits = inventory_intent(owner)
    checked = reconcile_transaction_log(
        [event(owner, "cycle_start"), intent], commits, [owner]
    )
    assert checked["committed"] == 1 and checked["response_lost_committed"] == 1
    assert checked["incomplete_cycles"] == 1 and checked["not_committed"] == 0
    assert checked["expected"]["resources"][result["id"]]["status"] == "QUARANTINE"
    assert not checked["errors"]


def test_oracle_detects_untracked_commit_missing_commit_and_identity_mismatch():
    owner = account()
    intent, result, commits = inventory_intent(owner)
    assert (
        "untracked_commit" in reconcile_transaction_log([], commits, [owner])["errors"]
    )
    rows = [
        event(owner, "cycle_start"),
        intent,
        event(owner, "response", key=intent["key"], result=result),
    ]
    assert (
        "response_without_commit"
        in reconcile_transaction_log(rows, {}, [owner])["errors"]
    )
    rows[1] = dict(intent, tenant_id=str(uuid4()))
    assert (
        "trace_identity" in reconcile_transaction_log(rows, commits, [owner])["errors"]
    )


def test_complete_sample_cycle_requires_three_correlated_commits_and_versions():
    owner = account()
    intent, unit, commits = inventory_intent(owner)
    sample_id, profile = str(uuid4()), str(uuid4())
    sample = {
        "id": sample_id,
        "tenant_id": owner["tenant_id"],
        "resource_id": unit["id"],
        "profile_id": profile,
        "identifier": "LOAD-SAMPLE",
        "status": "REQUESTED",
        "version": 1,
    }
    key2, key3 = str(uuid4()), str(uuid4())
    second = event(
        owner,
        "intent",
        service="compatibilidad",
        key=key2,
        path="/api/v1/laboratory/samples",
        body={
            "resource_id": unit["id"],
            "profile_id": profile,
            "identifier": "LOAD-SAMPLE",
        },
    )
    third = event(
        owner,
        "intent",
        service="compatibilidad",
        key=key3,
        path="/api/v1/laboratory/samples/" + sample_id + "/receive",
        body={"version": 1, "decision": "RECEIVED"},
    )
    received = dict(sample, status="RECEIVED", version=2)
    commits.update(
        {
            ("compatibilidad", owner["id"], key2): {
                "operation": "lab_sample_create",
                "result": sample,
            },
            ("compatibilidad", owner["id"], key3): {
                "operation": "lab_sample_receive:" + sample_id,
                "result": received,
            },
        }
    )
    rows = [
        event(owner, "cycle_start"),
        intent,
        event(owner, "response", key=intent["key"], result=unit),
        second,
        event(owner, "response", key=key2, result=sample),
        third,
        event(owner, "response", key=key3, result=received),
        event(owner, "cycle_end", success=True),
    ]
    checked = reconcile_transaction_log(rows, commits, [owner])
    assert not checked["errors"] and checked["completed"] == {"OPERATOR": 1}
    assert checked["expected"]["samples"][sample_id]["version"] == 2
    third["body"]["version"] = 2
    assert (
        "sample_version" in reconcile_transaction_log(rows, commits, [owner])["errors"]
    )


def phase():
    def stat(method, name, n):
        return {
            "method": method,
            "name": name,
            "requests": n,
            "failures": 0,
            "p95_ms": 10,
            "p99_ms": 20,
        }

    return {
        "runner_exit": 0,
        "stopped_by_guard": False,
        "session_revocation_verified": True,
        "session_count_verified": True,
        "cleanup_failures": 0,
        "failures": 0,
        "counts": {"Identidad / revocación al salir": 12},
        "timing": {
            "stage": "finished",
            "started": 1,
            "measured": 31,
            "finished": 151,
            "user_errors": 0,
            "warmup_min_users": 12,
            "measurement_min_users": 12,
            "warmup": {"requests": 20, "failures": 0},
            "http": {},
            "measurement": [
                stat("GET", "consulta", 90),
                stat("POST", "escritura", 60),
                stat("TRANSACTION", "Recorrido / DONOR", 10),
                stat("TRANSACTION", "Recorrido / OPERATOR", 10),
            ],
        },
        "business": {
            "persistence_verified": True,
            "not_committed": 0,
            "response_lost_committed": 0,
            "incomplete_cycles": 0,
            "replays": 12,
            "unconfirmed_replays": 0,
            "measured_completed": {"DONOR": 10, "OPERATOR": 10},
        },
    }


def test_http_and_business_rates_are_separate_and_receipts_must_match():
    result = phase()
    checked = evaluate_transactions(result, 12, 120)
    assert checked["execution_valid"]
    assert checked["http_requests"] == 150 and checked["business_completed"] == 20
    assert (
        checked["http_per_second"] == 150 / 120
        and checked["business_per_second"] == 20 / 120
    )
    result["business"]["measured_completed"]["OPERATOR"] = 9
    assert not evaluate_transactions(result, 12, 120)["execution_valid"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("not_committed", 1),
        ("response_lost_committed", 1),
        ("incomplete_cycles", 1),
        ("replays", 11),
        ("unconfirmed_replays", 1),
        ("persistence_verified", False),
    ],
)
def test_partial_or_uncertain_business_never_passes(field, value):
    result = phase()
    result["business"][field] = value
    assert not evaluate_transactions(result, 12, 120)["execution_valid"]


def test_cleanup_failure_rejects_despite_successful_business():
    result = phase()
    result["cleanup_failures"] = 1
    assert not evaluate_transactions(result, 12, 120)["execution_valid"]


@pytest.mark.parametrize(
    "index,p95,accepted",
    [
        (0, 1999, True),
        (0, 2000, False),
        (2, 4999, True),
        (2, 5000, False),
        (3, 5000, False),
    ],
)
def test_latency_targets_are_strict_and_do_not_invalidate_execution(
    index, p95, accepted
):
    result = phase()
    result["timing"]["measurement"][index]["p95_ms"] = p95
    checked = evaluate_transactions(result, 12, 120)
    assert checked["execution_valid"]
    assert checked["measurement_accepted"] is accepted
    assert checked["read_p95_limit_exclusive_ms"] == 2000
    assert checked["transaction_p95_limit_exclusive_ms"] == 5000
    assert set(checked["profile_targets"]) == {"DONOR", "OPERATOR"}


def test_measured_window_waits_for_warmup_and_snapshots_before_final_drain(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("LOCUST_SKIP_MONKEY_PATCH", "1")
    monkeypatch.syspath_prepend(str(Path(__file__).parent))
    workload = importlib.import_module("tests.locust_transactions")
    timing = importlib.import_module("tests.locust_sustained")
    clock = [0.0]
    entry = SimpleNamespace(num_requests=0, num_failures=0)
    resets, drains, quits = [], [], []

    def reset():
        resets.append(clock[0])
        entry.num_requests = 0

    environment = SimpleNamespace(
        stats=SimpleNamespace(entries={"http": entry}, reset_all=reset),
        runner=SimpleNamespace(quit=lambda: quits.append(True)),
    )

    def observe(_env, seconds):
        assert workload._admit.is_set()
        entry.num_requests = 8 if seconds == 30 else 20
        clock[0] += seconds
        return 12

    def drain():
        assert not workload._admit.is_set()
        drains.append(workload._stage)
        entry.num_requests += 3
        clock[0] += 2

    monkeypatch.setattr(workload.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(workload, "drain_cycles", drain)
    monkeypatch.setattr(timing, "observe_users", observe)
    monkeypatch.setattr(
        timing,
        "snapshot_stats",
        lambda _env, _duration: [{"requests": entry.num_requests}],
    )
    monkeypatch.setattr(timing, "_user_errors", 0)
    monkeypatch.setenv("REDHOUSE_LOAD_MARKER", str(tmp_path / "phase.json"))
    monkeypatch.setenv("REDHOUSE_LOAD_MEASURE_SECONDS", "120")
    workload.measured_transactions(environment)
    report = json.loads((tmp_path / "phase.json").read_text())
    assert report["stage"] == "finished" and quits == [True]
    assert drains == ["warmup_drain", "drain"] and resets == [0, 32]
    assert report["warmup"]["requests"] == 11
    assert report["measurement"] == [{"requests": 20}]
    assert (
        report["measured"] == 32
        and report["finished"] == 152
        and report["drained"] == 154
    )


def test_donor_cycle_versions_and_owned_appointment_are_reconciled():
    owner = dict(account(), role="DONOR", donor_id=str(uuid4()))
    identifier, campaign, slot1, slot2 = [str(uuid4()) for _ in range(4)]
    rows = [event(owner, "cycle_start")]
    commits = {}
    bodies = [
        {"donor_id": owner["donor_id"], "campaign_id": campaign, "slot_id": slot1},
        {"version": 1, "action": "RESCHEDULE", "slot_id": slot2},
        {"version": 2, "action": "CANCEL"},
    ]
    results = [
        {
            "id": identifier,
            "tenant_id": owner["tenant_id"],
            "donor_id": owner["donor_id"],
            "campaign_id": campaign,
            "status": "BOOKED",
        },
        {
            "id": identifier,
            "tenant_id": owner["tenant_id"],
            "slot_id": slot2,
            "status": "BOOKED",
            "version": 2,
        },
        {
            "id": identifier,
            "tenant_id": owner["tenant_id"],
            "slot_id": slot2,
            "status": "CANCELLED",
            "version": 3,
        },
    ]
    for index, (body, result) in enumerate(zip(bodies, results)):
        key = str(uuid4())
        operation = (
            "appointment_create" if index == 0 else "appointment_command:" + identifier
        )
        path = (
            "/api/v1/appointments"
            if index == 0
            else "/api/v1/appointments/" + identifier + "/commands"
        )
        rows += [
            event(owner, "intent", service="donantes", key=key, path=path, body=body),
            event(owner, "response", key=key, result=result),
        ]
        commits[("donantes", owner["id"], key)] = {
            "operation": operation,
            "result": result,
        }
    rows.append(event(owner, "cycle_end", success=True))
    checked = reconcile_transaction_log(rows, commits, [owner])
    assert not checked["errors"] and checked["completed"] == {"DONOR": 1}
    assert checked["expected"]["appointments"][identifier]["status"] == "CANCELLED"
    assert checked["expected"]["appointments"][identifier]["version"] == 3
    assert checked["alerts"] == {(identifier, owner["id"])}


@pytest.mark.parametrize("changed", [False, True])
def test_transaction_global_sources_detect_api_drift_outside_runtime_subset(
    tmp_path, monkeypatch, changed
):
    from scripts import prepare_load, sustained_read
    from tests import load_support

    snapshots = iter(
        [
            {"apps/services/ms_donantes/routes.py": "before"},
            {"apps/services/ms_donantes/routes.py": "after" if changed else "before"},
        ]
    )
    monkeypatch.setattr(prepare_load, "source_snapshot", lambda: next(snapshots))
    monkeypatch.setattr(
        sustained_read, "source_hashes", lambda _env: {"runtime": "same"}
    )
    monkeypatch.setattr(sustained_read, "topology", lambda _env: {})
    monkeypatch.setattr(sustained_read, "runtime_topology", lambda _env: {})
    monkeypatch.setattr(
        load_support,
        "prepare_transaction_fixture",
        lambda _env: {"accounts": [], "prefix": "test", "profile_id": "test"},
    )
    monkeypatch.setattr(
        sustained_read,
        "run_phase",
        lambda *_args, **_kwargs: {
            "execution_valid": True,
            "measurement_accepted": True,
        },
    )
    env = SimpleNamespace(
        directory=tmp_path, state={}, save=lambda: None, start=lambda: None
    )
    if changed:
        with pytest.raises(RuntimeError, match="Fuentes globales"):
            sustained_read.run_transactions(env, lambda _directory: None)
    else:
        sustained_read.run_transactions(env, lambda _directory: None)
    report = json.loads(next(tmp_path.glob("transactions-*/summary.json")).read_text())
    assert report["source_hashes_match"] is not changed
    assert report["status"] == ("failed" if changed else "passed")
    assert report["hashes_before"] == report["hashes_after"]
    assert "apps/services/ms_donantes/routes.py" in report["source_hashes_before"]
