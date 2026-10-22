"""Bajas reales con permisos, historia, concurrencia y formularios CSRF."""

from concurrent.futures import ThreadPoolExecutor
import json
from uuid import uuid4

import pytest
import requests
from lxml import etree

from redhouse.examples import request_xml
from redhouse.xml_response import validate_response

from .helpers import iso
from .test_continuity import autonomous
from .test_web_integration import web, login, post, form


def donor(p):
    return p.ok(
        "donantes",
        "POST",
        "/api/v1/donors",
        user="medical1",
        data={
            "folio": "BAJA-" + uuid4().hex[:12],
            "display_name": "Registro temporal",
            "blood_group": "O+",
            "consent": True,
        },
    )


def withdrawal(row):
    return {
        "version": row["version"],
        "human_confirmation": True,
        "reason": "Corrección de registro creado por error",
    }


def review(p, row):
    return p.ok(
        "donantes",
        "POST",
        f"/api/v1/donors/{row['id']}/reviews",
        user="medical1",
        data={**withdrawal(row), "decision": "ELIGIBLE"},
    )


def campaign(p):
    return p.ok(
        "donantes",
        "POST",
        "/api/v1/campaigns",
        user="operator1",
        data={
            "title": "Jornada temporal",
            "starts_at": iso(days=1),
            "ends_at": iso(days=2),
            "capacity": 1,
        },
    )


def test_empty_donor_is_deleted_with_idempotency_and_audit(p):
    row = donor(p)
    # Abrir el expediente no cuenta como historia que obligue a conservarlo.
    p.ok("donantes", "GET", f"/api/v1/donors/{row['id']}", user="medical1")
    path = f"/api/v1/donors/{row['id']}/withdraw"
    key = uuid4().hex
    result = p.ok(
        "donantes", "POST", path, user="medical1", data=withdrawal(row), key=key
    )
    assert result == {"id": row["id"], "mode": "DELETED", "cancelled_appointments": 0}
    assert (
        p.ok("donantes", "POST", path, user="medical1", data=withdrawal(row), key=key)
        == result
    )
    assert (
        p.request(
            "donantes", "GET", f"/api/v1/donors/{row['id']}", user="medical1"
        ).status_code
        == 404
    )
    with p.owner("donantes") as conn:
        assert (
            conn.execute(
                "SELECT count(*) FROM donors WHERE id=%s", (row["id"],)
            ).fetchone()[0]
            == 0
        )
        decisions = conn.execute(
            "SELECT action,reason FROM decisions WHERE resource_id=%s", (row["id"],)
        ).fetchall()
        assert decisions == [("DONOR_WITHDRAWN", withdrawal(row)["reason"])]
        assert (
            conn.execute(
                "SELECT count(*) FROM activity_events WHERE event->>'resource_id'=%s AND event->>'action'='DONOR_WITHDRAWN'",
                (row["id"],),
            ).fetchone()[0]
            == 1
        )
    p.drain()
    with p.owner("auditoria") as conn:
        assert (
            conn.execute(
                "SELECT count(*) FROM audit_events WHERE event->>'resource_id'=%s AND event->>'action'='DONOR_WITHDRAWN'",
                (row["id"],),
            ).fetchone()[0]
            == 1
        )


@pytest.mark.parametrize("user", ["operator1", "admin1", "donor1", "medical2", None])
def test_withdrawal_requires_same_institution_medical_role(p, user):
    row = donor(p)
    response = p.request(
        "donantes",
        "POST",
        f"/api/v1/donors/{row['id']}/withdraw",
        user=user,
        data=withdrawal(row),
    )
    assert response.status_code == (401 if user is None else 403)
    assert (
        p.ok("donantes", "GET", f"/api/v1/donors/{row['id']}", user="medical1")[
            "status"
        ]
        == "PRELIMINARY"
    )


@pytest.mark.parametrize(
    "change,status",
    [
        ({"version": 2}, 409),
        ({"reason": ""}, 422),
        ({"human_confirmation": False}, 422),
        ({"version": 0}, 422),
    ],
)
def test_withdrawal_rejects_stale_or_invalid_confirmation(p, change, status):
    row = donor(p)
    assert (
        p.request(
            "donantes",
            "POST",
            f"/api/v1/donors/{row['id']}/withdraw",
            user="medical1",
            data={**withdrawal(row), **change},
        ).status_code
        == status
    )
    assert (
        p.ok("donantes", "GET", f"/api/v1/donors/{row['id']}", user="medical1")[
            "version"
        ]
        == 1
    )


@pytest.mark.parametrize(
    "history_kind",
    ["review", "donation", "appointment", "cancelled_appointment", "edit"],
)
def test_donor_with_history_is_inactive_and_cannot_start_new_operations(
    p, history_kind
):
    row = donor(p)
    path = f"/api/v1/donors/{row['id']}"
    booked = None
    event = campaign(p)
    if history_kind in ("review", "donation"):
        review(p, row)
    if history_kind == "donation":
        p.ok(
            "donantes",
            "POST",
            "/api/v1/donations",
            user="medical1",
            data={
                "donor_id": row["id"],
                "kind": "BLOOD",
                "component": "RBC",
                "collected_at": iso(minutes=-5),
                "human_confirmation": True,
                "reason": "Registro de recolección para verificar conservación",
            },
        )
    if history_kind in ("appointment", "cancelled_appointment"):
        booked = p.ok(
            "donantes",
            "POST",
            "/api/v1/appointments",
            user="operator1",
            data={"donor_id": row["id"], "campaign_id": event["id"]},
        )
        if history_kind == "cancelled_appointment":
            p.ok(
                "donantes",
                "POST",
                f"/api/v1/appointments/{booked['id']}/cancel",
                user="operator1",
            )
    fields = {k: row[k] for k in ("folio", "display_name", "blood_group", "consent")}
    if history_kind == "edit":
        p.ok(
            "donantes",
            "PATCH",
            path,
            user="medical1",
            data={**fields, **withdrawal(row)},
        )
    before = p.ok("donantes", "GET", path, user="medical1")
    summary_before = p.ok("donantes", "GET", "/api/v1/summary", user="medical1")[
        "total"
    ]
    result = p.ok(
        "donantes", "POST", path + "/withdraw", user="medical1", data=withdrawal(before)
    )
    assert result["mode"] == "INACTIVE"
    assert result["cancelled_appointments"] == (
        1 if history_kind == "appointment" else 0
    )
    after = p.ok("donantes", "GET", path, user="medical1")
    assert after["status"] == "INACTIVE"
    assert after["version"] == before["version"] + 1
    assert after["reviews"] == before["reviews"]
    assert after["decisions"][:-1] == before["decisions"]
    assert (
        p.ok("donantes", "GET", "/api/v1/summary", user="medical1")["total"]
        == summary_before - 1
    )
    assert (
        p.ok("donantes", "GET", "/api/v1/donors?q=" + row["folio"], user="medical1")[
            "total"
        ]
        == 0
    )
    for method, url, data in [
        ("POST", path + "/reviews", {**withdrawal(after), "decision": "ELIGIBLE"}),
        ("PATCH", path, {**fields, **withdrawal(after)}),
        (
            "POST",
            "/api/v1/appointments",
            {"donor_id": row["id"], "campaign_id": event["id"]},
        ),
        (
            "POST",
            "/api/v1/donations",
            {
                "donor_id": row["id"],
                "kind": "BLOOD",
                "component": "RBC",
                "collected_at": iso(minutes=-1),
                "human_confirmation": True,
                "reason": "Recolección inválida por baja",
            },
        ),
        ("POST", path + "/withdraw", withdrawal(after)),
    ]:
        user = "operator1" if url == "/api/v1/appointments" else "medical1"
        response = p.request("donantes", method, url, user=user, data=data)
        assert response.status_code == 409, response.text
        assert response.json()["error"]["code"] == "donor_inactive"
    with p.owner("donantes") as conn:
        assert (
            conn.execute(
                "SELECT count(*) FROM donors WHERE id=%s", (row["id"],)
            ).fetchone()[0]
            == 1
        )
        if booked:
            assert (
                conn.execute(
                    "SELECT status FROM appointments WHERE id=%s", (booked["id"],)
                ).fetchone()[0]
                == "CANCELLED"
            )
        if history_kind == "donation":
            assert (
                conn.execute(
                    "SELECT count(*) FROM donations WHERE donor_id=%s", (row["id"],)
                ).fetchone()[0]
                == 1
            )
    # La baja libera el único cupo, sin borrar la inscripción anterior.
    other = donor(p)
    p.ok(
        "donantes",
        "POST",
        "/api/v1/appointments",
        user="operator1",
        data={"donor_id": other["id"], "campaign_id": event["id"]},
    )


def test_appointment_racing_with_withdrawal_has_no_orphan_or_active_booking(p):
    row = donor(p)
    event = campaign(p)
    with ThreadPoolExecutor(max_workers=2) as executor:
        withdraw = executor.submit(
            p.request,
            "donantes",
            "POST",
            f"/api/v1/donors/{row['id']}/withdraw",
            user="medical1",
            data=withdrawal(row),
        )
        book = executor.submit(
            p.request,
            "donantes",
            "POST",
            "/api/v1/appointments",
            user="operator1",
            data={"donor_id": row["id"], "campaign_id": event["id"]},
        )
        result, appointment = withdraw.result(), book.result()
    assert result.status_code == 200, result.text
    assert appointment.status_code in (201, 404), appointment.text
    with p.owner("donantes") as conn:
        assert (
            conn.execute(
                "SELECT count(*) FROM appointments WHERE donor_id=%s AND status='BOOKED'",
                (row["id"],),
            ).fetchone()[0]
            == 0
        )
        stored = conn.execute(
            "SELECT status FROM donors WHERE id=%s", (row["id"],)
        ).fetchone()
        assert stored == (("INACTIVE",) if appointment.status_code == 201 else None)


@pytest.mark.parametrize("mode", ["microservices", "monolith"])
def test_web_withdrawal_requires_csrf_and_preserves_inactive_history(p, request, mode):
    web = request.getfixturevalue("web" if mode == "microservices" else "autonomous")
    row = donor(p)
    medical = login(web, p, "medical1")
    operator = login(web, p, "operator1")
    path = f"/donantes/donor/{row['id']}"
    assert etree.HTML(medical.get(path).data).xpath(
        '//a[contains(@href,"/baja")]/img[contains(@src,"trash.svg")]'
    )
    assert not etree.HTML(operator.get(path).data).xpath('//a[contains(@href,"/baja")]')
    confirmation = medical.get(path + "/baja")
    assert row["folio"] in confirmation.text
    assert row["display_name"] in confirmation.text
    assert operator.get(path + "/baja").status_code == 403
    assert (
        medical.post(
            path + "/baja",
            data={"version": 1, "human_confirmation": "on", "reason": "Baja sin CSRF"},
        ).status_code
        == 400
    )
    # POST repetido después del borrado conserva la respuesta idempotente.
    data = {
        **form(medical, path + "/baja"),
        "human_confirmation": "on",
        "reason": "Registro creado por error",
    }
    assert medical.post(path + "/baja", data=data).status_code == 302
    assert medical.post(path + "/baja", data=data).status_code == 302
    row = donor(p)
    review(p, row)
    path = f"/donantes/donor/{row['id']}"
    assert (
        post(
            medical,
            path + "/baja",
            {
                "human_confirmation": "on",
                "reason": "Baja con conservación de historial",
            },
        )
        == "/donantes/donor"
    )
    page = medical.get(path)
    assert page.status_code == 200
    assert "Puedes consultar sus antecedentes" in page.text
    assert "Registrar dictamen" not in page.text
    assert "Registrar donación" not in page.text
    assert not etree.HTML(page.data).xpath('//a[contains(@href,"/baja")]')
    assert (
        medical.get("/opciones/donors", query_string={"q": row["folio"]}).json["total"]
        == 0
    )
    assert (
        medical.get("/opciones/eligible-donors", query_string={"q": row["folio"]}).json[
            "total"
        ]
        == 0
    )


def test_withdrawal_accepts_xml_and_validates_response_contract(p):
    row = donor(p)
    response = requests.post(
        p.urls["donantes"] + f"/api/v1/donors/{row['id']}/withdraw",
        data=request_xml(withdrawal(row)).encode(),
        headers={
            "Authorization": "Bearer " + p.tokens["medical1"],
            "Content-Type": "application/xml",
            "Accept": "application/xml",
            "Idempotency-Key": uuid4().hex,
        },
        timeout=20,
    )
    assert response.status_code == 200, response.text
    from redhouse.schema import service_path

    schema = json.loads(
        (
            service_path("donantes") / "contracts/donor_withdraw.response.json"
        ).read_text()
    )
    value = validate_response(response.content, schema)
    assert value["data"] == {
        "id": row["id"],
        "mode": "DELETED",
        "cancelled_appointments": 0,
    }
