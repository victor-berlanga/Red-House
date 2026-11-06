"""Deterministic query budgets; synthetic rows, no external services."""

from contextlib import contextmanager
from datetime import datetime, timezone

import pytest
from flask import Flask

from ms_compatibilidad import laboratory
from ms_transporte import tracking
from redhouse.errors import APIError

NOW = datetime(2026, 11, 4, tzinfo=timezone.utc)
PROFILE = dict(
    id="00000000-0000-4000-8000-000000000001",
    tenant_id="tenant",
    version=1,
    required_tests=["ABO"],
    required_loci=[],
    synthetic=True,
    rule_status="DRAFT",
    effective_at=NOW,
    policy=dict(
        version="COMPLETENESS-2.0", max_age_seconds=None, require_document=False
    ),
)


class Rows:
    def __init__(self, rows):
        self.rows = rows

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def fetchall(self):
        return self.rows


class LaboratoryConnection:
    def __init__(self):
        self.queries = []

    def execute(self, query, params=None):
        text = str(query)
        self.queries.append(text)
        if "SELECT * FROM" in text and "lab_profiles" in text:
            return Rows([PROFILE.copy()])
        return Rows([])


def test_completeness_reads_governance_once():
    conn = LaboratoryConnection()
    result = laboratory.completeness(
        conn, "resource", "00000000-0000-4000-8000-000000000001", "tenant", now=NOW
    )
    assert result["missing"] == ["ABO"]
    assert not result["clinical_enabled"]
    assert sum("rule_actions" in q for q in conn.queries) == 1
    assert len(conn.queries) == 5


def test_completeness_rejects_foreign_profile_before_results():
    conn = LaboratoryConnection()
    with pytest.raises(APIError) as error:
        laboratory.completeness(
            conn, "resource", "00000000-0000-4000-8000-000000000001", "foreign", now=NOW
        )
    assert error.value.code == "forbidden"
    assert len(conn.queries) == 1


@pytest.mark.parametrize("cursor,head,queries", [(0, 0, 2), (1, 1, 2), (0, 1, 3)])
def test_snapshot_skips_empty_replay_only(monkeypatch, cursor, head, queries):
    calls = []

    class Connection:
        def execute(self, query, params=None):
            calls.append(query)
            return Rows([{"n": head}] if "max(cursor)" in query else [])

    @contextmanager
    def transaction():
        yield Connection()

    access_calls = []
    monkeypatch.setattr(tracking, "transaction", transaction)
    monkeypatch.setattr(
        tracking,
        "access",
        lambda *args, **kwargs: access_calls.append(kwargs) or {"status": "IN_TRANSIT"},
    )
    with Flask(__name__).app_context():
        result = tracking.snapshot("shipment", cursor, live=True)
    assert result["events"] == []
    assert result["cursor"] == cursor
    assert result["head"] == head
    assert access_calls == [{"live": True, "lock": True}]
    assert len(calls) == queries


@pytest.fixture(params=["services", "web"])
def http_client_factory(request, monkeypatch):
    if request.param == "services":
        from redhouse.client import http_client
    else:
        from pathlib import Path

        monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "web"))
        from src.integration.client import http_client
    return http_client


def test_http_session_released_when_worker_thread_exits(http_client_factory):
    import gc
    import threading
    import weakref
    from unittest.mock import Mock

    http_client = http_client_factory

    references, adapters = [], []

    def worker():
        session = http_client()
        references.append(weakref.ref(session))
        for adapter in session.adapters.values():
            adapter.close = Mock(wraps=adapter.close)
            adapters.append(adapter)

    thread = threading.Thread(target=worker)
    thread.start()
    thread.join()
    gc.collect()
    assert references[0]() is None
    assert all(adapter.close.call_count == 1 for adapter in adapters)


def test_http_worker_reuses_pool_but_not_cookies(http_client_factory):
    import threading

    http_client = http_client_factory

    results = []

    def worker():
        first = http_client()
        first.cookies.set("synthetic", "value")
        second = http_client()
        results.append((first is second, len(second.cookies)))

    thread = threading.Thread(target=worker)
    thread.start()
    thread.join()
    assert results == [(True, 0)]


@pytest.mark.parametrize("captured", [None, {"completions": []}])
def test_freshness_reads_recipient_context_once(monkeypatch, captured):
    from ms_compatibilidad import freshness

    calls = []
    context = {"completions": []}
    monkeypatch.setattr(
        freshness, "recipient_laboratory", lambda *args: calls.append(args) or context
    )
    req = dict(
        version=1,
        status="OPEN",
        recipient_id="recipient",
        recipient=dict(version=1, status="ACTIVE"),
    )
    monkeypatch.setattr(
        freshness,
        "call",
        lambda service, *args: req if service == "receptores" else {"items": []},
    )
    result = freshness.current(
        None,
        dict(
            request_id="request",
            request_version=1,
            recipient_version=1,
            tenant_id="tenant",
            snapshot={"recipient_laboratory": captured},
            candidates=[],
        ),
    )
    assert result["reasons"] == (
        [] if captured is not None else ["RECIPIENT_LABORATORY_CHANGED"]
    )
    assert len(calls) == 1


@pytest.mark.parametrize("size", [4, 40, 400])
def test_evaluation_cost_tracks_filtered_candidates_and_linked_profiles(
    monkeypatch, size
):
    from datetime import timedelta
    from flask import g
    from ms_compatibilidad import routes

    app = Flask(__name__)
    app.extensions["contracts"] = []
    app.config["OPERATION_SCOPE"] = "ACADEMIC"
    routes.register(app)
    conn = LaboratoryConnection()
    transactions = []

    @contextmanager
    def transaction():
        transactions.append(1)
        yield conn

    resources = [
        dict(
            id=str(i),
            version=1,
            kind="BLOOD",
            component="RBC" if i % 4 < 2 else "PLASMA",
            blood_group="O-",
            tenant_id="tenant",
            expires_at=(datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
            lab_profile_id=PROFILE["id"] if i % 4 == 0 else None,
        )
        for i in range(size)
    ]
    req = dict(
        id="request",
        status="OPEN",
        kind="BLOOD",
        component="RBC",
        version=1,
        tenant_id="tenant",
        recipient_id="recipient",
        recipient=dict(status="ACTIVE", version=1, blood_group="O-"),
    )
    replies = dict(
        receptores=req,
        inventario={"items": resources},
        priorizacion_geografia={
            "items": [
                dict(
                    id="route",
                    version=1,
                    origin_id="tenant",
                    destination_id="tenant",
                    travel_minutes=1,
                    distance_km=1,
                )
            ]
        },
    )
    monkeypatch.setattr(routes, "call", lambda service, *args: replies[service])
    monkeypatch.setattr(routes, "transaction", transaction)
    monkeypatch.setattr(routes, "atomic", lambda operation, data, work: work(conn))
    monkeypatch.setattr(routes, "insert", lambda conn, table, data: data)
    monkeypatch.setattr(routes, "emit", lambda *args, **kwargs: None)
    with app.test_request_context("/"):
        g.actor = {"tenant_id": "tenant"}
        result = app.view_functions["evaluation_create"].__wrapped__(
            dict(request_id="request", profile_id=None)
        )
    assert len(result["snapshot"]["considered"]) == size
    assert len(result["candidates"]) == size // 2
    assert result["snapshot"]["missing_data"]["other_component"] == size // 2
    # One recipient read plus only the candidates actually linked to a profile.
    assert len(transactions) == 1 + size // 4
    assert len(conn.queries) == 3 + 5 * (size // 4)
