"""Labels authorize an output attempt, preserve idempotency and never claim print success."""

from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest

from .helpers import iso
from .test_final_operations import CONFIRM
from .test_final_quality import api


@pytest.mark.parametrize("fmt", ["json", "xml"])
def test_label_contract_scope_versions_reissue_and_concurrency(p, fmt):
    unit = api(
        p,
        "inventario",
        "/api/v1/resources",
        {
            "folio": "LABEL-" + uuid4().hex[:12],
            "kind": "BLOOD",
            "component": "RBC",
            "blood_group": "O+",
            "expires_at": iso(days=2),
        },
        "operator1",
    )
    path = f"/api/v1/resources/{unit['id']}/label-issuances"
    body = {**CONFIRM, "version": unit["version"], "action": "EXPORT_PDF"}
    first = api(p, "inventario", path, body, "operator1", fmt)
    assert first["resource_id"] == unit["id"]
    assert first["resource_version"] == unit["version"]
    assert first["reissue"] is False
    assert "printed" not in first
    key = uuid4().hex
    second = p.ok("inventario", "POST", path, user="operator1", data=body, key=key)
    assert second["reissue"] is True
    assert (
        p.ok("inventario", "POST", path, user="operator1", data=body, key=key) == second
    )
    assert (
        p.request(
            "inventario",
            "POST",
            path,
            user="operator1",
            data=dict(body, action="PRINT"),
            key=key,
        ).status_code
        == 409
    )
    assert (
        p.request("inventario", "POST", path, user="operator2", data=body).status_code
        == 403
    )
    assert (
        p.request("inventario", "POST", path, user="donor1", data=body).status_code
        == 403
    )
    assert (
        p.request(
            "inventario",
            "POST",
            path,
            user="operator1",
            data=dict(body, version=unit["version"] + 1),
        ).status_code
        == 412
    )
    with p.owner("inventario") as conn:
        events = conn.execute(
            "SELECT event FROM activity_events WHERE event->>'resource_id'=%s "
            "AND event->>'action'='LABEL_ISSUANCE_AUTHORIZED' ORDER BY created_at,id",
            (unit["id"],),
        ).fetchall()
    assert len(events) == 2
    assert {row[0]["event_id"] for row in events} == {
        first["issuance_id"],
        second["issuance_id"],
    }
    assert all(
        row[0]["metadata"]["audit"]["reason"] == CONFIRM["reason"] for row in events
    )
    # First/reissue is computed while holding the same resource lock.
    another = api(
        p,
        "inventario",
        "/api/v1/resources",
        {
            "folio": "LABEL-" + uuid4().hex[:12],
            "kind": "BLOOD",
            "component": "RBC",
            "blood_group": "O+",
            "expires_at": iso(days=2),
        },
        "operator1",
    )
    with ThreadPoolExecutor(2) as pool:
        replies = list(
            pool.map(
                lambda _: p.ok(
                    "inventario",
                    "POST",
                    f"/api/v1/resources/{another['id']}/label-issuances",
                    user="operator1",
                    data={**body, "version": another["version"], "action": "PRINT"},
                ),
                range(2),
            )
        )
    assert sorted(row["reissue"] for row in replies) == [False, True]
    assert len({row["issuance_id"] for row in replies}) == 2
    unchanged = api(
        p,
        "inventario",
        f"/api/v1/resources/{unit['id']}",
        user="operator1",
        fmt=fmt,
        method="GET",
    )
    assert unchanged["status"] == unit["status"]
    assert unchanged["version"] == unit["version"]
    # Synthetic transfer fixture: current custody differs from original tenant.
    with p.owner("inventario") as conn:
        conn.execute(
            "UPDATE resources SET current_institution_id=%s,version=version+1 WHERE id=%s",
            (p.env.state["tenants"][1], unit["id"]),
        )
    assert (
        p.request(
            "inventario", "POST", path, user="operator1", data=body, key=key
        ).status_code
        == 403
    )
    moved = api(
        p, "inventario", path, dict(body, version=unit["version"] + 1), "operator2", fmt
    )
    with p.owner("inventario") as conn:
        event = conn.execute(
            "SELECT event FROM activity_events WHERE id=%s", (moved["issuance_id"],)
        ).fetchone()[0]
    assert event["tenant_id"] == p.env.state["tenants"][1]
