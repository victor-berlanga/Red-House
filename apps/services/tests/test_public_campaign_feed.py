"""Public pagination over real PostgreSQL; approved fields only, JSON and XML."""

from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from uuid import uuid4

import pytest
from jsonschema import validate

from ms_donantes.publication import PublicCampaign
from redhouse.extension_contracts import page_schema
from redhouse.xml_response import validate_response


def read(p, fmt, params):
    response = p.request(
        "donantes",
        "GET",
        "/api/v1/public/campaign-feed?" + urlencode(params),
        user=None,
        headers={"Accept": "application/" + fmt},
    )
    payload = (
        response.json()
        if fmt == "json"
        else validate_response(response.content, {"type": "object"})
    )
    return response.status_code, payload


@pytest.mark.parametrize("fmt", ["json", "xml"])
def test_public_feed_pages_over_one_hundred_and_preserves_public_scope(p, fmt):
    prefix = "FEED-" + uuid4().hex[:12]
    tenants = [
        p.ok("identidad_acceso", "GET", "/api/v1/auth/me", user=user)["tenant_id"]
        for user in ("operator1", "operator2")
    ]
    start = datetime.now(timezone.utc).replace(microsecond=0) + timedelta(days=3)
    rows = []
    # Direct fixture insertion prepares volume, not evidence of campaign creation.
    with p.owner("donantes") as conn:
        for number in range(110):
            identifier = str(uuid4())
            tenant = tenants[number % 2]
            begins = start if number < 109 else start - timedelta(days=10)
            ends = begins + timedelta(days=1)
            title = f"{prefix} {number:03}"
            status = (
                "CLOSED" if number == 106 else "CANCELLED" if number == 107 else "OPEN"
            )
            conn.execute(
                "INSERT INTO campaigns(id,tenant_id,title,starts_at,ends_at,capacity,status) VALUES(%s,%s,%s,%s,%s,100,%s)",
                (identifier, tenant, title, begins, ends, status),
            )
            if number != 108:
                conn.execute(
                    "INSERT INTO campaign_publications(id,tenant_id,published,venue,information) VALUES(%s,%s,%s,%s,%s)",
                    (
                        identifier,
                        tenant,
                        number != 105,
                        f"Sede {prefix} {number:03}",
                        "Información pública sintética",
                    ),
                )
            if number < 105:
                rows.append((identifier, title))
    expected = [title for _, title in sorted(rows)]
    collected = []
    for page in range(1, 7):
        status, payload = read(p, fmt, {"q": prefix, "page": page, "page_size": 20})
        assert status == 200
        data = payload["data"]
        validate(data, page_schema(PublicCampaign))
        assert (data["page"], data["page_size"], data["total"]) == (page, 20, 105)
        assert len(data["items"]) == (20 if page < 6 else 5)
        for row in data["items"]:
            assert set(row) == {"title", "starts_at", "ends_at", "venue", "information"}
        collected.extend(row["title"] for row in data["items"])
    assert collected == expected and len(set(collected)) == 105
    assert read(p, fmt, {"q": prefix, "page": 7})[1]["data"]["items"] == []
    assert read(p, fmt, {"q": prefix, "page_size": 100})[1]["data"]["total"] == 105
    # No SQL wildcard expansion; dates are inclusive/exclusive over starts_at.
    for literal in ("%", "_", "\\"):
        assert read(p, fmt, {"q": prefix + literal})[1]["data"]["total"] == 0
    assert read(p, fmt, {"q": "Sede " + prefix + " 000"})[1]["data"]["total"] == 1
    assert (
        read(p, fmt, {"q": prefix, "from_at": start.isoformat()})[1]["data"]["total"]
        == 105
    )
    assert (
        read(p, fmt, {"q": prefix, "until_at": start.isoformat()})[1]["data"]["total"]
        == 0
    )
    for params in (
        {"page": 0},
        {"page_size": 101},
        {"page": "bad"},
        {"tenant_id": tenants[0]},
        {"q": "a" * 101},
        {"q": "\x00"},
        {"from_at": "bad"},
        {"from_at": start.isoformat(), "until_at": start.isoformat()},
        [("page", 1), ("page", 2)],
    ):
        assert read(p, fmt, params)[0] in (400, 422)
    legacy = p.ok("donantes", "GET", "/api/v1/public/campaigns", user=None)
    assert set(legacy) == {"items"}
    assert [
        item["title"] for item in legacy["items"] if item["title"].startswith(prefix)
    ] == expected
