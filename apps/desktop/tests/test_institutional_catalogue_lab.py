"""Sede y capacidad Qt/XML con administración sintética y auditoría."""
import os
import time
from pathlib import Path
from uuid import uuid4

import pytest
import redhouse_desktop.app as desktop
from cryptography.fernet import Fernet
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTableWidget,
)
from redhouse_desktop.client import ApiError, Client
from redhouse_desktop.journal import Journal
from test_real_lab import gateway as gateway  # noqa: PLC0414 - fixture compartido
from tests.conftest import platform as platform  # noqa: PLC0414 - fixture compartido


def wait_until(predicate):
    deadline = time.monotonic() + 40
    while time.monotonic() < deadline:
        QApplication.processEvents()
        if predicate(): return True
        time.sleep(0.02)
    return False


def test_admin_manages_sites_and_capacities(platform, gateway, monkeypatch, tmp_path):
    suffix = uuid4().hex[:8]
    site_name = 'Sede ' + suffix
    revised_site = 'Sede corregida ' + suffix
    capacity_name = 'Capacidad ' + suffix
    class Keys:
        def __init__(self): self.key = Fernet.generate_key()
        def get(self, identifier, exists): return self.key
    keys = Keys()
    monkeypatch.setattr(desktop, 'Journal', lambda _root, base, user, tenant: Journal(tmp_path, base, user, tenant, keys))
    monkeypatch.setenv('REDHOUSE_BASE_URL', gateway)
    app = QApplication.instance() or QApplication([])
    app.setStyleSheet(desktop.STYLE)
    output = Path(os.environ['DESKTOP_CAPTURE_DIR'])
    output.mkdir(parents=True, exist_ok=True)
    window = desktop.Window()
    errors = []
    window.show()
    def fill(kind, editing, desired_name, capture):
        deadline = time.monotonic() + 30
        def choose():
            dialog = app.activeModalWidget()
            if time.monotonic() >= deadline:
                errors.append('Tiempo agotado en formulario')
                if dialog: dialog.reject()
                return
            if not dialog: QTimer.singleShot(25, choose); return
            try:
                dialog.findChild(QLineEdit, 'catalogue_name').setText(desired_name)
                if kind == 'sites':
                    dialog.findChild(QLineEdit, 'catalogue_municipality').setText('Monterrey')
                    dialog.findChild(QLineEdit, 'catalogue_address').setText('Dirección sintética')
                else:
                    dialog.findChild(QLineEdit, 'catalogue_component').setText('RBC')
                    dialog.findChild(QSpinBox, 'catalogue_quantity').setValue(7 if editing else 4)
                    if not editing:
                        table = dialog.findChild(QTableWidget)
                        if not table or not table.rowCount(): QTimer.singleShot(25, choose); return
                        index = next((i for i in range(table.rowCount()) if table.item(i, 0).text() == revised_site), None)
                        if index is None: raise AssertionError('Sede sintética no visible')
                        table.selectRow(index)
                if editing:
                    next(x for x in dialog.findChildren(QLineEdit) if x.maxLength() == 1000).setText('Corrección sintética documentada')
                    for checkbox in dialog.findChildren(QCheckBox): checkbox.setChecked(True)
                title = 'Guardar corrección' if editing else 'Registrar ' + ('sede' if kind == 'sites' else 'capacidad')
                save = next(x for x in dialog.findChildren(QPushButton) if x.text() == title)
                if not save.isEnabled(): QTimer.singleShot(25, choose); return
                assert dialog.grab().save(str(output / capture))
                save.click()
            except Exception as exc:  # noqa: BLE001 - solo clase sin datos privados
                errors.append(type(exc).__name__)
                dialog.reject()
        QTimer.singleShot(0, choose)
        window.catalogue_action(editing)
        assert not errors
    try:
        window.username.setText('admin1')
        window.password.setText(platform.env.state['password'])
        window.login()
        assert wait_until(lambda: window.client and window.client.user and window.stack.currentIndex() == 1 and not window.busy)
        actor = window.client.user['id']
        window.switch('sites')
        assert wait_until(lambda: not window.busy)
        fill('sites', False, site_name, 'sede-alta-qt.png')
        assert wait_until(lambda: not window.busy and any(row['name'] == site_name for row in window.rows))
        site = next(row for row in window.rows if row['name'] == site_name)
        window.table.selectRow(next(i for i, row in enumerate(window.rows) if row['id'] == site['id']))
        fill('sites', True, revised_site, 'sede-correccion-qt.png')
        assert wait_until(lambda: not window.busy and any(row['name'] == revised_site and row['version'] == site['version'] + 1 for row in window.rows))
        window.switch('capacities')
        assert wait_until(lambda: not window.busy)
        fill('capacities', False, capacity_name, 'capacidad-alta-qt.png')
        assert wait_until(lambda: not window.busy and any(row['name'] == capacity_name for row in window.rows))
        capacity = next(row for row in window.rows if row['name'] == capacity_name)
        assert capacity['parent_id'] == site['id']
        window.table.selectRow(next(i for i, row in enumerate(window.rows) if row['id'] == capacity['id']))
        fill('capacities', True, capacity_name, 'capacidad-correccion-qt.png')
        assert wait_until(lambda: not window.busy and any(row['id'] == capacity['id'] and row['version'] == capacity['version'] + 1 and row['quantity'] == 7 for row in window.rows))
        with platform.owner('identidad_acceso') as conn:
            rows = conn.execute('SELECT id,version,parent_id,details FROM catalogue WHERE id=ANY(%s::uuid[])', ([site['id'], capacity['id']],)).fetchall()
        assert len(rows) == 2
        by_id = {str(row[0]): row for row in rows}
        assert by_id[site['id']][1] == site['version'] + 1
        assert by_id[capacity['id']][1] == capacity['version'] + 1 and str(by_id[capacity['id']][2]) == site['id'] and by_id[capacity['id']][3]['quantity'] == 7
        platform.drain()
        with platform.owner('identidad_acceso') as conn:
            events = conn.execute("SELECT event->>'resource_id',event->>'action',event->>'actor_id' FROM activity_events WHERE event->>'resource_id'=ANY(%s)", ([site['id'], capacity['id']],)).fetchall()
        for identifier in (site['id'], capacity['id']):
            assert (identifier, 'CATALOGUE_CREATED', actor) in events
            assert (identifier, 'CATALOGUE_UPDATED', actor) in events
        operator = Client(gateway)
        try:
            operator.login('operator1', platform.env.state['password'], '')
            with pytest.raises(ApiError) as denied:
                operator.authorized('identidad-acceso', '/api/v1/catalogues/sites', 'sites_create', method='POST', body={'name': 'No autorizado', 'municipality': 'Monterrey', 'address': 'Sintética'}, request_schema='sites_create.xsd', key=str(uuid4()))
            assert denied.value.status == 403
        finally:
            operator.logout()
    finally:
        if window.busy: wait_until(lambda: not window.busy)
        had_session = bool(window.client and window.client.access)
        window.close()
        if had_session: assert wait_until(lambda: window.closing)
