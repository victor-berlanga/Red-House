"""Qt con respuestas dobles: preparado para ventana GUI, sin backend o escrituras."""

import os
from pathlib import Path
from uuid import uuid4

import pytest
from PySide6.QtCore import QThreadPool, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QWidget,
)
from redhouse_desktop.app import STYLE, Work
from redhouse_desktop.institutional_catalogue import catalogue_dialog


def run_dialog(kind, client, choose, item=None):
    application = QApplication.instance() or QApplication([])
    application.setStyleSheet(STYLE)
    window = QWidget()
    window.client = client
    window.pool = QThreadPool(window)
    window.pool.setMaxThreadCount(1)
    errors = []
    timer, deadline = QTimer(), QTimer()
    timer.setInterval(20)
    deadline.setSingleShot(True)

    def step():
        dialog = application.activeModalWidget()
        if dialog is None:
            return
        try:
            choose(dialog)
        except Exception as exc:  # noqa: BLE001 - cierra el modal y conserva el fallo del doble.
            errors.append(type(exc).__name__)
            dialog.reject()

    def timeout():
        errors.append("timeout")
        dialog = application.activeModalWidget()
        if dialog:
            dialog.reject()

    timer.timeout.connect(step)
    deadline.timeout.connect(timeout)
    timer.start()
    deadline.start(5000)
    try:
        result = catalogue_dialog(window, kind, item, worker_factory=Work)
    finally:
        timer.stop()
        deadline.stop()
        window.pool.waitForDone(1000)
        window.close()
    assert not errors
    return result


def capture(dialog, name):
    if os.environ.get("DESKTOP_CAPTURE_DIR"):
        assert dialog.grab().save(str(Path(os.environ["DESKTOP_CAPTURE_DIR"]) / name))


class Client:
    def __init__(self):
        self.user = {"id": str(uuid4()), "tenant_id": str(uuid4()), "role": "ADMIN"}
        self.calls = []

    def site(self, name):
        return {
            "id": str(uuid4()),
            "tenant_id": self.user["tenant_id"],
            "kind": "sites",
            "name": name,
            "municipality": "Monterrey",
            "address": "Domicilio sintético",
            "version": 1,
            "active": True,
            "parent_id": None,
        }


def test_site_form_returns_body_without_network_or_write():
    client = Client()
    client.authorized = lambda *args, **kwargs: pytest.fail(
        "El alta de sede no consulta ni escribe desde el diálogo"
    )

    def choose(dialog):
        for name, value in (
            ("name", "Sede sintética"),
            ("municipality", "Monterrey"),
            ("address", "Dirección de prueba"),
        ):
            dialog.findChild(QLineEdit, "catalogue_" + name).setText(value)
        button = next(
            button
            for button in dialog.findChildren(QPushButton)
            if button.text() == "Registrar sede"
        )
        assert button.isEnabled()
        capture(dialog, "sede-alta-doble.png")
        button.click()

    body = run_dialog("sites", client, choose)
    assert body == {
        "name": "Sede sintética",
        "municipality": "Monterrey",
        "address": "Dirección de prueba",
    }


def test_capacity_selector_uses_second_server_page():
    client = Client()
    sites = [client.site(f"Sede de página inicial {index}") for index in range(10)]
    sites.append(client.site("Sede posterior a primera página"))

    def authorized(service, path, operation, **kwargs):
        assert (
            service == "identidad-acceso"
            and path == "/api/v1/catalogues/sites"
            and operation == "sites_list_rows"
        )
        assert set(kwargs) == {"params"}
        page = kwargs["params"]["page"]
        assert (
            kwargs["params"]["page_size"] == 10 and kwargs["params"]["active"] == "true"
        )
        client.calls.append(page)
        return {
            "items": sites[(page - 1) * 10 : page * 10],
            "page": page,
            "page_size": 10,
            "total": 11,
        }

    client.authorized = authorized
    changed_page = [False]

    def choose(dialog):
        table = dialog.findChild(QTableWidget)
        if not table.rowCount() or not table.isEnabled():
            return
        if not changed_page[0]:
            changed_page[0] = True
            next(
                button
                for button in dialog.findChildren(QPushButton)
                if button.text() == "Siguiente"
            ).click()
            return
        if table.item(0, 0).text() != sites[-1]["name"]:
            return
        table.selectRow(0)
        dialog.findChild(QLineEdit, "catalogue_name").setText("Capacidad documentada")
        dialog.findChild(QLineEdit, "catalogue_component").setText(
            "Componente documentado"
        )
        dialog.findChild(QSpinBox, "catalogue_quantity").setValue(4)
        button = next(
            button
            for button in dialog.findChildren(QPushButton)
            if button.text() == "Registrar capacidad"
        )
        assert button.isEnabled()
        capture(dialog, "capacidad-sede-pagina-2-doble.png")
        button.click()

    body = run_dialog("capacities", client, choose)
    assert body["parent_id"] == sites[-1]["id"]
    assert body["quantity"] == 4
    assert client.calls == [1, 2]


def test_capacity_correction_keeps_original_site_and_version():
    client = Client()
    site = client.site("Sede conservada")
    item = {
        "id": str(uuid4()),
        "tenant_id": client.user["tenant_id"],
        "kind": "capacities",
        "name": "Capacidad previa",
        "parent_id": site["id"],
        "component": "Componente documentado",
        "quantity": 2,
        "active": True,
        "version": 7,
    }

    def authorized(service, path, operation, **kwargs):
        assert (
            path == "/api/v1/catalogues/sites/" + site["id"]
            and operation == "sites_detail"
        )
        assert not kwargs
        client.calls.append(path)
        return site

    client.authorized = authorized

    def choose(dialog):
        dialog.findChild(QSpinBox, "catalogue_quantity").setValue(5)
        next(
            field
            for field in dialog.findChildren(QLineEdit)
            if field.maxLength() == 1000
        ).setText("Corrección de cantidad documentada")
        for checkbox in dialog.findChildren(QCheckBox):
            checkbox.setChecked(True)
        button = next(
            button
            for button in dialog.findChildren(QPushButton)
            if button.text() == "Guardar corrección"
        )
        if not button.isEnabled():
            return
        assert dialog.findChild(QTableWidget) is None
        capture(dialog, "capacidad-correccion-doble.png")
        button.click()

    body = run_dialog("capacities", client, choose, item)
    assert (
        body["version"] == 7
        and body["parent_id"] == site["id"]
        and body["quantity"] == 5
    )
    assert len(client.calls) == 1


def test_non_admin_cannot_open_write_form():
    application = QApplication.instance() or QApplication([])
    window = QWidget()
    window.client = Client()
    window.client.user["role"] = "OPERATOR"
    with pytest.raises(PermissionError):
        catalogue_dialog(window, "sites", worker_factory=Work)
    window.close()
    assert application is not None
