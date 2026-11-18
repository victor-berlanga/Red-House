"""Custody clock boundaries and real Flask route validation, without engines."""

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from flask import Flask, g
import redhouse.api as api
from redhouse.codec import respond
from redhouse.errors import APIError
from redhouse.examples import request_xml
from redhouse.xml_response import validate_response
from ms_transporte import routes
from ms_transporte.custody_time import validate_custody_capture_time

NOW = datetime(2026, 11, 17, 20, 33, 58, 720868, tzinfo=timezone.utc)
IDS = [f"00000000-0000-4000-8000-{n:012d}" for n in range(1, 8)]
SHIPMENT, RESOURCE, RESERVATION, TRANSPORT, OPERATOR, ORIGIN, REGION = IDS
BOUNDARIES = [
    (0, True),
    (637000, True),
    (5000000, True),
    (5000001, False),
    (-86400000000, True),
    (-86400000001, False),
]


@pytest.mark.parametrize("microseconds,accepted", BOUNDARIES)
def test_capture_window_inclusive_boundaries(microseconds, accepted):
    captured = NOW + timedelta(microseconds=microseconds)
    if accepted:
        assert validate_custody_capture_time(captured, NOW) is None
    else:
        with pytest.raises(APIError) as caught:
            validate_custody_capture_time(captured, NOW)
        assert (
            caught.value.code == "custody_timestamp_invalid"
            and caught.value.status == 409
        )
        assert (
            captured.isoformat() not in caught.value.message
            and NOW.isoformat() not in caught.value.message
        )


@pytest.fixture
def seam(monkeypatch):
    app = Flask(__name__)
    app.config.update(SERVICE="transporte", VERSION="0.4.1")
    app.extensions["contracts"] = []
    row = {
        "id": SHIPMENT,
        "reservation_id": RESERVATION,
        "transport_user_id": TRANSPORT,
        "region_id": REGION,
        "origin_id": ORIGIN,
        "destination_id": IDS[0],
        "status": "PREPARED",
        "version": 2,
        "sequence": 2,
        "inventory_pending": False,
        "expires_at": NOW + timedelta(hours=1),
    }
    actor = {
        "id": TRANSPORT,
        "tenant_id": ORIGIN,
        "region_id": REGION,
        "role": "TRANSPORT",
    }
    handover = {"id": OPERATOR, "active": True, "role": "OPERATOR", "tenant_id": ORIGIN}
    state = SimpleNamespace(
        row=row, actor=actor, handover=handover, effects=[], captures=[], clock_calls=0
    )

    class FrozenClock(datetime):
        @classmethod
        def now(cls, tz=None):
            state.clock_calls += 1
            return NOW if tz else NOW.replace(tzinfo=None)

    monkeypatch.setattr(routes, "datetime", FrozenClock)

    def authenticate(_roles):
        g.actor = deepcopy(state.actor)

    monkeypatch.setattr(api, "authenticate", authenticate)
    monkeypatch.setattr(api, "rate_limit", lambda *args: None)

    @app.before_request
    def correlation():
        g.correlation_id = "synthetic-unit-correlation"

    @app.errorhandler(APIError)
    def rejected(error):
        return respond(
            {
                "error": {
                    "code": error.code,
                    "message": error.message,
                    "details": error.details,
                },
                "meta": {
                    "service": "transporte",
                    "version": "0.4.1",
                    "correlation_id": g.correlation_id,
                },
            },
            error.status,
        )

    conn = SimpleNamespace(execute=lambda *args: None)
    monkeypatch.setattr(routes, "atomic", lambda _operation, _data, work: work(conn))
    monkeypatch.setattr(routes, "get", lambda *args: deepcopy(state.row))

    def call(service, *args, **kwargs):
        if service == "inventario":
            return {"resource_id": RESOURCE}
        if service == "identidad_acceso":
            return deepcopy(state.handover)
        raise AssertionError("Unexpected owner dependency")

    monkeypatch.setattr(routes, "call", call)

    def logistics(_conn, _row, _state, _actor, *args):
        state.effects.append(("event", deepcopy(args[-1])))
        return 3

    monkeypatch.setattr(routes, "logistics_event", logistics)
    monkeypatch.setattr(
        routes,
        "insert",
        lambda _conn, _table, value: state.effects.append(
            ("transition", deepcopy(value))
        ),
    )
    monkeypatch.setattr(
        routes,
        "update",
        lambda _conn, _table, _identifier, value: {**state.row, **value},
    )

    def capture(captured, now):
        state.captures.append((captured, now))
        return validate_custody_capture_time(captured, now)

    monkeypatch.setattr(routes, "validate_custody_capture_time", capture)
    routes.register(app)
    return app.test_client(), state


def request(client, microseconds, representation, **changes):
    stamp = (NOW + timedelta(microseconds=microseconds)).isoformat()
    body = {
        "human_confirmation": True,
        "reason": "Intercambio académico sintético",
        "version": 2,
        "state": "COLLECTED",
        "custody": {
            "scanned_resource_id": RESOURCE,
            "seal": "SELLO-SINTETICO",
            "captured_at": stamp,
            "reported_handover_user_id": OPERATOR,
            "electronic_acceptance": True,
        },
    }
    body.update(changes)
    options = (
        {"json": body}
        if representation == "json"
        else {"data": request_xml(body), "content_type": "application/xml"}
    )
    response = client.post(
        f"/api/v1/shipments/{SHIPMENT}/transitions",
        headers={"Accept": "application/" + representation},
        **options,
    )
    payload = (
        response.get_json()
        if representation == "json"
        else validate_response(response.data, {"type": "object"})
    )
    return response, payload, body


@pytest.mark.parametrize("representation", ["json", "xml"])
@pytest.mark.parametrize("microseconds,accepted", BOUNDARIES)
def test_route_clock_and_original_custody(seam, representation, microseconds, accepted):
    client, state = seam
    response, payload, body = request(client, microseconds, representation)
    assert response.status_code == (200 if accepted else 409)
    assert state.captures == [(NOW + timedelta(microseconds=microseconds), NOW)]
    assert (
        state.clock_calls == 2
    )  # One unchanged expiry check, one custody clock sample.
    if accepted:
        assert (
            payload["data"]["status"] == "COLLECTED" and payload["data"]["version"] == 3
        )
        assert state.effects[0] == (
            "event",
            body["custody"],
        )  # Keep original captured_at string.
        assert len(state.effects) == 2
    else:
        assert (
            payload["error"]["code"] == "custody_timestamp_invalid"
            and not state.effects
        )


@pytest.mark.parametrize(
    "failure,code",
    [
        ("qr", "custody_mismatch"),
        ("handover_role", "custody_mismatch"),
        ("handover_tenant", "custody_mismatch"),
        ("handover_inactive", "custody_mismatch"),
        ("actor", "forbidden"),
        ("version", "conflict"),
        ("expired", "expired_resource"),
    ],
)
def test_tolerance_never_bypasses_existing_guards(seam, failure, code):
    client, state = seam
    changes = {}
    if failure == "qr":
        custody = {
            "scanned_resource_id": IDS[-1],
            "seal": "SELLO-SINTETICO",
            "captured_at": (NOW + timedelta(microseconds=637000)).isoformat(),
            "reported_handover_user_id": OPERATOR,
            "electronic_acceptance": True,
        }
        changes["custody"] = custody
    if failure == "handover_role":
        state.handover["role"] = "TRANSPORT"
    if failure == "handover_tenant":
        state.handover["tenant_id"] = IDS[-1]
    if failure == "handover_inactive":
        state.handover["active"] = False
    if failure == "actor":
        state.actor["id"] = IDS[-1]
    if failure == "version":
        changes["version"] = 1
    if failure == "expired":
        state.row["expires_at"] = NOW
    response, payload, _body = request(client, 637000, "json", **changes)
    assert response.status_code in (403, 409) and payload["error"]["code"] == code
    assert not state.effects and not state.captures
