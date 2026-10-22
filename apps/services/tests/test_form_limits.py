"""Límites públicos, fechas y corrección de errores sin escrituras parciales."""

import hashlib
from uuid import uuid4

import pytest
from flask import Flask
from ms_donantes.routes import CampaignCreate
from ms_identidad_acceso.catalogue import Capacity
from ms_identidad_acceso.routes import Login
from ms_priorizacion_geografia.routes import RouteCreate
from ms_receptores.routes import RecipientCreate, RequestCreate
from ms_transporte.routes import Telemetry
from redhouse.codec import parse
from redhouse.errors import APIError
from redhouse.examples import request_xml
from redhouse.file_validation import inspect_content
from redhouse.models import Confirm

from .helpers import evaluation, iso, recipient_request, reservation, resource
from .test_validation_audit import donor_data

IDENTIFIER = "00000000-0000-4000-8000-000000000001"


@pytest.mark.parametrize("representation", ["json", "xml"])
@pytest.mark.parametrize(
    "model,body,field,low,high",
    [
        (
            CampaignCreate,
            {
                "title": "Campaña ficticia",
                "starts_at": iso(days=1),
                "ends_at": iso(days=2),
                "capacity": 1,
            },
            "capacity",
            1,
            10000,
        ),
        (
            RequestCreate,
            {
                "recipient_id": IDENTIFIER,
                "component": "RBC",
                "quantity": 1,
                "urgency": 1,
            },
            "quantity",
            1,
            100,
        ),
        (
            RequestCreate,
            {
                "recipient_id": IDENTIFIER,
                "component": "RBC",
                "quantity": 1,
                "urgency": 1,
            },
            "urgency",
            1,
            3,
        ),
        (
            Capacity,
            {
                "name": "Capacidad ficticia",
                "parent_id": IDENTIFIER,
                "component": "RBC",
                "quantity": 0,
            },
            "quantity",
            0,
            100000,
        ),
        (
            Telemetry,
            {"latitude": 0.0, "longitude": 0.0, "captured_at": iso()},
            "latitude",
            -90.0,
            90.0,
        ),
        (
            Telemetry,
            {"latitude": 0.0, "longitude": 0.0, "captured_at": iso()},
            "longitude",
            -180.0,
            180.0,
        ),
        (
            RouteCreate,
            {
                "origin_id": IDENTIFIER,
                "destination_id": IDENTIFIER,
                "distance_km": 0.0,
                "travel_minutes": 0,
                "source": "Fuente ficticia",
            },
            "distance_km",
            0.0,
            20000.0,
        ),
        (
            RouteCreate,
            {
                "origin_id": IDENTIFIER,
                "destination_id": IDENTIFIER,
                "distance_km": 0.0,
                "travel_minutes": 0,
                "source": "Fuente ficticia",
            },
            "travel_minutes",
            0,
            10080,
        ),
    ],
)
def test_numeric_boundaries_and_public_messages(
    representation, model, body, field, low, high
):
    app = Flask(__name__)
    for value, valid in (
        (low, True),
        (high, True),
        (low - 1, False),
        (high + 1, False),
    ):
        data = {**body, field: value}
        options = (
            {"json": data}
            if representation == "json"
            else {"data": request_xml(data), "content_type": "application/xml"}
        )
        with app.test_request_context("/", method="POST", **options):
            if valid:
                assert parse(model)[field] == value
            else:
                with pytest.raises(APIError) as caught:
                    parse(model)
                assert field in {d["field"] for d in caught.value.details}
                assert all(d.get("message") for d in caught.value.details)


@pytest.mark.parametrize("representation", ["json", "xml"])
@pytest.mark.parametrize(
    "model,body,field,low,high",
    [
        (
            Login,
            {"username": "cuenta", "password": "Clave ficticia privada"},
            "username",
            3,
            80,
        ),
        (
            Login,
            {"username": "cuenta", "password": "Clave ficticia privada"},
            "password",
            12,
            128,
        ),
        (
            Confirm,
            {"reason": "Motivo ficticio", "human_confirmation": True},
            "reason",
            6,
            1000,
        ),
        (
            RecipientCreate,
            {
                "folio": "FOLIO-01",
                "display_name": "Paciente ficticio",
                "kind": "BLOOD",
                "blood_group": "O+",
                "studies": "Estudios ficticios",
            },
            "studies",
            6,
            1000,
        ),
        (
            RecipientCreate,
            {
                "folio": "FOLIO-01",
                "display_name": "Paciente ficticio",
                "kind": "BLOOD",
                "blood_group": "O+",
                "studies": "Estudios ficticios",
            },
            "requirement",
            6,
            1000,
        ),
        (
            RecipientCreate,
            {
                "folio": "FOLIO-01",
                "display_name": "Paciente ficticio",
                "kind": "BLOOD",
                "blood_group": "O+",
                "studies": "Estudios ficticios",
            },
            "display_name",
            1,
            200,
        ),
        (
            RecipientCreate,
            {
                "folio": "FOLIO-01",
                "display_name": "Paciente ficticio",
                "kind": "BLOOD",
                "blood_group": "O+",
                "studies": "Estudios ficticios",
            },
            "folio",
            6,
            30,
        ),
    ],
)
def test_text_boundaries_json_xml(representation, model, body, field, low, high):
    app = Flask(__name__)
    for size, valid in ((low, True), (high, True), (low - 1, False), (high + 1, False)):
        data = {**body, field: "x" * size}
        options = (
            {"json": data}
            if representation == "json"
            else {"data": request_xml(data), "content_type": "application/xml"}
        )
        with app.test_request_context("/", method="POST", **options):
            if valid:
                assert parse(model)[field] == data[field]
            else:
                with pytest.raises(APIError) as caught:
                    parse(model)
                assert field in {d["field"] for d in caught.value.details}


def assert_fields(response, fields, status=422):
    assert response.status_code == status, response.text
    error = response.json()["error"]
    assert fields <= {d["field"] for d in error["details"]}
    return error


def test_campaign_dates_capacity_conflict_and_retry(p):
    data = {
        "title": "Campaña validada " + uuid4().hex[:8],
        "starts_at": iso(days=1),
        "ends_at": iso(days=2),
        "capacity": 2,
    }
    key = uuid4().hex
    assert_fields(
        p.request(
            "donantes",
            "POST",
            "/api/v1/campaigns",
            user="operator1",
            key=key,
            data={**data, "ends_at": data["starts_at"]},
        ),
        {"starts_at", "ends_at"},
    )
    expired = assert_fields(
        p.request(
            "donantes",
            "POST",
            "/api/v1/campaigns",
            user="operator1",
            key=key,
            data={**data, "starts_at": iso(days=-2), "ends_at": iso(days=-1)},
        ),
        {"ends_at"},
    )
    assert "venció" in expired["message"]
    with p.owner("donantes") as conn:
        assert (
            conn.execute(
                "SELECT count(*) FROM campaigns WHERE title=%s", (data["title"],)
            ).fetchone()[0]
            == 0
        )
    row = p.ok(
        "donantes", "POST", "/api/v1/campaigns", user="operator1", key=key, data=data
    )
    for _ in range(2):
        donor = p.ok(
            "donantes", "POST", "/api/v1/donors", user="medical1", data=donor_data()
        )
        p.ok(
            "donantes",
            "POST",
            "/api/v1/appointments",
            user="operator1",
            data={"donor_id": donor["id"], "campaign_id": row["id"]},
        )
    edited = {
        **data,
        "capacity": 1,
        "version": row["version"],
        "reason": "Ajuste documentado",
        "human_confirmation": True,
    }
    path = "/api/v1/campaigns/" + row["id"]
    error = assert_fields(
        p.request(
            "donantes", "PATCH", path, user="operator1", key=key + "edit", data=edited
        ),
        {"capacity"},
        409,
    )
    assert error["details"][0]["ge"] == 2
    edited["capacity"] = 2
    p.ok("donantes", "PATCH", path, user="operator1", key=key + "edit", data=edited)
    stale = p.request("donantes", "PATCH", path, user="operator1", data=edited)
    assert stale.status_code == 409 and stale.json()["error"]["code"] == "stale_version"


def test_inventory_and_shipment_date_rejections_are_atomic(p):
    data = {
        "folio": "INV-" + uuid4().hex[:12],
        "kind": "BLOOD",
        "component": "RBC",
        "blood_group": "O-",
        "expires_at": iso(days=1),
    }
    for changes, fields in [
        ({"expires_at": iso(days=-1)}, {"expires_at"}),
        ({"collected_at": iso(minutes=2)}, {"collected_at"}),
        ({"kind": "ORGAN", "component": "RBC"}, {"component"}),
    ]:
        assert_fields(
            p.request(
                "inventario",
                "POST",
                "/api/v1/resources",
                user="operator1",
                data={**data, **changes},
            ),
            fields,
        )
    with p.owner("inventario") as conn:
        assert (
            conn.execute(
                "SELECT count(*) FROM resources WHERE folio=%s", (data["folio"],)
            ).fetchone()[0]
            == 0
        )
    unit = resource(p)
    _, req = recipient_request(p)
    assigned = reservation(p, evaluation(p, req, [unit]), unit)["reservation"]
    plan = {
        "reservation_id": assigned["id"],
        "transport_user_id": p.env.state["accounts"]["transport1"]["id"],
        "departure_at": iso(minutes=2),
        "eta": iso(minutes=30),
        "reason": "Plan de prueba revisado",
        "human_confirmation": True,
    }
    key = uuid4().hex
    for changes, fields in [
        ({"eta": plan["departure_at"]}, {"departure_at", "eta"}),
        ({"eta": iso(days=3)}, {"eta"}),
        ({"departure_at": iso(minutes=-5)}, {"departure_at"}),
        ({"eta": iso(minutes=3)}, {"departure_at", "eta"}),
    ]:
        assert_fields(
            p.request(
                "transporte",
                "POST",
                "/api/v1/shipments",
                user="coordinator1",
                key=key,
                data={**plan, **changes},
            ),
            fields,
        )
    with p.owner("transporte") as conn:
        assert (
            conn.execute(
                "SELECT count(*) FROM shipments WHERE reservation_id=%s",
                (assigned["id"],),
            ).fetchone()[0]
            == 0
        )
    result = p.ok(
        "transporte",
        "POST",
        "/api/v1/shipments",
        user="coordinator1",
        key=key,
        data=plan,
    )
    assert result["reservation_id"] == assigned["id"]


def test_schedule_and_organ_request_dependencies(p):
    site = p.ok(
        "identidad_acceso",
        "POST",
        "/api/v1/catalogues/sites",
        user="admin1",
        data={
            "name": "Sede de validación",
            "municipality": "Municipio ficticio",
            "address": "Domicilio ficticio",
        },
    )
    schedule = {
        "parent_id": site["id"],
        "name": "Horario ficticio",
        "weekday": 1,
        "opens_at": "18:00",
        "closes_at": "08:00",
    }
    assert_fields(
        p.request(
            "identidad_acceso",
            "POST",
            "/api/v1/catalogues/schedules",
            user="admin1",
            data=schedule,
        ),
        {"opens_at", "closes_at"},
    )
    assert_fields(
        p.request(
            "identidad_acceso",
            "POST",
            "/api/v1/catalogues/schedules",
            user="admin1",
            data={**schedule, "opens_at": "29:00"},
        ),
        {"opens_at"},
    )
    p.ok(
        "identidad_acceso",
        "POST",
        "/api/v1/catalogues/schedules",
        user="admin1",
        data={**schedule, "opens_at": "07:00"},
    )
    person, _ = recipient_request(p, "ORGAN", "KIDNEY", "O+")
    request = {
        "recipient_id": person["id"],
        "component": "KIDNEY",
        "quantity": 2,
        "urgency": 1,
    }
    assert_fields(
        p.request("receptores", "POST", "/api/v1/requests", data=request), {"quantity"}
    )
    assert_fields(
        p.request(
            "receptores",
            "POST",
            "/api/v1/requests",
            data={**request, "quantity": 1, "component": "LIVER"},
        ),
        {"component"},
    )
    with p.owner("receptores") as conn:
        assert (
            conn.execute(
                "SELECT count(*) FROM requests WHERE recipient_id=%s", (person["id"],)
            ).fetchone()[0]
            == 1
        )


@pytest.mark.parametrize(
    "content,mime,digest,fragment",
    [
        (b"", "image/png", None, "vacío"),
        (b"archivo", "image/png", "0" * 64, "cambió"),
        (b"archivo", "image/png", None, "formato"),
        (b"archivo", "application/pdf", None, "PDF válido"),
    ],
)
def test_file_rejections_explain_correction(content, mime, digest, fragment):
    with pytest.raises(APIError) as caught:
        inspect_content(content, mime, digest or hashlib.sha256(content).hexdigest())
    assert fragment in caught.value.message
    assert caught.value.details[0]["field"] == "evidence"
