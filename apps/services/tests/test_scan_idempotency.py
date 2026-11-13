"""Verificación de identificador JSON/XML, ámbito, auditoría e idempotencia."""

from uuid import uuid4

import jsonschema
import pytest
import requests
from redhouse.examples import request_xml
from redhouse.xml_response import validate_response

from .test_documents_storage import planned


@pytest.mark.parametrize("fmt", ["json", "xml"])
def test_scan_scoped_idempotent_and_representation(p, fmt):
    shipment = planned(p)
    with p.owner("inventario") as conn:
        resource_id = str(
            conn.execute(
                "SELECT resource_id FROM reservations WHERE id=%s",
                (shipment["reservation_id"],),
            ).fetchone()[0]
        )
    path = "/api/v1/shipments/" + shipment["id"] + "/scan"
    body = {"scanned_resource_id": resource_id}
    key = uuid4().hex

    def send(user, data=body, idem=key):
        headers = {
            "Authorization": "Bearer " + p.tokens[user],
            "Idempotency-Key": idem,
            "Accept": "application/xml" if fmt == "xml" else "application/json",
        }
        if fmt == "xml":
            headers["Content-Type"] = "application/xml"
            return requests.post(
                p.urls["transporte"] + path,
                data=request_xml(data).encode(),
                headers=headers,
                timeout=20,
            )
        return requests.post(
            p.urls["transporte"] + path, json=data, headers=headers, timeout=20
        )

    assert send("donor1").status_code == 403
    assert send("transport2").status_code == 403
    first, replay = send("transport1"), send("transport1")
    assert first.status_code == replay.status_code == 200, (first.text, replay.text)
    contract = next(
        c
        for c in p.apps["transporte"].extensions["contracts"]
        if c["name"] == "shipment_scan"
    )["result"]
    if fmt == "xml":
        schema = {"type": "object", "properties": {"data": contract}}
        result = validate_response(first.content, schema)["data"]
        assert validate_response(replay.content, schema)["data"] == result
    else:
        result = first.json()["data"]
        jsonschema.validate(result, contract)
        assert replay.json()["data"] == result
    assert result["verified"] and result["resource_id"] == resource_id
    assert (
        send(
            "transport1", {"scanned_resource_id": str(uuid4())}, uuid4().hex
        ).status_code
        == 409
    )
    assert (
        send("transport1", {"scanned_resource_id": str(uuid4())}, key).status_code
        == 409
    )
    with p.owner("transporte") as conn:
        events = conn.execute(
            "SELECT event FROM activity_events WHERE event->>'action'='SHIPMENT_RESOURCE_IDENTIFIER_VERIFIED' AND event->>'resource_id'=%s",
            (shipment["id"],),
        ).fetchall()
        assert len(events) == 1
        metadata = events[0][0]["metadata"]
        assert (
            metadata["request_representation"] == fmt
            and metadata["response_representation"] == fmt
        )
        conn.execute(
            "UPDATE shipments SET transport_user_id=%s WHERE id=%s",
            (p.env.state["accounts"]["transport2"]["id"], shipment["id"]),
        )
    assert send("transport1").status_code == 403
    with p.owner("transporte") as conn:
        conn.execute(
            "UPDATE shipments SET transport_user_id=%s WHERE id=%s",
            (p.env.state["accounts"]["transport1"]["id"], shipment["id"]),
        )
        conn.execute(
            "UPDATE shipments SET version=version+1 WHERE id=%s", (shipment["id"],)
        )
    assert send("transport1").status_code == 409


def test_scan_replay_reauthorizes_after_concurrent_assignment_change(p, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event

    import ms_transporte.mobile as mobile

    shipment = planned(p)
    with p.owner("inventario") as conn:
        resource_id = str(
            conn.execute(
                "SELECT resource_id FROM reservations WHERE id=%s",
                (shipment["reservation_id"],),
            ).fetchone()[0]
        )
    path = "/api/v1/shipments/" + shipment["id"] + "/scan"
    body, key = {"scanned_resource_id": resource_id}, uuid4().hex
    assert (
        p.request(
            "transporte", "POST", path, user="transport1", data=body, key=key
        ).status_code
        == 200
    )
    reached, release = Event(), Event()
    original = mobile.call

    def delayed(*args, **kwargs):
        result = original(*args, **kwargs)
        if args[0] == "inventario" and args[2].endswith("/custody-check"):
            reached.set()
            assert release.wait(10)
        return result

    monkeypatch.setattr(mobile, "call", delayed)
    with ThreadPoolExecutor(1) as pool:
        replay = pool.submit(
            p.request, "transporte", "POST", path, user="transport1", data=body, key=key
        )
        try:
            assert reached.wait(10)
            with p.owner("transporte") as conn:
                conn.execute(
                    "UPDATE shipments SET transport_user_id=%s,version=version+1 WHERE id=%s",
                    (p.env.state["accounts"]["transport2"]["id"], shipment["id"]),
                )
        finally:
            release.set()
        assert replay.result(timeout=20).status_code == 403
    with p.owner("transporte") as conn:
        events = conn.execute(
            "SELECT count(*) FROM activity_events WHERE event->>'action'='SHIPMENT_RESOURCE_IDENTIFIER_VERIFIED' AND event->>'resource_id'=%s",
            (shipment["id"],),
        ).fetchone()[0]
    assert events == 1
