"""Upcoming donor booking uses slot time, ownership and current schedule state."""

from uuid import uuid4

import pytest

from .helpers import iso
from .test_final_operations import CONFIRM
from .test_final_quality import api


@pytest.mark.parametrize("fmt", ["json", "xml"])
def test_next_appointment_is_owned_future_and_not_limited_by_list_page(p, fmt):
    username = "next-" + uuid4().hex[:12]
    password = "Synthetic-appointment-password"
    api(
        p,
        "identidad_acceso",
        "/api/v1/users",
        {
            "username": username,
            "password": password,
            "tenant_id": p.env.state["tenants"][0],
            "role": "DONOR",
        },
        "admin1",
    )
    session = api(
        p,
        "identidad_acceso",
        "/api/v1/auth/login",
        {
            "username": username,
            "password": password,
        },
        None,
    )
    p.tokens[username] = session["access_token"]
    donor = api(
        p,
        "donantes",
        "/api/v1/donors",
        {
            "folio": "NEXT-" + uuid4().hex[:12],
            "display_name": "Persona ficticia",
            "blood_group": "O-",
            "consent": True,
        },
        username,
    )

    def upcoming(user=username):
        return api(
            p, "donantes", "/api/v1/appointments/next", user=user, fmt=fmt, method="GET"
        )["appointment"]

    assert upcoming() is None
    site = api(
        p,
        "identidad_acceso",
        "/api/v1/catalogues/sites",
        {
            "name": "Sede " + uuid4().hex[:12],
            "municipality": "Monterrey",
            "address": "Ubicación ficticia",
        },
        "admin1",
    )
    campaign = api(
        p,
        "donantes",
        "/api/v1/campaigns",
        {
            "title": "Próxima cita sintética",
            "starts_at": iso(minutes=5),
            "ends_at": iso(days=2),
            "capacity": 20,
        },
        "operator1",
    )
    slots = [
        api(
            p,
            "donantes",
            "/api/v1/campaign-slots",
            {
                "campaign_id": campaign["id"],
                "site_id": site["id"],
                "starts_at": iso(minutes=30 + i * 30),
                "ends_at": iso(minutes=45 + i * 30),
                "capacity": 10,
            },
            "operator1",
        )
        for i in range(2)
    ]
    booked = api(
        p,
        "donantes",
        "/api/v1/appointments",
        {
            "donor_id": donor["id"],
            "campaign_id": campaign["id"],
            "slot_id": slots[1]["id"],
        },
        username,
    )
    # More recent cancelled rows push the live booking past a 100-row page.
    # Owner SQL prepares only the synthetic fixture; all assertions use HTTP.
    with p.owner("donantes") as conn:
        for _ in range(105):
            conn.execute(
                "INSERT INTO appointments(id,tenant_id,donor_id,campaign_id,status) "
                "VALUES(%s,%s,%s,%s,'CANCELLED')",
                (str(uuid4()), donor["tenant_id"], donor["id"], campaign["id"]),
            )
    result = upcoming()
    assert result["id"] == booked["id"]
    assert result["slot_id"] == slots[1]["id"]
    assert result["title"] == campaign["title"]
    assert result["schedule_version"] == 1
    # Seed donor1 is another account in the same institution.
    assert upcoming("donor1") is None
    assert upcoming("donor2") is None
    assert (
        p.request(
            "donantes", "GET", "/api/v1/appointments/next", user="operator1"
        ).status_code
        == 403
    )
    api(
        p,
        "donantes",
        f"/api/v1/appointments/{booked['id']}/commands",
        {
            **CONFIRM,
            "version": 1,
            "action": "RESCHEDULE",
            "slot_id": slots[0]["id"],
        },
        username,
    )
    result = upcoming()
    assert result["slot_id"] == slots[0]["id"]
    assert result["starts_at"] == slots[0]["starts_at"]
    assert result["schedule_version"] == 2
    api(
        p,
        "donantes",
        f"/api/v1/appointments/{booked['id']}/commands",
        {
            **CONFIRM,
            "version": 2,
            "action": "CONFIRM",
        },
        username,
    )
    assert upcoming()["schedule_status"] == "CONFIRMED"
    api(
        p,
        "donantes",
        f"/api/v1/appointments/{booked['id']}/commands",
        {
            **CONFIRM,
            "version": 3,
            "action": "CANCEL",
        },
        username,
    )
    assert upcoming() is None
