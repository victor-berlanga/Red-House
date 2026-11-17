"""Planificación regional: selección autorizada y confirmación humana."""
from threading import Lock
from .session_context import OperationContext

from PySide6.QtCore import QDateTime, Qt, QTimer
from PySide6.QtWidgets import (
    QCheckBox, QDateTimeEdit, QDialog, QFormLayout, QHBoxLayout, QLabel,
    QLineEdit, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QHeaderView,
)


def planning_dialog(window, worker_type, display):
    binding = OperationContext(window)
    dialog = QDialog(window)
    dialog.setWindowTitle('Planificar traslado')
    dialog.resize(850, 720)
    layout = QVBoxLayout(dialog)
    note = QLabel('Selecciona una reserva confirmada y una cuenta de traslado de la institución de origen. El servicio verificará la ruta y la vigencia.')
    note.setWordWrap(True)
    layout.addWidget(note)
    state = {'alive': True, 'body': None, 'reservation': None, 'detail': None}
    panels = {}
    institution_cache = {'names': None}
    institution_lock = Lock()
    for key, title, headers in (
        ('reservation', 'Reservas sin traslado', ('Unidad', 'Producto', 'Origen', 'Destino')),
        ('transport', 'Personal de traslado', ('Cuenta', 'Institución')),
    ):
        layout.addWidget(QLabel(title))
        table = QTableWidget(0, len(headers))
        table.setAccessibleName(title)
        table.setHorizontalHeaderLabels(headers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSelectionMode(QTableWidget.SingleSelection)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.verticalHeader().hide()
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(table, 1)
        nav = QHBoxLayout()
        previous, following = QPushButton('Anterior'), QPushButton('Siguiente')
        previous.setAccessibleName('Página anterior de ' + title.lower())
        following.setAccessibleName('Página siguiente de ' + title.lower())
        page = QLabel()
        for widget in (previous, page, following): nav.addWidget(widget)
        refresh = QPushButton('Actualizar reservas') if key == 'reservation' else None
        if refresh:
            refresh.setAccessibleName('Actualizar reservas de la página actual')
            nav.addWidget(refresh)
        nav.addStretch()
        layout.addLayout(nav)
        panels[key] = {'table': table, 'previous': previous, 'following': following,
                       'page_label': page, 'refresh': refresh, 'page': 1, 'total': 0, 'rows': [], 'busy': False}
    search = QLineEdit()
    search.setPlaceholderText('Buscar cuenta de traslado')
    search.setAccessibleName('Buscar cuenta de traslado')
    search_row = QHBoxLayout()
    search_row.addWidget(search)
    search_button = QPushButton('Buscar cuenta')
    search_row.addWidget(search_button)
    layout.addLayout(search_row)
    info = QLabel('Selecciona una reserva para consultar su ruta y caducidad.')
    info.setWordWrap(True)
    layout.addWidget(info)
    fields = QFormLayout()
    fields.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
    departure = QDateTimeEdit(QDateTime.currentDateTime())
    arrival = QDateTimeEdit(QDateTime.currentDateTime())
    for field in (departure, arrival):
        field.setCalendarPopup(True)
        field.setDisplayFormat('dd/MM/yyyy HH:mm:ss')
    fields.addRow('Salida prevista · hora local', departure)
    fields.addRow('Llegada prevista · hora local', arrival)
    reason = QLineEdit()
    reason.setMaxLength(1000)
    fields.addRow('Motivo', reason)
    confirm = QCheckBox('Confirmo la reserva, responsable y horarios previstos.')
    fields.addRow(confirm)
    layout.addLayout(fields)
    status = QLabel('')
    status.setWordWrap(True)
    layout.addWidget(status)
    actions = QHBoxLayout()
    save, cancel = QPushButton('Planificar traslado'), QPushButton('Cancelar')
    actions.addWidget(save)
    actions.addWidget(cancel)
    layout.addLayout(actions)

    def selection(key):
        panel = panels[key]
        index = panel['table'].currentRow()
        return panel['rows'][index] if 0 <= index < len(panel['rows']) else None

    def ready():
        selected = selection('reservation')
        driver = selection('transport')
        valid = bool(selected and driver and state['detail'] and
                     state['reservation'] == selected['id'] and
                     selected['origin_id'] == driver['tenant_id'] and
                     not any(panel['busy'] for panel in panels.values()))
        save.setEnabled(valid)
        if valid: status.setText('Reserva y cuenta seleccionadas. Confirma los horarios y el motivo.')

    def launch(fn, done, failed):
        def guarded():
            binding.check(); result = fn(); binding.check(); return result
        worker = worker_type(guarded)
        if not hasattr(window, '_request_workers'): window._request_workers = []
        window._request_workers.append(worker)
        def finish(callback, value):
            window._request_workers.remove(worker)
            if state['alive'] and binding.current(): callback(value)
            elif state['alive']:
                for panel in panels.values(): panel['rows'] = []; panel['table'].setRowCount(0)
                save.setEnabled(False); status.setText('La sesión cambió. Cierra y vuelve a consultar.')
        worker.signals.done.connect(lambda value: finish(done, value))
        worker.signals.failed.connect(lambda error: finish(failed, error))
        window.pool.start(worker)

    def institutions():
        # Una sola carga por diálogo; el bloqueo conserva singleflight si cambia el pool.
        with institution_lock:
            if institution_cache['names'] is not None:
                return institution_cache['names']
            result = {}
            for page in range(1, 51):
                data = binding.client.authorized('identidad-acceso', '/api/v1/institutions', 'institutions', params={'page': page, 'page_size': 100})
                result.update({item['id']: item['name'] for item in data['items']})
                if page * 100 >= data['total']:
                    institution_cache['names'] = result
                    return result
            raise ValueError('El directorio regional supera el límite de consulta.')

    def fetch(key, page):
        panel = panels[key]
        if panel['busy']: return
        panel.update(busy=True, rows=[])
        panel['table'].setRowCount(0)
        panel['previous'].setEnabled(False)
        panel['following'].setEnabled(False)
        if panel['refresh']: panel['refresh'].setEnabled(False)
        if key == 'reservation': state.update(reservation=None, detail=None)
        ready()
        status.setText('Consultando información autorizada…')
        query = search.text().strip()
        def work():
            names = institutions()
            if key == 'reservation':
                data = binding.client.authorized('inventario', '/api/v1/reservations', 'reservation_list', params={'page': page, 'page_size': 10, 'status': 'RESERVED', 'unplanned': 'true'})
                rows = []
                for row in data['items']:
                    resource = binding.client.authorized('inventario', '/api/v1/resources/' + row['resource_id'], 'resource_detail')
                    rows.append((row, (resource['folio'], display(resource.get('component')), names.get(row['origin_id'], 'Institución no disponible'), names.get(row['destination_id'], 'Institución no disponible'))))
            else:
                params = {'page': page, 'page_size': 10, 'role': 'TRANSPORT'}
                if query: params['q'] = query
                data = binding.client.authorized('identidad-acceso', '/api/v1/users', 'user_list', params=params)
                rows = [(row, (row['username'], names.get(row['tenant_id'], 'Institución no disponible'))) for row in data['items']]
            return data, rows
        def done(result):
            data, rows = result
            panel.update(busy=False, page=data['page'], total=data['total'], rows=[row for row, _ in rows])
            panel['table'].setRowCount(len(rows))
            for index, (_, values) in enumerate(rows):
                for column, value in enumerate(values): panel['table'].setItem(index, column, QTableWidgetItem(str(value)))
            panel['page_label'].setText('Página ' + str(panel['page']) + ' · ' + str(panel['total']) + (' registro' if panel['total'] == 1 else ' registros'))
            panel['previous'].setEnabled(panel['page'] > 1)
            panel['following'].setEnabled(panel['page'] * 10 < panel['total'])
            if panel['refresh']: panel['refresh'].setEnabled(True)
            status.setText('Selecciona una reserva y una cuenta de su institución de origen.' if rows else 'No hay resultados en esta página.')
            ready()
        def failed(_error):
            panel['busy'] = False
            if panel['refresh']: panel['refresh'].setEnabled(True)
            status.setText('No se pudo consultar la información. Intenta de nuevo.')
            ready()
        launch(work, done, failed)

    def selected_reservation():
        row = selection('reservation')
        state.update(reservation=None, detail=None)
        ready()
        if not row:
            info.setText('Selecciona una reserva para consultar su ruta y caducidad.')
            return
        identifier = row['id']
        info.setText('Consultando la ruta y la caducidad…')
        def work():
            reservation = binding.client.authorized('inventario', '/api/v1/reservations/' + identifier, 'reservation_detail')
            route = binding.client.authorized('priorizacion-geografia', '/api/v1/routes/' + reservation['route_id'], 'route_detail')
            resource = binding.client.authorized('inventario', '/api/v1/resources/' + reservation['resource_id'], 'resource_detail')
            return reservation, route, resource
        def done(result):
            current = selection('reservation')
            if not current or current['id'] != identifier: return
            reservation, route, resource = result
            if (reservation['id'] != identifier or resource['id'] != reservation['resource_id'] or route['id'] != reservation['route_id']
                    or reservation['origin_id'] != current['origin_id']
                    or route['origin_id'] != reservation['origin_id']
                    or route['destination_id'] != reservation['destination_id']):
                info.setText('Los datos de la ruta no corresponden a la reserva. Actualiza la lista.')
                return
            if route['version'] != reservation['route_version']:
                info.setText('La ruta cambió desde la reserva. Solicita su revisión antes de planificar.')
                return
            state.update(reservation=identifier, detail=result)
            info.setText('Ruta: ' + str(route['distance_km']) + ' km · ' + str(route['travel_minutes']) + ' min · versión ' + str(route['version']) + '. Caducidad: ' + display(resource['expires_at']))
            ready()
        def failed(_error):
            current = selection('reservation')
            if current and current['id'] == identifier:
                info.setText('No se pudo consultar la ruta. Vuelve a seleccionar la reserva.')
        launch(work, done, failed)

    def submit():
        if not binding.current(): status.setText('La sesión cambió. Cierra y vuelve a consultar.'); return
        row, driver = selection('reservation'), selection('transport')
        if not row or not driver or not state['detail'] or state['reservation'] != row['id'] or driver['tenant_id'] != row['origin_id'] or len(reason.text().strip()) < 6 or not confirm.isChecked():
            QMessageBox.warning(dialog, 'Datos incompletos', 'Selecciona una reserva y una cuenta de origen, escribe el motivo y confirma los datos.')
            return
        if arrival.dateTime().toUTC() <= departure.dateTime().toUTC():
            QMessageBox.warning(dialog, 'Horarios inválidos', 'La llegada debe ser posterior a la salida.')
            return
        state['body'] = {'reservation_id': row['id'], 'transport_user_id': driver['id'], 'departure_at': departure.dateTime().toUTC().toString(Qt.ISODate), 'eta': arrival.dateTime().toUTC().toString(Qt.ISODate), 'reason': reason.text().strip(), 'human_confirmation': 'true'}
        dialog.accept()

    for key, panel in panels.items():
        panel['previous'].clicked.connect(lambda _=False, k=key: fetch(k, panels[k]['page'] - 1))
        panel['following'].clicked.connect(lambda _=False, k=key: fetch(k, panels[k]['page'] + 1))
        panel['table'].itemSelectionChanged.connect(selected_reservation if key == 'reservation' else ready)
        if panel['refresh']:
            panel['refresh'].clicked.connect(lambda _=False, k=key: fetch(k, panels[k]['page']))
    search.returnPressed.connect(lambda: fetch('transport', 1))
    search_button.clicked.connect(lambda: fetch('transport', 1))
    save.clicked.connect(submit)
    cancel.clicked.connect(dialog.reject)
    ready()
    QTimer.singleShot(0, lambda: fetch('reservation', 1))
    QTimer.singleShot(0, lambda: fetch('transport', 1))
    accepted = dialog.exec()
    state['alive'] = False
    return state['body'] if accepted == QDialog.Accepted else None
