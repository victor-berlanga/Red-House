"""Alta/corrección de receptor y corrección/cancelación de solicitud Qt/XML."""

import os
import time
import uuid
from pathlib import Path

import pytest
import redhouse_desktop.app as desktop
from cryptography.fernet import Fernet
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QLineEdit,
    QPushButton,
    QSpinBox,
)
from redhouse_desktop.client import ApiError, Client
from redhouse_desktop.journal import Journal
from test_real_lab import (
    gateway as gateway,  # noqa: PLC0414 - fixture compartido de pytest
)
from tests.conftest import (
    platform as platform,  # noqa: PLC0414 - fixture compartido de pytest
)


def wait_until(predicate):
    until = time.monotonic() + 40
    while time.monotonic() < until:
        QApplication.processEvents()
        if predicate():
            return True
        time.sleep(0.02)
    return False


def test_medical_recipient_and_request_corrections(
    platform, gateway, monkeypatch, tmp_path
):
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
    folio = "REC-" + uuid.uuid4().hex[:10]
    window = desktop.Window()
    window.show()
    window.username.setText("medical2")
    window.password.setText(platform.env.state["password"])
    window.login()
    assert wait_until(
        lambda: (
            window.client
            and window.client.user
            and window.stack.currentIndex() == 1
            and not window.busy
        )
    )
    denied = Client(gateway)
    denied.login("operator1", platform.env.state["password"], "")
    try:
        with pytest.raises(ApiError) as error:
            denied.authorized(
                "receptores",
                "/api/v1/recipients",
                "recipient_create",
                method="POST",
                body={
                    "folio": folio,
                    "display_name": "Persona sintética",
                    "kind": "BLOOD",
                    "blood_group": "O-",
                    "studies": "Estudios documentados",
                },
                request_schema="recipient_create.xsd",
                key=str(uuid.uuid4()),
            )
        assert error.value.status == 403
        window.switch("recipients")
        assert wait_until(lambda: not window.busy)
        errors = []

        def create():
            dialog = app.activeModalWidget()
            if not dialog:
                QTimer.singleShot(25, create)
                return
            try:
                fields = dialog.findChildren(QLineEdit)
                for widget, value in zip(
                    fields, (folio, "Persona sintética", "Estudios documentados")
                ):
                    widget.setText(value)
                combos = dialog.findChildren(QComboBox)
                combos[0].setCurrentIndex(combos[0].findData("BLOOD"))
                combos[2].setCurrentIndex(combos[2].findData("O-"))
                app.processEvents()
                assert dialog.grab().save(str(out / "receptor-alta-qt.png"))
                next(
                    x
                    for x in dialog.findChildren(QPushButton)
                    if x.text() == "Registrar receptor"
                ).click()
            except Exception as exc:  # noqa: BLE001 - solo clase para diagnóstico saneado
                errors.append(type(exc).__name__)
                dialog.reject()

        QTimer.singleShot(0, create)
        window.create_recipient()
        assert not errors and wait_until(
            lambda: (
                not window.busy and any(row["folio"] == folio for row in window.rows)
            )
        )
        recipient = next(row for row in window.rows if row["folio"] == folio)
        window.table.selectRow(
            next(i for i, row in enumerate(window.rows) if row["id"] == recipient["id"])
        )

        def edit_recipient():
            dialog = app.activeModalWidget()
            if not dialog:
                QTimer.singleShot(25, edit_recipient)
                return
            fields = dialog.findChildren(QLineEdit)
            fields[1].setText("Persona sintética corregida")
            fields[-1].setText("Corrección documentada")
            dialog.findChild(QCheckBox).setChecked(True)
            app.processEvents()
            assert dialog.grab().save(str(out / "receptor-edicion-qt.png"))
            next(
                x
                for x in dialog.findChildren(QPushButton)
                if x.text() == "Guardar corrección"
            ).click()

        QTimer.singleShot(0, edit_recipient)
        window.edit_recipient()
        assert wait_until(
            lambda: (
                not window.busy
                and any(
                    row["id"] == recipient["id"] and row["version"] == 2
                    for row in window.rows
                )
            )
        )
        request = window.client.authorized(
            "receptores",
            "/api/v1/requests",
            "request_create",
            method="POST",
            body={
                "recipient_id": recipient["id"],
                "component": "RBC",
                "quantity": 1,
                "urgency": 2,
            },
            request_schema="request_create.xsd",
            key=str(uuid.uuid4()),
        )
        window.switch("requests")
        assert wait_until(
            lambda: (
                not window.busy
                and any(row["id"] == request["id"] for row in window.rows)
            )
        )
        window.table.selectRow(
            next(i for i, row in enumerate(window.rows) if row["id"] == request["id"])
        )

        def edit_request():
            dialog = app.activeModalWidget()
            if not dialog:
                QTimer.singleShot(25, edit_request)
                return
            dialog.findChild(QSpinBox).setValue(2)
            dialog.findChild(QLineEdit).setText("Corrección documentada")
            dialog.findChild(QCheckBox).setChecked(True)
            app.processEvents()
            assert dialog.grab().save(str(out / "solicitud-edicion-qt.png"))
            next(
                x
                for x in dialog.findChildren(QPushButton)
                if x.text() == "Guardar corrección"
            ).click()

        QTimer.singleShot(0, edit_request)
        window.edit_request()
        assert wait_until(
            lambda: (
                not window.busy
                and any(
                    row["id"] == request["id"] and row["version"] == 2
                    for row in window.rows
                )
            )
        )
        window.table.selectRow(
            next(i for i, row in enumerate(window.rows) if row["id"] == request["id"])
        )

        def cancel():
            dialog = app.activeModalWidget()
            if not dialog:
                QTimer.singleShot(25, cancel)
                return
            dialog.findChild(QLineEdit).setText("Cancelación documentada")
            dialog.findChild(QCheckBox).setChecked(True)
            app.processEvents()
            assert dialog.grab().save(str(out / "solicitud-cancelacion-qt.png"))
            next(
                x
                for x in dialog.findChildren(QPushButton)
                if x.text() == "Confirmar cancelación"
            ).click()

        QTimer.singleShot(0, cancel)
        window.cancel_request()
        assert wait_until(
            lambda: (
                not window.busy
                and any(
                    row["id"] == request["id"] and row["status"] == "CANCELLED"
                    for row in window.rows
                )
            )
        )
        with platform.owner("receptores") as conn:
            row = conn.execute(
                "SELECT status,version,quantity FROM requests WHERE id=%s",
                (request["id"],),
            ).fetchone()
        assert row == ("CANCELLED", 3, 2)
        platform.drain()
        with platform.owner("receptores") as conn:
            actions = {
                row[0]
                for row in conn.execute(
                    "SELECT event->>'action' FROM activity_events WHERE event->>'resource_id' IN (%s,%s)",
                    (recipient["id"], request["id"]),
                ).fetchall()
            }
        assert {
            "RECIPIENT_CREATED",
            "RECIPIENT_UPDATED",
            "REQUEST_UPDATED",
            "REQUEST_CANCELLED",
        } <= actions
    finally:
        denied.logout()
        if window.client:
            window.client.logout()
            window.client = None
        window.close()
