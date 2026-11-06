"""Contratos y límites añadidos al cierre; dependencias y datos siempre aislados."""

import json
from pathlib import Path
from uuid import uuid4

import pytest
from lxml import etree

from .helpers import iso
from .test_final_operations import CONFIRM
from .test_final_quality import api


@pytest.mark.parametrize("fmt", ["json", "xml"])
def test_institution_services_responsibles_and_current_scope(p, fmt):
    site = api(
        p,
        "identidad_acceso",
        "/api/v1/catalogues/sites",
        {
            "name": "Sede " + uuid4().hex[:10],
            "municipality": "Monterrey",
            "address": "Domicilio sintético",
        },
        "admin1",
        fmt,
    )
    cases = {
        "services": {
            "description": "Laboratorio de demostración",
            "capability_reference": "Referencia sintética",
        },
        "responsibles": {
            "user_id": p.env.state["accounts"]["medical1"]["id"],
            "function": "Responsable de prueba",
            "authorization_reference": "Autorización sintética",
        },
    }
    for kind, fields in cases.items():
        base = "/api/v1/catalogues/" + kind
        body = dict(fields, parent_id=site["id"], name="Registro " + uuid4().hex[:10])
        row = api(p, "identidad_acceso", base, body, "admin1", fmt)
        api(
            p,
            "identidad_acceso",
            base + "/" + row["id"],
            user="admin1",
            fmt=fmt,
            method="GET",
        )
        api(p, "identidad_acceso", base, user="admin1", fmt=fmt, method="GET")
        assert (
            p.request(
                "identidad_acceso", "GET", base + "/" + row["id"], user="admin2"
            ).status_code
            == 403
        )
        changed = api(
            p,
            "identidad_acceso",
            base + "/" + row["id"],
            {**body, **CONFIRM, "active": False, "version": 1},
            "admin1",
            fmt,
            "PATCH",
        )
        assert not changed["active"] and changed["version"] == 2


def test_operational_release_cannot_omit_laboratory_profile(p, monkeypatch):
    unit = api(
        p,
        "inventario",
        "/api/v1/resources",
        {
            "folio": "GATE-" + uuid4().hex[:10],
            "kind": "BLOOD",
            "component": "RBC",
            "blood_group": "O-",
            "expires_at": iso(days=1),
        },
        "operator1",
    )
    monkeypatch.setitem(p.apps["inventario"].config, "REQUIRE_LAB_PROFILE", True)
    result = p.request(
        "inventario",
        "POST",
        f"/api/v1/resources/{unit['id']}/release",
        user="medical1",
        data={**CONFIRM, "version": 1},
    )
    assert (
        result.status_code == 409
        and result.json()["error"]["code"] == "laboratory_incomplete"
    )
    assert (
        p.ok("inventario", "GET", f"/api/v1/resources/{unit['id']}", user="medical1")[
            "status"
        ]
        == "QUARANTINE"
    )


def test_published_websocket_examples_validate_both_encodings():
    from ms_transporte.tracking_contracts import Message, Event, decode

    root = Path(__file__).resolve().parents[1] / "ms_transporte/contracts/websocket"
    count = 0
    for path in root.glob("*.json"):
        if path.name.endswith("schema.json"):
            continue
        model = Message if path.name.startswith("client-") else Event
        expected = decode(path.read_text().strip(), model)
        xml = path.with_suffix(".xml").read_text().strip()
        assert decode(xml, model, "xml") == expected
        xsd = root / ("message.xsd" if model is Message else "event.xsd")
        etree.XMLSchema(etree.parse(str(xsd))).assertValid(
            etree.fromstring(xml.encode())
        )
        count += 1
    assert count == 13


def test_acl_upgrade_preserves_accounts_passwords_and_sessions(p):
    import redis
    from scripts.upgrade_final_acl import upgrade_acl

    config = p.env.configs["identidad_acceso"]
    with redis.Redis.from_url(
        p.env.state["redis_admin"], decode_responses=True
    ) as admin:
        before = {
            name: admin.acl_getuser(name)["passwords"] for name in admin.acl_users()
        }
        key = config["REDIS_PREFIX"] + "session:upgrade-preservation"
        admin.set(key, "synthetic-session", ex=300)
        upgrade_acl(p.env.directory, p.env.state)
        assert {
            name: admin.acl_getuser(name)["passwords"] for name in admin.acl_users()
        } == before
        assert admin.get(key) == "synthetic-session"
    assert (
        p.request(
            "inventario", "GET", "/api/v1/resources", user="operator1"
        ).status_code
        == 200
    )


@pytest.mark.parametrize("fmt", ["json", "xml"])
def test_policy_corrections_keep_author_source_effectivity_and_history(p, fmt):
    bodies = [
        (
            "alertas",
            "/api/v1/alert-policies",
            "admin1",
            {
                "message_code": "POLICY_" + uuid4().hex.upper(),
                "severity": "WARNING",
                "reminder_seconds": 60,
                "escalate_seconds": 120,
                "escalation_role": "OPERATOR",
                "source": "Política institucional sintética",
                "effective_at": iso(),
            },
        ),
        (
            "inventario",
            "/api/v1/cold/profiles",
            "medical1",
            {
                "kind": "BLOOD",
                "component": "RBC",
                "minimum_c": 1.0,
                "maximum_c": 9.0,
                "max_gap_seconds": 600,
                "source": "Perfil térmico sintético",
                "synthetic": True,
                "effective_at": iso(),
            },
        ),
    ]
    for service, path, user, body in bodies:
        original = api(p, service, path, body, user, fmt)
        changed = api(
            p,
            service,
            path,
            dict(
                body,
                version=2,
                supersedes=original["id"],
                source="Corrección sintética autorizada",
            ),
            user,
            fmt,
        )
        assert (
            changed["version"] == 2
            and changed["author_id"] == p.env.state["accounts"][user]["id"]
        )
        assert changed["supersedes"] == original["id"]
        history = api(
            p, service, path + "/" + original["id"], user=user, fmt=fmt, method="GET"
        )
        assert history["version"] == 1 and history["source"] == body["source"]


def test_expiry_worker_quarantines_without_deleting_and_is_repeatable(p):
    from .helpers import resource
    from ms_inventario.quality import scan_quality

    unit = resource(p)
    with p.owner("inventario") as conn:
        conn.execute(
            "UPDATE resources SET expires_at=now()-interval '1 second' WHERE id=%s",
            (unit["id"],),
        )
    with p.apps["inventario"].app_context():
        scan_quality()
        scan_quality()
    changed = p.ok(
        "inventario", "GET", "/api/v1/resources/" + unit["id"], user="medical1"
    )
    assert changed["status"] == "QUARANTINE"
    with p.owner("inventario") as conn:
        assert (
            conn.execute(
                "SELECT count(*) FROM activity_events WHERE event->>'action'='RESOURCE_EXPIRED' AND event->>'resource_id'=%s",
                (unit["id"],),
            ).fetchone()[0]
            == 1
        )
