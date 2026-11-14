"""Consulta Qt/XML de cobertura con servicios efímeros y datos sintéticos."""

import os
import time
from pathlib import Path

import pytest
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QTableWidget
from redhouse_desktop.app import STYLE, Window
from redhouse_desktop.client import ApiError, Client
from test_real_lab import (
    gateway as gateway,  # noqa: PLC0414 - fixture compartido de pytest
)
from tests.conftest import (
    platform as platform,  # noqa: PLC0414 - fixture compartido de pytest
)
from tests.helpers import evaluation, recipient_request, resource


def wait_until(predicate):
    deadline = time.monotonic() + 40
    while time.monotonic() < deadline:
        QApplication.processEvents()
        if predicate():
            return True
        time.sleep(0.02)
    return False


def test_coverage_xml_roles_unit_and_empty(platform, gateway, monkeypatch):
    unit = resource(platform)
    _, request = recipient_request(platform, quantity=2)
    reviewed = evaluation(platform, request, [unit])
    proposal = platform.ok(
        "priorizacion_geografia",
        "POST",
        "/api/v1/allocation-proposals",
        data={"evaluation_ids": [reviewed["id"]]},
    )
    _, empty_request = recipient_request(platform)
    unreviewed = evaluation(platform, empty_request, [])
    empty = platform.ok(
        "priorizacion_geografia",
        "POST",
        "/api/v1/allocation-proposals",
        data={"evaluation_ids": [unreviewed["id"]]},
    )
    assert proposal["matched_count"] == 1 and proposal["slot_count"] == 2
    assert empty["matched_count"] == 0

    app = QApplication.instance() or QApplication([])
    app.setStyleSheet(STYLE)
    output = Path(os.environ["DESKTOP_CAPTURE_DIR"])
    output.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("REDHOUSE_BASE_URL", gateway)
    client = Client(gateway)
    client.login("medical2", platform.env.state["password"], "")
    medical = client.authorized(
        "priorizacion-geografia",
        "/api/v1/allocation-proposals/" + proposal["id"],
        "proposal_detail",
    )
    assert medical["result"][0]["resource_id"] == unit["id"]
    assert medical["snapshots"][request["id"]]["evaluation_id"] == reviewed["id"]
    # La unidad pertenece a otra institución: el médico no recibe su detalle.
    with pytest.raises(ApiError) as denied:
        client.authorized(
            "inventario", "/api/v1/resources/" + unit["id"], "resource_detail"
        )
    assert denied.value.status == 403
    medical_window = Window()
    medical_window.client = client
    evaluations = []
    show_evaluation = medical_window.evaluation_detail

    def observe_evaluation(value):
        evaluations.append(value)

        def close_evaluation():
            dialog = app.activeModalWidget()
            assert dialog.grab().save(str(output / "evaluacion-medica-qt.png"))
            dialog.reject()

        QTimer.singleShot(0, close_evaluation)
        show_evaluation(value)

    medical_window.evaluation_detail = observe_evaluation

    def inspect_medical():
        dialog = app.activeModalWidget()
        dialog.findChild(QTableWidget).selectRow(0)
        app.processEvents()
        buttons = {b.text(): b for b in dialog.findChildren(QPushButton)}
        assert buttons["Abrir evaluación"].isEnabled()
        assert dialog.grab().save(str(output / "cobertura-medica-qt.png"))
        buttons["Abrir evaluación"].click()

    QTimer.singleShot(0, inspect_medical)
    medical_window.coverage_detail(medical)
    assert wait_until(lambda: bool(evaluations) and not medical_window.busy)
    assert evaluations[0]["id"] == reviewed["id"]
    medical_window.client = None
    medical_window.close()
    client.logout()

    coordinator = Client(gateway)
    coordinator.login("coordinator1", platform.env.state["password"], "")
    regional = coordinator.authorized(
        "priorizacion-geografia",
        "/api/v1/allocation-proposals/" + proposal["id"],
        "proposal_detail",
    )
    assert regional["snapshots"] == {}
    observed_unit = coordinator.authorized(
        "inventario", "/api/v1/resources/" + unit["id"], "resource_detail"
    )
    assert (
        observed_unit["folio"] == unit["folio"]
        and observed_unit["status"] == unit["status"]
    )
    blank = coordinator.authorized(
        "priorizacion-geografia",
        "/api/v1/allocation-proposals/" + empty["id"],
        "proposal_detail",
    )
    assert blank["result"] == []
    window = Window()
    window.client = coordinator
    captured = []
    show_detail = window.detail

    def observe_detail(value):
        captured.append(value)

        def close_detail():
            dialog = app.activeModalWidget()
            assert any(
                unit["folio"] in label.text() for label in dialog.findChildren(QLabel)
            )
            assert dialog.grab().save(str(output / "unidad-coordinacion-qt.png"))
            dialog.reject()

        QTimer.singleShot(0, close_detail)
        show_detail(value)

    window.detail = observe_detail

    def select_unit():
        dialog = app.activeModalWidget()
        table = dialog.findChild(QTableWidget)
        table.selectRow(0)
        app.processEvents()
        buttons = {b.text(): b for b in dialog.findChildren(QPushButton)}
        assert not buttons["Abrir evaluación"].isVisible()
        assert dialog.grab().save(str(output / "cobertura-coordinacion-qt.png"))
        buttons["Consultar unidad"].click()

    QTimer.singleShot(0, select_unit)
    window.coverage_detail(regional)
    assert wait_until(lambda: bool(captured) and not window.busy)
    assert (
        captured[0]["folio"] == unit["folio"]
        and captured[0]["status"] == unit["status"]
    )

    def inspect_empty():
        dialog = app.activeModalWidget()
        assert any(
            "No hay unidades propuestas" in x.text()
            for x in dialog.findChildren(QLabel)
        )
        assert dialog.grab().save(str(output / "cobertura-vacia-qt.png"))
        dialog.reject()

    QTimer.singleShot(0, inspect_empty)
    window.coverage_detail(blank)
    coordinator.logout()
    window.client = None
    window.close()
