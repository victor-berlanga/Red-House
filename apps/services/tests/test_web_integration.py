"""Flask web real -> once API HTTP reales -> PostgreSQL/Redis/MongoDB físicos."""

import secrets
import sys
import threading
from pathlib import Path
from uuid import uuid4

import pytest
from lxml import etree
from werkzeug.serving import make_server

from .conftest import QuietHandler
from .helpers import iso, route

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "web"))
from src import create_app


@pytest.fixture
def web(p, monkeypatch):
    # The retired SQL backend must not be importable by the portal.
    import importlib.util

    assert importlib.util.find_spec("src.data_access") is None

    app = create_app(
        {
            "SECRET_KEY": secrets.token_hex(32),
            "JWT_SECRET_KEY": secrets.token_hex(32),
            "TESTING": True,
            "BACKEND_MODE": "microservices",
            "PRODUCTION": False,
            "SESSION_COOKIE_SECURE": False,
            "HIGHCHARTS_ENABLED": False,
            "DATABASE_URL": "postgresql://UNREACHABLE/legacy",
            "MICROSERVICES_CONFIG": {
                "SERVICE_URLS": p.urls,
                **p.env.state["web_sessions"],
                # Igual al valor normal del cliente: el login calcula un hash
                # costoso y las pruebas levantan once servicios en esta máquina.
                "SERVICE_TIMEOUT": 8,
            },
        }
    )
    return app


def form(client, path):
    response = client.get(path)
    assert response.status_code == 200, (
        path,
        response.status_code,
        response.data[:500],
    )
    parsed = etree.HTML(response.data)
    return {
        item.get("name"): item.get("value", "")
        for item in parsed.xpath('//input[@type="hidden"]')
    }


def login(web, p, user):
    client = web.test_client()
    values = form(client, "/login")
    values.update(login_email=user, password=p.env.state["password"])
    result = client.post("/login", data=values)
    assert result.status_code == 302
    return client


def post(client, path, data):
    values = form(client, path)
    values.update(data)
    response = client.post(path, data=values)
    assert response.status_code == 302, (
        path,
        response.status_code,
        response.data[:1800],
    )
    return response.headers["Location"]


@pytest.mark.parametrize(
    "user,paths",
    [
        (
            "admin1",
            [
                "/panel",
                "/administracion/institutions",
                "/administracion/users",
                "/administracion/components",
                "/configuracion",
                "/monitoreo",
            ],
        ),
        (
            "operator1",
            [
                "/panel",
                "/inventario",
                "/donantes/donor",
                "/donaciones",
                "/donantes/recipient",
                "/solicitudes",
                "/campanas",
                "/citas",
                "/rutas",
                "/traslados",
                "/organos",
            ],
        ),
        (
            "medical1",
            [
                "/panel",
                "/inventario",
                "/disponibilidad",
                "/donantes/donor",
                "/donantes/recipient",
                "/solicitudes",
                "/donaciones",
                "/organos",
                "/traslados",
                "/rutas",
            ],
        ),
        (
            "coordinator1",
            [
                "/panel",
                "/inventario",
                "/rutas",
                "/traslados",
                "/reservas",
                "/monitoreo",
                "/organos",
            ],
        ),
        ("transport1", ["/panel", "/traslados", "/rutas"]),
        ("auditor1", ["/panel", "/auditoria", "/monitoreo"]),
        ("donor1", ["/panel", "/donantes/donor", "/campanas", "/citas"]),
    ],
)
def test_roles_can_render_authorized_pages_through_http(web, p, user, paths):
    client = login(web, p, user)
    for path in paths + ["/notificaciones", "/sesion/estado"]:
        response = client.get(path, follow_redirects=True)
        assert response.status_code == 200, (
            user,
            path,
            response.status_code,
            response.data[:800],
        )
        assert (
            b"access_token" not in response.data
            and b"refresh_token" not in response.data
        )


@pytest.mark.parametrize(
    "kind,component,group",
    [
        ("BLOOD", "RBC", "A+"),
        ("ORGAN", "KIDNEY", "O+"),
        ("ORGAN", "LIVER", "O+"),
        ("ORGAN", "HEART", "O+"),
    ],
)
def test_full_reservation_transport_receipt_from_web_and_xml(
    web, p, kind, component, group
):
    operator1 = login(web, p, "operator1")
    medical1 = login(web, p, "medical1")
    medical2 = login(web, p, "medical2")
    coord = login(web, p, "coordinator1")
    transport = login(web, p, "transport1")
    operator2 = login(web, p, "operator2")
    code = "NL-WEB-" + uuid4().hex[:12]
    unit_url = post(
        operator1,
        "/inventario/nuevo?kind=" + kind,
        {
            "folio": code,
            "component": component,
            "blood_group": "O+" if kind == "ORGAN" else "O-",
            "expires_at": iso(days=2),
            "donation_id": "",
        },
    )
    post(
        medical1,
        unit_url + "/liberar",
        {
            "human_confirmation": "on",
            "reason": "Liberación humana ficticia desde el portal",
        },
    )
    recipient_url = post(
        medical2,
        "/donantes/recipient/nuevo",
        {
            "folio": "PAC-" + uuid4().hex[:12],
            "display_name": "Ana Sofía Garza Treviño",
            "kind": kind,
            "blood_group": group,
            "organ_type": component if kind == "ORGAN" else "",
            "studies": "Estudios ficticios; HLA documental sujeto a revisión humana",
        },
    )
    request_url = post(
        medical2,
        "/solicitudes/nueva",
        {
            "recipient_id": recipient_url.rsplit("/", 1)[1],
            "component": component,
            "quantity": "1",
            "urgency": "3",
        },
    )
    route(p)
    evaluation_url = post(medical2, request_url + "/evaluar", {})
    evaluation = p.ok(
        "compatibilidad",
        "GET",
        "/api/v1/evaluations/" + evaluation_url.rsplit("/", 1)[1],
    )
    unit_id = unit_url.rsplit("/", 1)[1]
    candidate = next(c for c in evaluation["candidates"] if c["resource_id"] == unit_id)
    assert candidate["resource_folio"] == code
    post(
        medical2,
        evaluation_url + "/dictamen/" + unit_id,
        {
            "decision": "FAVORABLE",
            "human_confirmation": "on",
            "reason": "Dictamen humano favorable ficticio desde la web",
        },
    )
    post(medical2, evaluation_url + "/ordenar", {})
    operation_url = post(
        medical2,
        evaluation_url + "/reservar/" + unit_id,
        {
            "human_confirmation": "on",
            "reason": "Reserva autorizada ficticia desde la web",
        },
    )
    operation = p.ok(
        "inventario", "GET", "/api/v1/operations/" + operation_url.rsplit("/", 1)[1]
    )
    assert operation["status"] == "COMPLETED"
    shipment_url = post(
        coord,
        "/traslados/nuevo",
        {
            "reservation_id": operation["reservation"]["id"],
            "transport_user_id": p.env.state["accounts"]["transport1"]["id"],
            "departure_at": iso(minutes=1),
            "eta": iso(minutes=40),
            "human_confirmation": "on",
            "reason": "Planeación autorizada ficticia desde el portal",
        },
    )
    for state, client in [
        ("PREPARED", operator1),
        ("COLLECTED", transport),
        ("IN_TRANSIT", transport),
        ("DELIVERED", transport),
        ("ACCEPTED", operator2),
    ]:
        post(
            client,
            shipment_url + "/paso/" + state,
            {
                "human_confirmation": "on",
                "reason": "Confirmación física ficticia desde el portal",
            },
        )
    p.drain()
    assert b"Aceptado" in operator2.get(shipment_url).data
    req = p.ok("receptores", "GET", "/api/v1/requests/" + request_url.rsplit("/", 1)[1])
    assert req["status"] == "CLOSED"
    xml = p.request(
        "inventario",
        "GET",
        "/api/v1/resources/" + unit_id,
        user="operator2",
        headers={"Accept": "application/xml"},
    )
    assert xml.status_code == 200
    document = etree.fromstring(xml.content)
    assert document.xpath('string(//field[@name="status"])') == "RECEIVED"
    assert etree.tostring(document).find(p.env.state["tenants"][1].encode()) >= 0
    cookie = operator2.get_cookie(web.config["JWT_COOKIE_NAME"])
    assert len(cookie.value) == 43 and not cookie.value.startswith("eyJ")


def test_forms_keep_values_and_same_idempotency_after_error(web, p):
    client = login(web, p, "operator1")
    values = form(client, "/inventario/nuevo")
    values.update(
        folio="invalid",
        kind="BLOOD",
        component="RBC",
        blood_group="O+",
        expires_at="2020-01-01T10:00",
        donation_id="",
    )
    response = client.post("/inventario/nuevo", data=values)
    assert response.status_code == 422
    assert b'id="expires_at-error"' in response.data
    assert values["idempotency_key"].encode() in response.data
    assert b'value="invalid"' in response.data
    assert b"2020-01-01T10:00" in response.data


def test_web_rejects_csrf_wrong_role_and_cross_institution(web, p):
    client = login(web, p, "admin1")
    assert client.get("/inventario").status_code == 403
    assert client.post("/administracion/users/nuevo", data={}).status_code == 400
    operator = login(web, p, "operator1")
    unit = post(
        operator,
        "/inventario/nuevo",
        {
            "folio": "SAFE-" + uuid4().hex[:12],
            "component": "RBC",
            "blood_group": "O+",
            "expires_at": iso(days=2),
        },
    )
    other = login(web, p, "operator2")
    assert other.get(unit).status_code == 403
    data = p.request("identidad_acceso", "GET", "/api/v1/users", user="admin1").json()[
        "data"
    ]["items"]
    assert all(
        row["tenant_id"] == p.env.state["tenants"][0] and "password_hash" not in row
        for row in data
    )


def test_filtered_pagination_counts_and_minimized_recipient_search(web, p):
    client = login(web, p, "operator1")
    code = "SEARCH-" + uuid4().hex[:12]
    post(
        client,
        "/inventario/nuevo",
        {
            "folio": code,
            "component": "RBC",
            "blood_group": "O+",
            "expires_at": iso(days=2),
        },
    )
    result = p.ok("inventario", "GET", "/api/v1/resources?q=" + code, user="operator1")
    assert result["total"] == 1 and result["items"][0]["folio"] == code
    assert client.get("/inventario?q=" + code).status_code == 200
    assert (
        client.get("/inventario?format=csv&q=" + code)
        .headers["Content-Type"]
        .startswith("text/csv")
    )
    assert (
        p.request(
            "inventario",
            "GET",
            "/api/v1/resources?q=_%27OR&unexpected=x",
            user="operator1",
        ).status_code
        == 400
    )


def test_identity_outage_reports_503_without_legacy_fallback(web, p):
    client = login(web, p, "operator1")
    server = p.servers["identidad_acceso"]
    port = server.server_port
    server.shutdown()
    server.server_close()
    try:
        result = client.get("/inventario")
        assert result.status_code == 503
        assert b"postgresql://" not in result.data and b"UNREACHABLE" not in result.data
        assert client.get("/").status_code == 200
    finally:
        replacement = make_server(
            "127.0.0.1",
            port,
            p.apps["identidad_acceso"],
            threaded=True,
            request_handler=QuietHandler,
        )
        p.servers["identidad_acceso"] = replacement
        threading.Thread(target=replacement.serve_forever, daemon=True).start()
    assert client.get("/inventario").status_code == 200


def test_renewal_and_logout_revoke_backend_session_without_exposing_tokens(web, p):
    client = login(web, p, "medical1")
    csrf = form(client, "/solicitudes/nueva")["csrf_token"]
    cookie = client.get_cookie(web.config["JWT_COOKIE_NAME"]).value
    result = client.post("/sesion/continuar", headers={"X-CSRFToken": csrf})
    assert result.status_code == 200 and "csrf_token" in result.json
    assert "access_token" not in result.json and "refresh_token" not in result.json
    from src.integration.sessions import load, redis_client, redis_key, key

    with web.app_context():
        value = load(cookie)
        payload = redis_client().get(redis_key("session", key(cookie)))
        assert value["access_token"].encode() not in payload
        assert value["refresh_token"].encode() not in payload
    logout = client.post("/logout", data={"csrf_token": result.json["csrf_token"]})
    assert logout.status_code == 302 and client.get("/inventario").status_code == 302
    revoked = p.request(
        "identidad_acceso",
        "GET",
        "/api/v1/auth/me",
        user=None,
        headers={"Authorization": "Bearer " + value["access_token"]},
    )
    assert revoked.status_code == 401


def test_donor_campaign_appointment_processing_and_inventory_source_from_web(web, p):
    operator = login(web, p, "operator1")
    medical = login(web, p, "medical1")
    donor_url = post(
        operator,
        "/donantes/donor/nuevo",
        {
            "folio": "DON-WEB-" + uuid4().hex[:10],
            "display_name": "Daniela Salinas Cavazos",
            "blood_group": "O+",
            "consent": "on",
        },
    )
    donor_id = donor_url.rsplit("/", 1)[1]
    post(
        medical,
        "/donantes/evaluacion/" + donor_id,
        {
            "decision": "ELIGIBLE",
            "human_confirmation": "on",
            "reason": "Dictamen humano ficticio de elegibilidad",
        },
    )
    title = "Jornada solidaria ficticia " + uuid4().hex[:12]
    post(
        operator,
        "/campanas/nueva",
        {"title": title, "starts_at": iso(), "ends_at": iso(days=2), "capacity": "15"},
    )
    campaigns = p.ok(
        "donantes", "GET", "/api/v1/campaigns?page_size=100", user="operator1"
    )["items"]
    campaign = next(row for row in campaigns if row["title"] == title)
    post(
        operator, "/citas/nueva", {"donor_id": donor_id, "campaign_id": campaign["id"]}
    )
    donation_url = post(
        medical,
        "/donaciones/nueva",
        {
            "donor_id": donor_id,
            "kind": "BLOOD",
            "component": "RBC",
            "collected_at": iso(),
            "human_confirmation": "on",
            "reason": "Registro de recolección ficticia autorizada",
        },
    )
    post(
        operator,
        donation_url + "/procesar",
        {
            "state": "PROCESSED",
            "human_confirmation": "on",
            "reason": "Procesamiento ficticio documentado",
        },
    )
    resource_url = post(
        operator,
        "/inventario/nuevo",
        {
            "folio": "SAN-SRC-" + uuid4().hex[:10],
            "component": "RBC",
            "blood_group": "O+",
            "expires_at": iso(days=2),
            "donation_id": donation_url.rsplit("/", 1)[1],
        },
    )
    row = p.ok(
        "inventario",
        "GET",
        "/api/v1/resources/" + resource_url.rsplit("/", 1)[1],
        user="operator1",
    )
    assert (
        row["status"] == "QUARANTINE"
        and row["donation_id"] == donation_url.rsplit("/", 1)[1]
    )


def test_matching_proposal_from_web_does_not_reserve(web, p):
    from .helpers import evaluation, recipient_request, resource

    unit = resource(p)
    _, req = recipient_request(p)
    ev = evaluation(p, req, [unit])
    with p.owner("inventario") as conn:
        before = conn.execute("SELECT count(*) FROM reservations").fetchone()[0]
    client = login(web, p, "medical2")
    result_url = post(client, "/propuestas/nueva", {"evaluation_ids": [ev["id"]]})
    proposal = p.ok(
        "priorizacion_geografia",
        "GET",
        "/api/v1/allocation-proposals/" + result_url.rsplit("/", 1)[1],
    )
    assert proposal["matched_count"] == 1
    assert (
        client.get(result_url).status_code == 200
        and client.get("/propuestas").status_code == 200
    )
    with p.owner("inventario") as conn:
        assert conn.execute("SELECT count(*) FROM reservations").fetchone()[0] == before


def test_admin_web_creation_deactivation_revokes_new_user(web, p):
    admin = login(web, p, "admin1")
    username = "doctor-" + uuid4().hex[:12] + "@redhouse.test"
    post(
        admin,
        "/administracion/users/nuevo",
        {"username": username, "password": p.env.state["password"], "role": "MEDICAL"},
    )
    client = login(web, p, username)
    assert client.get("/inventario").status_code == 200
    user = p.ok(
        "identidad_acceso", "GET", "/api/v1/users?q=" + username, user="admin1"
    )["items"][0]
    post(
        admin,
        "/administracion/usuarios/" + user["id"] + "/estado?version=1&active=false",
        {"version": "1"},
    )
    assert client.get("/inventario").status_code == 302
