"""Resaltado de la barra lateral del portal: una URL, una sección.

La sección activa sale de ``src.integration.navigation`` (mapa endpoint -> id de
``NAV`` con respaldo por prefijo de ruta). Estas pruebas fijan tres cosas:

* cobertura: todo endpoint del portal tiene sección declarada y existente en NAV;
* consistencia: el respaldo por prefijo coincide con el mapa por endpoint;
* extremo a extremo, por rol: cada enlace de la barra resalta exactamente
  su propia entrada y los detalles/formularios que se abren desde un listado
  resaltan la entrada de ese listado.
"""

import sys
from pathlib import Path
from urllib.parse import urlsplit
from uuid import uuid4

import pytest
from lxml import etree

from .test_web_integration import login, web  # noqa: F401

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "web"))
from src.integration import NAV  # noqa: E402
from src.integration import navigation  # noqa: E402

NAV_IDS = {entry[1] for entry in NAV}
PORTAL_ROLES = ["admin1", "operator1", "medical1", "coordinator1", "auditor1"]
UUID = str(uuid4())
# Valores de ejemplo para completar los parámetros de ruta.
SAMPLE_ARGS = {
    "kind": "donor",
    "entity": "users",
    "identifier": UUID,
    "resource_id": UUID,
    "assignment_id": UUID,
    "state": "x",
    "source": "x",
}


def portal_rules(app):
    """Reglas con barra lateral: todas menos sitio público y estáticos."""
    return [
        rule
        for rule in app.url_map.iter_rules()
        if rule.endpoint.split(".")[0] not in navigation.EXCLUDED_BLUEPRINTS
        and rule.endpoint != "static"
    ]


def sample_path(rule):
    path = rule.rule
    for name in rule.arguments:
        path = path.replace(f"<uuid:{name}>", SAMPLE_ARGS[name])
        path = path.replace(f"<{name}>", SAMPLE_ARGS[name])
    return path


def test_every_portal_endpoint_declares_an_existing_section(web):  # noqa: F811
    missing = [
        r.endpoint
        for r in portal_rules(web)
        if r.endpoint not in navigation.ENDPOINT_SECTIONS
    ]
    assert not missing, (
        f"Endpoints sin sección en navigation.ENDPOINT_SECTIONS: {missing}"
    )
    unknown_endpoints = set(navigation.ENDPOINT_SECTIONS) - {
        r.endpoint for r in web.url_map.iter_rules()
    }
    assert not unknown_endpoints, unknown_endpoints
    for rule in portal_rules(web):
        value = navigation.ENDPOINT_SECTIONS[rule.endpoint]
        results = {
            sample_kind: (
                value({"kind": sample_kind, "entity": sample_kind})
                if callable(value)
                else value
            )
            for sample_kind in (
                "donor",
                "recipient",
                "users",
                "institutions",
                "donors",
                "resources",
                "x",
            )
        }
        for result in results.values():
            assert result is None or result in NAV_IDS, (rule.endpoint, result)


def test_nav_entries_resolve_to_themselves(web):  # noqa: F811
    with web.test_request_context():
        from flask import url_for

        for _group, section, label, _glyph, endpoint, args, *_ in NAV:
            path = urlsplit(url_for(endpoint, **args)).path
            matched, view_args = web.url_map.bind("localhost").match(path)
            assert matched == endpoint
            assert navigation.resolve(matched, path, view_args) == section, label


def test_path_prefix_fallback_agrees_with_endpoint_map(web):  # noqa: F811
    """Una ruta nueva sin mapa explícito cae en la misma sección que tendría."""
    disagreements = []
    for rule in portal_rules(web):
        if "GET" not in rule.methods:
            continue
        path = sample_path(rule)
        expected = navigation.resolve(rule.endpoint, path, SAMPLE_ARGS)
        # Se desactiva el mapa para ejercitar solo el respaldo por prefijo.
        by_prefix = next(
            (
                s
                for p, s in navigation.PATH_PREFIXES
                if path == p or path.startswith(p + "/")
            ),
            None,
        )
        if expected is not None and by_prefix != expected:
            disagreements.append((rule.endpoint, path, expected, by_prefix))
    assert not disagreements, disagreements


def sidebar(html):
    """Enlaces de la barra: lista de (href, active, aria_current)."""
    return [
        (
            link.get("href"),
            "active" in link.get("class").split(),
            link.get("aria-current"),
        )
        for link in html.xpath(
            '//nav[@class="sidebar-nav"]//a[contains(@class,"nav-link")]'
        )
    ]


def assert_highlight(client, path, expected_href, role):
    """Exactamente el enlace ``expected_href`` queda activo (o ninguno si None)."""
    response = client.get(path, follow_redirects=False)
    assert response.status_code == 200, (role, path, response.status_code)
    assert response.headers["Cache-Control"] == "no-store"
    links = sidebar(etree.HTML(response.data))
    active = [href for href, is_active, _ in links if is_active]
    current = [href for href, _, aria in links if aria == "page"]
    expected = [expected_href] if expected_href else []
    assert active == expected, (role, path, active, expected)
    assert current == expected, (role, path, current, expected)
    return etree.HTML(response.data)


@pytest.mark.parametrize("role", PORTAL_ROLES)
def test_sidebar_highlights_exactly_the_open_section(web, p, role):  # noqa: F811
    client = login(web, p, role)
    first = client.get("/notificaciones")
    assert first.status_code == 200
    hrefs = [href for href, _, _ in sidebar(etree.HTML(first.data))]
    assert hrefs, role
    visited_details = 0
    for href in hrefs:
        listing = assert_highlight(client, href, href, role)
        # Detalles y formularios abiertos desde este listado conservan su resaltado
        # (y por tanto también al recargar o volver con Atrás: es una petición nueva).
        targets = {
            link.get("href")
            for link in listing.xpath(
                '//*[@data-filter-results]//a[contains(@class,"record-link")] | //a[@data-list-return]'
            )
            if link.get("href", "").startswith("/")
        }
        for target in sorted(targets)[:6]:
            target_path = urlsplit(target).path
            matched, _args = web.url_map.bind("localhost").match(target_path)
            if matched.split(".")[0] in ("public", "static"):
                continue
            if href == "/notificaciones":
                # La bandeja enlaza registros de otras secciones (p. ej. una cita):
                # la URL determina la sección, así que ahí resalta la del registro.
                # Solo aparecen si otra prueba generó avisos; por eso falla según datos.
                continue
            response = client.get(target)
            if response.status_code != 200:
                continue  # fuera del ámbito del rol; el control de acceso no es de esta prueba
            links = sidebar(etree.HTML(response.data))
            active = [h for h, a, _ in links if a]
            assert active in ([href], []), (role, href, target, active)
            assert active == [href], (role, href, target, "no resalta su listado")
            visited_details += 1
        # Recarga: la misma URL produce el mismo resaltado.
        assert_highlight(client, href, href, role)
    assert visited_details >= 1, (role, "ningún detalle ni formulario recorrido")


def test_error_page_inside_a_section_keeps_that_section(web, p):  # noqa: F811
    """Un 404 de un recurso dentro de una sección sigue marcando esa sección."""
    client = login(web, p, "operator1")
    cases = {
        "/laboratorio/muestras/" + UUID: "/laboratorio/muestras",
        "/solicitudes/" + UUID: "/solicitudes",
        "/inventario/" + UUID: "/inventario",
        "/apoyo-decisiones/" + UUID: "/apoyo-decisiones",
        "/conservacion/perfiles/" + UUID: "/conservacion",
    }
    for path, section_href in cases.items():
        response = client.get(path)
        assert response.status_code in (403, 404), (path, response.status_code)
        links = sidebar(etree.HTML(response.data))
        active = [h for h, a, _ in links if a]
        # Si el rol no ve esa entrada en la barra, ninguna otra debe resaltarse.
        assert active in ([section_href], []), (path, active)
