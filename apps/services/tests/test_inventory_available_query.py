"""Pure endpoint regression: regional availability must not query per resource."""

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

import pytest
from flask import Flask, g

from ms_inventario import routes


@pytest.mark.parametrize("size", [0, 3, 400])
def test_internal_availability_reads_once_and_preserves_rows(monkeypatch, size):
    now = datetime(2026, 11, 17, tzinfo=timezone.utc)
    # Driver rows include both a missing control and a control with a NULL profile.
    rows = [
        dict(
            id=str(i),
            folio="UNIT-" + str(i),
            tenant_id="institution",
            region_id="region",
            kind="BLOOD",
            component="RBC",
            blood_group="O+",
            expires_at=now + timedelta(days=1),
            status="AVAILABLE",
            version=1,
            lab_profile_id="profile" if i % 3 == 0 else None,
        )
        for i in range(size)
    ]
    queries = []

    class Connection:
        def execute(self, query, params):
            queries.append((query, params))
            assert len(queries) == 1, "Availability must not issue per-resource reads"
            return self

        def fetchall(self):
            return rows

    @contextmanager
    def transaction():
        yield Connection()

    monkeypatch.setattr(routes, "transaction", transaction)
    app = Flask(__name__)
    app.extensions["contracts"] = []
    routes.register(app)
    with app.test_request_context("/"):
        g.actor = {"region_id": "region"}
        result = app.view_functions["resources_internal"].__wrapped__()

    assert result == {"items": rows}
    assert len(queries) == 1
    query, params = queries[0]
    assert params == ("region",)
    assert "LEFT JOIN resource_controls c ON c.id=r.id" in query
    assert "r.region_id=%s AND r.status='AVAILABLE' AND r.expires_at>now()" in query
    assert query.endswith("ORDER BY r.expires_at,r.id")
    assert "c.lab_profile_id" in query
