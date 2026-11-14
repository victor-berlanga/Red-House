"""Interacción de evaluación con proyecciones sintéticas del contrato."""

import os
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
)

from redhouse_desktop.app import Window


app = QApplication.instance() or QApplication([])


def test_candidate_actions_follow_server_validity():
    window = Window()
    observed = []
    evaluation = {
        "id": "evaluacion",
        "snapshot": {"clinical_notice": "Filtro ilustrativo; requiere dictamen."},
        "candidates": [
            {
                "resource_id": "recurso-a",
                "resource_folio": "UNIDAD-A",
                "distance_km": 2,
                "travel_minutes": 5,
                "expires_at": "2030-01-01T00:00:00Z",
                "explanation": "Explicación del candidato A",
            },
            {
                "resource_id": "recurso-b",
                "resource_folio": "UNIDAD-B",
                "distance_km": 3,
                "travel_minutes": 6,
                "expires_at": "2030-01-01T00:00:00Z",
                "explanation": "Explicación del candidato B",
            },
        ],
        "validity": {
            "candidates": [
                {"resource_id": "recurso-a", "current": True},
                {"resource_id": "recurso-b", "current": False},
            ]
        },
    }

    def inspect():
        modal = app.activeModalWidget()
        assert modal
        table = modal.findChild(QTableWidget)
        buttons = {button.text(): button for button in modal.findChildren(QPushButton)}
        assert not buttons["Dictamen favorable"].isEnabled()
        table.selectRow(0)
        app.processEvents()
        observed.append(buttons["Dictamen favorable"].isEnabled())
        assert not buttons["Reservar unidad"].isEnabled()
        assert any(
            "primero registra un dictamen favorable" in label.text()
            for label in modal.findChildren(QLabel)
        )
        if os.environ.get("DESKTOP_CAPTURE_DIR"):
            modal.grab().save(
                str(Path(os.environ["DESKTOP_CAPTURE_DIR"]) / "sin-dictamen-doble.png")
            )
        table.selectRow(1)
        app.processEvents()
        observed.append(buttons["Dictamen favorable"].isEnabled())
        assert any(
            "vigencia no está confirmada" in label.text()
            for label in modal.findChildren(QLabel)
        )
        modal.reject()

    QTimer.singleShot(0, inspect)
    window.evaluation_detail(evaluation)
    assert observed == [True, False]
    window.close()


def test_reservation_requires_prior_favorable_review():
    window = Window()
    observed = []
    evaluation = {
        "id": "evaluacion",
        "candidates": [
            {
                "resource_id": "recurso-a",
                "resource_folio": "UNIDAD-A",
                "distance_km": 2,
                "travel_minutes": 5,
                "expires_at": "2030-01-01T00:00:00Z",
            }
        ],
        "validity": {"candidates": [{"resource_id": "recurso-a", "current": True}]},
        "reviews": [{"resource_id": "recurso-a", "decision": "FAVORABLE"}],
    }

    def inspect():
        modal = app.activeModalWidget()
        assert modal
        modal.findChild(QTableWidget).selectRow(0)
        app.processEvents()
        buttons = {button.text(): button for button in modal.findChildren(QPushButton)}
        assert not buttons["Dictamen favorable"].isEnabled()
        assert not buttons["Dictamen desfavorable"].isEnabled()
        assert any(
            "Dictamen favorable registrado" in label.text()
            for label in modal.findChildren(QLabel)
        )
        if os.environ.get("DESKTOP_CAPTURE_DIR"):
            modal.grab().save(
                str(
                    Path(os.environ["DESKTOP_CAPTURE_DIR"])
                    / "dictamen-favorable-doble.png"
                )
            )
        observed.append(
            next(
                button
                for button in modal.findChildren(QPushButton)
                if button.text() == "Reservar unidad"
            ).isEnabled()
        )
        modal.reject()

    QTimer.singleShot(0, inspect)
    window.evaluation_detail(evaluation)
    assert observed == [True]
    window.close()


def test_recorded_unfavorable_review_cannot_be_changed_or_reserved():
    window = Window()
    evaluation = {
        "id": "evaluacion",
        "candidates": [{"resource_id": "recurso-a", "resource_folio": "UNIDAD-A"}],
        "validity": {"candidates": [{"resource_id": "recurso-a", "current": True}]},
        "reviews": [{"resource_id": "recurso-a", "decision": "UNFAVORABLE"}],
    }

    def inspect():
        modal = app.activeModalWidget()
        modal.findChild(QTableWidget).selectRow(0)
        app.processEvents()
        buttons = {button.text(): button for button in modal.findChildren(QPushButton)}
        assert all(
            not buttons[name].isEnabled()
            for name in (
                "Dictamen favorable",
                "Dictamen desfavorable",
                "Reservar unidad",
            )
        )
        assert any(
            "Dictamen desfavorable registrado" in label.text()
            for label in modal.findChildren(QLabel)
        )
        modal.reject()

    QTimer.singleShot(0, inspect)
    window.evaluation_detail(evaluation)
    window.close()


def test_new_evaluation_fetches_validity_before_opening(monkeypatch):
    window = Window()
    seen = []

    class Client:
        access = None

        def authorized(self, service, path, operation, **kwargs):
            seen.append((service, path, operation))
            return {"id": "evaluation", "validity": {"current": True}, "candidates": []}

    window.client = Client()
    window.selected = lambda: {"id": "request"}
    window.durable = lambda *args: {"id": "evaluation"}
    window.run = lambda fn, success, label: success(fn())
    window.evaluation_detail = lambda value: seen.append(value)
    monkeypatch.setattr(
        QMessageBox, "question", lambda *args, **kwargs: QMessageBox.Yes
    )
    window.evaluate_request()
    assert seen[0] == (
        "compatibilidad",
        "/api/v1/evaluations/evaluation",
        "evaluation_detail",
    )
    assert seen[1]["validity"]["current"] is True
    window.close()
