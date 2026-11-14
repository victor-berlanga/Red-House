"""Formularios de receptor y solicitud con datos sintéticos, sin red."""

import os
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QLineEdit,
    QPushButton,
    QSpinBox,
)
from redhouse_desktop.app import STYLE, Window

app = QApplication.instance() or QApplication([])
app.setStyleSheet(STYLE)


def capture(dialog, name):
    if os.environ.get("DESKTOP_CAPTURE_DIR"):
        assert dialog.grab().save(str(Path(os.environ["DESKTOP_CAPTURE_DIR"]) / name))


def test_register_recipient_with_documented_values():
    window = Window()
    recorded = []
    window.secure_command = lambda *args: recorded.append(args)

    def inspect():
        dialog = app.activeModalWidget()
        fields = dialog.findChildren(QLineEdit)
        for widget, value in zip(
            fields, ("REC-001", "Persona sintética", "Estudios documentados")
        ):
            widget.setText(value)
        combos = dialog.findChildren(QComboBox)
        combos[0].setCurrentIndex(combos[0].findData("BLOOD"))
        combos[2].setCurrentIndex(combos[2].findData("O-"))
        app.processEvents()
        capture(dialog, "receptor-doble.png")
        next(
            x
            for x in dialog.findChildren(QPushButton)
            if x.text() == "Registrar receptor"
        ).click()

    QTimer.singleShot(0, inspect)
    window.recipient_form(None)
    assert len(recorded) == 1
    operation, target, body = recorded[0]
    assert operation == "recipient_create" and target is None
    assert (
        body["folio"] == "REC-001"
        and body["kind"] == "BLOOD"
        and "organ_type" not in body
    )
    window.close()


def test_edit_request_includes_version_and_confirmation():
    window = Window()
    recorded = []
    window.secure_command = lambda *args: recorded.append(args)
    request = {
        "id": "00000000-0000-4000-8000-000000000001",
        "can_edit": True,
        "kind": "BLOOD",
        "component": "RBC",
        "quantity": 1,
        "urgency": 2,
        "version": 4,
    }

    def inspect():
        dialog = app.activeModalWidget()
        dialog.findChild(QSpinBox).setValue(2)
        dialog.findChild(QLineEdit).setText("Corrección documentada")
        dialog.findChild(QCheckBox).setChecked(True)
        app.processEvents()
        capture(dialog, "solicitud-edicion-doble.png")
        next(
            x
            for x in dialog.findChildren(QPushButton)
            if x.text() == "Guardar corrección"
        ).click()

    QTimer.singleShot(0, inspect)
    window.request_edit_form(request, {})
    assert recorded[0][0] == "request_edit" and recorded[0][1] == request["id"]
    assert recorded[0][2]["version"] == 4 and recorded[0][2]["quantity"] == 2
    assert recorded[0][2]["human_confirmation"] == "true"
    window.close()


def test_cancel_requires_reason_and_version():
    window = Window()
    recorded = []
    window.secure_command = lambda *args: recorded.append(args)
    request = {
        "id": "00000000-0000-4000-8000-000000000001",
        "status": "OPEN",
        "version": 2,
    }

    def inspect():
        dialog = app.activeModalWidget()
        dialog.findChild(QLineEdit).setText("Cancelación documentada")
        dialog.findChild(QCheckBox).setChecked(True)
        app.processEvents()
        capture(dialog, "solicitud-cancelacion-doble.png")
        next(
            x
            for x in dialog.findChildren(QPushButton)
            if x.text() == "Confirmar cancelación"
        ).click()

    QTimer.singleShot(0, inspect)
    window.request_cancel_form(request)
    assert recorded[0][0] == "request_cancel" and recorded[0][2]["version"] == 2
    window.close()


def test_operator_can_list_but_cannot_modify_recipients():
    window = Window()
    window.client = type("Client", (), {"user": {"role": "OPERATOR"}, "access": None})()
    window.mode = "recipients"
    window.set_controls(True)
    assert window.areas.model().item(11).isEnabled()
    assert not window.recipient_create_button.isEnabled()
    assert not window.recipient_edit_button.isEnabled()
    assert not window.request_edit_button.isEnabled()
    assert not window.request_cancel_button.isEnabled()
    window.client = None
    window.close()


def test_changing_kind_clears_and_hides_previous_organ():
    window = Window()
    observed = []

    def inspect():
        dialog = app.activeModalWidget()
        kind, organ, *_ = dialog.findChildren(QComboBox)
        kind.setCurrentIndex(kind.findData("ORGAN"))
        organ.setCurrentIndex(organ.findData("KIDNEY"))
        assert organ.isVisible()
        kind.setCurrentIndex(kind.findData("BLOOD"))
        observed.append((organ.isVisible(), organ.currentData()))
        dialog.reject()

    QTimer.singleShot(0, inspect)
    window.recipient_form(None)
    assert observed == [(False, "")]
    window.close()
