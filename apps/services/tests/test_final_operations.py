from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest

from .helpers import iso, resource, recipient_request
from .test_final_quality import api

CONFIRM = {
    "human_confirmation": True,
    "reason": "Verificación autorizada con datos sintéticos",
}


@pytest.mark.parametrize("fmt", ["json", "xml"])
def test_consent_agenda_capacity_reminders_processing_and_lineage(p, fmt):
    donor_user = "agenda-" + uuid4().hex[:12]
    password = "Synthetic-agenda-password"
    api(
        p,
        "identidad_acceso",
        "/api/v1/users",
        {
            "username": donor_user,
            "password": password,
            "tenant_id": p.env.state["tenants"][0],
            "role": "DONOR",
        },
        "admin1",
        fmt,
    )
    session = api(
        p,
        "identidad_acceso",
        "/api/v1/auth/login",
        {"username": donor_user, "password": password},
        None,
        fmt,
    )
    p.tokens[donor_user] = session["access_token"]
    donor = api(
        p,
        "donantes",
        "/api/v1/donors",
        {
            "folio": "FINAL-" + uuid4().hex[:10],
            "display_name": "Persona ficticia",
            "blood_group": "O-",
            "consent": True,
        },
        donor_user,
        fmt,
    )
    consent = api(
        p,
        "donantes",
        f"/api/v1/donors/{donor['id']}/consents",
        {
            **CONFIRM,
            "version": 1,
            "policy_version": "SYNTHETIC-1",
            "reference": "Referencia autorizada",
            "effective_at": iso(),
            "granted": False,
        },
        donor_user,
        fmt,
    )
    assert consent["granted"] is False
    assert (
        p.request(
            "donantes",
            "POST",
            f"/api/v1/donors/{donor['id']}/reviews",
            user="medical1",
            data={**CONFIRM, "version": 2, "decision": "ELIGIBLE"},
        ).status_code
        == 409
    )
    api(
        p,
        "donantes",
        f"/api/v1/donors/{donor['id']}/consents",
        {
            **CONFIRM,
            "version": 2,
            "policy_version": "SYNTHETIC-2",
            "reference": "Nueva autorización",
            "effective_at": iso(),
            "granted": True,
        },
        donor_user,
        fmt,
    )
    assert (
        api(
            p,
            "donantes",
            f"/api/v1/donors/{donor['id']}/consents",
            user=donor_user,
            fmt=fmt,
            method="GET",
        )["total"]
        == 2
    )
    site = api(
        p,
        "identidad_acceso",
        "/api/v1/catalogues/sites",
        {
            "name": "Sede sintética " + uuid4().hex[:8],
            "municipality": "Monterrey",
            "address": "Ubicación ficticia",
        },
        "admin1",
        fmt,
    )
    campaign = api(
        p,
        "donantes",
        "/api/v1/campaigns",
        {
            "title": "Campaña sintética",
            "starts_at": iso(minutes=5),
            "ends_at": iso(minutes=120),
            "capacity": 10,
        },
        "operator1",
        fmt,
    )
    slots = [
        api(
            p,
            "donantes",
            "/api/v1/campaign-slots",
            {
                "campaign_id": campaign["id"],
                "site_id": site["id"],
                "starts_at": iso(minutes=10 + i * 20),
                "ends_at": iso(minutes=20 + i * 20),
                "capacity": 1,
            },
            "operator1",
            fmt,
        )
        for i in range(2)
    ]
    body = {
        "donor_id": donor["id"],
        "campaign_id": campaign["id"],
        "slot_id": slots[0]["id"],
    }
    with ThreadPoolExecutor(2) as pool:
        responses = list(
            pool.map(
                lambda _: p.request(
                    "donantes",
                    "POST",
                    "/api/v1/appointments",
                    user=donor_user,
                    data=body,
                ),
                range(2),
            )
        )
    assert sorted(r.status_code for r in responses) == [201, 409]
    appointment = next(r.json()["data"] for r in responses if r.status_code == 201)
    api(
        p,
        "donantes",
        f"/api/v1/appointments/{appointment['id']}/commands",
        {**CONFIRM, "version": 1, "action": "CONFIRM"},
        donor_user,
        fmt,
    )
    api(
        p,
        "donantes",
        f"/api/v1/appointments/{appointment['id']}/commands",
        {**CONFIRM, "version": 2, "action": "RESCHEDULE", "slot_id": slots[1]["id"]},
        donor_user,
        fmt,
    )
    from ms_donantes.agenda import reminders

    with p.apps["donantes"].app_context():
        reminders()
        reminders()
    with p.owner("donantes") as conn:
        assert (
            conn.execute(
                "SELECT count(*) FROM activity_events WHERE event->>'resource_id'=%s AND event->>'action'='APPOINTMENT_REMINDER'",
                (appointment["id"],),
            ).fetchone()[0]
            == 1
        )
    api(
        p,
        "donantes",
        f"/api/v1/appointments/{appointment['id']}/commands",
        {**CONFIRM, "version": 3, "action": "ATTEND"},
        "operator1",
        fmt,
    )
    api(
        p,
        "donantes",
        f"/api/v1/appointments/{appointment['id']}/schedule",
        user=donor_user,
        fmt=fmt,
        method="GET",
    )
    donation_body = {
        **CONFIRM,
        "donor_id": donor["id"],
        "kind": "BLOOD",
        "component": "RBC",
        "collected_at": iso(minutes=-2),
    }
    assert (
        p.request(
            "donantes", "POST", "/api/v1/donations", user="medical1", data=donation_body
        ).status_code
        == 409
    )
    api(
        p,
        "donantes",
        f"/api/v1/donors/{donor['id']}/reviews",
        {**CONFIRM, "version": 3, "decision": "ELIGIBLE"},
        "medical1",
        fmt,
    )
    donation = api(p, "donantes", "/api/v1/donations", donation_body, "medical1", fmt)
    api(
        p,
        "donantes",
        f"/api/v1/donations/{donation['id']}/steps",
        {**CONFIRM, "version": 1, "state": "PROCESSED"},
        "operator1",
        fmt,
    )
    parent = api(
        p,
        "inventario",
        "/api/v1/resources",
        {
            "folio": "PARENT-" + uuid4().hex[:8],
            "kind": "BLOOD",
            "component": "RBC",
            "blood_group": "O-",
            "expires_at": iso(days=2),
            "donation_id": donation["id"],
        },
        "operator1",
        fmt,
    )
    children = [
        {
            "folio": "CHILD-" + uuid4().hex[:8],
            "component": "RBC",
            "expires_at": iso(days=1),
        }
        for _ in range(2)
    ]
    result = api(
        p,
        "inventario",
        f"/api/v1/resources/{parent['id']}/components",
        {**CONFIRM, "version": 1, "children": children},
        "operator1",
        fmt,
    )
    links = api(
        p,
        "inventario",
        f"/api/v1/resources/{parent['id']}/lineage",
        user="medical1",
        fmt=fmt,
        method="GET",
    )
    assert len(links) == 2
    trace = api(
        p,
        "inventario",
        f"/api/v1/resources/{parent['id']}/trace",
        user="medical1",
        fmt=fmt,
        method="GET",
    )
    assert trace["donation_id"] == donation["id"] and len(trace["child_ids"]) == 2
    assert result
    p.drain()
    for action, identifier in [
        ("DONOR_CONSENT_RECORDED", donor["id"]),
        ("DONOR_CONSENT_WITHDRAWN", donor["id"]),
        ("APPOINTMENT_CONFIRM", appointment["id"]),
        ("APPOINTMENT_RESCHEDULE", appointment["id"]),
        ("APPOINTMENT_ATTEND", appointment["id"]),
    ]:
        events = api(
            p,
            "auditoria",
            "/api/v1/events?action=" + action + "&resource=" + identifier,
            user="auditor1",
            fmt=fmt,
            method="GET",
        )
        assert events["total"] >= 1
        assert all(
            row["result"] == "RECORDED" and row["category"] in ("BUSINESS", "DECISION")
            for row in events["items"]
        )
    p.tokens.pop(donor_user)


@pytest.mark.parametrize("fmt", ["json", "xml"])
def test_interoperability_accreditations_analytics_and_external_authorizations(p, fmt):
    unit = resource(p)
    mapping = api(
        p,
        "inventario",
        "/api/v1/interoperability/reconcile",
        {
            **CONFIRM,
            "system": "TEST-LIS",
            "external_id": "EXTERNAL-" + uuid4().hex,
            "resource_id": unit["id"],
            "resource_version": unit["version"],
            "folio": unit["folio"],
            "kind": unit["kind"],
            "component": unit["component"],
        },
        "operator1",
        fmt,
    )
    exported = api(
        p,
        "inventario",
        "/api/v1/interoperability/export/" + mapping["id"],
        user="operator1",
        fmt=fmt,
        method="GET",
    )
    assert (
        exported["resource_id"] == unit["id"] and not exported["clinical_authorization"]
    )
    assert (
        p.request(
            "inventario",
            "GET",
            "/api/v1/interoperability/export/" + mapping["id"],
            user="operator2",
        ).status_code
        == 403
    )
    api(
        p,
        "inventario",
        "/api/v1/external-mappings",
        user="operator1",
        fmt=fmt,
        method="GET",
    )
    api(
        p,
        "inventario",
        "/api/v1/external-mappings/" + mapping["id"],
        user="operator1",
        fmt=fmt,
        method="GET",
    )
    analytics = api(
        p,
        "inventario",
        "/api/v1/analytics/inventory?days=30",
        user="medical1",
        fmt=fmt,
        method="GET",
    )
    assert analytics["method"] == "EMPIRICAL-USE-1"
    assert analytics["demand_complete"]
    api(
        p,
        "transporte",
        "/api/v1/analytics/transport?days=30",
        user="medical1",
        fmt=fmt,
        method="GET",
    )
    assert all(x["estimated_surplus"] is None for x in analytics["products"])
    accreditation = api(
        p,
        "identidad_acceso",
        "/api/v1/accreditations",
        {
            **CONFIRM,
            "issuer": "Emisor ficticio",
            "category": "LICENSE",
            "reference": "Referencia sin certificación",
            "valid_from": iso(days=-1),
            "valid_until": iso(days=2),
        },
        "admin1",
        fmt,
    )
    api(
        p,
        "identidad_acceso",
        "/api/v1/accreditations/" + accreditation["id"],
        user="admin1",
        fmt=fmt,
        method="GET",
    )
    api(
        p,
        "identidad_acceso",
        "/api/v1/accreditations",
        user="admin1",
        fmt=fmt,
        method="GET",
    )
    _, req = recipient_request(p, kind="ORGAN", component="KIDNEY")
    auth = api(
        p,
        "receptores",
        f"/api/v1/requests/{req['id']}/external-authorizations",
        {
            **CONFIRM,
            "authority": "Autoridad ficticia; caso académico",
            "reference": "Constancia externa sintética",
            "valid_from": iso(days=-1),
            "valid_until": iso(days=1),
            "effective_at": iso(),
            "decision": "RECORDED",
        },
        "medical2",
        fmt,
    )
    assert auth["version"] == 1
    api(
        p,
        "receptores",
        f"/api/v1/requests/{req['id']}/external-authorizations",
        user="medical2",
        fmt=fmt,
        method="GET",
    )
