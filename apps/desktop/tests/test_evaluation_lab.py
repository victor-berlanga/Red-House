"""Evaluación y dictamen Qt/XML con datos sintéticos y auditoría aislada."""

import os
from pathlib import Path
import uuid

from cryptography.fernet import Fernet
from psycopg.rows import dict_row
from PySide6.QtCore import QTimer
from PySide6.QtTest import QTest
from PySide6.QtWidgets import (
    QApplication,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
)
import pytest

from tests.conftest import platform
from tests.helpers import recipient_request, resource, route
from test_real_lab import gateway
from redhouse_desktop.client import ApiError, Client
from redhouse_desktop.journal import Journal
import redhouse_desktop.app as desktop


def wait_until(predicate):
    for _ in range(2000):
        QTest.qWait(20)
        if predicate():
            return True
    return False


def test_medical_evaluation_review_and_stale_candidate(
    platform, gateway, monkeypatch, tmp_path
):
    unit = resource(platform)
    _, request = recipient_request(platform)
    route(platform)

    class Keys:
        def __init__(self):
            self.key = Fernet.generate_key()

        def get(self, identifier, exists):
            return self.key

    keys = Keys()
    monkeypatch.setattr(
        desktop,
        "Journal",
        lambda _root, base, user, tenant: Journal(tmp_path, base, user, tenant, keys),
    )
    monkeypatch.setenv("REDHOUSE_BASE_URL", gateway)
    monkeypatch.setattr(
        QMessageBox, "question", lambda *args, **kwargs: QMessageBox.Yes
    )
    app = QApplication.instance() or QApplication([])
    app.setStyleSheet(desktop.STYLE)
    doctor = desktop.Window()
    doctor.show()
    doctor.username.setText("medical2")
    doctor.password.setText(platform.env.state["password"])
    doctor.login()
    assert wait_until(lambda: doctor.stack.currentIndex() == 1 and not doctor.busy)
    doctor.switch("requests")
    assert wait_until(
        lambda: (
            not doctor.busy and any(row["id"] == request["id"] for row in doctor.rows)
        )
    )
    doctor.table.selectRow(
        next(i for i, row in enumerate(doctor.rows) if row["id"] == request["id"])
    )
    out = Path(os.environ["DESKTOP_CAPTURE_DIR"])
    out.mkdir(parents=True, exist_ok=True)
    selected = []

    def review():
        modal = QApplication.activeModalWidget()
        if not modal:
            QTimer.singleShot(50, review)
            return
        table = modal.findChild(QTableWidget)
        assert table is not None
        row = next(
            i
            for i in range(table.rowCount())
            if table.item(i, 0).text() == unit["folio"]
        )
        table.selectRow(row)
        modal.findChild(QLineEdit).setText("Dictamen sintético documentado")
        button = next(
            button
            for button in modal.findChildren(QPushButton)
            if button.text() == "Dictamen favorable"
        )
        assert button.isEnabled()
        app.processEvents()
        assert modal.grab().save(str(out / "candidato-qt.png"))
        selected.append(True)
        button.click()

    QTimer.singleShot(50, review)
    doctor.evaluate_request()
    assert wait_until(
        lambda: (
            selected
            and not doctor.busy
            and len(doctor.journal.list()) >= 2
            and doctor.journal.list()[-1]["state"] == "DONE"
        )
    )
    records = doctor.journal.list()
    evaluation_id = records[0]["operation_id"]
    assert evaluation_id and records[1]["status"] == "COMPLETED"
    with platform.owner("compatibilidad") as conn:
        conn.row_factory = dict_row
        saved = conn.execute(
            "SELECT request_id,candidates FROM evaluations WHERE id=%s",
            (evaluation_id,),
        ).fetchone()
        reviews = conn.execute(
            "SELECT resource_id,decision,actor_id FROM reviews WHERE evaluation_id=%s",
            (evaluation_id,),
        ).fetchall()
    assert str(saved["request_id"]) == request["id"] and any(
        candidate["resource_id"] == unit["id"] for candidate in saved["candidates"]
    )
    assert (
        len(reviews) == 1
        and str(reviews[0]["resource_id"]) == unit["id"]
        and reviews[0]["decision"] == "FAVORABLE"
        and str(reviews[0]["actor_id"]) == doctor.client.user["id"]
    )
    operator = Client(gateway)
    operator.login("operator1", platform.env.state["password"], "")
    with pytest.raises(ApiError) as denied:
        operator.authorized(
            "compatibilidad",
            "/api/v1/evaluations/" + evaluation_id,
            "evaluation_detail",
        )
    assert denied.value.status == 403
    operator.logout()
    platform.ok(
        "inventario",
        "POST",
        "/api/v1/resources/" + unit["id"] + "/withdraw",
        user="operator1",
        data={
            "version": unit["version"],
            "human_confirmation": True,
            "reason": "Retiro sintético para comprobar vigencia",
        },
    )
    stale = doctor.client.authorized(
        "compatibilidad", "/api/v1/evaluations/" + evaluation_id, "evaluation_detail"
    )
    assert any(
        entry["resource_id"] == unit["id"] and not entry["current"]
        for entry in stale["validity"]["candidates"]
    )

    def inspect_stale():
        modal = QApplication.activeModalWidget()
        if not modal:
            QTimer.singleShot(50, inspect_stale)
            return
        table = modal.findChild(QTableWidget)
        row = next(
            i
            for i in range(table.rowCount())
            if table.item(i, 0).text() == unit["folio"]
        )
        table.selectRow(row)
        app.processEvents()
        assert not next(
            button
            for button in modal.findChildren(QPushButton)
            if button.text() == "Dictamen favorable"
        ).isEnabled()
        assert modal.grab().save(str(out / "candidato-no-vigente-qt.png"))
        modal.reject()

    QTimer.singleShot(50, inspect_stale)
    doctor.evaluation_detail(stale)
    with pytest.raises(ApiError) as conflict:
        doctor.client.authorized(
            "compatibilidad",
            "/api/v1/evaluations/" + evaluation_id + "/reviews",
            "evaluation_review",
            method="POST",
            body={
                "resource_id": unit["id"],
                "decision": "FAVORABLE",
                "reason": "Revisión sintética posterior",
                "human_confirmation": "true",
            },
            request_schema="evaluation_review.xsd",
            key=str(uuid.uuid4()),
        )
    assert conflict.value.status == 409
    platform.drain()
    with platform.owner("auditoria") as conn:
        conn.row_factory = dict_row
        events = conn.execute(
            "SELECT action FROM audit_events WHERE event->>'resource_id'=%s AND action IN ('EVALUATION_CREATED','EVALUATION_REVIEWED')",
            (evaluation_id,),
        ).fetchall()
    assert sorted(row["action"] for row in events) == [
        "EVALUATION_CREATED",
        "EVALUATION_REVIEWED",
    ]
    doctor.close()
