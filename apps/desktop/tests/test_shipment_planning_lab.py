"""Planificación Qt/XML en plataforma sintética; se ejecuta solo con ventana de laboratorio."""
import os
import time
from pathlib import Path

import redhouse_desktop.app as desktop
from cryptography.fernet import Fernet
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QCheckBox, QDateTimeEdit, QLineEdit, QPushButton, QTableWidget
from redhouse_desktop.journal import Journal
from test_real_lab import gateway as gateway  # noqa: PLC0414 - fixture compartido
from tests.conftest import platform as platform  # noqa: PLC0414 - fixture compartido
from tests.helpers import evaluation, recipient_request, reservation, resource


def wait_until(predicate):
    deadline = time.monotonic() + 40
    while time.monotonic() < deadline:
        QApplication.processEvents()
        if predicate(): return True
        time.sleep(0.02)
    return False


def test_coordinator_plans_and_reads_shipment(platform, gateway, monkeypatch, tmp_path):
    unit = resource(platform)
    _, request = recipient_request(platform)
    allocation = reservation(platform, evaluation(platform, request, [unit]), unit)['reservation']
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
        window.username.setText('coordinator1')
        window.password.setText(platform.env.state['password'])
        window.login()
        assert wait_until(lambda: window.client and window.client.user and window.stack.currentIndex() == 1 and not window.busy)
        window.switch('shipments')
        assert wait_until(lambda: not window.busy)
        assert window.shipment_create_button.isVisible() and window.shipment_create_button.isEnabled()
        selected = {'started': False}
        def choose():
            dialog = app.activeModalWidget()
            if not dialog:
                QTimer.singleShot(25, choose); return
            tables = dialog.findChildren(QTableWidget)
            if len(tables) != 2 or not all(table.rowCount() for table in tables):
                QTimer.singleShot(25, choose); return
            try:
                reservations, users = tables
                row = next(i for i in range(reservations.rowCount()) if reservations.item(i, 0).text() == unit['folio'])
                transport = next(i for i in range(users.rowCount()) if users.item(i, 0).text() == 'transport1')
                if not selected['started']:
                    reservations.selectRow(row); users.selectRow(transport); selected['started'] = True
                button = next(x for x in dialog.findChildren(QPushButton) if x.text() == 'Planificar traslado')
                if not button.isEnabled(): QTimer.singleShot(25, choose); return
                dates = dialog.findChildren(QDateTimeEdit)
                dates[0].setDateTime(desktop.QDateTime.currentDateTime().addSecs(60))
                dates[1].setDateTime(desktop.QDateTime.currentDateTime().addSecs(1800))
                next(x for x in dialog.findChildren(QLineEdit) if x.maxLength() == 1000).setText('Planificación sintética autorizada')
                dialog.findChild(QCheckBox).setChecked(True)
                assert dialog.grab().save(str(output / 'planificacion-qt.png'))
                button.click()
            except Exception as exc:  # noqa: BLE001 - conserva solo la clase, sin datos privados
                errors.append(type(exc).__name__)
                dialog.reject()
        QTimer.singleShot(0, choose)
        window.plan_shipment()
        assert not errors
        assert wait_until(lambda: not window.busy and any(row.get('reservation_id') == allocation['id'] for row in window.rows))
        shipment = next(row for row in window.rows if row.get('reservation_id') == allocation['id'])
        assert shipment['inventory_pending'] is False and shipment['status'] == 'PLANNED'
        assert shipment['transport_user_id'] == platform.env.state['accounts']['transport1']['id']
        with platform.owner('transporte') as conn:
            saved = conn.execute('SELECT id,reservation_id,transport_user_id,status,inventory_pending FROM shipments WHERE id=%s', (shipment['id'],)).fetchone()
        assert str(saved[1]) == allocation['id'] and str(saved[2]) == shipment['transport_user_id']
        assert saved[3] == 'PLANNED' and not saved[4]
        detail = window.client.authorized('transporte', '/api/v1/shipments/' + shipment['id'], 'shipment_detail')
        assert detail['reservation_id'] == allocation['id'] and detail['transport_user_id'] == shipment['transport_user_id']
        assert window.grab().save(str(output / 'traslado-qt.png'))
    finally:
        if window.busy: wait_until(lambda: not window.busy)
        had_session = bool(window.client and window.client.access)
        window.close()
        if had_session: assert wait_until(lambda: window.closing)
