"""Recuperación Qt/XML tras detener un servicio del fixture aislado."""

import os
import threading
import time
from pathlib import Path

import redhouse_desktop.app as desktop
from cryptography.fernet import Fernet
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
from redhouse_desktop.app import STYLE, Window
from redhouse_desktop.journal import Journal
from test_real_lab import (
    gateway as gateway,  # noqa: PLC0414 - fixture compartido de pytest
)
from tests.conftest import QuietHandler
from tests.conftest import (
    platform as platform,  # noqa: PLC0414 - fixture compartido de pytest
)
from tests.helpers import evaluation, recipient_request, resource
from werkzeug.serving import make_server


def wait_until(predicate):
    deadline = time.monotonic() + 40
    while time.monotonic() < deadline:
        QApplication.processEvents()
        if predicate():
            return True
        time.sleep(0.02)
    return False


def test_coverage_service_failure_recovers_in_authenticated_window(
    platform, gateway, monkeypatch, tmp_path
):
    unit = resource(platform)
    _, request = recipient_request(platform)
    evaluated = evaluation(platform, request, [unit])
    proposal = platform.ok(
        "priorizacion_geografia",
        "POST",
        "/api/v1/allocation-proposals",
        data={"evaluation_ids": [evaluated["id"]]},
    )
    app = QApplication.instance() or QApplication([])
    app.setStyleSheet(STYLE)
    monkeypatch.setenv("REDHOUSE_BASE_URL", gateway)

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
    window = Window()
    window.show()
    try:
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
        assert window.client.user["role"] == "MEDICAL"
        window.switch("coverage")
        assert wait_until(
            lambda: (
                not window.busy
                and any(row["id"] == proposal["id"] for row in window.rows)
            )
        )
        output = Path(os.environ["DESKTOP_CAPTURE_DIR"])
        output.mkdir(parents=True, exist_ok=True)
        assert window.grab().save(str(output / "cobertura-antes-qt.png"))

        name = "priorizacion_geografia"
        server = platform.servers[name]
        port = server.server_port
        stopped = False
        try:
            server.shutdown()
            server.server_close()
            stopped = True
            ticks = []
            QTimer.singleShot(0, lambda: ticks.append(True))
            window.load()
            assert wait_until(lambda: not window.busy and bool(ticks))
            assert not window.rows and window.table.rowCount() == 0
            assert window.reload_button.isEnabled()
            message = window.status.text()
            assert (
                message
                == "No se pudo completar la operación. Comprueba tu conexión o contacta a soporte institucional."
            )
            assert (
                "127.0.0.1" not in message
                and platform.env.state["password"] not in message
            )
            assert window.grab().save(str(output / "servicio-caido-qt.png"))
        finally:
            if stopped:
                replacement = make_server(
                    "127.0.0.1",
                    port,
                    platform.apps[name],
                    threaded=True,
                    request_handler=QuietHandler,
                )
                platform.servers[name] = replacement
                threading.Thread(target=replacement.serve_forever, daemon=True).start()

        window.reload_button.click()
        assert wait_until(
            lambda: (
                not window.busy
                and any(row["id"] == proposal["id"] for row in window.rows)
            )
        )
        assert window.client.user["role"] == "MEDICAL"
        with platform.owner(name) as conn:
            conn.execute("SET TRANSACTION READ ONLY")
            assert (
                conn.execute(
                    "SELECT count(*) FROM proposals WHERE id=%s", (proposal["id"],)
                ).fetchone()[0]
                == 1
            )
        assert window.grab().save(str(output / "servicio-recuperado-qt.png"))
    finally:
        wait_until(lambda: not window.busy)
        try:
            if window.client:
                window.client.logout()
        finally:
            window.client = None
            window.close()
