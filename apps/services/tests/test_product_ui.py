"""Regresión de tareas del portal: permisos reales, POST, agenda y captura puntual."""

from uuid import uuid4

from lxml import etree

from .helpers import iso
from .test_web_integration import web as web
from .test_web_integration import login, form, post


def test_admin_redirects_and_weekday_roundtrip(web, p):
    admin = login(web, p, "admin1")
    page = admin.get("/panel")
    assert b"Roles y par" not in page.data
    # Desde 9ab04c4 «Configuración» es un índice propio, con acceso a usuarios.
    settings = admin.get("/configuracion")
    assert settings.status_code == 200
    assert etree.HTML(settings.data).xpath('//a[@href="/administracion/users"]')
    assert admin.get("/administracion/components").location == "/catalogos/sites"
    # DONOR ya no entra al portal; un perfil no administrativo sigue sin ver configuración.
    operator = login(web, p, "operator1")
    assert operator.get("/configuracion").status_code == 403
    assert operator.get("/administracion/components").status_code == 403
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
    # Las alertas toman created_at al entregarse. Si el outbox trae eventos de
    # pruebas previas, al drenarlos después de este caso generan avisos más
    # recientes que empujan el propio fuera de la primera página: se entregan antes.
    p.drain(rounds=1000)
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
    p.drain(rounds=1000)
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
    # DONOR ya no usa el portal: el operador registra donante y cita en su nombre.
    donor = login(web, p, "operator1")
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
    # Desde 9ab04c4 la recuperación es autoservicio (ya no redirige a la ayuda).
    response = public.get("/recuperar-acceso")
    assert response.status_code == 200
    parsed = etree.HTML(response.data)
    assert parsed.xpath('//form[@method="post"]//input[@name="username"]')
    assert parsed.xpath('//a[@href="/recuperar-acceso/confirmar"]')
    response = public.get("/login?help=access")
    assert response.status_code == 200
    assert etree.HTML(response.data).xpath('//details[@id="access-help" and @open]')
    for user, expected in [
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


def test_location_capture_is_not_available_in_portal(web, p):
    """La captura de ubicación del traslado es de la aplicación móvil (TRANSPORT).

    El portal ya no admite TRANSPORT: su login web es 403 `client_not_allowed` y la
    página de captura sigue denegada a los perfiles del portal.
    """
    from .helpers import resource, recipient_request, evaluation, reservation, plan

    unit = resource(p)
    _, req = recipient_request(p)
    ev = evaluation(p, req, [unit])
    reserve = reservation(p, ev, unit)
    trip = plan(p, reserve["reservation"])
    url = f"/traslados/{trip['id']}/ubicacion"
    for user in ("operator1", "coordinator1"):
        denied = login(web, p, user).get(url)
        assert (
            denied.status_code == 403
            and "geolocation=()" in denied.headers["Permissions-Policy"]
        )
    client = web.test_client()
    values = form(client, "/login")
    values.update(login_email="transport1", password=p.env.state["password"])
    refused = client.post("/login", data=values)
    assert refused.status_code == 403 and b"aplicaci" in refused.data
