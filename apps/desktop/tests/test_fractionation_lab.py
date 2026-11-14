"""Fraccionamiento Qt/XML con procedencia y persistencia sintéticas."""
import os
import time
from pathlib import Path
from uuid import uuid4

import redhouse_desktop.app as desktop
from cryptography.fernet import Fernet
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDateTimeEdit,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QTableWidget,
)
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


def test_operator_fractionates_traced_blood_unit(platform, gateway, monkeypatch, tmp_path):
    suffix = uuid4().hex[:8]
    confirm = {'human_confirmation': True, 'reason': 'Proceso sintético documentado'}
    donor = platform.ok('donantes', 'POST', '/api/v1/donors', user='operator1', data={'folio': 'DONOR-' + suffix, 'display_name': 'Donante ficticio', 'blood_group': 'O-', 'consent': True})
    platform.ok('donantes', 'POST', '/api/v1/donors/' + donor['id'] + '/reviews', user='medical1', data={**confirm, 'version': donor['version'], 'decision': 'ELIGIBLE'})
    donation = platform.ok('donantes', 'POST', '/api/v1/donations', user='medical1', data={**confirm, 'donor_id': donor['id'], 'kind': 'BLOOD', 'component': 'RBC', 'collected_at': iso(minutes=-2)})
    platform.ok('donantes', 'POST', '/api/v1/donations/' + donation['id'] + '/steps', user='operator1', data={**confirm, 'version': donation['version'], 'state': 'PROCESSED'})
    parent_folio = 'PARENT-' + suffix
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
        creation = {'selected': False}
        deadline = time.monotonic() + 30
        def create_unit():
            dialog = app.activeModalWidget()
            if time.monotonic() >= deadline:
                errors.append('Tiempo agotado al seleccionar donación')
                if dialog: dialog.reject()
                return
            if not dialog: QTimer.singleShot(25, create_unit); return
            try:
                if dialog.windowTitle() == 'Seleccionar donación procesada':
                    table = dialog.findChild(QTableWidget)
                    if not table or not table.rowCount(): QTimer.singleShot(25, create_unit); return
                    target = next((i for i in range(table.rowCount()) if donor['folio'] in table.item(i, 0).text()), None)
                    if target is None: raise AssertionError('Donación sintética no visible')
                    table.selectRow(target)
                    reference = next(x for x in dialog.findChildren(QLineEdit) if x.isReadOnly())
                    assert reference.text() == donation['id']
                    assert dialog.grab().save(str(output / 'donacion-qt.png'))
                    next(x for x in dialog.findChildren(QPushButton) if x.text() == 'Usar donación').click()
                    return
                if dialog.windowTitle() != 'Registrar unidad u oferta': QTimer.singleShot(25, create_unit); return
                if not creation['selected']:
                    creation['selected'] = True
                    QTimer.singleShot(25, create_unit)
                    next(x for x in dialog.findChildren(QPushButton) if x.text() == 'Seleccionar donación').click()
                    QTimer.singleShot(25, create_unit)
                    return
                next(x for x in dialog.findChildren(QLineEdit) if x.maxLength() == 30).setText(parent_folio)
                dates = dialog.findChildren(QDateTimeEdit)
                dates[-1].setDateTime(dates[-1].dateTime().addDays(2))
                next(x for x in dialog.findChildren(QCheckBox) if 'caducidad' in x.text().lower()).setChecked(True)
                assert dialog.grab().save(str(output / 'alta-con-donacion-qt.png'))
                next(x for x in dialog.findChildren(QPushButton) if x.text() == 'Registrar unidad').click()
            except Exception as exc:  # noqa: BLE001 - sin datos privados
                errors.append(type(exc).__name__)
                dialog.reject()
        QTimer.singleShot(0, create_unit)
        window.create_resource()
        assert not errors
        assert wait_until(lambda: not window.busy and any(row.get('folio') == parent_folio for row in window.rows))
        parent = next(row for row in window.rows if row.get('folio') == parent_folio)
        assert parent['donation_id'] == donation['id'] and parent['status'] == 'QUARANTINE'
        window.table.selectRow(next(i for i, row in enumerate(window.rows) if row['id'] == parent['id']))
        deadline = time.monotonic() + 30
        def choose():
            dialog = app.activeModalWidget()
            if time.monotonic() >= deadline:
                errors.append('Tiempo agotado al abrir derivados')
                if dialog: dialog.reject()
                return
            if not dialog: QTimer.singleShot(25, choose); return
            try:
                next(x for x in dialog.findChildren(QPushButton) if x.text() == 'Agregar derivado').click()
                folios = [x for x in dialog.findChildren(QLineEdit) if x.maxLength() == 30]
                assert len(folios) == 2
                for index, field in enumerate(folios): field.setText('CHILD' + str(index) + '-' + suffix)
                combos = dialog.findChildren(QComboBox)
                combos[0].setCurrentIndex(1)
                combos[1].setCurrentIndex(2)
                for date in dialog.findChildren(QDateTimeEdit): date.setDateTime(date.dateTime().addDays(1))
                next(x for x in dialog.findChildren(QLineEdit) if x.maxLength() == 1000).setText('Fraccionamiento sintético documentado')
                dialog.findChild(QCheckBox).setChecked(True)
                app.processEvents()
                assert dialog.grab().save(str(output / 'derivados-qt.png'))
                dialog.findChild(QScrollArea).ensureWidgetVisible(dialog.findChildren(QDateTimeEdit)[1])
                app.processEvents()
                assert dialog.grab().save(str(output / 'derivados-segundo-qt.png'))
                next(x for x in dialog.findChildren(QPushButton) if x.text() == 'Registrar derivados').click()
            except Exception as exc:  # noqa: BLE001 - sin datos privados
                errors.append(type(exc).__name__)
                dialog.reject()
        QTimer.singleShot(0, choose)
        window.fractionate_resource()
        assert wait_until(lambda: bool(errors) or (not window.busy and any(row.get('folio') == 'CHILD0-' + suffix for row in window.rows)))
        assert not errors
        links = window.client.authorized('inventario', '/api/v1/resources/' + parent['id'] + '/lineage', 'resource_lineage')
        relevant = [link for link in links if link['parent_id'] == parent['id']]
        assert len(relevant) == 2 and all(link['donation_id'] == donation['id'] for link in relevant)
        with platform.owner('inventario') as conn:
            original = conn.execute('SELECT status,version FROM resources WHERE id=%s', (parent['id'],)).fetchone()
            derived = conn.execute('SELECT status,version FROM resources WHERE id=ANY(%s::uuid[])', ([x['child_id'] for x in relevant],)).fetchall()
        assert original == ('WITHDRAWN', parent['version'] + 1)
        assert len(derived) == 2 and all(row == ('QUARANTINE', 1) for row in derived)
        platform.drain()
        with platform.owner('inventario') as conn:
            events = conn.execute("SELECT event->>'action',event->>'resource_id',event->>'actor_id' FROM activity_events WHERE event->>'resource_id'=%s", (parent['id'],)).fetchall()
        assert ('RESOURCE_FRACTIONATED', parent['id'], window.client.user['id']) in events
    finally:
        if window.busy: wait_until(lambda: not window.busy)
        had_session = bool(window.client and window.client.access)
        window.close()
        if had_session: assert wait_until(lambda: window.closing)
