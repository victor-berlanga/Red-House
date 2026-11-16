"""Formularios de calidad con respuestas sintéticas, sin servicios."""
import os
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QApplication, QCheckBox, QLabel, QLineEdit, QPushButton, QTableWidget
import redhouse_desktop.app as desktop
from redhouse_desktop.resource_quality import quality_dialog

app = QApplication.instance() or QApplication([])
app.setStyleSheet(desktop.STYLE)


def test_profile_binding_disables_other_products_and_preserves_cold_controls():
    tenant, user, profile, equipment, cold = [str(uuid4()) for _ in range(5)]
    resource = {'id': str(uuid4()), 'folio': 'UNIT-TEST', 'component': 'RBC', 'kind': 'BLOOD', 'blood_group': 'O-', 'version': 2}
    class Client:
        def __init__(self): self.user = {'id': user, 'tenant_id': tenant, 'role': 'MEDICAL'}
        def authorized(self, *_args, **_kwargs):
            return {'page': 1, 'total': 2, 'items': [
                {'id': profile, 'name': 'Perfil sintético', 'kind': 'BLOOD', 'component': 'RBC', 'version': 1},
                {'id': str(uuid4()), 'name': 'Otro perfil', 'kind': 'BLOOD', 'component': 'PLASMA', 'version': 1}]}
    window = desktop.Window(); window.client = Client(); errors = []
    def fill():
        dialog = app.activeModalWidget()
        if not dialog or not dialog.findChild(QTableWidget).rowCount(): QTimer.singleShot(20, fill); return
        try:
            table = dialog.findChild(QTableWidget)
            assert not table.item(1, 0).flags() & Qt.ItemIsSelectable
            assert table.item(0, 1).text() == 'Eritrocitos'
            table.selectRow(0); dialog.findChild(QLineEdit).setText('Perfil documentado'); dialog.findChild(QCheckBox).setChecked(True)
            app.processEvents(); assert dialog.grab().save(str(Path(os.environ['DESKTOP_CAPTURE_DIR']) / 'perfil-doble.png'))
            next(button for button in dialog.findChildren(QPushButton) if button.text() == 'Vincular perfil').click()
        except Exception as exc:  # noqa: BLE001 - no incluir datos en evidencia
            errors.append(type(exc).__name__); dialog.reject()
    QTimer.singleShot(0, fill)
    body = quality_dialog(window, resource, {'cold_equipment_id': equipment, 'cold_profile_id': cold}, desktop.Work, desktop.label)
    assert not errors and body['lab_profile_id'] == profile
    assert body['cold_equipment_id'] == equipment and body['cold_profile_id'] == cold


def test_release_shows_missing_and_blocks_unready_unit():
    window = desktop.Window(); window.client = SimpleNamespace(user={'id': str(uuid4()), 'tenant_id': str(uuid4()), 'role': 'MEDICAL'})
    resource = {'id': str(uuid4()), 'folio': 'UNIT-TEST', 'component': 'RBC', 'kind': 'BLOOD', 'blood_group': 'O-', 'version': 2}
    controls = {'_profile': {'name': 'Perfil sintético', 'synthetic': True}, '_completeness': {'complete': False, 'missing': ['ABO']}}
    def inspect():
        dialog = app.activeModalWidget()
        assert not next(button for button in dialog.findChildren(QPushButton) if button.text() == 'Liberar unidad').isEnabled()
        assert any('ABO' in label.text() and 'no autoriza uso clínico' in label.text() for label in dialog.findChildren(QLabel))
        assert dialog.grab().save(str(Path(os.environ['DESKTOP_CAPTURE_DIR']) / 'pendiente-doble.png')); dialog.reject()
    QTimer.singleShot(0, inspect)
    assert quality_dialog(window, resource, controls, desktop.Work, desktop.label, release=True) is None


def test_session_change_after_modal_does_not_prepare_command(monkeypatch):
    tenant, user = str(uuid4()), str(uuid4())
    resource = {'id': str(uuid4()), 'current_institution_id': tenant, 'status': 'QUARANTINE'}
    class Client:
        def __init__(self): self.user = {'id': user, 'tenant_id': tenant, 'role': 'MEDICAL'}
        def authorized(self, _service, path, *_args, **_kwargs):
            if path.endswith('/controls'): return {'id': resource['id']}
            return resource
    window = desktop.Window(); window.client = Client(); commands = []
    monkeypatch.setattr(window, 'selected', lambda: resource)
    monkeypatch.setattr(window, 'run', lambda work, success, _message: success(work()))
    monkeypatch.setattr(window, 'secure_command', lambda *args: commands.append(args))
    def replace(_window, _resource, _controls, _work, _display, **_kwargs):
        window.client = SimpleNamespace(user={'id': str(uuid4()), 'tenant_id': tenant, 'role': 'MEDICAL'})
        return {'version': 1}
    monkeypatch.setattr(desktop, 'quality_dialog', replace)
    window.resource_quality(False)
    assert not commands and 'sesión cambió' in window.status.text().lower()


def test_result_session_change_never_submits():
    tenant, user = str(uuid4()), str(uuid4())
    window = desktop.Window(); window.client = SimpleNamespace(user={'id': user, 'tenant_id': tenant, 'role': 'OPERATOR'})
    window.selected = lambda: {'id': str(uuid4()), 'identifier': 'MUESTRA-TEST', 'status': 'RECEIVED'}
    commands = []; window.secure_command = lambda *args: commands.append(args)
    def fill():
        dialog = app.activeModalWidget()
        for field, value in zip(dialog.findChildren(QLineEdit), ('ABO', 'O', 'Método', 'Laboratorio', 'Referencia')): field.setText(value)
        dialog.findChild(QCheckBox).setChecked(True)
        window.client = SimpleNamespace(user={'id': str(uuid4()), 'tenant_id': tenant, 'role': 'OPERATOR'})
        next(button for button in dialog.findChildren(QPushButton) if button.text() == 'Registrar resultado').click()
    QTimer.singleShot(0, fill); window.capture_result()
    assert not commands and 'sesión cambió' in window.status.text().lower()


def test_sample_response_after_session_change_is_not_shown():
    from threading import Event
    tenant, user = str(uuid4()), str(uuid4())
    gate = Event(); started = Event(); errors = []
    class Client:
        def __init__(self): self.user = {'id': user, 'tenant_id': tenant, 'role': 'OPERATOR'}
        def authorized(self, *_args, **_kwargs):
            started.set(); gate.wait(2)
            return {'page': 1, 'total': 1, 'items': [{'id': str(uuid4()), 'folio': 'NO-MOSTRAR', 'component': 'RBC', 'status': 'QUARANTINE'}]}
    window = desktop.Window(); window.client = Client()
    def change():
        if not started.is_set(): QTimer.singleShot(20, change); return
        window.client = SimpleNamespace(user={'id': str(uuid4()), 'tenant_id': tenant, 'role': 'OPERATOR'}); gate.set()
        QTimer.singleShot(200, inspect)
    def inspect():
        dialog = app.activeModalWidget()
        try:
            assert all(table.rowCount() == 0 for table in dialog.findChildren(QTableWidget))
            assert not next(button for button in dialog.findChildren(QPushButton) if button.text() == 'Registrar muestra').isEnabled()
        except Exception as exc: errors.append(type(exc).__name__)  # noqa: BLE001
        finally: dialog.reject()
    QTimer.singleShot(0, change); window.create_sample()
    window.pool.waitForDone(3000)
    assert not errors
