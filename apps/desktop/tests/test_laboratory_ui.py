"""Interacciones locales de captura y revisión sin servicio clínico."""

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
    user = {"role": "OPERATOR"}
    access = None


def test_result_uses_confirmed_documented_measurement():
    window = Window()
    window.client = Client()
    window.selected = lambda: {
        "id": "sample",
        "identifier": "MUESTRA-1",
        "status": "RECEIVED",
    }
    sent = []
    window.secure_command = lambda operation, identifier, body: sent.append((operation, body))

    def fill():
        modal = app.activeModalWidget()
        assert modal
        for field, value in zip(
            modal.findChildren(QLineEdit),
            ("ABO", "O", "Método", "Laboratorio", "Referencia"),
        ):
            field.setText(value)
        date = modal.findChild(QDateTimeEdit)
        date.setDateTime(QDateTime.fromString("2020-01-02T12:00:00Z", Qt.ISODate))
        modal.findChild(QCheckBox).setChecked(True)
        next(
            button
            for button in modal.findChildren(QPushButton)
            if button.text() == "Registrar resultado"
        ).click()

    QTimer.singleShot(0, fill)
    window.capture_result()
    assert (
        sent[0][0] == "lab_result_create"
        and sent[0][1]["measured_at"] == "2020-01-02T12:00:00Z"
    )
    window.close()


def test_medical_review_requires_explicit_decision():
    window = Window()
    window.client = Client()
    window.client.user = {"role": "MEDICAL"}
    window.selected = lambda: {
        "id": "result",
        "test_code": "ABO",
        "value": "O",
        "status": "CAPTURED",
        "version": 3,
    }
    sent = []
    window.secure_command = lambda operation, identifier, body: sent.append(
        (operation, identifier, body)
    )

    def fill():
        modal = app.activeModalWidget()
        assert modal
        choice = modal.findChild(QComboBox)
        assert choice.currentData() == ""
        choice.setCurrentIndex(choice.findData("REJECTED"))
        modal.findChild(QLineEdit).setText("Revisión documentada")
        next(
            button
            for button in modal.findChildren(QPushButton)
            if button.text() == "Registrar revisión"
        ).click()

    QTimer.singleShot(0, fill)
    window.review_result()
    assert (
        sent[0][0] == "lab_result_review"
        and sent[0][2]["decision"] == "REJECTED"
        and sent[0][2]["version"] == 3
    )
    window.close()


def test_unreceived_sample_and_operator_review_are_blocked():
    window = Window()
    window.client = Client()
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
