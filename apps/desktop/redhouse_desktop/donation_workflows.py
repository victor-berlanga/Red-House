"""Colecta y procesamiento documentados con revisión humana."""
from uuid import UUID

from .session_context import OperationContext

from PySide6.QtCore import QDateTime, Qt, QTimer
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateTimeEdit,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from .client import ContractError


def collect_dialog(window, worker_type):
    dialog = QDialog(window)
    dialog.setWindowTitle('Registrar colecta documentada')
    dialog.resize(780, 640)
    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(24, 20, 24, 20)
    layout.setSpacing(12)
    title = QLabel(dialog.windowTitle())
    title.setObjectName('title')
    layout.addWidget(title)
    hint = QLabel('Busca y selecciona al donante con evaluación vigente. La institución comprobará el consentimiento y la elegibilidad al registrar.')
    hint.setWordWrap(True)
    layout.addWidget(hint)
    search_row = QHBoxLayout()
    search = QLineEdit()
    search.setPlaceholderText('Buscar por nombre o folio')
    search.setAccessibleName('Buscar donante por nombre o folio')
    find = QPushButton('Buscar')
    search_row.addWidget(search)
    search_row.addWidget(find)
    layout.addLayout(search_row)
    table = QTableWidget(0, 3)
    table.setAccessibleName('Donantes con evaluación elegible')
    table.setHorizontalHeaderLabels(('Folio', 'Nombre', 'Grupo'))
    table.setSelectionBehavior(QTableWidget.SelectRows)
    table.setSelectionMode(QTableWidget.SingleSelection)
    table.setEditTriggers(QTableWidget.NoEditTriggers)
    table.verticalHeader().hide()
    table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    layout.addWidget(table, 1)
    nav = QHBoxLayout()
    previous, following, refresh = QPushButton('Anterior'), QPushButton('Siguiente'), QPushButton('Actualizar')
    page_label = QLabel()
    page_label.setMinimumWidth(160)
    for widget in (previous, page_label, following, refresh): nav.addWidget(widget)
    nav.addStretch()
    layout.addLayout(nav)
    form = QFormLayout()
    kind = QComboBox()
    kind.addItem('Selecciona un tipo', '')
    kind.addItem('Sangre', 'BLOOD')
    kind.addItem('Órgano', 'ORGAN')
    form.addRow('Tipo de donación', kind)
    component = QComboBox()
    component.addItem('Selecciona un tipo primero', '')
    form.addRow('Producto u órgano', component)
    def choose_kind():
        component.clear()
        component.addItem('Selecciona una opción', '')
        options = (('Eritrocitos', 'RBC'), ('Plasma', 'PLASMA'), ('Plaquetas', 'PLATELETS')) if kind.currentData() == 'BLOOD' else (('Riñón', 'KIDNEY'), ('Hígado', 'LIVER'), ('Corazón', 'HEART')) if kind.currentData() == 'ORGAN' else ()
        for name, code in options: component.addItem(name, code)
    kind.currentIndexChanged.connect(choose_kind)
    collected = QDateTimeEdit(QDateTime.currentDateTime())
    collected.setCalendarPopup(True)
    collected.setDisplayFormat('dd/MM/yyyy HH:mm:ss')
    form.addRow('Colecta documentada · hora local', collected)
    date_confirm = QCheckBox('Confirmo la fecha y hora documentadas.')
    form.addRow(date_confirm)
    reason = QLineEdit()
    reason.setMaxLength(1000)
    form.addRow('Motivo documentado', reason)
    confirm = QCheckBox('Confirmo el registro de esta colecta.')
    form.addRow(confirm)
    layout.addLayout(form)
    status = QLabel('')
    status.setWordWrap(True)
    layout.addWidget(status)
    actions = QHBoxLayout()
    cancel, save = QPushButton('Cancelar'), QPushButton('Registrar colecta')
    save.setObjectName('primary')
    actions.addStretch()
    actions.addWidget(cancel)
    actions.addWidget(save)
    layout.addLayout(actions)
    binding = OperationContext(window)
    client = binding.client
    state = {'alive': True, 'busy': False, 'rows': [], 'page': 1, 'total': 0, 'body': None}

    def current():
        return binding.current()

    def selection():
        index = table.currentRow()
        return state['rows'][index] if 0 <= index < len(state['rows']) else None

    def ready():
        row = selection()
        save.setEnabled(bool(row and current() and not state['busy']))
        if row and current() and not state['busy']:
            status.setText('Donante seleccionado: ' + row['folio'] + ' · ' + row['display_name'] + '.')

    def fetch(page):
        if state['busy']: return
        state.update(busy=True, rows=[])
        table.setRowCount(0)
        for button in (previous, following, refresh, save): button.setEnabled(False)
        status.setText('Consultando donantes…')
        params = {'page': page, 'page_size': 10, 'status': 'ELIGIBLE'}
        if search.text().strip(): params['q'] = search.text().strip()
        def work():
            data = client.authorized('donantes', '/api/v1/donors', 'donors', params=params)
            if type(data.get('page')) is not int or data['page'] != page or type(data.get('total')) is not int or data['total'] < 0 or not isinstance(data.get('items'), list) or len(data['items']) > 10:
                raise ContractError('Página de donantes inválida.')
            rows = []
            for row in data['items']:
                try:
                    if str(UUID(row['id'])) != row['id'] or row['tenant_id'] != actor[1] or row['status'] != 'ELIGIBLE' or not row['folio'] or not row['display_name']:
                        raise ValueError()
                except (KeyError, TypeError, ValueError, AttributeError) as exc:
                    raise ContractError('Donante no disponible para la selección.') from exc
                rows.append({key: row[key] for key in ('id', 'folio', 'display_name', 'blood_group')})
            return data, rows
        worker = worker_type(work)
        if not hasattr(window, '_request_workers'): window._request_workers = []
        window._request_workers.append(worker)
        def finish(result, error=False):
            window._request_workers.remove(worker)
            if not state['alive']: return
            state['busy'] = False
            if not current():
                status.setText('La sesión cambió. Cierra este formulario y vuelve a ingresar.')
                return
            refresh.setEnabled(True)
            if error:
                status.setText('No se pudieron consultar donantes. Vuelve a intentar.')
                return
            data, rows = result
            state.update(page=data['page'], total=data['total'], rows=rows)
            table.setRowCount(len(rows))
            for index, row in enumerate(rows):
                for column, key in enumerate(('folio', 'display_name', 'blood_group')):
                    cell = QTableWidgetItem(str(row[key]))
                    cell.setToolTip(str(row[key]))
                    table.setItem(index, column, cell)
            page_label.setText('Página ' + str(page) + ' · ' + str(data['total']) + (' registro' if data['total'] == 1 else ' registros'))
            previous.setEnabled(page > 1)
            following.setEnabled(page * 10 < data['total'])
            status.setText('Selecciona un donante.' if rows else 'No hay donantes para esta búsqueda.')
            ready()
        worker.signals.done.connect(lambda result: finish(result))
        worker.signals.failed.connect(lambda error: finish(error, True))
        window.pool.start(worker)

    def submit():
        row = selection()
        if not current() or state['busy'] or not row or not kind.currentData() or not component.currentData() or not date_confirm.isChecked() or len(reason.text().strip()) < 6 or not confirm.isChecked():
            QMessageBox.warning(dialog, 'Datos incompletos', 'Selecciona donante y producto; confirma la fecha, escribe el motivo y confirma el registro.')
            return
        state['body'] = {'donor_id': row['id'], 'kind': kind.currentData(), 'component': component.currentData(), 'collected_at': collected.dateTime().toUTC().toString(Qt.ISODate), 'reason': reason.text().strip(), 'human_confirmation': 'true'}
        dialog.accept()
    table.itemSelectionChanged.connect(ready)
    find.clicked.connect(lambda: fetch(1))
    search.returnPressed.connect(lambda: fetch(1))
    previous.clicked.connect(lambda: fetch(state['page'] - 1))
    following.clicked.connect(lambda: fetch(state['page'] + 1))
    refresh.clicked.connect(lambda: fetch(state['page']))
    save.clicked.connect(submit)
    cancel.clicked.connect(dialog.reject)
    save.setEnabled(False)
    QTimer.singleShot(0, lambda: fetch(1))
    accepted = dialog.exec()
    state['alive'] = False
    return state['body'] if accepted == QDialog.Accepted else None


def processing_dialog(window, donation):
    dialog = QDialog(window)
    dialog.setWindowTitle('Documentar procesamiento')
    dialog.resize(650, 420)
    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(24, 20, 24, 20)
    layout.setSpacing(12)
    title = QLabel(dialog.windowTitle())
    title.setObjectName('title')
    layout.addWidget(title)
    hint = QLabel('Revisa la colecta seleccionada. Rechazarla impide continuar su procesamiento.')
    hint.setWordWrap(True)
    layout.addWidget(hint)
    form = QFormLayout()
    form.addRow('Donante', QLabel(donation['_donor_folio'] + ' · ' + donation['_donor_name']))
    moment = QDateTime.fromString(donation['collected_at'], Qt.ISODate)
    if not moment.isValid(): raise ContractError('La fecha de la colecta no está disponible.')
    form.addRow('Colecta · hora local', QLabel(moment.toLocalTime().toString('dd/MM/yyyy HH:mm:ss')))
    product = {'RBC':'Eritrocitos','PLASMA':'Plasma','PLATELETS':'Plaquetas','KIDNEY':'Riñón','LIVER':'Hígado','HEART':'Corazón'}.get(donation.get('component'), 'Producto no disponible')
    form.addRow('Producto', QLabel(product))
    reference = QLineEdit(donation['id'])
    reference.setReadOnly(True)
    reference.setAccessibleName('Referencia completa de la colecta')
    form.addRow('Referencia de colecta', reference)
    choice = QComboBox()
    choice.addItem('Selecciona un resultado', '')
    choice.addItem('Procesada', 'PROCESSED')
    choice.addItem('Rechazada', 'REJECTED')
    form.addRow('Resultado documentado', choice)
    reason = QLineEdit()
    reason.setMaxLength(1000)
    form.addRow('Motivo documentado', reason)
    confirm = QCheckBox('Confirmo el resultado documentado.')
    form.addRow(confirm)
    layout.addLayout(form)
    actions = QHBoxLayout()
    cancel, save = QPushButton('Cancelar'), QPushButton('Registrar resultado')
    save.setObjectName('primary')
    actions.addStretch()
    actions.addWidget(cancel)
    actions.addWidget(save)
    layout.addLayout(actions)
    body = {'value': None}
    def submit():
        if not choice.currentData() or len(reason.text().strip()) < 6 or not confirm.isChecked():
            QMessageBox.warning(dialog, 'Datos incompletos', 'Selecciona el resultado, escribe el motivo y confirma.')
            return
        if choice.currentData() == 'REJECTED' and QMessageBox.question(dialog, 'Confirmar rechazo', 'La colecta quedará rechazada. ¿Confirmas este resultado documentado?') != QMessageBox.Yes:
            return
        body['value'] = {'state': choice.currentData(), 'version': donation['version'], 'reason': reason.text().strip(), 'human_confirmation': 'true'}
        dialog.accept()
    cancel.clicked.connect(dialog.reject)
    save.clicked.connect(submit)
    return body['value'] if dialog.exec() == QDialog.Accepted else None
