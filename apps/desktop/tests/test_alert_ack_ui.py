"""Acuse de aviso con doble de sesión, sin servicios."""
import os
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QMessageBox
from redhouse_desktop.app import STYLE, Window

app = QApplication.instance() or QApplication([])
app.setStyleSheet(STYLE)


def account(tenant, actor):
    return SimpleNamespace(user={'id': actor, 'tenant_id': tenant, 'role': 'OPERATOR'})


def choose(button_name, errors, before=None, capture=False):
    dialog = app.activeModalWidget()
    if not isinstance(dialog, QMessageBox): QTimer.singleShot(20, lambda: choose(button_name, errors, before, capture)); return
    try:
        buttons = {button.text(): button for button in dialog.buttons()}
        assert set(buttons) == {'Confirmar', 'Cancelar'}
        assert dialog.defaultButton() is buttons['Cancelar']
        if capture:
            app.processEvents()
            assert dialog.grab().save(str(Path(os.environ['DESKTOP_CAPTURE_DIR']) / 'confirmacion-es.png'))
        if before: before()
        buttons[button_name].click()
    except Exception as exc:  # noqa: BLE001 - nunca incluir datos privados
        errors.append(type(exc).__name__); dialog.reject()


def test_acknowledgement_uses_secure_command(monkeypatch):
    tenant, actor, identifier = (str(uuid4()) for _ in range(3))
    window = Window(); window.client = account(tenant, actor)
    monkeypatch.setattr(window, 'selected', lambda: {'id': identifier, 'status': 'OPEN'})
    commands, errors = [], []; monkeypatch.setattr(window, 'secure_command', lambda *args: commands.append(args))
    QTimer.singleShot(0, lambda: choose('Confirmar', errors, capture=True)); window.acknowledge()
    assert not errors and commands == [('alert_ack', identifier, None)]


def test_acknowledgement_rejects_session_change(monkeypatch):
    tenant, actor = str(uuid4()), str(uuid4())
    window = Window(); window.client = account(tenant, actor)
    monkeypatch.setattr(window, 'selected', lambda: {'id': str(uuid4()), 'status': 'OPEN'})
    commands, errors = [], []; monkeypatch.setattr(window, 'secure_command', lambda *args: commands.append(args))
    QTimer.singleShot(0, lambda: choose('Confirmar', errors, before=lambda: setattr(window, 'client', account(tenant, str(uuid4())))))
    window.acknowledge()
    assert not errors and not commands and 'sesión cambió' in window.status.text().lower()


def test_cancelling_acknowledgement_sends_nothing(monkeypatch):
    tenant, actor = str(uuid4()), str(uuid4())
    window = Window(); window.client = account(tenant, actor)
    monkeypatch.setattr(window, 'selected', lambda: {'id': str(uuid4()), 'status': 'OPEN'})
    commands, errors = [], []; monkeypatch.setattr(window, 'secure_command', lambda *args: commands.append(args))
    QTimer.singleShot(0, lambda: choose('Cancelar', errors)); window.acknowledge()
    assert not errors and not commands
