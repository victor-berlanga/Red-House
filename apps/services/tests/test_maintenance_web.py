"""Formularios restaurados y búsquedas más allá de la primera página."""

from uuid import uuid4
from .test_web_integration import web, login, post, form
from .helpers import iso


def test_catalogues_bootstrap_and_edits_through_web(web, p):
    client = login(web, p, "admin1")
    for kind in ("sites", "contacts", "schedules", "capacities", "locations"):
        assert client.get("/catalogos/" + kind).status_code == 200
    post(
        client,
        "/catalogos/sites/nuevo",
        {
            "name": "Sede Web " + uuid4().hex[:8],
            "municipality": "Guadalupe",
            "address": "Dirección ficticia de prueba",
        },
    )
    url = post(
        client,
        "/administracion/institutions/nuevo",
        {"name": "Hospital Web " + uuid4().hex[:8]},
    )
    assert "/responsable" in url
    post(
        client,
        url,
        {
            "username": "web_admin_" + uuid4().hex[:8],
            "password": uuid4().hex,
            "human_confirmation": "on",
            "reason": "Alta institucional ficticia autorizada",
        },
    )
    operator = login(web, p, "operator1")
    person = post(
        operator,
        "/donantes/donor/nuevo",
        {
            "folio": "EDIT-" + uuid4().hex[:8],
            "display_name": "María Garza",
            "blood_group": "O-",
            "consent": "on",
        },
    )
    identifier = person.rsplit("/", 1)[1]
    post(
        operator,
        "/registros/donors/" + identifier + "/editar",
        {
            "folio": "EDIT-" + uuid4().hex[:8],
            "display_name": "María Garza López",
            "blood_group": "O-",
            "consent": "on",
            "human_confirmation": "on",
            "reason": "Corrección ficticia autorizada",
        },
    )
    assert "María Garza López" in operator.get(person).text


def test_search_and_pagination_reach_records_after_first_hundred(web, p):
    prefix = "LOOKUP-" + uuid4().hex[:8]
    tenant = p.env.state["tenants"][0]
    ids = [str(uuid4()) for _ in range(125)]
    with p.owner("donantes") as conn:
        with conn.cursor() as cursor:
            cursor.executemany(
                "INSERT INTO donors(id,tenant_id,folio,display_name,blood_group,consent) VALUES(%s,%s,%s,%s,'O-',true)",
                [
                    (identifier, tenant, prefix + str(i), prefix + f" Persona {i:03d}")
                    for i, identifier in enumerate(ids)
                ],
            )
    client = login(web, p, "operator1")
    seen = set()
    for page in range(1, 8):
        response = client.get(
            "/opciones/donors", query_string={"q": prefix, "page": page}
        )
        assert response.status_code == 200
        assert response.json["total"] == 125
        seen.update(row["id"] for row in response.json["items"])
    assert seen == set(ids)
    assert client.get("/opciones/donors", query_string={"page": 0}).status_code == 422
    assert client.get("/opciones/https://example.com").status_code == 404


def test_location_reference_and_receipt_fields_render(web, p):
    admin = login(web, p, "admin1")
    post(
        admin,
        "/catalogos/sites/nuevo",
        {
            "name": "Ubicación Web " + uuid4().hex[:6],
            "municipality": "Apodaca",
            "address": "Domicilio ficticio",
        },
    )
    site = p.ok("identidad_acceso", "GET", "/api/v1/catalogues/sites", user="admin1")[
        "items"
    ][0]
    post(
        admin,
        "/catalogos/locations/nuevo",
        {
            "name": "Almacén " + uuid4().hex[:6],
            "parent_id": site["id"],
            "description": "Ubicación controlada demostrativa",
        },
    )
    location = p.ok(
        "identidad_acceso", "GET", "/api/v1/catalogues/locations", user="admin1"
    )["items"][0]
    operator = login(web, p, "operator1")
    url = post(
        operator,
        "/inventario/nuevo?kind=BLOOD",
        {
            "folio": "LOC-" + uuid4().hex[:8],
            "component": "RBC-DEMO",
            "blood_group": "O-",
            "expires_at": iso(days=2),
            "location_id": location["id"],
        },
    )
    row = p.ok(
        "inventario",
        "GET",
        "/api/v1/resources/" + url.rsplit("/", 1)[1],
        user="operator1",
    )
    assert row["location_id"] == location["id"]
    assert client_permissions(p, row, location) == 403


def client_permissions(p, row, location):
    return p.request(
        "inventario",
        "POST",
        "/api/v1/resources",
        user="operator2",
        data={
            "folio": "FOREIGN-" + uuid4().hex[:8],
            "kind": "BLOOD",
            "component": "RBC-DEMO",
            "blood_group": "O-",
            "expires_at": iso(days=2),
            "location_id": location["id"],
        },
    ).status_code
