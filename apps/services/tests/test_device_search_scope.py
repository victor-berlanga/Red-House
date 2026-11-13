"""Búsqueda de dispositivos por nombre con ámbito y paginación."""

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from uuid import uuid4
from urllib.parse import quote

import pytest


@pytest.mark.parametrize("representation", ["application/json", "application/xml"])
def test_device_search_name_scope_and_pagination(p, representation):
    marker = "PruebaBusqueda" + uuid4().hex[:10]
    expiry = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    created = []
    for admin, transport, suffix in [
        ("admin1", "transport1", "A"),
        ("admin1", "transport1", "B"),
        ("admin2", "transport2", "C"),
    ]:
        created.append(
            p.ok(
                "identidad_acceso",
                "POST",
                "/api/v1/devices",
                user=admin,
                data={
                    "id": str(uuid4()),
                    "user_id": p.env.state["accounts"][transport]["id"],
                    "source": "SIMULATOR",
                    "label": marker + suffix,
                    "expires_at": expiry,
                },
            )
        )

    def get(user, query, page=1):
        response = p.request(
            "identidad_acceso",
            "GET",
            f"/api/v1/devices?q={quote(query)}&page={page}&page_size=1",
            user=user,
            headers={"Accept": representation},
        )
        assert response.status_code == 200
        if representation == "application/xml":
            from redhouse.xml_response import validate_response

            schema = json.loads(
                (
                    Path(__file__).parents[1]
                    / "ms_identidad_acceso/contracts/device_list.response.json"
                ).read_text()
            )
            value = validate_response(response.content, schema)["data"]
        else:
            value = response.json()["data"]
        return value["total"], [item["id"] for item in value["items"]]

    total, first = get("admin1", marker.lower())
    total2, second = get("admin1", marker.lower(), 2)
    assert total == total2 == 2 and set(first + second) == {
        created[0]["id"],
        created[1]["id"],
    }
    total, other = get("admin2", marker)
    assert total == 1 and other == [created[2]["id"]]
    total, by_id = get("admin1", created[0]["id"])
    assert total == 1 and by_id == [created[0]["id"]]
    assert (
        p.request(
            "identidad_acceso",
            "GET",
            "/api/v1/devices?q=" + quote(marker),
            user="operator1",
            headers={"Accept": representation},
        ).status_code
        == 403
    )
