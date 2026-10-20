"""Expediente HTTP: contratos de infraestructura, errores y ediciones de negocio."""

import re
from uuid import uuid4

from .helpers import (
    evaluation,
    iso,
    move,
    plan,
    recipient_request,
    reservation,
    resource,
)

USERS = {
    "ADMIN": "admin1",
    "MEDICAL": "medical1",
    "OPERATOR": "operator1",
    "COORDINATOR": "coordinator1",
    "AUDITOR": "auditor1",
    "TRANSPORT": "transport1",
    "DONOR": "donor1",
}
CONFIRM = {
    "human_confirmation": True,
    "reason": "Corrección ficticia autorizada para evidencia HTTP",
}


def test_all_registered_routes_expose_real_http_contracts_and_controlled_errors(p):
    for service, app in p.apps.items():
        for path in (
            "/health/live",
            "/health/ready",
            "/health/database",
            "/health/redis",
            "/health/mongodb",
            "/health/storage",
            "/health/worker",
            "/openapi.json",
            "/docs/",
        ):
            assert p.request(service, "GET", path, user=None).status_code == 200
        assert (
            p.request(
                service, "GET", "/docs/static/swagger-ui.css", user=None
            ).status_code
            == 200
        )
        assert (
            p.request(
                service, "GET", "/docs/static/missing-file.css", user=None
            ).status_code
            == 404
        )
        first = app.extensions["contracts"][0]
        assert (
            p.request(
                service,
                "GET",
                "/schemas/" + first["name"] + ".response.json",
                user=None,
            ).status_code
            == 200
        )
        assert (
            p.request(service, "GET", "/schemas/response.xsd", user=None).status_code
            == 200
        )
        models = [c for c in app.extensions["contracts"] if c["model"]]
        if models:
            assert (
                p.request(
                    service, "GET", "/schemas/" + models[0]["name"] + ".xsd", user=None
                ).status_code
                == 200
            )
        assert (
            p.request(service, "GET", "/schemas/missing.xsd", user=None).status_code
            == 404
        )
        assert (
            p.request(
                service, "GET", "/schemas/missing.response.json", user=None
            ).status_code
            == 404
        )
        for contract in app.extensions["contracts"]:
            path = re.sub(r"<[^>]+>", lambda _: str(uuid4()), contract["path"])
            for mime in ("application/json", "application/xml"):
                result = p.request(
                    service,
                    contract["method"],
                    path,
                    user=None,
                    data={} if contract["method"] != "GET" else None,
                    headers={"Accept": mime},
                )
                assert result.status_code in (400, 401, 403, 415, 422), (
                    service,
                    path,
                    result.status_code,
                )
            if contract["method"] == "GET" and not contract.get("internal"):
                user = USERS[(contract.get("roles") or ("MEDICAL",))[0]]
                response = p.request(service, "GET", path, user=user)
                assert response.status_code in (200, 404), (
                    service,
                    path,
                    response.status_code,
                )


def test_edits_details_and_recovery_have_http_and_committed_evidence(p):
    identity = "identidad_acceso"
    institution = p.ok(
        identity,
        "GET",
        "/api/v1/institutions/" + p.env.state["tenants"][0],
        user="admin1",
    )
    p.ok(
        identity,
        "PATCH",
        "/api/v1/institutions/" + institution["id"],
        user="admin1",
        data=dict(CONFIRM, name=institution["name"], version=institution["version"]),
    )
    site = None
    for kind in ("sites", "contacts", "schedules", "capacities", "locations"):
        data = {"name": "Registro ficticio " + uuid4().hex[:8]}
        if kind == "sites":
            data.update(municipality="Monterrey", address="Dirección ficticia")
        elif kind == "contacts":
            data["value"] = "contacto@example.invalid"
        else:
            data["parent_id"] = site
            if kind == "schedules":
                data.update(weekday=1, opens_at="08:00", closes_at="16:00")
            elif kind == "capacities":
                data.update(component="RBC", quantity=5)
            else:
                data["description"] = "Ubicación ficticia autorizada"
        base = "/api/v1/catalogues/" + kind
        row = p.ok(identity, "POST", base, user="admin1", data=data)
        if kind == "sites":
            site = row["id"]
        p.ok(identity, "GET", base + "/" + row["id"], user="admin1")
        updated = p.ok(
            identity,
            "PATCH",
            base + "/" + row["id"],
            user="admin1",
            data=dict(data, **CONFIRM, active=True, version=row["version"]),
        )
        assert updated["version"] == row["version"] + 1
        with p.owner(identity) as conn:
            assert (
                conn.execute(
                    "SELECT version FROM catalogue WHERE id=%s", (row["id"],)
                ).fetchone()[0]
                == updated["version"]
            )
    donor = p.ok(
        "donantes",
        "POST",
        "/api/v1/donors",
        user="operator1",
        data={
            "folio": "EVID-" + uuid4().hex[:10],
            "display_name": "Donante ficticio",
            "blood_group": "O-",
            "consent": True,
        },
    )
    p.ok(
        "donantes",
        "POST",
        "/api/v1/donors/" + donor["id"] + "/reviews",
        user="medical1",
        data=dict(CONFIRM, decision="ELIGIBLE", version=donor["version"]),
    )
    donation = p.ok(
        "donantes",
        "POST",
        "/api/v1/donations",
        user="medical1",
        data=dict(
            CONFIRM,
            donor_id=donor["id"],
            kind="BLOOD",
            component="RBC",
            collected_at=iso(minutes=-5),
        ),
    )
    p.ok("donantes", "GET", "/api/v1/donations/" + donation["id"], user="medical1")
    p.ok(
        "donantes",
        "PATCH",
        "/api/v1/donations/" + donation["id"],
        user="medical1",
        data=dict(CONFIRM, collected_at=iso(minutes=-4), version=donation["version"]),
    )
    campaign_data = {
        "title": "Campaña ficticia",
        "starts_at": iso(),
        "ends_at": iso(days=1),
        "capacity": 10,
    }
    campaign = p.ok(
        "donantes", "POST", "/api/v1/campaigns", user="operator1", data=campaign_data
    )
    p.ok(
        "donantes",
        "PATCH",
        "/api/v1/campaigns/" + campaign["id"],
        user="operator1",
        data=dict(campaign_data, **CONFIRM, version=campaign["version"]),
    )
    person_data = {
        "folio": "EVID-" + uuid4().hex[:10],
        "display_name": "Receptor ficticio",
        "kind": "BLOOD",
        "blood_group": "A+",
        "studies": "Estudios ficticios",
    }
    person = p.ok("receptores", "POST", "/api/v1/recipients", data=person_data)
    p.ok(
        "receptores",
        "PATCH",
        "/api/v1/recipients/" + person["id"],
        data=dict(person_data, **CONFIRM, version=person["version"]),
    )
    _, req = recipient_request(p)
    req = p.ok(
        "receptores",
        "PATCH",
        "/api/v1/requests/" + req["id"],
        data=dict(
            CONFIRM, component="RBC", quantity=1, urgency=2, version=req["version"]
        ),
    )
    unit = resource(p)
    ev = evaluation(p, req, [unit])
    p.ok("compatibilidad", "GET", "/api/v1/evaluations")
    ranking = p.ok(
        "priorizacion_geografia",
        "POST",
        "/api/v1/rankings",
        data={"evaluation_id": ev["id"]},
    )
    p.ok("priorizacion_geografia", "GET", "/api/v1/rankings/" + ranking["id"])
    proposal = p.ok(
        "priorizacion_geografia",
        "POST",
        "/api/v1/allocation-proposals",
        data={"evaluation_ids": [ev["id"]]},
    )
    p.ok(
        "priorizacion_geografia",
        "GET",
        "/api/v1/allocation-proposals/" + proposal["id"],
    )
    operation = reservation(p, ev, unit)
    p.ok(
        "inventario",
        "POST",
        "/api/v1/operations/" + operation["operation_id"] + "/resume",
    )
    p.ok("inventario", "GET", "/api/v1/reservations/" + operation["reservation"]["id"])
    p.ok(
        "inventario",
        "POST",
        "/api/v1/reservations/" + operation["reservation"]["id"] + "/cancel",
        data=CONFIRM,
    )
    p.drain()
    events = p.ok("auditoria", "GET", "/api/v1/events", user="auditor1")
    p.ok(
        "auditoria",
        "GET",
        "/api/v1/events/" + events["items"][0]["id"],
        user="auditor1",
    )
    routes = p.ok(
        "priorizacion_geografia", "GET", "/api/v1/routes", user="coordinator1"
    )["items"]
    row = routes[0]
    p.ok(
        "priorizacion_geografia",
        "GET",
        "/api/v1/routes/" + row["id"],
        user="coordinator1",
    )
    p.ok(
        "priorizacion_geografia",
        "PATCH",
        "/api/v1/routes/" + row["id"],
        user="coordinator1",
        data={
            "version": row["version"],
            "distance_km": row["distance_km"],
            "travel_minutes": row["travel_minutes"],
            "source": "Estimación ficticia verificada",
        },
    )
    another = resource(p)
    _, request = recipient_request(p)
    evaluated = evaluation(p, request, [another])
    shipment = plan(p, reservation(p, evaluated, another)["reservation"])
    shipment = move(p, shipment, "PREPARED", "operator1")
    shipment = move(p, shipment, "COLLECTED", "transport1")
    p.ok(
        "transporte",
        "POST",
        "/api/v1/shipments/" + shipment["id"] + "/telemetry",
        user="transport1",
        data={"latitude": 25.6, "longitude": -100.3, "captured_at": iso()},
    )
    p.ok(
        "transporte",
        "GET",
        "/api/v1/shipments/" + shipment["id"] + "/telemetry",
        user="transport1",
    )


def test_pooled_transactions_preserve_rollback_credentials_and_recover(p, monkeypatch):
    import pytest
    from redhouse.db import transaction
    from redhouse.errors import APIError

    app = p.apps["inventario"]
    unit = resource(p)
    monkeypatch.setitem(app.config, "DATABASE_POOL_SIZE", 2)
    try:
        with app.app_context():
            with transaction() as conn:
                first = conn.execute(
                    "SELECT pg_backend_pid() AS pid,current_user AS owner"
                ).fetchone()
            with transaction() as conn:
                second = conn.execute(
                    "SELECT pg_backend_pid() AS pid,current_user AS owner"
                ).fetchone()
            assert first == second
            with pytest.raises(RuntimeError), transaction() as conn:
                conn.execute(
                    "UPDATE resources SET folio=%s WHERE id=%s",
                    ("ROLLBACK-" + uuid4().hex, unit["id"]),
                )
                raise RuntimeError("rollback")
            with transaction() as conn:
                assert (
                    conn.execute(
                        "SELECT folio FROM resources WHERE id=%s", (unit["id"],)
                    ).fetchone()["folio"]
                    == unit["folio"]
                )
            with monkeypatch.context() as outage:
                outage.setitem(
                    app.config,
                    "DATABASE_URL",
                    "postgresql://invalid@127.0.0.1:1/missing",
                )
                with pytest.raises(APIError) as error, transaction():
                    pass
                assert error.value.status == 503
            with transaction() as conn:
                assert (
                    conn.execute("SELECT current_user AS owner").fetchone()["owner"]
                    == first["owner"]
                )
    finally:
        for pool in app.extensions.pop("database_pools", {}).values():
            pool.close()
