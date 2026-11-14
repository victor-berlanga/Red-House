"""Registro de muestra con selecciones y respuestas sintéticas, sin red."""

import os
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QLineEdit,
    QPushButton,
    QTableWidget,
)
from redhouse_desktop.app import STYLE, Window

app = QApplication.instance() or QApplication([])
app.setStyleSheet(STYLE)


def test_sample_form_uses_selected_unit_profile_and_documented_time():
    window = Window()
    calls = []
    errors = []

    class Client:
        access = None

        def __init__(self):
            self.user = {"role": "OPERATOR"}

        def authorized(self, service, path, operation, **kwargs):
            if operation == "resources_list":
                rows = [
                    {
                        "id": "00000000-0000-4000-8000-000000000001",
                        "folio": "UNIDAD-01",
                        "component": "RBC",
                        "status": "QUARANTINE",
                    }
                ]
            elif operation == "lab_profiles_list":
                rows = [
                    {
                        "id": "00000000-0000-4000-8000-000000000002",
                        "name": "Perfil documentado",
                        "component": "RBC",
                        "version": 1,
                    }
                ]
            else:
                raise AssertionError(operation)
            return {"items": rows, "page": 1, "page_size": 20, "total": 1}

    window.client = Client()
    window.secure_command = lambda operation, identifier, body: calls.append(
        (operation, identifier, body)
    )
    attempts = [0]

    def inspect():
        dialog = app.activeModalWidget()
        tables = dialog.findChildren(QTableWidget)
        if any(table.rowCount() != 1 for table in tables):
            attempts[0] += 1
            if attempts[0] < 200:
                QTimer.singleShot(20, inspect)
                return
            errors.append("Consulta no terminó")
            dialog.reject()
            return
        try:
            for table in tables:
                table.selectRow(0)
            app.processEvents()
            inputs = dialog.findChildren(QLineEdit)
            next(field for field in inputs if field.maxLength() == 200).setText(
                "MUESTRA-01"
            )
            dialog.findChild(QCheckBox).setChecked(True)
            if os.environ.get("DESKTOP_CAPTURE_DIR"):
                assert dialog.grab().save(
                    str(Path(os.environ["DESKTOP_CAPTURE_DIR"]) / "muestra-doble.png")
                )
            next(
                button
                for button in dialog.findChildren(QPushButton)
                if button.text() == "Registrar muestra"
            ).click()
        except Exception as exc:  # noqa: BLE001 - solo clase, sin datos privados
            errors.append(type(exc).__name__)
            dialog.reject()

    QTimer.singleShot(0, inspect)
    window.create_sample()
    assert not errors
    assert len(calls) == 1
    operation, target, body = calls[0]
    assert operation == "lab_sample_create" and target is None
    assert body["resource_id"].endswith("0001") and body["profile_id"].endswith("0002")
    assert body["identifier"] == "MUESTRA-01" and body["collected_at"].endswith("Z")
    window.client = None
    window.close()
