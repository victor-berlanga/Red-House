"""Alta y recepción de muestra en Qt/XML con fixture efímero."""

import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import redhouse_desktop.app as desktop
from cryptography.fernet import Fernet
from psycopg.rows import dict_row
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDateTimeEdit,
    QLineEdit,
    QPushButton,
    QTableWidget,
)
from redhouse_desktop.journal import Journal
from test_real_lab import gateway as gateway  # noqa: PLC0414 - fixture de pytest
from tests.conftest import platform as platform  # noqa: PLC0414 - fixture de pytest
from tests.helpers import resource


def wait_until(predicate):
    deadline = time.monotonic() + 40
    while time.monotonic() < deadline:
        QApplication.processEvents()
        if predicate():
            return True
        time.sleep(0.02)
    return False


def test_operator_registers_and_receives_selected_sample(
    platform, gateway, monkeypatch, tmp_path
):
    unit = resource(platform)
    now = datetime.now(timezone.utc)
    profile = platform.ok(
        "compatibilidad",
        "POST",
        "/api/v1/laboratory/profiles",
        user="medical1",
        data={
            "name": "Perfil de muestra sintética",
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
    output = Path(os.environ["DESKTOP_CAPTURE_DIR"])
    output.mkdir(parents=True, exist_ok=True)
    operator = desktop.Window()
    operator.show()
    operator.username.setText("operator1")
    operator.password.setText(platform.env.state["password"])
    operator.login()
    assert wait_until(
        lambda: (
            operator.client
            and operator.client.user
            and operator.stack.currentIndex() == 1
            and not operator.busy
        )
    )
    operator.switch("samples")
    assert wait_until(lambda: not operator.busy)
    errors = []

    def choose():
        dialog = app.activeModalWidget()
        if not dialog:
            QTimer.singleShot(25, choose)
            return
        tables = dialog.findChildren(QTableWidget)
        if len(tables) != 2 or not all(table.rowCount() for table in tables):
            QTimer.singleShot(25, choose)
            return
        try:
            units, profiles = tables
            unit_row = next(
                i
                for i in range(units.rowCount())
                if units.item(i, 0).text() == unit["folio"]
            )
            profile_row = next(
                i
                for i in range(profiles.rowCount())
                if profiles.item(i, 0).text() == profile["name"]
            )
            units.selectRow(unit_row)
            profiles.selectRow(profile_row)
            app.processEvents()
            next(
                x for x in dialog.findChildren(QLineEdit) if x.maxLength() == 200
            ).setText(identifier)
            dialog.findChild(QDateTimeEdit).setDateTime(
                desktop.QDateTime.currentDateTime().addSecs(-60)
            )
            dialog.findChild(QCheckBox).setChecked(True)
            app.processEvents()
            assert dialog.grab().save(str(output / "alta-muestra-qt.png"))
            next(
                x
                for x in dialog.findChildren(QPushButton)
                if x.text() == "Registrar muestra"
            ).click()
        except Exception as exc:  # noqa: BLE001 - solo clase, sin datos privados
            errors.append(type(exc).__name__)
            dialog.reject()

    try:
        QTimer.singleShot(0, choose)
        operator.create_sample()
        assert not errors
        assert wait_until(
            lambda: (
                not operator.busy
                and any(row["identifier"] == identifier for row in operator.rows)
            )
        )
        sample = next(row for row in operator.rows if row["identifier"] == identifier)
        assert (
            sample["resource_id"] == unit["id"]
            and sample["profile_id"] == profile["id"]
            and sample["status"] == "REQUESTED"
        )
        with (
            platform.owner("compatibilidad") as conn,
            conn.cursor(row_factory=dict_row) as cursor,
        ):
            row = cursor.execute(
                "SELECT id,resource_id,profile_id,status,version FROM lab_samples WHERE id=%s",
                (sample["id"],),
            ).fetchone()
        assert (
            str(row["resource_id"]) == unit["id"]
            and str(row["profile_id"]) == profile["id"]
            and row["status"] == "REQUESTED"
            and row["version"] == 1
        )
        operator.table.selectRow(
            next(i for i, row in enumerate(operator.rows) if row["id"] == sample["id"])
        )

        def receive():
            dialog = app.activeModalWidget()
            if not dialog:
                QTimer.singleShot(25, receive)
                return
            dialog.findChild(QLineEdit).setText("Recepción sintética documentada")
            next(
                x
                for x in dialog.findChildren(QPushButton)
                if x.text() == "Confirmar recepción"
            ).click()

        QTimer.singleShot(0, receive)
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
        platform.drain()
        with platform.owner("compatibilidad") as conn:
            events = conn.execute(
                "SELECT event->>'action' FROM activity_events WHERE event->>'resource_id'=%s",
                (sample["id"],),
            ).fetchall()
        assert ("LAB_SAMPLE_REQUESTED",) in events and (
            "LAB_SAMPLE_RECEIVED",
        ) in events
    finally:
        if operator.client:
            operator.client.logout()
            operator.client = None
        operator.close()
