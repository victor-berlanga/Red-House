"""Recorrido local del botón de reserva, sin red."""

from uuid import uuid4

from cryptography.fernet import Fernet
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QApplication,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
)

from redhouse_desktop.app import Window
from redhouse_desktop.journal import Journal


app = QApplication.instance() or QApplication([])


def test_reservation_button_prepares_and_sends_same_candidate(tmp_path, monkeypatch):
    class Keys:
        def __init__(self):
            self.key = Fernet.generate_key()

        def get(self, identifier, exists):
            return self.key

    class Client:
        user = {"role": "MEDICAL"}
        access = None

        def __init__(self):
            self.calls = []

        def authorized(self, service, path, operation, **kwargs):
            self.calls.append((operation, kwargs))
            return {
                "status": "PENDING",
                "operation_id": str(uuid4()),
                "reservation": None,
            }

    window = Window()
    window.client = Client()
    window.journal = Journal(
        tmp_path, "https://lab", str(uuid4()), str(uuid4()), Keys()
    )
    window.run = lambda fn, success, label: success(fn())
    monkeypatch.setattr(
        QMessageBox, "information", lambda *args, **kwargs: QMessageBox.Ok
    )
    evaluation = {
        "id": str(uuid4()),
        "candidates": [
            {
                "resource_id": str(uuid4()),
                "resource_folio": "UNIDAD-SINTETICA",
                "distance_km": 2,
                "travel_minutes": 5,
                "expires_at": "2030-01-01T00:00:00Z",
            }
        ],
    }
    candidate = evaluation["candidates"][0]
    evaluation["validity"] = {
        "candidates": [{"resource_id": candidate["resource_id"], "current": True}]
    }
    evaluation["reviews"] = [
        {"resource_id": candidate["resource_id"], "decision": "FAVORABLE"}
    ]

    def submit():
        modal = app.activeModalWidget()
        assert modal
        modal.findChild(QTableWidget).selectRow(0)
        modal.findChild(QLineEdit).setText("Reserva sintética documentada")
        next(
            button
            for button in modal.findChildren(QPushButton)
            if button.text() == "Reservar unidad"
        ).click()

    QTimer.singleShot(0, submit)
    window.evaluation_detail(evaluation)
    assert len(window.client.calls) == 1
    operation, kwargs = window.client.calls[0]
    record = window.journal.list()[0]
    assert operation == "reservation_create" and kwargs["key"] == record["key"]
    assert (
        kwargs["body"]["resource_id"] == candidate["resource_id"]
        and kwargs["body"]["evaluation_id"] == evaluation["id"]
    )
    assert record["status"] == "PENDING" and record["operation_id"]
    window.close()
