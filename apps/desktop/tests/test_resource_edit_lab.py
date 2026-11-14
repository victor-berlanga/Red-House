"""Corrección Qt/XML de unidad sintética; requiere fixture aislado."""
import os
import time
from pathlib import Path
from uuid import uuid4

import redhouse_desktop.app as desktop
from cryptography.fernet import Fernet
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QCheckBox, QComboBox, QLineEdit, QPushButton
from redhouse_desktop.journal import Journal
from test_real_lab import gateway as gateway  # noqa: PLC0414 - fixture compartido
from tests.conftest import platform as platform  # noqa: PLC0414 - fixture compartido
from tests.helpers import iso


def wait_until(predicate):
    deadline = time.monotonic() + 40
    while time.monotonic() < deadline:
        QApplication.processEvents()
        if predicate(): return True
        time.sleep(0.02)
    return False


def test_operator_corrects_quarantine_unit(platform, gateway, monkeypatch, tmp_path):
    suffix = uuid4().hex[:8]
    site = platform.ok('identidad_acceso', 'POST', '/api/v1/catalogues/sites', user='admin1', data={'name': 'Sede ' + suffix, 'municipality': 'Monterrey', 'address': 'Dirección sintética'})
    location = platform.ok('identidad_acceso', 'POST', '/api/v1/catalogues/locations', user='admin1', data={'name': 'Refrigerador ' + suffix, 'parent_id': site['id'], 'description': 'Ubicación sintética'})
    unit = platform.ok('inventario', 'POST', '/api/v1/resources', user='operator1', data={'folio': 'UNIT-' + suffix, 'kind': 'BLOOD', 'component': 'RBC', 'blood_group': 'O-', 'expires_at': iso(days=2)})
    corrected = 'FIXED-' + suffix
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
    try:
        window.username.setText('operator1')
        window.password.setText(platform.env.state['password'])
        window.login()
        assert wait_until(lambda: window.client and window.client.user and window.stack.currentIndex() == 1 and not window.busy)
        assert wait_until(lambda: any(row['id'] == unit['id'] for row in window.rows))
        window.table.selectRow(next(i for i, row in enumerate(window.rows) if row['id'] == unit['id']))
        deadline = time.monotonic() + 30
        def choose():
            dialog = app.activeModalWidget()
            if time.monotonic() >= deadline:
                errors.append('Tiempo agotado al seleccionar ubicación')
                if dialog: dialog.reject()
                return
            if not dialog: QTimer.singleShot(25, choose); return
            combo = dialog.findChild(QComboBox)
            index = combo.findText(location['name']) if combo else -1
            if index < 0: QTimer.singleShot(25, choose); return
            try:
                combo.setCurrentIndex(index)
                next(x for x in dialog.findChildren(QLineEdit) if x.maxLength() == 30).setText(corrected)
                next(x for x in dialog.findChildren(QLineEdit) if x.maxLength() == 1000).setText('Corrección sintética autorizada')
                for check in dialog.findChildren(QCheckBox): check.setChecked(True)
                assert dialog.grab().save(str(output / 'correccion-qt.png'))
                next(x for x in dialog.findChildren(QPushButton) if x.text() == 'Guardar corrección').click()
            except Exception as exc:  # noqa: BLE001 - solo clase sin datos privados
                errors.append(type(exc).__name__)
                dialog.reject()
        QTimer.singleShot(0, choose)
        window.edit_resource()
        assert wait_until(lambda: bool(errors) or (not window.busy and any(row.get('folio') == corrected for row in window.rows)))
        assert not errors
        result = window.client.authorized('inventario', '/api/v1/resources/' + unit['id'], 'resource_detail')
        assert result['folio'] == corrected and result['location_id'] == location['id']
        assert result['version'] == unit['version'] + 1 and result['status'] == 'QUARANTINE'
        with platform.owner('inventario') as conn:
            row = conn.execute('SELECT folio,location_id,version,status FROM resources WHERE id=%s', (unit['id'],)).fetchone()
        assert row[0] == corrected and str(row[1]) == location['id'] and row[2] == result['version'] and row[3] == 'QUARANTINE'
        platform.drain()
        with platform.owner('inventario') as conn:
            events = conn.execute("SELECT event->>'action',event->>'resource_id',event->>'actor_id' FROM activity_events WHERE event->>'resource_id'=%s", (unit['id'],)).fetchall()
        assert ('RESOURCE_UPDATED', unit['id'], window.client.user['id']) in events
    finally:
        if window.busy: wait_until(lambda: not window.busy)
        had_session = bool(window.client and window.client.access)
        window.close()
        if had_session: assert wait_until(lambda: window.closing)
