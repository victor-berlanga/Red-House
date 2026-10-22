"""Regresiones de errores útiles, investigación regional y atención de hallazgos."""

import csv
import io
import json
import os
from uuid import uuid4

import psycopg
import pytest
from flask import Flask
from lxml import etree
from ms_donantes.routes import DonorCreate
from ms_priorizacion_geografia.routes import RouteCreate
from psycopg.types.json import Jsonb
from redhouse.codec import parse
from redhouse.errors import APIError
from redhouse.examples import request_xml

from .helpers import iso
from .test_continuity import autonomous as autonomous  # noqa: PLC0414 - pytest fixture
from .test_web_integration import form, login
from .test_web_integration import web as web  # noqa: PLC0414 - pytest fixture


def donor_data(**changes):
    return {
        "folio": "VALID-" + uuid4().hex[:12],
        "display_name": "Persona ficticia",
        "blood_group": "O+",
        "consent": True,
        **changes,
    }


@pytest.mark.parametrize("representation", ["json", "xml"])
@pytest.mark.parametrize(
    "changes,fields",
    [
        ({"restrictions": "abc", "background": "abcd"}, {"restrictions", "background"}),
        (
            {"consent_reference": "Referencia ficticia"},
            {"consent_at", "consent_reference"},
        ),
        (
            {"consent_reference": "Referencia ficticia", "consent_at": iso(days=1)},
            {"consent_at"},
        ),
        (
            {
                "consent_reference": "Referencia ficticia",
                "consent_at": "fecha incorrecta",
            },
            {"consent_at"},
        ),
        ({"folio": "FOLIO con acento á"}, {"folio"}),
        ({"restrictions": " "}, {"restrictions"}),
        ({"display_name": "x" * 201}, {"display_name"}),
    ],
)
def test_safe_field_errors_json_xml(representation, changes, fields):
    app = Flask(__name__)
    data = donor_data(**changes)
    kwargs = (
        {"json": data}
        if representation == "json"
        else {"data": request_xml(data), "content_type": "application/xml"}
    )
    with app.test_request_context("/", method="POST", **kwargs):
        with pytest.raises(APIError) as error:
            parse(DonorCreate)
        assert error.value.status in (400, 422)
        assert fields <= {d["field"] for d in error.value.details}
        assert all(d.get("message") for d in error.value.details)
        assert "input" not in json.dumps(error.value.details)
        assert data["display_name"] not in json.dumps(error.value.details)


@pytest.mark.parametrize("length", [6, 1000])
def test_exact_text_limits_and_empty_optionals(length):
    app = Flask(__name__)
    with app.test_request_context(
        "/", method="POST", json=donor_data(restrictions="x" * length, background=None)
    ):
        assert parse(DonorCreate)["restrictions"] == "x" * length


@pytest.mark.parametrize(
    "field,value",
    [
        ("distance_km", -1),
        ("distance_km", 20001),
        ("travel_minutes", 10081),
        ("travel_minutes", 0.5),
        ("source", "corto"),
    ],
)
def test_numeric_and_source_limits_keep_field(field, value):
    data = {
        "origin_id": str(uuid4()),
        "destination_id": str(uuid4()),
        "distance_km": 0.0,
        "travel_minutes": 0,
        "source": "Fuente documentada",
    }
    data[field] = value
    app = Flask(__name__)
    with app.test_request_context("/", method="POST", json=data):
        with pytest.raises(APIError) as error:
            parse(RouteCreate)
        assert field in {item["field"] for item in error.value.details}


@pytest.mark.parametrize("mode", ["web", "autonomous"])
def test_web_preserves_fields_marks_errors_and_retries_atomically(p, request, mode):
    app = request.getfixturevalue(mode)
    client = login(app, p, "medical1")
    path = "/donantes/donor/nuevo"
    initial = client.get(path)
    root = etree.HTML(initial.data)
    assert not root.xpath('//*[@aria-invalid="true"]')
    assert root.xpath('//*[@name="restrictions"]/@minlength') == ["6"]
    assert root.xpath('//*[@name="display_name"]/@maxlength') == ["200"]
    data = {
        **form(client, path),
        **donor_data(),
        "consent": "on",
        "restrictions": "abc",
        "background": "abcd",
    }
    response = client.post(path, data=data)
    assert response.status_code == 422, response.text[:1000]
    parsed = etree.HTML(response.data)
    assert set(parsed.xpath('//*[@aria-invalid="true"]/@name')) == {
        "restrictions",
        "background",
    }
    assert len(parsed.xpath('//*[@id="form-error"]//a')) == 2
    assert parsed.xpath('//*[@name="display_name"]/@value') == [data["display_name"]]
    assert parsed.xpath('//*[@name="consent"]/@checked')
    assert parsed.xpath('//*[@name="idempotency_key"]/@value') == [
        data["idempotency_key"]
    ]
    with p.owner("donantes") as conn:
        assert (
            conn.execute(
                "SELECT count(*) FROM donors WHERE folio=%s", (data["folio"],)
            ).fetchone()[0]
            == 0
        )
    data.update(restrictions="      ", background="Antecedentes verificados")
    assert client.post(path, data=data).status_code == 302
    assert client.post(path, data=data).status_code == 302
    with p.owner("donantes") as conn:
        rows = conn.execute(
            "SELECT restrictions,background FROM donors WHERE folio=%s",
            (data["folio"],),
        ).fetchall()
        assert rows == [(None, "Antecedentes verificados")]


def test_web_login_does_not_echo_password(web, p):
    client = web.test_client()
    data = {**form(client, "/login"), "login_email": "a", "password": "PRIVADO"}
    result = client.post("/login", data=data)
    assert result.status_code == 422
    root = etree.HTML(result.data)
    assert not root.xpath('//*[@name="password"]/@value')
    assert "PRIVADO" not in result.text
    assert set(root.xpath('//*[@aria-invalid="true"]/@name')) == {
        "login_email",
        "password",
    }


def test_selector_retains_value_from_later_page_on_failed_submit(web, p):
    identifiers = [str(uuid4()) for _ in range(21)]
    with p.owner("donantes") as conn, conn.cursor() as cursor:
        cursor.executemany(
            "INSERT INTO donors(id,tenant_id,folio,display_name,blood_group,consent,status) VALUES(%s,%s,%s,'Persona ficticia','O+',true,'ELIGIBLE')",
            [
                (identifier, p.env.state["tenants"][0], "AAA-" + uuid4().hex[:12])
                for identifier in identifiers
            ],
        )
        chosen = str(uuid4())
        conn.execute(
            "INSERT INTO donors(id,tenant_id,folio,display_name,blood_group,consent,status) VALUES(%s,%s,%s,'Última persona ficticia','O+',true,'ELIGIBLE')",
            (chosen, p.env.state["tenants"][0], "ZZZ-" + uuid4().hex[:12]),
        )
    client = login(web, p, "medical1")
    path = "/donaciones/nueva"
    visible = p.ok(
        "donantes",
        "GET",
        "/api/v1/donors?status=ELIGIBLE&page_size=20",
        user="medical1",
    )["items"]
    first_page = {row["id"] for row in visible}
    chosen = next(
        identifier
        for identifier in [*identifiers, chosen]
        if identifier not in first_page
    )
    assert chosen not in client.get(path).text
    data = {
        **form(client, path),
        "donor_id": chosen,
        "kind": "BLOOD",
        "component": "RBC",
        "collected_at": "2026-10-01T10:00",
        "reason": "corto",
        "human_confirmation": "on",
    }
    response = client.post(path, data=data)
    assert response.status_code == 422
    root = etree.HTML(response.data)
    assert root.xpath('//*[@name="donor_id"]/option[@selected]/@value') == [chosen]
    assert root.xpath('//*[@name="human_confirmation"]/@checked')


def test_file_form_marks_reselection_without_creating_records(web, p):
    from .test_documents_storage import planned

    shipment = planned(p)
    client = login(web, p, "transport1")
    path = "/traslados/" + shipment["id"] + "/archivos"
    values = form(client, path)
    for content, filename, mime in [
        (b"texto", "evidencia.txt", "text/plain"),
        (b"", "evidencia.png", "image/png"),
    ]:
        response = client.post(
            path,
            data={**values, "evidence": (io.BytesIO(content), filename, mime)},
            content_type="multipart/form-data",
        )
        assert response.status_code == 422
        root = etree.HTML(response.data)
        assert root.xpath('//*[@name="evidence"]/@aria-invalid') == ["true"]
        assert "Selecciona nuevamente el archivo" in response.text
        assert root.xpath('//*[@name="idempotency_key"]/@value') == [
            values["idempotency_key"]
        ]
    with p.owner("transporte") as conn:
        assert (
            conn.execute(
                "SELECT count(*) FROM files WHERE shipment_id=%s", (shipment["id"],)
            ).fetchone()[0]
            == 0
        )


def seed_event(
    p,
    action="DONOR_REGISTERED",
    *,
    resource=None,
    region=None,
    metadata=None,
    correlation=None,
):
    identifier = str(uuid4())
    tenant = p.env.state["tenants"][0]
    actor = p.env.state["accounts"]["medical1"]["id"]
    event = {
        "event_id": identifier,
        "source": "donantes",
        "action": action,
        "resource_id": resource or str(uuid4()),
        "tenant_id": tenant,
        "region_id": region or p.env.state["region_id"],
        "actor_id": actor,
        "correlation_id": correlation or str(uuid4()),
        "occurred_at": iso(),
        "metadata": metadata or {},
    }
    with p.owner("auditoria") as conn:
        conn.execute(
            "INSERT INTO audit_events(id,tenant_id,region_id,source,action,actor_id,event) VALUES(%s,%s,%s,%s,%s,%s,%s)",
            (
                identifier,
                tenant,
                event["region_id"],
                event["source"],
                action,
                actor,
                Jsonb(event),
            ),
        )
    return event


def test_audit_default_categories_filters_exports_and_scope(p):
    resource = str(uuid4())
    ids = {seed_event(p, resource=resource)["event_id"] for _ in range(23)}
    for action in ("READ", "LOGIN", "TELEMETRY_RECORDED"):
        seed_event(p, action, resource=resource)
    foreign = seed_event(p, resource=resource, region=str(uuid4()))
    params = "?resource=" + resource
    data = p.ok("auditoria", "GET", "/api/v1/events" + params, user="auditor1")
    assert data["total"] == 23 and len(data["items"]) == 20
    second = p.ok(
        "auditoria", "GET", "/api/v1/events" + params + "&page=2", user="auditor1"
    )
    assert ids == {r["id"] for r in data["items"] + second["items"]}
    export = p.ok("auditoria", "GET", "/api/v1/events/export" + params, user="auditor1")
    assert ids == {r["id"] for r in export["items"]}
    assert (
        p.ok(
            "auditoria",
            "GET",
            "/api/v1/events" + params + "&categories=ALL",
            user="auditor1",
        )["total"]
        == 26
    )
    assert (
        p.ok(
            "auditoria",
            "GET",
            "/api/v1/events" + params + "&categories=NONE",
            user="auditor1",
        )["total"]
        == 0
    )
    filtered = (
        params
        + "&action=DONOR_REGISTERED&result=RECORDED&actor="
        + p.env.state["accounts"]["medical1"]["id"]
        + "&institution_id="
        + p.env.state["tenants"][0]
    )
    assert (
        p.ok("auditoria", "GET", "/api/v1/events" + filtered, user="auditor1")["total"]
        == 23
    )
    assert (
        p.request(
            "auditoria", "GET", "/api/v1/events/" + foreign["event_id"], user="auditor1"
        ).status_code
        == 404
    )
    assert (
        p.request("auditoria", "GET", "/api/v1/events", user="coordinator1").status_code
        == 403
    )
    assert (
        p.request(
            "auditoria", "GET", "/api/v1/events?from=invalid", user="auditor1"
        ).status_code
        == 422
    )


def test_audit_related_uses_documented_links_and_never_invents_history(p):
    unit, request_id, shipment = [str(uuid4()) for _ in range(3)]
    first = seed_event(p, resource=request_id)
    reservation = seed_event(
        p, "RESOURCE_RESERVED", resource=unit, metadata={"request_id": request_id}
    )
    last = seed_event(
        p, "SHIPMENT_DELIVERED", resource=shipment, metadata={"resource_id": unit}
    )
    foreign = seed_event(p, resource=unit, region=str(uuid4()))
    related = p.ok(
        "auditoria",
        "GET",
        "/api/v1/events/" + first["event_id"] + "/related",
        user="auditor1",
    )
    assert {first["event_id"], reservation["event_id"], last["event_id"]} <= {
        r["id"] for r in related["items"]
    }
    assert foreign["event_id"] not in {r["id"] for r in related["items"]}
    detail = p.ok(
        "auditoria", "GET", "/api/v1/events/" + first["event_id"], user="auditor1"
    )
    assert (
        detail["actor_role"] is None
        and detail["actor_name"] is None
        and detail["reason"] is None
    )
    assert detail["event"] == first


def test_new_events_capture_actor_without_clinical_fields(p):
    row = p.ok(
        "donantes",
        "POST",
        "/api/v1/donors",
        user="medical1",
        data=donor_data(background="Antecedente clínico privado"),
    )
    p.drain()
    events = p.ok(
        "auditoria", "GET", "/api/v1/events?resource=" + row["id"], user="auditor1"
    )["items"]
    saved = next(e for e in events if e["action"] == "DONOR_REGISTERED")
    assert saved["actor_name"] == "medical1" and saved["actor_role"] == "MEDICAL"
    assert saved["resource_folio"] == row["folio"]
    assert "Antecedente clínico privado" not in json.dumps(saved)
    before = len(events)
    p.ok("auditoria", "GET", "/api/v1/events", user="auditor1")
    p.drain()
    assert (
        p.ok(
            "auditoria", "GET", "/api/v1/events?resource=" + row["id"], user="auditor1"
        )["total"]
        == before
    )


def test_finding_lifecycle_permissions_idempotency_and_history(p):
    event = seed_event(p)
    body = {
        "description": "Revisar documentación de la operación",
        "priority": "HIGH",
        "assignee_id": p.env.state["accounts"]["coordinator1"]["id"],
        "event_ids": [event["event_id"]],
        "evidence": "Registro de revisión inicial",
    }
    key = uuid4().hex
    finding = p.ok(
        "auditoria", "POST", "/api/v1/findings", user="auditor1", data=body, key=key
    )
    assert (
        p.ok(
            "auditoria", "POST", "/api/v1/findings", user="auditor1", data=body, key=key
        )
        == finding
    )
    path = "/api/v1/findings/" + finding["id"]
    assert p.request("auditoria", "GET", path, user="coordinator2").status_code == 404
    assert (
        p.request(
            "auditoria", "POST", "/api/v1/findings", user="medical1", data=body
        ).status_code
        == 403
    )
    action = {
        "version": 1,
        "status": "CLOSED",
        "reason": "Verificación completada",
        "human_confirmation": True,
        "evidence": "Comprobante de corrección",
    }
    assert (
        p.request(
            "auditoria", "POST", path + "/actions", user="auditor1", data=action
        ).status_code
        == 403
    )
    action.update(
        status="IN_PROGRESS",
        corrective_action="Revisar evidencia y documentar corrección",
    )
    row = p.ok("auditoria", "POST", path + "/actions", user="coordinator1", data=action)
    assert row["version"] == 2
    assert (
        p.request(
            "auditoria", "POST", path + "/actions", user="coordinator1", data=action
        ).status_code
        == 409
    )
    action.update(version=2, status="PENDING_VERIFICATION", evidence=None)
    assert (
        p.request(
            "auditoria", "POST", path + "/actions", user="coordinator1", data=action
        ).status_code
        == 422
    )
    action["evidence"] = "Comprobante de corrección verificado"
    row = p.ok("auditoria", "POST", path + "/actions", user="coordinator1", data=action)
    action.update(version=3, status="CLOSED", evidence=None)
    assert (
        p.request(
            "auditoria", "POST", path + "/actions", user="auditor1", data=action
        ).status_code
        == 422
    )
    action["evidence"] = "Evidencia revisada y aceptada por auditoría"
    row = p.ok("auditoria", "POST", path + "/actions", user="auditor1", data=action)
    assert row["status"] == "CLOSED" and row["version"] == 4
    detail = p.ok("auditoria", "GET", path, user="auditor1")
    assert [r["status"] for r in detail["history"]] == [
        "OPEN",
        "IN_PROGRESS",
        "PENDING_VERIFICATION",
        "CLOSED",
    ]
    for table in ("audit_events", "audit_finding_actions", "audit_finding_links"):
        with (
            psycopg.connect(p.env.configs["auditoria"]["DATABASE_URL"]) as conn,
            pytest.raises(psycopg.errors.InsufficientPrivilege),
        ):
            conn.execute("DELETE FROM " + table)
    p.drain()
    notices = p.ok("alertas", "GET", "/api/v1/alerts", user="coordinator1")["items"]
    assert any(r["resource_id"] == finding["id"] for r in notices)


def test_web_audit_preserves_filters_and_csv_escapes_formulas(web, p):
    resource = str(uuid4())
    seed_event(p, resource=resource, metadata={"audit": {"actor_name": " =1+1"}})
    client = login(web, p, "auditor1")
    path = "/auditoria?applied=1&categories=BUSINESS&resource=" + resource
    response = client.get(path)
    assert response.status_code == 200, response.text[:1000]
    root = etree.HTML(response.data)
    detail_link = root.xpath('//a[text()="Investigar"]/@href')[0]
    assert "return_to=" in detail_link and resource in detail_link
    detail = client.get(detail_link)
    assert detail.status_code == 200
    assert (
        resource
        in etree.HTML(detail.data).xpath('//a[contains(@class,"back-link")]/@href')[0]
    )
    exported = client.get(path + "&format=csv&scope=all")
    assert exported.status_code == 200
    rows = list(csv.reader(io.StringIO(exported.data.decode("utf-8-sig"))))
    assert len(rows) == 2 and rows[1][1] == "' =1+1"


def test_findings_without_http_services(autonomous, p):
    test_finding_lifecycle_permissions_idempotency_and_history(p)
    client = login(autonomous, p, "auditor1")
    assert client.get("/auditoria").status_code == 200
    assert client.get("/hallazgos").status_code == 200


def test_finding_xml_contract_and_foreign_links(p):
    from pathlib import Path

    import requests
    from redhouse.openapi import ERROR
    from redhouse.xml_response import validate_response

    headers = {
        "Authorization": "Bearer " + p.tokens["auditor1"],
        "Accept": "application/xml",
        "Content-Type": "application/xml",
        "Idempotency-Key": uuid4().hex,
    }
    body = {
        "description": "Hallazgo XML ficticio",
        "priority": "HIGH",
        "assignee_id": p.env.state["accounts"]["coordinator1"]["id"],
        "event_ids": [],
    }
    url = p.urls["auditoria"] + "/api/v1/findings"
    result = requests.post(
        url, headers=headers, data=request_xml(body).encode(), timeout=20
    )
    assert result.status_code == 422
    error = validate_response(result.content, ERROR)["error"]
    assert {d["field"] for d in error["details"]} == {"resource_id", "event_ids"}
    foreign = seed_event(p, region=str(uuid4()))
    body["event_ids"] = [foreign["event_id"]]
    assert (
        p.request(
            "auditoria", "POST", "/api/v1/findings", user="auditor1", data=body
        ).status_code
        == 404
    )
    body["event_ids"] = [seed_event(p)["event_id"]]
    result = requests.post(
        url, headers=headers, data=request_xml(body).encode(), timeout=20
    )
    assert result.status_code == 201, result.text
    folder = Path(__file__).resolve().parents[1] / "ms_auditoria/contracts"
    saved = validate_response(
        result.content,
        json.loads((folder / "finding_create.response.json").read_text()),
    )["data"]
    detail = p.request(
        "auditoria",
        "GET",
        "/api/v1/findings/" + saved["id"],
        user="auditor1",
        headers={"Accept": "application/xml"},
    )
    decoded = validate_response(
        detail.content,
        json.loads((folder / "finding_detail.response.json").read_text()),
    )["data"]
    assert decoded["history"][0]["status"] == "OPEN"
    assert decoded["events"][0]["event_id"] == body["event_ids"][0]


def test_audit_export_limit_and_date_window(p):
    resource = str(uuid4())
    template = seed_event(p, resource=resource)
    with p.owner("auditoria") as conn, conn.cursor() as cursor:
        rows = []
        for _ in range(4999):
            event = {**template, "event_id": str(uuid4())}
            rows.append(
                (
                    event["event_id"],
                    event["tenant_id"],
                    event["region_id"],
                    event["source"],
                    event["action"],
                    event["actor_id"],
                    Jsonb(event),
                )
            )
        cursor.executemany(
            "INSERT INTO audit_events(id,tenant_id,region_id,source,action,actor_id,event) VALUES(%s,%s,%s,%s,%s,%s,%s)",
            rows,
        )
    query = "?resource=" + resource
    export = p.ok("auditoria", "GET", "/api/v1/events/export" + query, user="auditor1")
    assert export["total"] == len(export["items"]) == 5000
    seed_event(p, resource=resource)
    limited = p.request(
        "auditoria", "GET", "/api/v1/events/export" + query, user="auditor1"
    )
    assert (
        limited.status_code == 422 and limited.json()["error"]["code"] == "export_limit"
    )
    import urllib.parse

    future = urllib.parse.urlencode({"resource": resource, "from": iso(days=1)})
    assert (
        p.ok("auditoria", "GET", "/api/v1/events?" + future, user="auditor1")["total"]
        == 0
    )


@pytest.mark.skipif(
    not os.environ.get("REDHOUSE_BROWSER_TESTS"),
    reason="Recorrido de navegador explícito: REDHOUSE_BROWSER_TESTS=1, Node y Playwright.",
)
def test_browser_validation_and_finding_workflow(web, p):
    import os
    import subprocess
    import threading
    from pathlib import Path

    from werkzeug.serving import make_server

    from .conftest import QuietHandler

    root = Path(__file__).resolve().parents[3]

    def drain():
        p.drain()
        return {"drained": True}

    web.add_url_rule(
        "/test/drain",
        "test_drain",
        web.extensions["csrf"].exempt(drain),
        methods=["POST"],
    )
    server = make_server(
        "127.0.0.1", 0, web, threaded=True, request_handler=QuietHandler
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        result = subprocess.run(
            ["node", str(root / "scripts/verify_audit_forms.cjs")],
            input=json.dumps(
                {
                    "base": f"http://127.0.0.1:{server.server_port}",
                    "password": p.env.state["password"],
                    "coordinator": p.env.state["accounts"]["coordinator1"]["id"],
                    "output": str(
                        root / "documentation/evidencias/auditoria-formularios/browser"
                    ),
                }
            ),
            text=True,
            capture_output=True,
            check=False,
            timeout=300,
            env=dict(os.environ),
        )
        assert result.returncode == 0, result.stdout + result.stderr
    finally:
        server.shutdown()
        server.server_close()
