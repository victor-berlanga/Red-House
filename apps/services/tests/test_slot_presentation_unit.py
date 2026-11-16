"""Bounded, authorized slot labels and contracts; no databases or network processes."""

from contextlib import nullcontext
from uuid import uuid4

import pytest
from flask import Flask, g
from jsonschema import Draft202012Validator, ValidationError
from ms_donantes import agenda
from ms_identidad_acceso import catalogue, create_app
from pydantic import ValidationError as ModelValidationError
from redhouse.errors import APIError
from redhouse.examples import response_xml
from redhouse.extension_contracts import schema
from redhouse.xml_response import validate_response


def test_slot_labels_resolve_only_the_authorized_page(monkeypatch):
    tenant, campaign_a, campaign_b, site_a, site_b = [str(uuid4()) for _ in range(5)]
    rows = [
        {"id": str(uuid4()), "campaign_id": campaign_a, "site_id": site_a},
        {"id": str(uuid4()), "campaign_id": campaign_b, "site_id": site_b},
    ]
    calls = []

    class Connection:
        def execute(self, sql, params):
            assert params == (tenant, sorted([campaign_a, campaign_b]))
            return self

        def fetchall(self):
            return [
                {"id": campaign_a, "title": "Campaign outside a client catalogue page"},
                {"id": campaign_b, "title": "Second campaign"},
            ]

    def labels(service, method, path, body):
        calls.append((service, method, path, body))
        return {
            "items": [
                {"id": site_b, "name": "Second site"},
                {"id": site_a, "name": "First site"},
            ]
        }

    monkeypatch.setattr(agenda, "call", labels)
    with Flask(__name__).app_context():
        g.actor = {"tenant_id": tenant}
        result = agenda.slot_site_labels(
            agenda.slot_campaign_labels(Connection(), rows)
        )
    assert [(r["campaign_title"], r["site_name"]) for r in result] == [
        ("Campaign outside a client catalogue page", "First site"),
        ("Second campaign", "Second site"),
    ]
    assert len(calls) == 1
    assert calls[0][:3] == (
        "identidad_acceso",
        "POST",
        "/internal/v1/appointment-site-labels",
    )
    assert calls[0][3] == {"ids": sorted([site_a, site_b])}
    assert all("site_name" not in row for row in rows)


def test_missing_site_fails_closed_instead_of_showing_an_identifier(monkeypatch):
    monkeypatch.setattr(agenda, "call", lambda *args: {"items": []})
    with pytest.raises(APIError) as error:
        agenda.slot_site_labels([{"site_id": str(uuid4())}])
    assert error.value.code == "dependency_unavailable"
    monkeypatch.setattr(
        agenda, "call", lambda *args: pytest.fail("Empty page must not call Identity")
    )
    assert agenda.slot_site_labels([]) == []


def test_internal_site_projection_is_bounded_delegated_and_tenant_scoped(monkeypatch):
    app = create_app(
        {
            "DATABASE_URL": "unused",
            "JWT_PUBLIC_KEY": "unused",
            "JWT_PRIVATE_KEY": "unused",
        }
    )
    contract = next(
        c for c in app.extensions["contracts"] if c["name"] == "appointment_site_labels"
    )
    assert contract["internal"] == ("donantes",)
    assert contract["roles"] == ("DONOR", "OPERATOR")
    assert contract["delegate"] is True
    with pytest.raises(ModelValidationError):
        catalogue.AppointmentSiteLabelsQuery(ids=[str(uuid4()) for _ in range(101)])
    tenant, site = str(uuid4()), str(uuid4())
    observed = []

    class Connection:
        def execute(self, sql, params):
            observed.append(params)
            assert "tenant_id=%s" in sql and "kind='sites'" in sql
            return self

        def fetchall(self):
            return [{"id": site, "name": "Authorized site"}]

    monkeypatch.setattr(catalogue, "transaction", lambda: nullcontext(Connection()))
    monkeypatch.setattr("redhouse.events.audit_read", lambda *_: None)
    with app.test_request_context():
        g.actor = {"tenant_id": tenant}
        result = app.view_functions["appointment_site_labels"].__wrapped__(
            data={"ids": [site]}
        )
    assert observed == [(tenant, [site])]
    assert result == {"items": [{"id": site, "name": "Authorized site"}]}


def test_slot_labels_are_required_in_json_and_xml():
    result = {
        "id": str(uuid4()),
        "tenant_id": str(uuid4()),
        "campaign_id": str(uuid4()),
        "site_id": str(uuid4()),
        "starts_at": "2026-11-17T18:00:00Z",
        "ends_at": "2026-11-17T19:00:00Z",
        "capacity": 1,
        "active": True,
        "version": 1,
        "created_at": "2026-11-16T18:00:00Z",
        "occupied": 0,
        "attended": 0,
        "available": 1,
        "campaign_title": "Academic campaign",
        "site_name": "Academic site",
    }
    contract = schema(agenda.SlotAvailability)
    Draft202012Validator(contract).validate(result)
    assert validate_response(response_xml(result).encode(), contract) == result
    for field in ("campaign_title", "site_name"):
        incomplete = {k: v for k, v in result.items() if k != field}
        with pytest.raises(ValidationError):
            Draft202012Validator(contract).validate(incomplete)
        with pytest.raises(ValueError):
            validate_response(response_xml(incomplete).encode(), contract)


def test_existing_active_booking_has_a_specific_rejection_before_insertion(monkeypatch):
    donor_id, campaign_id, tenant, user = [str(uuid4()) for _ in range(4)]
    donor = {
        "id": donor_id,
        "tenant_id": tenant,
        "user_id": user,
        "status": "PRELIMINARY",
    }
    campaign = {"id": campaign_id, "tenant_id": tenant}
    monkeypatch.setattr(
        agenda, "get", lambda _, table, *args: donor if table == "donors" else campaign
    )
    monkeypatch.setattr(
        agenda, "insert", lambda *args: pytest.fail("Duplicate must not be inserted")
    )

    class Connection:
        def execute(self, sql, params):
            assert params == (donor_id, campaign_id)
            return self

        def fetchone(self):
            return {"exists": 1}

    with Flask(__name__).app_context():
        g.actor = {"id": user, "role": "DONOR", "tenant_id": tenant}
        with pytest.raises(APIError) as error:
            agenda.book(
                Connection(), {"donor_id": donor_id, "campaign_id": campaign_id}
            )
    assert error.value.status == 409
    assert error.value.code == "active_appointment"
