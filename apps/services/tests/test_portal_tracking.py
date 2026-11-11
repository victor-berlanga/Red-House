"""Portal y tickets restringidos contra almacenes y WSS reales."""

import hashlib
import os

import pytest

from .test_final_tracking import connect, point, receive, send
from .test_final_tracking import tracking as tracking
from .test_web_integration import login
from .test_web_integration import web as web


def test_browser_ticket_scope_publish_expiry_and_web_csrf(p, tracking, web):
    identifier = tracking["shipment"]["id"]
    path = f"/api/v1/shipments/{identifier}/tracking/ticket"
    client = login(web, p, "coordinator1")
    page = client.get(f"/traslados/{identifier}/mapa")
    assert page.status_code == 200
    assert b"tracking-map" in page.data
    assert p.tokens["coordinator1"].encode() not in page.data
    assert client.post(f"/traslados/{identifier}/mapa/acceso").status_code == 400
    assert (
        login(web, p, "donor1").get(f"/traslados/{identifier}/mapa").status_code == 403
    )
    assert (
        login(web, p, "transport2").get(f"/traslados/{identifier}/mapa").status_code
        == 403
    )
    ticket = p.ok("transporte", "POST", path, user="coordinator1")
    assert ticket["expires_in"] == 90
    subscriber = connect(tracking, ticket["credential"], "browser")
    receive(subscriber, "authenticated")
    send(subscriber, {"type": "subscribe", "shipment_id": identifier})
    receive(subscriber, "subscribed")
    publisher = connect(tracking, tracking["credential"]["credential"], "device")
    receive(publisher, "authenticated")
    send(publisher, {"type": "position.publish", "position": point(tracking)})
    receive(publisher, "position.ack")
    assert receive(subscriber, "position.updated")["position"]["source"] == "SIMULATOR"
    send(subscriber, {"type": "position.publish", "position": point(tracking, 2)})
    assert receive(subscriber, "error")["code"] == "forbidden"
    subscriber.close()
    subscriber = connect(tracking, ticket["credential"], "browser")
    receive(subscriber, "authenticated")
    send(
        subscriber,
        {"type": "subscribe", "shipment_id": "00000000-0000-0000-0000-000000000001"},
    )
    assert receive(subscriber, "error")["code"] == "forbidden"
    subscriber.close()
    app = p.apps["transporte"]
    from redhouse.security import key, redis_call

    with app.app_context():
        digest = hashlib.sha256(ticket["credential"].encode()).hexdigest()
        redis_call(lambda r: r.delete(key("tracking:ticket:" + digest)))
    subscriber = connect(tracking, ticket["credential"], "browser")
    assert receive(subscriber, "error")["code"] == "unauthorized"
    subscriber.close()
    publisher.close()


@pytest.mark.skipif(
    not os.environ.get("REDHOUSE_BROWSER_TESTS"),
    reason="Requiere Chrome y Playwright; activar REDHOUSE_BROWSER_TESTS=1.",
)
def test_portal_browser_profiles_and_live_map(p, tracking, web, tmp_path):
    import json
    import subprocess
    import threading
    from pathlib import Path

    from werkzeug.serving import make_server

    web.config["HIGHCHARTS_ENABLED"] = True
    output = Path(os.environ.get("REDHOUSE_BROWSER_RESULTS", str(tmp_path))) / "cartografia-degradada"
    output.mkdir(parents=True, exist_ok=True)
    socket_origin = tracking["url"].split("/ws/")[0]

    @web.after_request
    def test_socket_policy(response):
        response.headers["Content-Security-Policy"] = response.headers.get(
            "Content-Security-Policy", ""
        ).replace("connect-src 'self'", "connect-src 'self' " + socket_origin)
        return response

    web.after_request_funcs[None].remove(test_socket_policy)
    web.after_request_funcs[None].insert(0, test_socket_policy)
    server = make_server(
        "127.0.0.1",
        0,
        web,
        threaded=True,
        ssl_context=(tracking["cert"], str(Path(tracking["cert"]).with_suffix(".key"))),
    )
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"https://localhost:{server.server_port}"
    p.apps["transporte"].config["TRACKING_ALLOWED_ORIGINS"] = [base]
    try:
        result = subprocess.run(
            ["node", "scripts/verify_portal_tracking.cjs"],
            input=json.dumps(
                {
                    "base": base,
                    "socket": tracking["url"] + "json",
                    "password": p.env.state["password"],
                    "shipment": tracking["shipment"]["id"],
                    "deviceToken": tracking["credential"]["credential"],
                    "position": point(tracking),
                    "output": str(output),
                }
            ),
            capture_output=True,
            text=True,
            timeout=240,
            check=False,
        )
        assert result.returncode == 0, (
            result.stdout,
            result.stderr,
            (output / "browser.json").read_text(),
        )
    finally:
        server.shutdown()
        server.server_close()


def test_web_password_recovery_real_smtp_single_use(p, web, monkeypatch):
    from uuid import uuid4
    from .final_receivers import smtp_receiver
    from .test_final_identity import email_token
    from .test_web_integration import form
    from ms_identidad_acceso.strong_auth import deliver_pending

    username = "portal_" + uuid4().hex[:12]
    password = "Synthetic-password-only-2026"
    p.ok(
        "identidad_acceso",
        "POST",
        "/api/v1/users",
        user="admin1",
        data={
            "username": username,
            "password": password,
            "tenant_id": p.env.state["tenants"][0],
            "role": "DONOR",
        },
    )
    auth = p.ok(
        "identidad_acceso",
        "POST",
        "/api/v1/auth/login",
        user=None,
        data={"username": username, "password": password},
    )
    p.tokens[username] = auth["access_token"]
    app = p.apps["identidad_acceso"]
    with smtp_receiver() as (port, messages):
        for key, value in {
            "SMTP_HOST": "127.0.0.1",
            "SMTP_PORT": port,
            "SMTP_TEST_RECEIVER": True,
            "SMTP_FROM": "tests@redhouse.invalid",
        }.items():
            monkeypatch.setitem(app.config, key, value)
        p.ok(
            "identidad_acceso",
            "POST",
            "/api/v1/auth/contact",
            user=username,
            data={"email": username + "@example.invalid", "password": password},
        )
        with app.app_context():
            deliver_pending()
        p.ok(
            "identidad_acceso",
            "POST",
            "/api/v1/auth/contact/verify",
            user=username,
            data={"token": email_token(messages[-1])},
        )
        client = web.test_client()
        data = form(client, "/recuperar-acceso")
        data["username"] = username
        assert client.post("/recuperar-acceso", data=data).status_code == 200
        with app.app_context():
            deliver_pending()
        token = email_token(messages[-1])
        data = form(client, "/recuperar-acceso/confirmar")
        data.update(
            token=token, password=password + "new", confirmation=password + "new"
        )
        assert client.post("/recuperar-acceso/confirmar", data=data).status_code == 200
        assert client.post("/recuperar-acceso/confirmar", data=data).status_code == 401
        assert (
            p.request(
                "identidad_acceso", "GET", "/api/v1/auth/me", user=username
            ).status_code
            == 401
        )
        assert (
            p.request(
                "identidad_acceso",
                "POST",
                "/api/v1/auth/login",
                user=None,
                data={"username": username, "password": password + "new"},
            ).status_code
            == 200
        )


def test_web_consent_and_hourly_agenda_persist(p, web):
    from uuid import uuid4
    from .helpers import iso
    from .test_web_integration import post

    donor = p.ok(
        "donantes",
        "POST",
        "/api/v1/donors",
        user="donor1",
        data={
            "folio": "PORTAL-" + uuid4().hex[:10],
            "display_name": "Persona sintética",
            "blood_group": "O-",
            "consent": True,
        },
    )
    client = login(web, p, "donor1")
    post(
        client,
        f"/donantes/donor/{donor['id']}/consentimientos/nuevo",
        {
            "policy_version": "SYNTHETIC-PORTAL-1",
            "reference": "Consentimiento de prueba",
            "effective_at": iso(minutes=-5),
            "granted": "on",
            "human_confirmation": "on",
            "reason": "Prueba de consentimiento informado",
        },
    )
    assert (
        p.ok(
            "donantes", "GET", f"/api/v1/donors/{donor['id']}/consents", user="donor1"
        )["total"]
        == 1
    )
    site = p.ok(
        "identidad_acceso",
        "POST",
        "/api/v1/catalogues/sites",
        user="admin1",
        data={
            "name": "Sede " + uuid4().hex[:8],
            "municipality": "Monterrey",
            "address": "Domicilio sintético",
        },
    )
    campaign = p.ok(
        "donantes",
        "POST",
        "/api/v1/campaigns",
        user="operator1",
        data={
            "title": "Campaña " + uuid4().hex[:8],
            "starts_at": iso(minutes=5),
            "ends_at": iso(minutes=120),
            "capacity": 10,
        },
    )
    operator = login(web, p, "operator1")
    post(
        operator,
        f"/campanas/{campaign['id']}/horarios/nuevo",
        {
            "site_id": site["id"],
            "starts_at": iso(minutes=10),
            "ends_at": iso(minutes=20),
            "capacity": "1",
        },
    )
    slot = p.ok(
        "donantes",
        "GET",
        "/api/v1/campaign-slots?campaign_id=" + campaign["id"],
        user="donor1",
    )["items"][0]
    post(
        client,
        f"/citas/nueva?campaign_id={campaign['id']}&slot_id={slot['id']}",
        {"donor_id": donor["id"], "campaign_id": campaign["id"], "slot_id": slot["id"]},
    )
    appointment = p.ok("donantes", "GET", "/api/v1/appointments", user="donor1")[
        "items"
    ][0]
    post(
        client,
        f"/citas/{appointment['id']}/horario",
        {
            "action": "CONFIRM",
            "human_confirmation": "on",
            "reason": "Confirmación de horario sintético",
        },
    )
    schedule = p.ok(
        "donantes",
        "GET",
        f"/api/v1/appointments/{appointment['id']}/schedule",
        user="donor1",
    )
    assert schedule["status"] == "CONFIRMED"
    post(
        client,
        f"/citas/{appointment['id']}/horario",
        {
            "action": "CANCEL",
            "human_confirmation": "on",
            "reason": "Cancelación de horario sintético",
        },
    )
    assert (
        p.ok(
            "donantes",
            "GET",
            f"/api/v1/appointments/{appointment['id']}/schedule",
            user="donor1",
        )["status"]
        == "CANCELLED"
    )
