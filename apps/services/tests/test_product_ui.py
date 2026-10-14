"""Regresión de tareas del portal: permisos reales, POST, agenda y captura puntual."""

from uuid import uuid4

from lxml import etree

from .helpers import iso
from .test_web_integration import web, login, form, post


def test_admin_redirects_and_weekday_roundtrip(web, p):
    admin = login(web, p, "admin1")
    page = admin.get("/panel")
    assert b"Roles y par" not in page.data
    assert admin.get("/configuracion").location == "/administracion/users"
    assert admin.get("/administracion/components").location == "/catalogos/sites"
    donor = login(web, p, "donor1")
    assert donor.get("/configuracion").status_code == 403
    assert donor.get("/administracion/components").status_code == 403
    site = p.ok(
        "identidad_acceso",
        "POST",
        "/api/v1/catalogues/sites",
        user="admin1",
        data={
            "name": "Sede " + uuid4().hex[:8],
            "municipality": "Monterrey",
            "address": "Dirección de prueba",
        },
    )
    path = "/catalogos/schedules/nuevo"
    parsed = etree.HTML(admin.get(path).data)
    assert len(parsed.xpath('//select[@name="weekday"]/option[@value!=""]')) == 7
    assert parsed.xpath('//input[@type="time" and @name="opens_at"]')
    title = "Horario " + uuid4().hex[:8]
    post(
        admin,
        path,
        {
            "name": title,
            "parent_id": site["id"],
            "weekday": "0",
            "opens_at": "08:00",
            "closes_at": "16:00",
        },
    )
    saved = p.ok(
        "identidad_acceso",
        "GET",
        "/api/v1/catalogues/schedules?q=" + title,
        user="admin1",
    )["items"][0]
    assert saved["weekday"] == 0 and saved["opens_at"] == "08:00"
    target = p.env.state["accounts"]["operator1"]["id"]
    parsed = etree.HTML(
        admin.get(
            f"/administracion/usuarios/{target}/estado?active=false&version=999"
        ).data
    )
    assert parsed.xpath('//input[@name="version" and @type="hidden"]')
    assert not parsed.xpath('//input[@name="version" and @value="999"]')


def test_notifications_read_post_is_authorized_and_translated(web, p):
    operator = login(web, p, "operator1")
    donor = p.ok(
        "donantes",
        "POST",
        "/api/v1/donors",
        user="operator1",
        data={
            "folio": "NOTICE-" + uuid4().hex[:8],
            "display_name": "Donante de prueba",
            "blood_group": "O+",
            "consent": True,
        },
    )
    p.ok(
        "donantes",
        "POST",
        "/api/v1/donors/" + donor["id"] + "/reviews",
        user="medical1",
        data={
            "decision": "ELIGIBLE",
            "version": donor["version"],
            "human_confirmation": True,
            "reason": "Evaluación humana de prueba para notificación",
        },
    )
    p.drain()
    doc = etree.HTML(operator.get("/notificaciones").data)
    assert "Evaluación del donante registrada" in " ".join(doc.itertext())
    assert "DONOR_REVIEWED" not in " ".join(doc.itertext())
    assert any(
        donor["id"] in link for link in doc.xpath("//a[@data-record-view]/@href")
    )
    form_node = doc.xpath('//form[contains(@class,"inline-action")]')[0]
    target = form_node.get("action")
    assert operator.post(target, data={}).status_code == 400
    other = login(web, p, "operator2")
    values = form(other, "/panel")
    assert other.post(target, data=values).status_code == 403
    values = {i.get("name"): i.get("value", "") for i in form_node.xpath(".//input")}
    assert operator.post(target, data=values).status_code == 302
    alert_id = target.split("/notificaciones/")[1].split("/")[0]
    alerts = p.ok("alertas", "GET", "/api/v1/alerts?page_size=100", user="operator1")[
        "items"
    ]
    assert next(a for a in alerts if a["id"] == alert_id)["status"] == "ACKNOWLEDGED"


def test_campaign_registration_context_and_cancel_modal(web, p):
    username = "appointments-" + uuid4().hex[:12]
    p.ok(
        "identidad_acceso",
        "POST",
        "/api/v1/users",
        user="admin1",
        data={
            "username": username,
            "password": p.env.state["password"],
            "role": "DONOR",
            "tenant_id": p.env.state["tenants"][0],
        },
    )
    donor = login(web, p, username)
    person_url = post(
        donor,
        "/donantes/donor/nuevo",
        {
            "folio": "OWN-" + uuid4().hex[:8],
            "display_name": "Donante propio",
            "blood_group": "O+",
            "consent": "on",
        },
    )
    campaign = p.ok(
        "donantes",
        "POST",
        "/api/v1/campaigns",
        user="operator1",
        data={
            "title": "Campaña " + uuid4().hex[:8],
            "starts_at": iso(minutes=10),
            "ends_at": iso(days=2),
            "capacity": 5,
        },
    )
    post(
        donor,
        "/citas/nueva",
        {"donor_id": person_url.rsplit("/", 1)[1], "campaign_id": campaign["id"]},
    )
    listing = etree.HTML(donor.get("/citas").data)
    assert campaign["title"] in " ".join(listing.itertext())
    detail_url = listing.xpath("//a[@data-record-view]/@href")[0]
    assert donor.get(detail_url).status_code == 200
    other = login(web, p, "operator2")
    assert other.get(detail_url).status_code == 404
    cancel_url = listing.xpath("//a[@data-action-dialog]/@href")[0]
    response = donor.get(cancel_url, headers={"X-Action-Modal": "1"})
    assert response.status_code == 200 and b"<!doctype" not in response.data.lower()
    assert campaign["title"].encode() in response.data
    assert b"campos marcados" not in response.data
    parsed = etree.HTML(response.data)
    action = parsed.xpath("//form/@action")[0]
    values = {
        i.get("name"): i.get("value", "")
        for i in parsed.xpath('//input[@type="hidden"]')
    }
    assert action == cancel_url and donor.post(action, data=values).status_code == 302
    assert b"Cancelado" in donor.get("/citas").data


def test_personal_dashboards_timezone_and_help(web, p):
    public = web.test_client()
    response = public.get("/recuperar-acceso", follow_redirects=True)
    assert response.status_code == 200
    assert etree.HTML(response.data).xpath('//details[@id="access-help" and @open]')
    for user, expected in [
        ("donor1", "Mis inscripciones recientes"),
        ("auditor1", "Actividad reciente de la red"),
    ]:
        client = login(web, p, user)
        response = client.get("/panel")
        assert expected.encode() in response.data
        assert b"Instituciones de la regi" not in response.data
        parsed = etree.HTML(response.data)
        assert len(parsed.xpath('//select[@name="timezone"]')) == 1
        assert parsed.xpath('//header//select[@name="timezone"]')
        assert not parsed.xpath('//main//select[@name="timezone"]')
    coordinator = login(web, p, "coordinator1")
    assert b"service-grid" in coordinator.get("/monitoreo").data


def test_location_capture_requires_assigned_active_shipment(web, p):
    from .helpers import resource, recipient_request, evaluation, reservation, plan

    unit = resource(p)
    _, req = recipient_request(p)
    ev = evaluation(p, req, [unit])
    reserve = reservation(p, ev, unit)
    trip = plan(p, reserve["reservation"])
    transport = login(web, p, "transport1")
    operator = login(web, p, "operator1")
    url = f"/traslados/{trip['id']}/ubicacion"
    assert transport.get(url).status_code == 403
    for state, actor in [("PREPARED", "operator1"), ("COLLECTED", "transport1")]:
        current = p.ok(
            "transporte", "GET", "/api/v1/shipments/" + trip["id"], user=actor
        )
        p.ok(
            "transporte",
            "POST",
            f"/api/v1/shipments/{trip['id']}/transitions",
            user=actor,
            data={
                "state": state,
                "version": current["version"],
                "human_confirmation": True,
                "reason": "Confirmación física de prueba",
            },
        )
        p.drain()
    response = transport.get(url)
    assert response.status_code == 200 and b"data-capture-location" in response.data
    assert "geolocation=(self)" in response.headers["Permissions-Policy"]
    denied = operator.get(url)
    assert (
        denied.status_code == 403
        and "geolocation=()" in denied.headers["Permissions-Policy"]
    )
    assert "geolocation=()" in transport.get("/panel").headers["Permissions-Policy"]
    # Prueba opcional en Chrome con ubicación simulada y el mismo entorno aislado.
    # Nunca utiliza credenciales ni expedientes del entorno de presentación.
    import json
    import os
    import subprocess
    import threading
    from pathlib import Path
    from werkzeug.serving import make_server
    from .conftest import QuietHandler

    if os.environ.get("REDHOUSE_BROWSER_MODULES"):
        server = make_server(
            "127.0.0.1", 0, web, threaded=True, request_handler=QuietHandler
        )
        threading.Thread(target=server.serve_forever, daemon=True).start()
        state = p.env.directory / "location-browser.json"
        output = (
            Path(__file__).resolve().parents[1]
            / "../../documentation/historial/integracion/resultados/product-ui"
        )
        output.mkdir(parents=True, exist_ok=True)
        state.touch(mode=0o600)
        state.write_text(
            json.dumps(
                {
                    "url": f"http://127.0.0.1:{server.server_port}",
                    "path": url,
                    "cookie_name": web.config["JWT_COOKIE_NAME"],
                    "cookie_value": transport.get_cookie(
                        web.config["JWT_COOKIE_NAME"]
                    ).value,
                }
            )
        )
        try:
            script = (
                Path(__file__).resolve().parents[2] / "web/tests/location_browser.cjs"
            )
            subprocess.run(
                ["node", str(script), str(state), str(output)],
                check=True,
                timeout=90,
                env={**os.environ, "NODE_PATH": os.environ["REDHOUSE_BROWSER_MODULES"]},
            )
        finally:
            state.unlink(missing_ok=True)
            server.shutdown()
            server.server_close()
