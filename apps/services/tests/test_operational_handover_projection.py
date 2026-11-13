"""Identidad operativa mínima de un traslado; sin datos de contacto."""

import json
from pathlib import Path

import pytest
from jsonschema import validate
from redhouse.xml_response import validate_response
from .test_final_tracking import tracking


@pytest.mark.parametrize("fmt", ["json", "xml"])
def test_projection_is_limited_to_authorized_shipment(p, tracking, fmt):
    shipment = tracking["shipment"]
    path = f"/api/v1/shipments/{shipment['id']}/operational-handover"
    expected = p.env.state["accounts"]["transport1"]["id"]
    with p.owner("identidad_acceso") as conn:
        name = conn.execute(
            "SELECT username FROM users WHERE id=%s", (expected,)
        ).fetchone()[0]
    contract_path = (
        Path(__file__).parents[1]
        / "ms_transporte/contracts/operational_handover.response.json"
    )
    contract = json.loads(contract_path.read_text())
    for actor in ("operator1", "operator2", "transport1", "coordinator1"):
        response = p.request(
            "transporte",
            "GET",
            path,
            user=actor,
            headers={"Accept": "application/" + fmt},
        )
        assert response.status_code == 200, response.text
        envelope = (
            response.json()
            if fmt == "json"
            else validate_response(response.content, contract)
        )
        validate(envelope, contract)
        assert envelope["data"] == {
            "shipment_id": shipment["id"],
            "shipment_version": shipment["version"],
            "transport_user": {"id": expected, "name": name},
        }
    for actor in ("donor1", "transport2"):
        response = p.request(
            "transporte",
            "GET",
            path,
            user=actor,
            headers={"Accept": "application/" + fmt},
        )
        assert response.status_code == 403
    direct = f"/internal/v1/transport-users/{expected}/operational-name"
    assert p.request(
        "identidad_acceso", "GET", direct, user="operator2"
    ).status_code in (401, 403)


def test_reassignment_during_identity_read_is_reauthorized(p, tracking, monkeypatch):
    import ms_transporte.mobile as mobile

    shipment = tracking["shipment"]
    old = mobile.call

    def reassign(service, method, path, *args, **kwargs):
        result = old(service, method, path, *args, **kwargs)
        if service == "identidad_acceso" and "/operational-name" in path:
            with p.owner("transporte") as conn:
                conn.execute(
                    "UPDATE shipments SET transport_user_id=%s,version=version+1 WHERE id=%s",
                    (p.env.state["accounts"]["transport2"]["id"], shipment["id"]),
                )
        return result

    monkeypatch.setattr(mobile, "call", reassign)
    path = f"/api/v1/shipments/{shipment['id']}/operational-handover"
    response = p.request("transporte", "GET", path, user="operator2")
    assert response.status_code == 409
    assert p.request("transporte", "GET", path, user="transport1").status_code == 403


def test_operator_outside_origin_and_destination_is_rejected(p, tracking):
    shipment = tracking["shipment"]
    path = f"/api/v1/shipments/{shipment['id']}/operational-handover"
    with p.owner("transporte") as conn:
        conn.execute(
            "UPDATE shipments SET destination_id=origin_id,version=version+1 WHERE id=%s",
            (shipment["id"],),
        )
    assert p.request("transporte", "GET", path, user="operator2").status_code == 403
    assert p.request("transporte", "GET", path, user="operator1").status_code == 200
