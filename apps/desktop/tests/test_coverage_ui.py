"""Presentación de cobertura con proyecciones sintéticas y sin red."""

import os
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QTableWidget
from redhouse_desktop.app import STYLE, Window

app = QApplication.instance() or QApplication([])
app.setStyleSheet(STYLE)
REQUEST = "00000000-0000-4000-8000-000000000001"
RESOURCE = "00000000-0000-4000-8000-000000000002"
EVALUATION = "00000000-0000-4000-8000-000000000003"


def test_coverage_selection_and_authorized_evaluation():
    window = Window()
    window.client = type("Client", (), {"user": {"role": "MEDICAL"}, "access": None})()
    calls = []
    window.run = lambda work, callback, status: calls.append(status)
    item = {
        "slot_count": 2,
        "matched_count": 1,
        "algorithm_version": "COVERAGE-HK-1.0",
        "created_at": "2030-01-01T12:00:00Z",
        "result": [{"request_id": REQUEST, "resource_id": RESOURCE}],
        "snapshots": {REQUEST: {"evaluation_id": EVALUATION}},
    }

    def inspect():
        dialog = app.activeModalWidget()
        table = dialog.findChild(QTableWidget)
        buttons = {b.text(): b for b in dialog.findChildren(QPushButton)}
        assert not buttons["Consultar unidad"].isEnabled()
        assert not buttons["Abrir evaluación"].isEnabled()
        table.selectRow(0)
        app.processEvents()
        assert buttons["Consultar unidad"].isEnabled()
        assert buttons["Abrir evaluación"].isEnabled()
        assert table.item(0, 0).text() == "Solicitud 1"
        assert RESOURCE not in table.item(0, 1).text()
        if os.environ.get("DESKTOP_CAPTURE_DIR"):
            dialog.grab().save(
                str(Path(os.environ["DESKTOP_CAPTURE_DIR"]) / "cobertura-doble.png")
            )
        buttons["Abrir evaluación"].click()

    QTimer.singleShot(0, inspect)
    window.coverage_detail(item)
    assert calls == ["Consultando evaluación…"]
    window.close()


def test_coverage_empty_and_coordinator_scope():
    window = Window()
    window.client = type(
        "Client", (), {"user": {"role": "COORDINATOR"}, "access": None}
    )()

    def inspect():
        dialog = app.activeModalWidget()
        assert any(
            "No hay unidades propuestas" in x.text()
            for x in dialog.findChildren(QLabel)
        )
        buttons = {b.text(): b for b in dialog.findChildren(QPushButton)}
        assert not buttons["Consultar unidad"].isEnabled()
        assert not buttons["Abrir evaluación"].isVisible()
        dialog.reject()

    QTimer.singleShot(0, inspect)
    window.coverage_detail(
        {"slot_count": 1, "matched_count": 0, "result": [], "snapshots": {}}
    )
    window.close()


def test_invalid_proposal_is_rejected():
    window = Window()
    window.coverage_detail(
        {
            "slot_count": 1,
            "matched_count": 1,
            "result": [{"request_id": "../", "resource_id": RESOURCE}],
        }
    )
    assert "No se pudo mostrar" in window.status.text()
    window.close()
