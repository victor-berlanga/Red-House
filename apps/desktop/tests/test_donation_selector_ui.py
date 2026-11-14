"""Selección paginada de procedencia con dos registros visualmente similares."""
import os
import time
from pathlib import Path
from uuid import uuid4

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QLineEdit, QPushButton, QTableWidget
from redhouse_desktop.app import STYLE, Window, Work, label
from redhouse_desktop.donation_selector import select_processed_donation

app = QApplication.instance() or QApplication([])
app.setStyleSheet(STYLE)


def test_selected_reference_distinguishes_similar_donations():
    tenant, donor, first, second = (str(uuid4()) for _ in range(4))
    class Client:
        access = None
        def __init__(self): self.user = {'id': str(uuid4()), 'tenant_id': tenant, 'role': 'OPERATOR'}
        def authorized(self, _service, _path, operation, **kwargs):
            if operation == 'donations_list':
                assert kwargs['params']['kind'] == 'BLOOD' and kwargs['params']['status'] == 'PROCESSED'
                rows = [{'id': value, 'donor_id': donor, 'tenant_id': tenant, 'kind': 'BLOOD', 'status': 'PROCESSED', 'component': 'RBC', 'blood_group': 'O-', 'collected_at': '2026-11-14T12:00:00Z'} for value in (first, second)]
                return {'items': rows, 'page': 1, 'total': 2}
            assert operation == 'donor_detail'
            return {'id': donor, 'tenant_id': tenant, 'folio': 'DONANTE-01', 'display_name': 'Persona ficticia'}
    window = Window()
    window.client = Client()
    errors = []
    deadline = time.monotonic() + 8
    def choose():
        dialog = app.activeModalWidget()
        if time.monotonic() >= deadline:
            errors.append('timeout')
            if dialog: dialog.reject()
            return
        if not dialog: QTimer.singleShot(20, choose); return
        table = dialog.findChild(QTableWidget)
        if table.rowCount() != 2: QTimer.singleShot(20, choose); return
        try:
            table.selectRow(1)
            reference = next(x for x in dialog.findChildren(QLineEdit) if x.isReadOnly())
            assert reference.text() == second
            if os.environ.get('DESKTOP_CAPTURE_DIR'):
                assert dialog.grab().save(str(Path(os.environ['DESKTOP_CAPTURE_DIR']) / 'donacion-doble.png'))
            next(x for x in dialog.findChildren(QPushButton) if x.text() == 'Usar donación').click()
        except Exception as exc:  # noqa: BLE001 - sin datos privados
            errors.append(type(exc).__name__)
            dialog.reject()
    QTimer.singleShot(0, choose)
    selected = select_processed_donation(window, Work, label)
    assert not errors and selected['id'] == second


def test_resource_form_keeps_selected_origin(monkeypatch):
    import redhouse_desktop.app as desktop
    from PySide6.QtWidgets import QCheckBox, QDateTimeEdit

    donation = {'id': str(uuid4()), 'kind': 'BLOOD', 'component': 'RBC', 'blood_group': 'O-',
                'collected_at': '2026-11-14T12:00:01.123456Z', '_donor_folio': 'DONANTE-01',
                '_donor_name': 'Persona ficticia'}
    window = Window()
    class Client:
        def __init__(self): self.user = {'id': str(uuid4()), 'tenant_id': str(uuid4()), 'role': 'OPERATOR'}
    window.client = Client()
    errors, calls = [], []
    monkeypatch.setattr(desktop, 'select_processed_donation', lambda *_args: donation)
    monkeypatch.setattr(window, 'durable', lambda operation, identifier, body: calls.append((operation, identifier, body)))
    monkeypatch.setattr(window, 'run', lambda work, _success, _message: work())
    def fill():
        dialog = app.activeModalWidget()
        if not dialog: QTimer.singleShot(20, fill); return
        try:
            next(x for x in dialog.findChildren(QPushButton) if x.text() == 'Seleccionar donación').click()
            assert next(x for x in dialog.findChildren(QLineEdit) if x.isReadOnly()).text() == donation['id']
            next(x for x in dialog.findChildren(QLineEdit) if x.maxLength() == 30).setText('UNIT-001')
            dates = dialog.findChildren(QDateTimeEdit)
            dates[-1].setDateTime(dates[-1].dateTime().addDays(2))
            next(x for x in dialog.findChildren(QCheckBox) if 'caducidad' in x.text().lower()).setChecked(True)
            if os.environ.get('DESKTOP_CAPTURE_DIR'):
                assert dialog.grab().save(str(Path(os.environ['DESKTOP_CAPTURE_DIR']) / 'alta-donacion-doble.png'))
            next(x for x in dialog.findChildren(QPushButton) if x.text() == 'Registrar unidad').click()
        except Exception as exc:  # noqa: BLE001 - sin datos privados
            errors.append(type(exc).__name__)
            dialog.reject()
    QTimer.singleShot(0, fill)
    window.create_resource()
    assert not errors and len(calls) == 1
    body = calls[0][2]
    assert body['donation_id'] == donation['id'] and body['collected_at'] == donation['collected_at']
    assert body['kind'] == 'BLOOD' and body['component'] == 'RBC' and body['blood_group'] == 'O-'
