"""Corrección documentada de unidad en cuarentena."""
import re

from .session_context import OperationContext

from PySide6.QtCore import QDateTime, Qt, QTimer
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateTimeEdit,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)


def resource_edit_dialog(window, item, location_name, worker_type, display):
    binding = OperationContext(window)
    dialog = QDialog(window)
    dialog.setWindowTitle('Corregir unidad en cuarentena')
    dialog.resize(650, 500)
    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(24, 20, 24, 20)
    layout.setSpacing(12)
    heading = QLabel(dialog.windowTitle())
    heading.setObjectName('title')
    layout.addWidget(heading)
    hint = QLabel('Revisa y corrige el folio, la caducidad o la ubicación según la documentación de la unidad.')
    hint.setWordWrap(True)
    layout.addWidget(hint)
    form = QFormLayout()
    folio = QLineEdit(item['folio'])
    folio.setMaxLength(30)
    form.addRow('Folio de unidad', folio)
    form.addRow('Tipo y producto', QLabel(display(item['kind']) + ' · ' + display(item['component'])))
    form.addRow('Grupo sanguíneo', QLabel(item['blood_group']))
    current = QDateTime.fromString(item['expires_at'], Qt.ISODate)
    if not current.isValid():
        raise ValueError('La fecha de caducidad no está disponible para corregir.')
    original_expiry = current.toLocalTime()
    expiry = QDateTimeEdit(original_expiry)
    expiry.setCalendarPopup(True)
    expiry.setDisplayFormat('dd/MM/yyyy HH:mm:ss')
    form.addRow('Caducidad documentada · hora local', expiry)
    confirm_expiry = QCheckBox('Confirmo la caducidad documentada.')
    form.addRow(confirm_expiry)
    form.addRow('Ubicación actual', QLabel(location_name))
    choices = QComboBox()
    choices.setAccessibleName('Nueva ubicación de la unidad')
    form.addRow('Cambiar ubicación', choices)
    layout.addLayout(form)
    navigation = QHBoxLayout()
    previous, following = QPushButton('Anterior'), QPushButton('Siguiente')
    previous.setAccessibleName('Página anterior de ubicaciones')
    following.setAccessibleName('Página siguiente de ubicaciones')
    page_label = QLabel()
    retry = QPushButton('Actualizar ubicaciones')
    for widget in (previous, page_label, following, retry): navigation.addWidget(widget)
    layout.addLayout(navigation)
    fields = QFormLayout()
    reason = QLineEdit()
    reason.setMaxLength(1000)
    fields.addRow('Motivo de corrección', reason)
    confirm = QCheckBox('Confirmo la corrección documentada.')
    fields.addRow(confirm)
    layout.addLayout(fields)
    status = QLabel('')
    status.setWordWrap(True)
    layout.addWidget(status)
    controls = QHBoxLayout()
    save, cancel = QPushButton('Guardar corrección'), QPushButton('Cancelar')
    save.setObjectName('primary')
    controls.addWidget(save)
    controls.addWidget(cancel)
    layout.addLayout(controls)
    state = {'alive': True, 'busy': False, 'page': 1, 'total': 0, 'body': None}

    def reset_choices():
        choices.clear()
        choices.addItem('Mantener ubicación actual', 'KEEP')
        choices.addItem('Dejar sin ubicación', 'NONE')

    def fetch(page):
        if state['busy']: return
        state['busy'] = True
        previous.setEnabled(False)
        following.setEnabled(False)
        retry.setEnabled(False)
        save.setEnabled(False)
        reset_choices()
        status.setText('Consultando ubicaciones de tu institución…')
        def query():
            binding.check()
            result = binding.client.authorized('identidad-acceso', '/api/v1/catalogues/locations', 'locations_list_rows',
                                               params={'page': page, 'page_size': 20, 'active': 'true'})
            binding.check(); return result
        worker = worker_type(query)
        if not hasattr(window, '_request_workers'): window._request_workers = []
        window._request_workers.append(worker)
        def finish(data, error=False):
            window._request_workers.remove(worker)
            if not state['alive']: return
            if not binding.current(): choices.clear(); save.setEnabled(False); status.setText('La sesión cambió. Cierra y vuelve a consultar.'); return
            state['busy'] = False
            retry.setEnabled(True)
            save.setEnabled(True)
            if error:
                status.setText('No se pudieron consultar ubicaciones. Actualiza o conserva la actual.')
                return
            state.update(page=data['page'], total=data['total'])
            for row in data['items']:
                if row['active']: choices.addItem(row['name'], row['id'])
            page_label.setText('Página ' + str(state['page']) + ' · ' + str(state['total']) + (' registro' if state['total'] == 1 else ' registros'))
            previous.setEnabled(state['page'] > 1)
            following.setEnabled(state['page'] * 20 < state['total'])
            status.setText('Selecciona una ubicación o conserva la actual.' if data['items'] else 'No hay ubicaciones activas en esta página.')
        worker.signals.done.connect(lambda data: finish(data))
        worker.signals.failed.connect(lambda error: finish(error, True))
        window.pool.start(worker)

    def submit():
        if not binding.current(): status.setText('La sesión cambió. Cierra y vuelve a consultar.'); return
        if not re.fullmatch(r'[A-Za-z0-9_-]{6,30}', folio.text().strip()) or len(reason.text().strip()) < 6 or not confirm_expiry.isChecked() or not confirm.isChecked():
            QMessageBox.warning(dialog, 'Datos incompletos', 'Revisa el folio, confirma la caducidad y escribe y confirma el motivo.')
            return
        selected = choices.currentData()
        location = item.get('location_id') if selected == 'KEEP' else None if selected == 'NONE' else selected
        state['body'] = {
            'folio': folio.text().strip(), 'kind': item['kind'], 'component': item['component'],
            'blood_group': item['blood_group'], 'expires_at': item['expires_at'] if expiry.dateTime() == original_expiry else expiry.dateTime().toUTC().toString(Qt.ISODate),
            'collected_at': item.get('collected_at'), 'location_id': location, 'donation_id': item.get('donation_id'),
            'version': item['version'], 'reason': reason.text().strip(), 'human_confirmation': 'true',
        }
        dialog.accept()

    previous.clicked.connect(lambda: fetch(state['page'] - 1))
    following.clicked.connect(lambda: fetch(state['page'] + 1))
    retry.clicked.connect(lambda: fetch(state['page']))
    save.clicked.connect(submit)
    cancel.clicked.connect(dialog.reject)
    reset_choices()
    QTimer.singleShot(0, lambda: fetch(1))
    accepted = dialog.exec()
    state['alive'] = False
    return state['body'] if accepted == QDialog.Accepted else None
