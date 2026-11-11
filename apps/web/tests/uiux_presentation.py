"""Presentation regression using real Jinja templates; no backend writes.

Run from repository root with apps/web/.venv/bin/python apps/web/tests/uiux_presentation.py.
Requires the existing private local web configuration. Does not authenticate.
"""
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / 'apps/web'), str(ROOT / 'apps/services')]
from src import create_app
from src.integration import NAV, PERMISSIONS, ROLES
from flask import g, render_template, flash
import re

app = create_app({'MICROSERVICES_CONFIG': ROOT / '.local/runtime/web-client.json', 'BACKEND_MODE': 'microservices'})
for role in ROLES:
    with app.test_request_context('/panel'):
        g.principal = SimpleNamespace(role_code=role, role_name=ROLES[role], party_name='Cuenta sintética',
            account_id='test', institution_id='test', institution_name='Institución de prueba',
            region_name='Nuevo León', can=lambda permission: role in PERMISSIONS.get(permission, set()))
        flash('Operación pendiente de confirmación', 'warning')
        html = render_template('integration/dashboard.html', title='Panel principal', active='dashboard',
            metrics=[], failures=[], stats=[], charts=[], alerts=[], appointments=[], audit_events=[])
        groups = re.findall(r'class="nav-group">([^<]+)', html)
        assert len(groups) == len(set(groups)), role
        assert 'img/icons/triangle-alert.svg' in html
        assert 'img/icons/circle-check.svg' not in html
        expected = [entry for entry in NAV if g.principal.can(entry[6]) and
                    not (entry[1] == 'trazabilidad' and g.principal.can('logistics'))]
        assert len(re.findall(r'class="nav-link', html)) == len(expected), role
        macro = app.jinja_env.get_template('integration/values.html').make_module({'principal': g.principal})
        assert 'Autorizado documentalmente' in macro.status_badge('AUTHORIZED')
        assert 'Sin comprobar' in macro.status_badge('NOT_CHECKED')
        assert macro.value_view('AUTHORIZED', 'title').strip() == 'AUTHORIZED'
        assert 'Corregido' in macro.status_badge('CORRECTED')
for name in app.jinja_env.list_templates():
    app.jinja_env.get_template(name)
print('PASS: siete perfiles, navegación, avisos inciertos, estados y compilación de plantillas')

# Shared action contract: read remains POST+CSRF+idempotency; destructive actions
# retain their dialog; full detail and quick view have distinct links and icons.
from flask import render_template_string
from html.parser import HTMLParser
class Controls(HTMLParser):
    def __init__(self):
        super().__init__(); self.tags=[]
    def handle_starttag(self, tag, attrs):
        self.tags.append((tag,dict(attrs)))
with app.test_request_context('/notificaciones'):
    g.principal=None
    html=render_template_string("{% from 'integration/row_actions.html' import record_actions with context %}{{ record_actions(row,'Aviso de prueba',true) }}",row={
        '_href':'/detail', '_action_key':'same-key', '_actions':[
            ('Marcar como leída','/ack','read'),('Cancelar','/cancel','cancel'),('Editar','/edit','pencil')]})
    parsed=Controls();parsed.feed(html)
    assert ('form',{'method':'post','action':'/ack','class':'inline-action'}) in parsed.tags
    assert any(tag=='input' and attrs.get('name')=='csrf_token' and attrs.get('value') for tag,attrs in parsed.tags)
    assert any(tag=='input' and attrs.get('name')=='idempotency_key' and attrs.get('value')=='same-key' for tag,attrs in parsed.tags)
    assert any(tag=='a' and attrs.get('href')=='/cancel' and 'data-action-dialog' in attrs for tag,attrs in parsed.tags)
    direct=[attrs for tag,attrs in parsed.tags if tag in ('a','button') and attrs.get('class')=='icon-button']
    assert len(direct)==2
    assert direct[0]['href']=='/detail' and 'data-record-view' not in direct[0]
    assert direct[1]['data-record-view']=='/detail'
    assert all('aria-label' in item and 'data-tooltip' in item for item in direct)
print('PASS: acciones directas limitadas, apertura distinta, POST/CSRF/idempotencia y diálogo conservados')
