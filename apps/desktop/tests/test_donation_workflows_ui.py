"""Formularios Qt de colecta y procesamiento con respuestas sintéticas."""
import os
import time
from pathlib import Path
from uuid import uuid4

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDateTimeEdit,
    QLineEdit,
    QPushButton,
    QTableWidget,
)
from redhouse_desktop.app import STYLE, Window, Work
from redhouse_desktop.donation_workflows import collect_dialog, processing_dialog

app = QApplication.instance() or QApplication([])
app.setStyleSheet(STYLE)


def test_medical_selects_donor_and_documents_collection():
    tenant, donor = str(uuid4()), str(uuid4())
    class Client:
        def __init__(self): self.user = {'id': str(uuid4()), 'tenant_id': tenant, 'role': 'MEDICAL'}
        def authorized(self, _service, _path, operation, **kwargs):
            assert operation == 'donors' and kwargs['params']['status'] == 'ELIGIBLE'
            return {'items': [{'id': donor, 'tenant_id': tenant, 'status': 'ELIGIBLE', 'folio': 'DONANTE-01', 'display_name': 'Persona ficticia', 'blood_group': 'O-'}], 'page': 1, 'total': 1}
    window = Window()
    window.client = Client()
    errors = []
    deadline = time.monotonic() + 8
    def fill():
        dialog = app.activeModalWidget()
        if time.monotonic() >= deadline:
            errors.append('timeout')
            if dialog: dialog.reject()
            return
        if not dialog: QTimer.singleShot(20, fill); return
        table = dialog.findChild(QTableWidget)
        if not table.rowCount(): QTimer.singleShot(20, fill); return
        try:
            table.selectRow(0)
            combos = dialog.findChildren(QComboBox)
            combos[0].setCurrentIndex(combos[0].findData('BLOOD'))
            combos[1].setCurrentIndex(combos[1].findData('RBC'))
            date = dialog.findChild(QDateTimeEdit)
            date.setDateTime(date.dateTime().addSecs(-60))
            next(field for field in dialog.findChildren(QLineEdit) if field.maxLength() == 1000).setText('Colecta documentada')
            for check in dialog.findChildren(QCheckBox): check.setChecked(True)
            if os.environ.get('DESKTOP_CAPTURE_DIR'):
                assert dialog.grab().save(str(Path(os.environ['DESKTOP_CAPTURE_DIR']) / 'colecta-doble.png'))
            next(button for button in dialog.findChildren(QPushButton) if button.text() == 'Registrar colecta').click()
        except Exception as exc:  # noqa: BLE001 - sin datos privados
            errors.append(type(exc).__name__)
            dialog.reject()
    QTimer.singleShot(0, fill)
    body = collect_dialog(window, Work)
    assert not errors and body['donor_id'] == donor and body['component'] == 'RBC'
    assert body['collected_at'].endswith('Z') and body['human_confirmation'] == 'true'


def test_operator_must_choose_processing_result():
    donation = {'id': str(uuid4()), '_donor_folio': 'DONANTE-01', '_donor_name': 'Persona ficticia', 'collected_at': '2026-11-14T12:00:00Z', 'component': 'RBC', 'version': 3}
    window = Window()
    errors = []
    def fill():
        dialog = app.activeModalWidget()
        if not dialog: QTimer.singleShot(20, fill); return
        try:
            choice = dialog.findChild(QComboBox)
            assert choice.currentData() == ''
            choice.setCurrentIndex(choice.findData('PROCESSED'))
            next(field for field in dialog.findChildren(QLineEdit) if field.maxLength() == 1000).setText('Procesamiento documentado')
            dialog.findChild(QCheckBox).setChecked(True)
            if os.environ.get('DESKTOP_CAPTURE_DIR'):
                assert dialog.grab().save(str(Path(os.environ['DESKTOP_CAPTURE_DIR']) / 'procesamiento-doble.png'))
            next(button for button in dialog.findChildren(QPushButton) if button.text() == 'Registrar resultado').click()
        except Exception as exc:  # noqa: BLE001 - sin datos privados
            errors.append(type(exc).__name__)
            dialog.reject()
    QTimer.singleShot(0, fill)
    body = processing_dialog(window, donation)
    assert not errors and body['state'] == 'PROCESSED' and body['version'] == 3


def test_donations_list_does_not_offer_uuid_only_search():
    class Client:
        access = None
        def __init__(self): self.user = {'role': 'OPERATOR'}
    window = Window()
    window.client = Client()
    window.mode = 'donations'
    window.show_rows({'items': [], 'page': 1, 'total': 0})
    assert not window.search.isEnabled() and not window.search_button.isEnabled()
    window.close()
