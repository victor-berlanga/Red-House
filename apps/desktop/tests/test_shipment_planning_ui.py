"""Selección de planificación con respuestas dobles; sin backend."""
import os
from pathlib import Path
from uuid import uuid4

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QCheckBox, QDateTimeEdit, QLineEdit, QPushButton, QTableWidget
from redhouse_desktop.app import STYLE, Window

app = QApplication.instance() or QApplication([])
app.setStyleSheet(STYLE)


def test_coordinator_selects_reservation_and_origin_account():
    ids = [str(uuid4()) for _ in range(6)]
    origin, destination, reservation, resource, route, transport = ids
    class Client:
        access = None
        user = {'role': 'COORDINATOR'}
        def authorized(self, _service, _path, operation, **_kwargs):
            page = lambda rows: {'items': rows, 'page': 1, 'total': len(rows)}
            if operation == 'institutions': return page([{'id': origin, 'name': 'Hospital Norte'}, {'id': destination, 'name': 'Hospital Sur'}])
            if operation == 'reservation_list': return page([{'id': reservation, 'resource_id': resource, 'origin_id': origin, 'destination_id': destination}])
            if operation == 'resource_detail': return {'id': resource, 'folio': 'UNIDAD-01', 'component': 'RBC', 'expires_at': '2026-11-16T12:00:00Z'}
            if operation == 'user_list': return page([{'id': transport, 'username': 'turno-traslado', 'tenant_id': origin}])
            if operation == 'reservation_detail': return {'id': reservation, 'origin_id': origin, 'destination_id': destination, 'resource_id': resource, 'route_id': route, 'route_version': 1, 'expires_at': '2026-11-16T12:00:00Z'}
            if operation == 'route_detail': return {'id': route, 'origin_id': origin, 'destination_id': destination, 'version': 1, 'distance_km': 10, 'travel_minutes': 15}
            raise AssertionError(operation)
    window = Window()
    window.client = Client()
    calls, errors = [], []
    window.secure_command = lambda operation, identifier, body: calls.append((operation, identifier, body))
    selected = [False]
    def choose():
        dialog = app.activeModalWidget()
        if not dialog: QTimer.singleShot(20, choose); return
        tables = dialog.findChildren(QTableWidget)
        if len(tables) != 2 or not all(t.rowCount() for t in tables): QTimer.singleShot(20, choose); return
        try:
            if not selected[0]:
                for table in tables: table.selectRow(0)
                selected[0] = True
            button = next(x for x in dialog.findChildren(QPushButton) if x.text() == 'Planificar traslado')
            if not button.isEnabled(): QTimer.singleShot(20, choose); return
            next(x for x in dialog.findChildren(QLineEdit) if x.maxLength() == 1000).setText('Plan sintético autorizado')
            dates = dialog.findChildren(QDateTimeEdit)
            dates[1].setDateTime(dates[0].dateTime().addSecs(1800))
            dialog.findChild(QCheckBox).setChecked(True)
            if os.environ.get('DESKTOP_CAPTURE_DIR'):
                assert dialog.grab().save(str(Path(os.environ['DESKTOP_CAPTURE_DIR']) / 'planificacion-doble.png'))
            button.click()
        except Exception as exc:  # noqa: BLE001 - sin datos privados en la evidencia
            errors.append(type(exc).__name__)
            dialog.reject()
    QTimer.singleShot(0, choose)
    window.plan_shipment()
    assert not errors
    assert len(calls) == 1
    operation, identifier, body = calls[0]
    assert operation == 'shipment_create' and identifier is None
    assert body['reservation_id'] == reservation and body['transport_user_id'] == transport
    assert body['human_confirmation'] == 'true'
