"""Recepción, captura y revisión humana Qt/XML con datos sintéticos."""

import datetime
import os
from pathlib import Path
import uuid

from cryptography.fernet import Fernet
from PySide6.QtCore import QDateTime, QTimer
from PySide6.QtTest import QTest
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDateTimeEdit,
    QLineEdit,
    QPushButton,
)
import pytest
from psycopg.rows import dict_row

from tests.conftest import platform
from tests.helpers import resource
from test_real_lab import gateway
from redhouse_desktop.client import ApiError
from redhouse_desktop.journal import Journal
import redhouse_desktop.app as desktop


def wait_until(predicate):
    for _ in range(2000):
        QTest.qWait(20)
        if predicate():
            return True
    return False


def test_operator_receives_and_captures_doctor_reviews(
    platform, gateway, monkeypatch, tmp_path
):
    now = datetime.datetime.now(datetime.timezone.utc)
    unit = resource(platform)
    profile = platform.ok(
        "compatibilidad",
        "POST",
        "/api/v1/laboratory/profiles",
        user="medical1",
        data={
            "name": "Perfil sintético",
            "kind": "BLOOD",
            "component": "RBC",
            "version": 1,
            "required_tests": ["ABO"],
            "source": "Prueba sintética sin uso clínico",
            "synthetic": True,
            "effective_at": now.isoformat(),
        },
    )
    identifier = "MUESTRA-" + uuid.uuid4().hex[:10]
    sample = platform.ok(
        "compatibilidad",
        "POST",
        "/api/v1/laboratory/samples",
        user="operator1",
        data={
            "resource_id": unit["id"],
            "profile_id": profile["id"],
            "identifier": identifier,
            "collected_at": (now - datetime.timedelta(minutes=5)).isoformat(),
        },
    )

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
    app = QApplication.instance() or QApplication([])
    app.setStyleSheet(desktop.STYLE)
    out = Path(os.environ["DESKTOP_CAPTURE_DIR"])
    out.mkdir(parents=True, exist_ok=True)

    def login(username):
        window = desktop.Window()
        window.show()
        window.username.setText(username)
        window.password.setText(platform.env.state["password"])
        window.login()
        assert wait_until(lambda: window.stack.currentIndex() == 1 and not window.busy)
        return window

    operator = login("operator1")
    operator.switch("samples")
    assert wait_until(lambda: not operator.busy)
    operator.search.setText(identifier)
    operator.search_now()
    assert wait_until(
        lambda: (
            not operator.busy
            and any(row["id"] == sample["id"] for row in operator.rows)
        )
    )
    operator.table.selectRow(
        next(i for i, row in enumerate(operator.rows) if row["id"] == sample["id"])
    )

    def receive():
        modal = QApplication.activeModalWidget()
        if not modal:
            QTimer.singleShot(50, receive)
            return
        modal.findChild(QLineEdit).setText("Recepción sintética documentada")
        app.processEvents()
        assert modal.grab().save(str(out / "recepcion-qt.png"))
        next(
            button
            for button in modal.findChildren(QPushButton)
            if button.text() == "Confirmar recepción"
        ).click()

    QTimer.singleShot(50, receive)
    operator.receive()
    assert wait_until(
        lambda: (
            not operator.busy
            and any(
                row["id"] == sample["id"] and row["status"] == "RECEIVED"
                for row in operator.rows
            )
        )
    )
    with pytest.raises(ApiError) as conflict:
        operator.client.authorized(
            "compatibilidad",
            "/api/v1/laboratory/samples/" + sample["id"] + "/receive",
            "lab_sample_receive",
            method="POST",
            body={
                "decision": "RECEIVED",
                "version": sample["version"],
                "reason": "Recepción duplicada sintética",
                "human_confirmation": "true",
            },
            request_schema="lab_sample_receive.xsd",
            key=str(uuid.uuid4()),
        )
    assert conflict.value.status in (409, 412)
    operator.table.selectRow(
        next(i for i, row in enumerate(operator.rows) if row["id"] == sample["id"])
    )
    measured = []

    def capture():
        modal = QApplication.activeModalWidget()
        if not modal:
            QTimer.singleShot(50, capture)
            return
        for field, value in zip(
            modal.findChildren(QLineEdit),
            (
                "ABO",
                "O",
                "Método sintético",
                "Laboratorio sintético",
                "Referencia sintética",
            ),
        ):
            field.setText(value)
        date = modal.findChild(QDateTimeEdit)
        date.setDateTime(QDateTime.currentDateTime().addSecs(-60))
        measured.append(date.dateTime().toUTC().toString(desktop.Qt.ISODate))
        modal.findChild(QCheckBox).setChecked(True)
        app.processEvents()
        assert modal.grab().save(str(out / "captura-qt.png"))
        next(
            button
            for button in modal.findChildren(QPushButton)
            if button.text() == "Registrar resultado"
        ).click()

    QTimer.singleShot(50, capture)
    operator.capture_result()
    assert wait_until(
        lambda: (
            not operator.busy
            and len(operator.journal.list()) >= 2
            and operator.journal.list()[-1]["state"] == "DONE"
        )
    )
    operator.switch("results")
    assert wait_until(
        lambda: (
            not operator.busy
            and any(
                row.get("sample_id") == sample["id"] and row.get("test_code") == "ABO"
                for row in operator.rows
            )
        )
    )
    result = next(
        row
        for row in operator.rows
        if row.get("sample_id") == sample["id"] and row.get("test_code") == "ABO"
    )
    assert result["status"] == "CAPTURED" and not operator.review_button.isEnabled()
    assert datetime.datetime.fromisoformat(
        result["measured_at"].replace("Z", "+00:00")
    ) == datetime.datetime.fromisoformat(measured[0].replace("Z", "+00:00"))
    with pytest.raises(ApiError) as denied:
        operator.client.authorized(
            "compatibilidad",
            "/api/v1/laboratory/results/" + result["id"] + "/review",
            "lab_result_review",
            method="POST",
            body={
                "decision": "AUTHORIZED",
                "version": result["version"],
                "reason": "Revisión sintética",
                "human_confirmation": "true",
            },
            request_schema="lab_result_review.xsd",
            key=str(uuid.uuid4()),
        )
    assert denied.value.status == 403
    operator.client.logout()
    operator.client = None
    operator.close()
    doctor = login("medical1")
    doctor.switch("results")
    assert wait_until(
        lambda: (
            not doctor.busy and any(row["id"] == result["id"] for row in doctor.rows)
        )
    )
    doctor.table.selectRow(
        next(i for i, row in enumerate(doctor.rows) if row["id"] == result["id"])
    )

    def review():
        modal = QApplication.activeModalWidget()
        if not modal:
            QTimer.singleShot(50, review)
            return
        choice = modal.findChild(QComboBox)
        choice.setCurrentIndex(choice.findData("AUTHORIZED"))
        modal.findChild(QLineEdit).setText("Revisión profesional sintética")
        app.processEvents()
        assert modal.grab().save(str(out / "revision-qt.png"))
        next(
            button
            for button in modal.findChildren(QPushButton)
            if button.text() == "Registrar revisión"
        ).click()

    QTimer.singleShot(50, review)
    doctor.review_result()
    assert wait_until(
        lambda: (
            not doctor.busy
            and any(
                row["id"] == result["id"] and row["status"] == "AUTHORIZED"
                for row in doctor.rows
            )
        )
    )
    with platform.owner("compatibilidad") as conn:
        conn.row_factory = dict_row
        saved_sample = conn.execute(
            "SELECT status,version FROM lab_samples WHERE id=%s", (sample["id"],)
        ).fetchone()
        saved_result = conn.execute(
            "SELECT sample_id,status,version,measured_at FROM lab_results WHERE id=%s",
            (result["id"],),
        ).fetchone()
    assert (
        saved_sample["status"] == "RECEIVED"
        and saved_sample["version"] == sample["version"] + 1
    )
    assert (
        str(saved_result["sample_id"]) == sample["id"]
        and saved_result["status"] == "AUTHORIZED"
        and saved_result["version"] == result["version"]
    )
    assert saved_result["measured_at"] == datetime.datetime.fromisoformat(
        measured[0].replace("Z", "+00:00")
    )
    platform.drain()
    with platform.owner("auditoria") as conn:
        conn.row_factory = dict_row
        events = conn.execute(
            "SELECT action,event->>'resource_id' AS resource_id FROM audit_events WHERE action IN ('LAB_SAMPLE_RECEIVED','LAB_RESULT_RECORDED','LAB_RESULT_AUTHORIZED') AND event->>'resource_id' IN (%s,%s)",
            (sample["id"], result["id"]),
        ).fetchall()
    assert {(row["action"], row["resource_id"]) for row in events} == {
        ("LAB_SAMPLE_RECEIVED", sample["id"]),
        ("LAB_RESULT_RECORDED", result["id"]),
        ("LAB_RESULT_AUTHORIZED", result["id"]),
    }
    assert len(events) == 3
    doctor.close()
