"""Referencias de negocio en el listado Jinja real y su exportación CSV.

Sin servicios ni sesión: solo se sustituye la API propietaria y la envoltura
base de navegación; la tabla y sus macros se renderizan desde las plantillas.
"""
import csv
import io
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID

import pytest
from flask import Flask, g
from jinja2 import ChoiceLoader, DictLoader
from markupsafe import escape
from src.integration.routes import common, requests

IDENTIFIER = '12345678-1234-1234-1234-123456789abc'
REFERENCE = 'Constancia <sintética> & autorizada'


@pytest.fixture
def portal(monkeypatch):
    import src
    templates = Path(src.__file__).parent / 'presentation/templates'
    app = Flask(__name__, template_folder=str(templates))
    app.config.update(TESTING=True, DEFAULT_DISPLAY_TIMEZONE='America/Monterrey')
    app.jinja_loader = ChoiceLoader([
        DictLoader({'base.html': '<main>{% block content %}{% endblock %}</main>'}),
        app.jinja_loader,
    ])
    app.jinja_env.filters.update(portal_html=common.display_html, event_label=common.event_label,
                                service_label=lambda value: value)
    rows = [{'id': IDENTIFIER, 'reference': REFERENCE, 'folio': 'NO-SUSTITUIR'},
            {'id': 'abcdef01-1234-1234-1234-123456789abc', 'folio': 'FOLIO-VALIDO'},
            {'id': 'fedcba09-1234-1234-1234-123456789abc'}]
    monkeypatch.setattr(common, 'call', lambda *a, **k: {'items': deepcopy(rows), 'total': len(rows)})
    monkeypatch.setattr(common, 'edit_action', lambda *a: [])
    principal = SimpleNamespace(role_code='MEDICAL', institution_name='Institución sintética', region_name='Región sintética')

    @app.before_request
    def identity():
        g.principal = principal

    @app.context_processor
    def presentation():
        return {'principal': principal}

    @app.get('/listado')
    def listing():
        return common.table('Listado', 'solicitudes', 'receptores', '/api/v1/requests',
                            [('reference', 'Referencia')], new='/nuevo')

    app.add_url_rule('/solicitudes/<uuid:identifier>/constancias',
                     endpoint='regional.external_authorizations', view_func=requests.external_authorizations)
    app.add_url_rule('/solicitudes/<uuid:identifier>/constancias/nueva',
                     endpoint='regional.external_authorization_new', view_func=lambda identifier: '')
    return app.test_client(), rows


def test_list_preserves_reference_and_falls_back_only_when_missing(portal):
    client, rows = portal
    response = client.get('/listado')
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert str(escape(REFERENCE)) in html
    assert REFERENCE not in html
    assert 'NO-SUSTITUIR' not in html and 'REG-12345678' not in html
    assert 'FOLIO-VALIDO' in html and 'REG-FEDCBA09' in html
    assert rows[0]['reference'] == REFERENCE


def test_csv_preserves_reference_and_uses_the_same_fallback(portal):
    client, _ = portal
    response = client.get('/listado?format=csv')
    assert response.status_code == 200 and response.mimetype == 'text/csv'
    records = list(csv.reader(io.StringIO(response.get_data(as_text=True).lstrip('\ufeff'))))
    assert [row[0] for row in records[1:]] == [REFERENCE, 'FOLIO-VALIDO', 'REG-FEDCBA09']


def test_csv_retains_formula_protection_for_preserved_reference(portal):
    client, rows = portal
    rows[0]['reference'] = '=1+1'
    response = client.get('/listado?format=csv')
    records = list(csv.reader(io.StringIO(response.get_data(as_text=True).lstrip('\ufeff'))))
    assert records[1][0] == "'=1+1"


def test_authorizations_have_explicit_action_without_changing_request_default(portal):
    client, _ = portal
    response = client.get(f'/solicitudes/{UUID(IDENTIFIER)}/constancias')
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'Documentar constancia' in html and 'Crear solicitud' not in html
    assert str(escape(REFERENCE)) in html
    assert 'Crear solicitud' in client.get('/listado').get_data(as_text=True)
