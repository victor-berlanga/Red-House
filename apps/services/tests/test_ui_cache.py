"""Regresión del portal Jinja y caché privada con dependencias reales."""

from concurrent.futures import ThreadPoolExecutor
from threading import Event
from urllib.parse import urlencode
from uuid import uuid4

from lxml import etree

from .helpers import iso, resource, recipient_request
from .test_web_integration import web, login, form


def test_inventory_cache_scope_filters_commit_rollback_and_xml(p):
    unit = resource(p)
    path = "/api/v1/resources?" + urlencode({"q": unit["folio"], "blood_group": "O-"})

    def read(user="operator1", **kwargs):
        return p.request("inventario", "GET", path, user=user, **kwargs)

    first, hit = read(), read()
    assert first.status_code == hit.status_code == 200
    assert first.headers["X-Cache"] == "MISS" and hit.headers["X-Cache"] == "HIT"
    assert read("operator2").json()["data"]["total"] == 0
    assert read("coordinator1").json()["data"]["items"][0].get("donation_id") is None
    assert read("admin1").status_code == 403
    assert read(headers={"Accept": "application/xml"}).status_code == 200
    assert read(headers={"Cache-Control": "no-cache"}).headers["X-Cache"] == "BYPASS"
    assert (
        p.request(
            "inventario", "GET", path + "&expiry=invalid", user="operator1"
        ).status_code
        == 400
    )
    with p.owner("inventario") as conn:
        conn.execute("UPDATE resources SET blood_group='A+' WHERE id=%s", (unit["id"],))
        conn.rollback()
    assert read().headers["X-Cache"] == "HIT"
    p.ok(
        "inventario",
        "POST",
        f"/api/v1/resources/{unit['id']}/withdraw",
        user="operator1",
        data={
            "version": unit["version"],
            "human_confirmation": True,
            "reason": "Retiro autorizado de prueba de caché",
        },
    )
    after = read()
    assert after.headers["X-Cache"] == "MISS" and after.json()["data"]["total"] == 0


def test_cache_late_fill_cannot_restore_previous_generation(p, monkeypatch):
    import ms_inventario.routes as routes

    unit = resource(p)
    path = "/api/v1/resources?q=" + unit["folio"]
    ready, proceed = Event(), Event()
    original = routes.listing

    def paused(*args, **kwargs):
        result = original(*args, **kwargs)
        ready.set()
        assert proceed.wait(10)
        return result

    monkeypatch.setattr(routes, "listing", paused)
    with ThreadPoolExecutor(max_workers=1) as executor:
        pending = executor.submit(
            p.request, "inventario", "GET", path, user="operator1"
        )
        try:
            assert ready.wait(10)
            with p.owner("inventario") as conn:
                conn.execute(
                    "UPDATE resources SET status='WITHDRAWN' WHERE id=%s", (unit["id"],)
                )
        finally:
            proceed.set()
        assert pending.result().status_code == 200
    monkeypatch.setattr(routes, "listing", original)
    after = p.request("inventario", "GET", path, user="operator1")
    assert after.headers["X-Cache"] == "MISS" and after.json()["data"]["total"] == 0


def test_catalogue_cache_invalidation_and_revocation(p):
    credentials = p.ok(
        "identidad_acceso",
        "POST",
        "/api/v1/auth/login",
        user=None,
        data={"username": "admin1", "password": p.env.state["password"]},
    )
    headers = {"Authorization": "Bearer " + credentials["access_token"]}
    name = "CACHE-" + uuid4().hex[:10]
    path = "/api/v1/catalogues/sites?q=" + name

    def read():
        return p.request("identidad_acceso", "GET", path, user=None, headers=headers)

    assert read().json()["data"]["total"] == 0
    assert read().headers["X-Cache"] == "HIT"
    p.ok(
        "identidad_acceso",
        "POST",
        "/api/v1/catalogues/sites",
        user="admin1",
        data={
            "name": name,
            "municipality": "Monterrey",
            "address": "Domicilio ficticio de prueba",
        },
    )
    assert read().json()["data"]["total"] == 1
    p.ok(
        "identidad_acceso",
        "POST",
        "/api/v1/auth/revoke",
        user=None,
        headers=headers,
        data={"refresh_token": credentials["refresh_token"]},
    )
    assert read().status_code == 401


def test_jinja_fragments_readonly_modal_and_return_after_edit(web, p):
    client = login(web, p, "operator1")
    unit = p.ok(
        "inventario",
        "POST",
        "/api/v1/resources",
        user="operator1",
        data={
            "folio": "UI-" + uuid4().hex[:10],
            "kind": "BLOOD",
            "component": "RBC-DEMO",
            "blood_group": "O+",
            "expires_at": iso(days=2),
        },
    )
    target = "/inventario?" + urlencode(
        {"q": unit["folio"], "status": "QUARANTINE", "page": 1}
    )
    full = client.get(target)
    fragment = client.get(target, headers={"X-Filter-Fragment": "1"})
    assert full.status_code == fragment.status_code == 200
    assert b"<!doctype" not in fragment.data.lower() and b"<script" not in fragment.data
    parsed = etree.HTML(fragment.data)
    view = parsed.xpath("//a[@data-record-view]/@href")[0]
    edit = parsed.xpath('//a[starts-with(@aria-label,"Editar ")]/@href')[0]
    modal = client.get(view, headers={"X-Detail-Modal": "1"})
    assert modal.status_code == 200
    assert b"<form" not in modal.data and b"<script" not in modal.data
    assert b"record-toolbar" not in modal.data and b"Abrir expediente" in modal.data
    values = form(client, edit)
    assert values["return_to"] == target
    values.update(
        folio=unit["folio"],
        component="RBC-DEMO",
        blood_group="O+",
        expires_at=iso(days=3),
        human_confirmation="on",
        reason="Corrección de prueba UX",
    )
    saved = client.post(edit, data=values)
    assert saved.status_code == 302 and saved.headers["Location"] == target
    assert (
        p.ok("inventario", "GET", "/api/v1/resources/" + unit["id"], user="operator1")[
            "version"
        ]
        == 2
    )
    malicious = client.get(
        "/inventario/" + unit["id"] + "?return_to=https://example.com"
    )
    assert b'href="https://example.com"' not in malicious.data
    medical = login(web, p, "medical1")
    assert medical.get(edit).status_code == 403


def test_history_disables_edit_and_account_view_is_not_deactivation(web, p):
    person, req = recipient_request(p)
    client = login(web, p, "medical2")
    listing = etree.HTML(client.get("/donantes/recipient?q=" + person["folio"]).data)
    assert not listing.xpath('//a[starts-with(@aria-label,"Editar ")]')
    detail = client.get("/donantes/recipient/" + person["id"])
    assert b"Editar expediente" not in detail.data
    assert (
        client.get("/registros/recipients/" + person["id"] + "/editar").status_code
        == 409
    )
    admin = login(web, p, "admin1")
    listing = etree.HTML(admin.get("/administracion/users").data)
    assert listing.xpath("//button[@data-row-preview]")
    assert not listing.xpath('//a[@data-record-view and contains(@href,"/estado")]')
    assert listing.xpath('//a[contains(@href,"/estado")]')


def test_pagination_controls_preserve_filters_and_recover_last_page(web, p):
    prefix = "PAGE-" + uuid4().hex[:8]
    tenant = p.env.state["tenants"][0]
    with p.owner("inventario") as conn:
        with conn.cursor() as cursor:
            cursor.executemany(
                "INSERT INTO resources(id,tenant_id,region_id,current_institution_id,folio,kind,component,blood_group,expires_at) VALUES(%s,%s,%s,%s,%s,'BLOOD','RBC-DEMO','O-',now()+interval '2 days')",
                [
                    (
                        str(uuid4()),
                        tenant,
                        p.env.state["region_id"],
                        tenant,
                        prefix + str(i),
                    )
                    for i in range(45)
                ],
            )
    client = login(web, p, "operator1")
    path = "/inventario?q=" + prefix
    first = etree.HTML(client.get(path).data)
    next_url = first.xpath("//a[@data-page-next]/@href")[0]
    assert "page=2" in next_url and prefix in next_url
    assert not first.xpath("//a[@data-page-previous]")
    second = etree.HTML(client.get(next_url, headers={"X-Filter-Fragment": "1"}).data)
    assert second.xpath("//a[@data-page-previous]") and second.xpath(
        "//a[@data-page-next]"
    )
    last = etree.HTML(
        client.get(path + "&page=999", headers={"X-Filter-Fragment": "1"}).data
    )
    assert last.xpath("string(//*[@data-filter-results]/@data-page)") == "3"
    assert not last.xpath("//a[@data-page-next]")
    assert len(last.xpath("//tbody/tr")) == 5
    assert b"Entorno de pruebas" not in client.get(path).data
    assert b"Red House \xc2\xb7 Red regional" not in client.get(path).data


def test_timezone_async_converts_form_dates_and_persists_without_redirect(web, p):
    client = login(web, p, "operator1")
    values = form(client, "/inventario/nuevo")
    response = client.post(
        "/preferencias/horario",
        data={
            "csrf_token": values["csrf_token"],
            "_timezone": "America/Monterrey",
            "timezone": "UTC",
            "date_values": ["2026-10-15T10:30", ""],
        },
        headers={"X-Timezone-Update": "1"},
    )
    assert response.status_code == 200 and not response.location
    assert response.json["date_values"] == ["2026-10-15T16:30", ""]
    assert client.get_cookie("display_timezone").value == "UTC"
    invalid = client.post(
        "/preferencias/horario",
        data={
            "csrf_token": values["csrf_token"],
            "_timezone": "UTC",
            "timezone": "America/Monterrey",
            "date_values": ["invalid"],
        },
        headers={"X-Timezone-Update": "1"},
    )
    assert invalid.status_code == 422
    assert client.get_cookie("display_timezone").value == "UTC"
    assert (
        client.post(
            "/preferencias/horario",
            data={"timezone": "UTC"},
            headers={"X-Timezone-Update": "1"},
        ).status_code
        == 400
    )
    assert (
        client.post(
            "/preferencias/horario",
            data={
                "csrf_token": values["csrf_token"],
                "timezone": "America/Monterrey",
                "next": "/inventario",
            },
        ).status_code
        == 302
    )
