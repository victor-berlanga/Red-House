"""Selección paginada de procedencia institucional ya procesada."""
from datetime import datetime
from uuid import UUID

from PySide6.QtCore import QDateTime, Qt, QTimer
from PySide6.QtWidgets import (
    QCheckBox,
    QDateTimeEdit,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from .client import ContractError


def select_processed_donation(window, worker_type, display):
    dialog = QDialog(window)
    dialog.setWindowTitle('Seleccionar donación procesada')
    dialog.resize(900, 520)
    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(24, 20, 24, 20)
    layout.setSpacing(12)
    heading = QLabel(dialog.windowTitle())
    heading.setObjectName('title')
    layout.addWidget(heading)
    help_text = QLabel('Donaciones sanguíneas procesadas de tu institución. Selecciona una fila y verifica su referencia antes de continuar.')
    help_text.setWordWrap(True)
    layout.addWidget(help_text)
    filters = QHBoxLayout()
    use_date = QCheckBox('Desde fecha de registro · hora local')
    start_date = QDateTimeEdit(QDateTime.currentDateTime())
    start_date.setCalendarPopup(True)
    start_date.setDisplayFormat('dd/MM/yyyy HH:mm:ss')
    start_date.setAccessibleName('Fecha inicial de registro')
    start_date.setEnabled(False)
    use_date.toggled.connect(start_date.setEnabled)
    apply_date = QPushButton('Aplicar fecha')
    for widget in (use_date, start_date, apply_date): filters.addWidget(widget)
    layout.addLayout(filters)
    table = QTableWidget(0, 4)
    table.setAccessibleName('Donaciones procesadas')
    table.setHorizontalHeaderLabels(('Donante', 'Colecta · hora local', 'Producto', 'Grupo'))
    table.setSelectionBehavior(QTableWidget.SelectRows)
    table.setSelectionMode(QTableWidget.SingleSelection)
    table.setEditTriggers(QTableWidget.NoEditTriggers)
    table.verticalHeader().hide()
    table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
    for column in (1, 2, 3):
        table.horizontalHeader().setSectionResizeMode(column, QHeaderView.ResizeToContents)
    layout.addWidget(table, 1)
    nav = QHBoxLayout()
    previous, following, refresh = QPushButton('Anterior'), QPushButton('Siguiente'), QPushButton('Actualizar')
    page_label = QLabel()
    for widget in (previous, page_label, following, refresh): nav.addWidget(widget)
    nav.addStretch()
    layout.addLayout(nav)
    layout.addWidget(QLabel('Referencia del registro seleccionado · se puede copiar'))
    reference = QLineEdit()
    reference.setReadOnly(True)
    reference.setAccessibleName('Referencia completa de la donación seleccionada')
    layout.addWidget(reference)
    status = QLabel('')
    status.setWordWrap(True)
    layout.addWidget(status)
    actions = QHBoxLayout()
    cancel, select = QPushButton('Cancelar'), QPushButton('Usar donación')
    select.setObjectName('primary')
    actions.addStretch()
    actions.addWidget(cancel)
    actions.addWidget(select)
    layout.addLayout(actions)
    client = window.client
    actor = (client.user['id'], client.user['tenant_id'], client.user['role'])
    state = {'alive': True, 'busy': False, 'rows': [], 'page': 1, 'total': 0, 'chosen': None}

    def current():
        user = client.user or {}
        return window.client is client and (user.get('id'), user.get('tenant_id'), user.get('role')) == actor

    def choice():
        index = table.currentRow()
        return state['rows'][index] if 0 <= index < len(state['rows']) else None

    def selection_changed():
        row = choice()
        reference.setText(row['id'] if row else '')
        select.setEnabled(bool(row and current() and not state['busy']))
        if row: status.setText('Verifica la referencia y confirma la donación seleccionada.')

    def fetch(page):
        if state['busy']: return
        state.update(busy=True, rows=[])
        table.setRowCount(0)
        reference.clear()
        for widget in (previous, following, refresh, select): widget.setEnabled(False)
        status.setText('Consultando donaciones procesadas…')
        params={'page': page, 'page_size': 10, 'kind': 'BLOOD', 'status': 'PROCESSED'}
        if use_date.isChecked():
            params.update(from_at=start_date.dateTime().toUTC().toString(Qt.ISODate), date_field='created_at')
        def work():
            data = client.authorized('donantes', '/api/v1/donations', 'donations_list', params=params)
            if type(data.get('page')) is not int or data['page'] != page or type(data.get('total')) is not int or data['total'] < 0 or not isinstance(data.get('items'), list) or len(data['items']) > 10:
                raise ContractError('Página de donaciones inválida.')
            rows = []
            donors = {}
            for row in data['items']:
                try:
                    if str(UUID(row['id'])) != row['id'] or str(UUID(row['donor_id'])) != row['donor_id']:
                        raise ValueError()
                    instant = datetime.fromisoformat(row['collected_at'].replace('Z', '+00:00'))
                    if instant.tzinfo is None or row['tenant_id'] != actor[1] or row['kind'] != 'BLOOD' or row['status'] != 'PROCESSED':
                        raise ValueError()
                except (KeyError, TypeError, ValueError, AttributeError) as exc:
                    raise ContractError('Donación no disponible para la selección.') from exc
                donor_id = row['donor_id']
                if donor_id not in donors:
                    detail = client.authorized('donantes', '/api/v1/donors/' + donor_id, 'donor_detail')
                    if detail.get('id') != donor_id or detail.get('tenant_id') != actor[1] or not detail.get('folio') or not detail.get('display_name'):
                        raise ContractError('La referencia del donante no corresponde a la donación.')
                    donors[donor_id] = {'id': detail['id'], 'tenant_id': detail['tenant_id'], 'folio': detail['folio'], 'display_name': detail['display_name']}
                    del detail
                donor = donors[donor_id]
                rows.append((dict(row, _donor_name=donor['display_name'], _donor_folio=donor['folio']), donor))
            return data, rows
        worker = worker_type(work)
        if not hasattr(window, '_request_workers'): window._request_workers = []
        window._request_workers.append(worker)
        def finish(result, error=False):
            window._request_workers.remove(worker)
            if not state['alive']: return
            state['busy'] = False
            if not current():
                status.setText('La sesión cambió. Cierra esta ventana y vuelve a ingresar.')
                return
            refresh.setEnabled(True)
            if error:
                status.setText('No se pudieron consultar donaciones. Vuelve a intentar.')
                return
            data, rows = result
            state.update(page=data['page'], total=data['total'], rows=[row for row, _ in rows])
            table.setRowCount(len(rows))
            for index, (row, donor) in enumerate(rows):
                instant = datetime.fromisoformat(row['collected_at'].replace('Z', '+00:00')).astimezone()
                values = (donor['folio'] + ' · ' + donor['display_name'], instant.strftime('%d/%m/%Y %H:%M:%S'), display(row.get('component')), row.get('blood_group', '—'))
                for column, value in enumerate(values):
                    cell = QTableWidgetItem(str(value))
                    if column == 0: cell.setToolTip(str(value))
                    table.setItem(index, column, cell)
            page_label.setText('Página ' + str(page) + ' · ' + str(data['total']) + (' registro' if data['total'] == 1 else ' registros'))
            previous.setEnabled(page > 1)
            following.setEnabled(page * 10 < data['total'])
            status.setText('Selecciona una donación.' if rows else 'No hay donaciones procesadas en esta página.')
        worker.signals.done.connect(lambda result: finish(result))
        worker.signals.failed.connect(lambda error: finish(error, True))
        window.pool.start(worker)

    def accept():
        if not current() or state['busy'] or not choice(): return
        state['chosen'] = dict(choice())
        dialog.accept()

    table.itemSelectionChanged.connect(selection_changed)
    previous.clicked.connect(lambda: fetch(state['page'] - 1))
    following.clicked.connect(lambda: fetch(state['page'] + 1))
    refresh.clicked.connect(lambda: fetch(state['page']))
    apply_date.clicked.connect(lambda: fetch(1))
    cancel.clicked.connect(dialog.reject)
    select.clicked.connect(accept)
    select.setEnabled(False)
    QTimer.singleShot(0, lambda: fetch(1))
    accepted = dialog.exec()
    state['alive'] = False
    return state['chosen'] if accepted == QDialog.Accepted else None
