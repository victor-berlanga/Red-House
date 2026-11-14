"""Reserva Qt/XML recuperada tras respuesta perdida, con datos sintéticos."""

import json
import os
import re
import time
import uuid
from pathlib import Path
from urllib.parse import urlsplit

import pytest
import redhouse_desktop.app as desktop
import requests
from cryptography.fernet import Fernet
from psycopg.rows import dict_row
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QApplication,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
)
from redhouse_desktop.client import ApiError
from redhouse_desktop.journal import Journal
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


@pytest.fixture(scope="session")
def safe_trace():
    """Conserva solo etapas y metadatos; se escribe aun si falla una aserción."""
    trace = {"attempts": [], "statuses": [], "failures": [], "dependencies": []}
    try:
        yield trace
    finally:
        output = Path(os.environ["DESKTOP_CAPTURE_DIR"])
        output.mkdir(parents=True, exist_ok=True)
        sanitized = dict(
            trace,
            attempts=len(trace["attempts"]),
            dependencies=trace["dependencies"][-40:],
        )
        (output / "diagnostico-saneado.json").write_text(
            json.dumps(sanitized, ensure_ascii=False, indent=2) + "\n"
        )


def test_reservation_recovers_same_attempt_and_unique_review(
    safe_trace, platform, gateway, monkeypatch, tmp_path
):
    unit = resource(platform)
    _, request = recipient_request(platform)
    evaluated = evaluation(platform, request, [unit])
    with platform.owner("compatibilidad") as conn:
        constraints = conn.execute(
            "SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid='red_house.blood_review'::regclass AND contype='u'"
        ).fetchall()
    assert any("UNIQUE (evaluation_id, resource_id)" in row[0] for row in constraints)

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
    monkeypatch.setattr(
        QMessageBox, "information", lambda *args, **kwargs: QMessageBox.Ok
    )
    statuses = safe_trace["statuses"]
    real_http = requests.request
    gateway_origin = urlsplit(gateway)

    def observe_http(method, url, *args, **kwargs):
        response = real_http(method, url, *args, **kwargs)
        parsed = urlsplit(url)
        if (
            method == "POST"
            and (parsed.scheme, parsed.netloc)
            == (gateway_origin.scheme, gateway_origin.netloc)
            and parsed.path == "/services/inventario/api/v1/reservations"
        ):
            statuses.append(response.status_code)
        return response

    monkeypatch.setattr(requests, "request", observe_http)
    dependency_events = safe_trace["dependencies"]
    real_session_request = requests.sessions.Session.request
    service_ports = {
        urlsplit(url).port: service for service, url in platform.urls.items()
    }

    def observe_dependency(session, method, url, **kwargs):
        headers = kwargs.get("headers") or {}
        caller = headers.get("X-Service")
        parsed = urlsplit(url)
        destination = service_ports.get(parsed.port)
        safe_path = re.sub(r"[0-9a-fA-F-]{36}", "{id}", parsed.path)
        started = time.monotonic()
        try:
            response = real_session_request(session, method, url, **kwargs)
        except requests.RequestException as exc:
            if caller and destination:
                dependency_events.append(
                    (
                        caller,
                        destination,
                        method,
                        safe_path,
                        type(exc).__name__,
                        round((time.monotonic() - started) * 1000),
                    )
                )
            raise
        if caller and destination:
            try:
                value = response.json()
                valid_envelope = isinstance(value, dict) and isinstance(
                    value.get("meta"), dict
                )
            except ValueError:
                valid_envelope = False
            dependency_events.append(
                (
                    caller,
                    destination,
                    method,
                    safe_path,
                    response.status_code,
                    valid_envelope,
                    round((time.monotonic() - started) * 1000),
                )
            )
        return response

    monkeypatch.setattr(requests.sessions.Session, "request", observe_dependency)
    dropped = []
    attempts = safe_trace["attempts"]
    original = desktop.Client.authorized

    def lose_once(client, service, path, operation, *args, **kwargs):
        if operation == "reservation_create":
            attempts.append(True)
        result = original(client, service, path, operation, *args, **kwargs)
        if operation == "reservation_create" and not dropped:
            dropped.append(True)
            raise ConnectionError("Respuesta sintética perdida después del commit")
        return result

    monkeypatch.setattr(desktop.Client, "authorized", lose_once)
    failures = safe_trace["failures"]
    original_failure = desktop.Window.failed

    def observe_failure(window, exc):
        failures.append(
            (
                type(exc).__name__,
                getattr(exc, "status", None),
                getattr(exc, "code", None),
            )
        )
        return original_failure(window, exc)

    monkeypatch.setattr(desktop.Window, "failed", observe_failure)
    app = QApplication.instance() or QApplication([])
    app.setStyleSheet(desktop.STYLE)
    doctor = desktop.Window()
    doctor.show()
    doctor.username.setText("medical2")
    doctor.password.setText(platform.env.state["password"])
    doctor.login()
    assert wait_until(lambda: doctor.stack.currentIndex() == 1 and not doctor.busy)
    path = "/api/v1/evaluations/" + evaluated["id"] + "/reviews"
    with pytest.raises(ApiError) as duplicate:
        doctor.client.authorized(
            "compatibilidad",
            path,
            "evaluation_review",
            method="POST",
            body={
                "resource_id": unit["id"],
                "decision": "UNFAVORABLE",
                "reason": "Segundo dictamen sintético",
                "human_confirmation": "true",
            },
            request_schema="evaluation_review.xsd",
            key=str(uuid.uuid4()),
        )
    assert duplicate.value.status == 409
    with platform.owner("compatibilidad") as conn:
        reviews = conn.execute(
            "SELECT decision FROM reviews WHERE evaluation_id=%s AND resource_id=%s",
            (evaluated["id"], unit["id"]),
        ).fetchall()
    assert reviews == [("FAVORABLE",)]
    detail = doctor.client.authorized(
        "compatibilidad", "/api/v1/evaluations/" + evaluated["id"], "evaluation_detail"
    )
    out = Path(os.environ["DESKTOP_CAPTURE_DIR"])
    out.mkdir(parents=True, exist_ok=True)

    interaction_errors = []

    def reserve():
        modal = QApplication.activeModalWidget()
        if not modal:
            QTimer.singleShot(50, reserve)
            return
        try:
            table = modal.findChild(QTableWidget)
            row = next(
                i
                for i in range(table.rowCount())
                if table.item(i, 0).text() == unit["folio"]
            )
            table.selectRow(row)
            modal.findChild(QLineEdit).setText("Reserva sintética documentada")
            button = next(
                button
                for button in modal.findChildren(QPushButton)
                if button.text() == "Reservar unidad"
            )
            assert button.isEnabled()
            app.processEvents()
            assert modal.grab().save(str(out / "reserva-qt.png"))
            button.click()
        except Exception as exc:  # noqa: BLE001 - registrar solo la clase, sin datos del diálogo
            interaction_errors.append(type(exc).__name__)
            modal.reject()

    QTimer.singleShot(50, reserve)
    doctor.evaluation_detail(detail)
    assert not interaction_errors, interaction_errors
    assert wait_until(lambda: not doctor.busy and (dropped or failures)), (
        len(attempts),
        statuses,
        failures,
    )
    if not dropped:
        pytest.fail("Reserva sin respuesta válida; ver diagnóstico saneado.")
    pending = doctor.journal.list()[0]
    original_key = pending["key"]
    assert pending["state"] == "PREPARED" and statuses == [202]
    assert "resultado incierto" in doctor.status.text()
    app.processEvents()
    assert doctor.grab().save(str(out / "resultado-incierto-qt.png"))
    doctor.journal = Journal(
        tmp_path,
        doctor.client.base,
        doctor.client.user["id"],
        doctor.client.user["tenant_id"],
        keys,
    )
    doctor.recover_operation(doctor.journal.list())
    assert wait_until(
        lambda: not doctor.busy and doctor.journal.list()[0].get("operation_id")
    )
    recovered = doctor.journal.list()[0]
    assert (
        recovered["key"] == original_key
        and recovered["status"] in ("PENDING", "COMPLETED")
        and statuses == [202, 202]
    )
    if recovered["status"] == "PENDING":
        doctor.resume_pending(doctor.journal.list())
        assert wait_until(
            lambda: (
                not doctor.busy and doctor.journal.list()[0]["status"] == "COMPLETED"
            )
        )
        recovered = doctor.journal.list()[0]
    assert recovered["status"] == "COMPLETED" and recovered["state"] == "DONE"
    assert "Reserva confirmada" in doctor.status.text()
    app.processEvents()
    assert doctor.grab().save(str(out / "resultado-recuperado-qt.png"))
    with platform.owner("inventario") as conn:
        conn.row_factory = dict_row
        operations = conn.execute(
            "SELECT id,status FROM operations WHERE user_id=%s AND key=%s",
            (doctor.client.user["id"], original_key),
        ).fetchall()
        reservations = conn.execute(
            "SELECT id,resource_id,evaluation_id,status FROM reservations WHERE operation_id=%s",
            (recovered["operation_id"],),
        ).fetchall()
        saved_resource = conn.execute(
            "SELECT status FROM resources WHERE id=%s", (unit["id"],)
        ).fetchone()
    assert (
        len(operations) == 1
        and str(operations[0]["id"]) == recovered["operation_id"]
        and operations[0]["status"] == "COMPLETED"
        and len(reservations) == 1
    )
    assert (
        str(reservations[0]["resource_id"]) == unit["id"]
        and str(reservations[0]["evaluation_id"]) == evaluated["id"]
        and reservations[0]["status"] == "RESERVED"
        and saved_resource["status"] == "RESERVED"
    )
    with platform.owner("receptores") as conn:
        conn.row_factory = dict_row
        saved_request = conn.execute(
            "SELECT status FROM requests WHERE id=%s", (request["id"],)
        ).fetchone()
        holds = conn.execute(
            "SELECT status FROM holds WHERE operation_id=%s",
            (recovered["operation_id"],),
        ).fetchall()
    assert (
        saved_request["status"] == "IN_PROGRESS"
        and len(holds) == 1
        and holds[0]["status"] == "CONFIRMED"
    )
    import jwt
    from redhouse.security import key, redis_call

    claims = jwt.decode(doctor.client.access, options={"verify_signature": False})
    with platform.apps["identidad_acceso"].app_context():
        assert redis_call(lambda redis: redis.get(key("session:" + claims["sid"])))
    platform.drain()
    with platform.owner("auditoria") as conn:
        events = conn.execute(
            "SELECT count(*) FROM audit_events WHERE action='RESOURCE_RESERVED' AND event->>'resource_id'=%s",
            (str(reservations[0]["id"]),),
        ).fetchone()[0]
    assert events == 1
    doctor.close()
