"""Formulario Qt de derivados con datos sintéticos."""
import os
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDateTimeEdit,
    QLineEdit,
    QPushButton,
)
from redhouse_desktop.app import STYLE, Window
from redhouse_desktop.fractionation import fractionation_dialog

app = QApplication.instance() or QApplication([])
app.setStyleSheet(STYLE)


def test_fractionation_requires_documented_product_and_expiry():
    window = Window()
    errors = []
    def choose():
        dialog = app.activeModalWidget()
        if not dialog: QTimer.singleShot(20, choose); return
        try:
            next(x for x in dialog.findChildren(QLineEdit) if x.maxLength() == 30).setText('CHILD-01')
            dialog.findChild(QComboBox).setCurrentIndex(1)
            date = dialog.findChild(QDateTimeEdit)
            date.setDateTime(date.dateTime().addDays(1))
            next(x for x in dialog.findChildren(QLineEdit) if x.maxLength() == 1000).setText('Procesamiento documentado')
            dialog.findChild(QCheckBox).setChecked(True)
            if os.environ.get('DESKTOP_CAPTURE_DIR'):
                assert dialog.grab().save(str(Path(os.environ['DESKTOP_CAPTURE_DIR']) / 'derivados-doble.png'))
            next(x for x in dialog.findChildren(QPushButton) if x.text() == 'Registrar derivados').click()
        except Exception as exc:  # noqa: BLE001 - sin datos privados
            errors.append(type(exc).__name__)
            dialog.reject()
    QTimer.singleShot(0, choose)
    body = fractionation_dialog(window, {'folio': 'PARENT-01', 'version': 2})
    assert not errors and body['version'] == 2 and body['human_confirmation'] == 'true'
    assert body['children'][0]['folio'] == 'CHILD-01' and body['children'][0]['component'] == 'RBC'


def test_session_replaced_after_modal_never_prepares_command(monkeypatch):
    from types import SimpleNamespace
    from uuid import uuid4

    import redhouse_desktop.app as desktop

    resource = {'id': str(uuid4()), 'status': 'QUARANTINE', 'kind': 'BLOOD', 'donation_id': str(uuid4())}
    class Client:
        def __init__(self):
            self.user = {'id': str(uuid4()), 'tenant_id': str(uuid4()), 'role': 'OPERATOR'}
            self.session_id = str(uuid4())
        def authorized(self, *_args, **_kwargs): return resource
    window = Window()
    window.client = Client()
    window.journal = object()
    calls = []
    monkeypatch.setattr(window, 'selected', lambda: resource)
    monkeypatch.setattr(window, 'run', lambda work, success, _message, _failure=None: success(work()))
    monkeypatch.setattr(window, 'secure_command', lambda *args: calls.append(args))
    def replace_session(_window, _resource):
        window.client = SimpleNamespace(user={'id': str(uuid4()), 'tenant_id': str(uuid4()), 'role': 'OPERATOR'}, session_id=str(uuid4()))
        return {'children': []}
    monkeypatch.setattr(desktop, 'fractionation_dialog', replace_session)
    window.fractionate_resource()
    assert not calls and 'sesión cambió' in window.status.text().lower()


def test_two_derivatives_remain_reachable_in_scroll_area():
    from PySide6.QtWidgets import QScrollArea

    window = Window()
    errors = []
    def fill():
        dialog = app.activeModalWidget()
        if not dialog: QTimer.singleShot(20, fill); return
        try:
            next(x for x in dialog.findChildren(QPushButton) if x.text() == 'Agregar derivado').click()
            folios = [x for x in dialog.findChildren(QLineEdit) if x.maxLength() == 30]
            for i, field in enumerate(folios): field.setText('CHILD-0' + str(i + 1))
            for combo in dialog.findChildren(QComboBox): combo.setCurrentIndex(1)
            for date in dialog.findChildren(QDateTimeEdit): date.setDateTime(date.dateTime().addDays(1))
            next(x for x in dialog.findChildren(QLineEdit) if x.maxLength() == 1000).setText('Procesamiento documentado')
            dialog.findChild(QCheckBox).setChecked(True)
            app.processEvents()
            # Las capturas son opcionales: el CI no define DESKTOP_CAPTURE_DIR.
            output = os.environ.get('DESKTOP_CAPTURE_DIR')
            if output: assert dialog.grab().save(str(Path(output) / 'derivados-primero.png'))
            scroll = dialog.findChild(QScrollArea)
            scroll.ensureWidgetVisible(dialog.findChildren(QDateTimeEdit)[1])
            app.processEvents()
            assert scroll.verticalScrollBar().value() > 0
            if output: assert dialog.grab().save(str(Path(output) / 'derivados-segundo.png'))
            next(x for x in dialog.findChildren(QPushButton) if x.text() == 'Registrar derivados').click()
        except Exception as exc:  # noqa: BLE001 - sin datos privados
            errors.append(type(exc).__name__)
            dialog.reject()
    QTimer.singleShot(0, fill)
    body = fractionation_dialog(window, {'folio': 'PARENT-01', 'version': 2})
    assert not errors and len(body['children']) == 2
