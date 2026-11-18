"""Interacciones locales de captura y revisión sin servicio clínico."""

from uuid import uuid4

from PySide6.QtCore import QDateTime, QTimer, Qt
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDateTimeEdit,
    QLineEdit,
    QPushButton,
)

from redhouse_desktop.app import Window


app = QApplication.instance() or QApplication([])


class Client:
    # Contrato de OperationContext: usuario con ámbito completo y sesión identificada.
    access = None

    def __init__(self, role="OPERATOR", detail=None):
        self.user = {"id": str(uuid4()), "tenant_id": str(uuid4()), "role": role}
        self.session_id = str(uuid4())
        self.detail = detail or {}

    def authorized(self, service, path, operation, **kwargs):
        # Catálogo de referencia vacío y detalle del resultado de la propia institución.
        if operation == "reference_sources":
            return {"catalogues": []}
        return {**self.detail, "tenant_id": self.user["tenant_id"]}


def signed_in(role="OPERATOR", detail=None):
    window = Window()
    window.client = Client(role, detail)
    window.journal = object()
    window.run = lambda fn, success, label, failure=None: success(fn())
    return window


def test_result_uses_confirmed_documented_measurement():
    window = signed_in()
    window.selected = lambda: {
        "id": "sample",
        "identifier": "MUESTRA-1",
        "status": "RECEIVED",
    }
    sent, errors = [], []
    window.secure_command = lambda operation, identifier, body, **kwargs: sent.append((operation, body))

    def fill():
        modal = app.activeModalWidget()
        if not modal:
            QTimer.singleShot(20, fill)
            return
        try:
            modal.findChild(QLineEdit, "result_code").setText("ABO")
            state = modal.findChild(QComboBox, "result_state")
            state.setCurrentIndex(state.findData("REPORTED"))
            for key, value in (("value", "O"), ("method", "Método"), ("laboratory", "Laboratorio"), ("reference", "Referencia")):
                modal.findChild(QLineEdit, "result_" + key).setText(value)
            date = modal.findChild(QDateTimeEdit, "measured_time")
            date.setDateTime(QDateTime.fromString("2020-01-02T12:00:00Z", Qt.ISODate))
            modal.findChild(QCheckBox, "confirm_measured").setChecked(True)
            next(
                button
                for button in modal.findChildren(QPushButton)
                if button.text() == "Guardar resultado"
            ).click()
        except Exception as exc:  # noqa: BLE001 - sin datos privados
            errors.append(type(exc).__name__)
            modal.reject()

    QTimer.singleShot(0, fill)
    window.capture_result()
    assert not errors
    assert (
        sent[0][0] == "lab_result_create"
        and sent[0][1]["measured_at"] == "2020-01-02T12:00:00Z"
        and sent[0][1]["result_state"] == "REPORTED"
        and sent[0][1]["value"] == "O"
    )
    window.close()


def test_medical_review_requires_explicit_decision():
    window = signed_in("MEDICAL", {
        "id": "result",
        "test_code": "ABO",
        "value": "O",
        "status": "CAPTURED",
        "version": 3,
    })
    window.selected = lambda: {"id": "result", "status": "CAPTURED", "version": 3}
    sent, errors = [], []
    window.secure_command = lambda operation, identifier, body: sent.append(
        (operation, identifier, body)
    )

    def fill():
        modal = app.activeModalWidget()
        if not modal:
            QTimer.singleShot(20, fill)
            return
        try:
            choice = modal.findChild(QComboBox)
            assert choice.currentData() == ""
            choice.setCurrentIndex(choice.findData("REJECTED"))
            modal.findChild(QLineEdit).setText("Revisión documentada")
            next(
                button
                for button in modal.findChildren(QPushButton)
                if button.text() == "Registrar revisión"
            ).click()
        except Exception as exc:  # noqa: BLE001 - sin datos privados
            errors.append(type(exc).__name__)
            modal.reject()

    QTimer.singleShot(0, fill)
    window.review_result()
    assert not errors
    assert (
        sent[0][0] == "lab_result_review"
        and sent[0][2]["decision"] == "REJECTED"
        and sent[0][2]["version"] == 3
    )
    window.close()


def test_unreceived_sample_and_operator_review_are_blocked():
    window = signed_in()
    window.selected = lambda: {
        "id": "sample",
        "identifier": "MUESTRA-1",
        "status": "REQUESTED",
    }
    window.capture_result()
    assert "muestra recibida" in window.status.text()
    window.selected = lambda: {"id": "result", "status": "CAPTURED", "version": 1}
    window.review_result()
    assert "personal médico" in window.status.text()
    window.close()
