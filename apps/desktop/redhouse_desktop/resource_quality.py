"""Selección documentada de perfil y confirmación de liberación."""
from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QDialog, QFormLayout, QHeaderView,
    QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QTableWidget,
    QTableWidgetItem, QVBoxLayout,
)


def missing_label(value):
    value = str(value)
    prefixes = {'STALE:': 'Resultado vencido: ', 'DOCUMENT:': 'Documento pendiente: ',
                'CONTRADICTORY:': 'Resultados por revisar: ', 'HLA:': 'Estudio HLA por completar: '}
    for prefix, description in prefixes.items():
        if value.startswith(prefix): return description + value[len(prefix):]
    return 'Resultado o revisión pendiente: ' + value


def quality_dialog(window, resource, controls, work_type, display, *, release=False):
    client = window.client
    actor = tuple(client.user.get(key) for key in ('id', 'tenant_id', 'role'))
    dialog = QDialog(window)
    dialog.setWindowTitle('Liberar unidad' if release else 'Vincular perfil de laboratorio')
    dialog.resize(680, 540 if not release else 310)
    layout = QVBoxLayout(dialog)
    title = QLabel(dialog.windowTitle()); title.setObjectName('title'); layout.addWidget(title)
    summary = QLabel(f"Unidad {resource['folio']} · {display(resource['component'])} · {resource['blood_group']}")
    summary.setWordWrap(True); layout.addWidget(summary)
    guidance = QLabel('La liberación requiere resultados autorizados y una revisión médica documentada.' if release else 'Selecciona el perfil documentado para esta unidad. Se conservan los controles de conservación existentes.')
    guidance.setWordWrap(True); layout.addWidget(guidance)
    if release:
        profile = controls.get('_profile')
        check = controls.get('_completeness')
        if not profile or not check:
            text = 'Esta unidad aún no tiene un perfil de laboratorio vinculado.'
        elif check['complete']:
            text = 'Perfil: ' + profile['name'] + '. Los resultados requeridos están completos. Confirma la revisión.'
        else:
            missing = '; '.join(missing_label(item) for item in check.get('missing', []))
            text = 'Perfil: ' + profile['name'] + '. Pendiente: ' + (missing or 'revisión de laboratorio') + '.'
        if profile and profile.get('synthetic'): text += ' Perfil sintético para pruebas; no autoriza uso clínico.'
        readiness = QLabel(text); readiness.setWordWrap(True); layout.addWidget(readiness)
    state = {'alive': True, 'rows': [], 'page': 1, 'total': 0, 'busy': False, 'body': None}
    def same_session():
        return window.client is client and bool(client.user) and tuple(client.user.get(key) for key in ('id', 'tenant_id', 'role')) == actor
    if not release:
        table = QTableWidget(0, 3); table.setAccessibleName('Perfiles de laboratorio')
        table.setHorizontalHeaderLabels(['Nombre', 'Producto', 'Versión'])
        table.setSelectionBehavior(QAbstractItemView.SelectRows); table.setSelectionMode(QAbstractItemView.SingleSelection)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers); table.verticalHeader().hide()
        header = table.horizontalHeader(); header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents); header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        layout.addWidget(table, 1)
        navigation = QHBoxLayout(); previous = QPushButton('Anterior'); following = QPushButton('Siguiente'); refresh = QPushButton('Actualizar'); page_label = QLabel()
        for widget in (previous, page_label, following, refresh): navigation.addWidget(widget)
        navigation.addStretch(); layout.addLayout(navigation)
    fields = QFormLayout(); reason = QLineEdit(); reason.setMaxLength(1000); fields.addRow('Motivo documentado', reason)
    confirm = QCheckBox('Confirmo la decisión documentada.'); fields.addRow(confirm); layout.addLayout(fields)
    status = QLabel(''); status.setWordWrap(True); layout.addWidget(status)
    buttons = QHBoxLayout(); save = QPushButton('Liberar unidad' if release else 'Vincular perfil'); save.setObjectName('primary')
    save.setStyleSheet('QPushButton:disabled { background: #e1e5e9; color: #596572; }')
    cancel = QPushButton('Cancelar'); buttons.addWidget(save); buttons.addWidget(cancel); layout.addLayout(buttons)
    if release and (not controls.get('_completeness') or not controls['_completeness']['complete']): save.setEnabled(False)
    cancel.clicked.connect(dialog.reject)
    if not release:
        def fetch(page):
            if state['busy']: return
            state.update(busy=True, rows=[]); table.setRowCount(0); save.setEnabled(False)
            previous.setEnabled(False); following.setEnabled(False); status.setText('Consultando perfiles…')
            def query():
                if not same_session():
                    raise ValueError('La sesión cambió.')
                return client.authorized('compatibilidad', '/api/v1/laboratory/profiles', 'lab_profiles_list', params={'page': page, 'page_size': 20})
            worker = work_type(query)
            if not hasattr(window, '_request_workers'): window._request_workers = []
            window._request_workers.append(worker)
            def done(data):
                window._request_workers.remove(worker)
                if not state['alive']: return
                if not same_session():
                    state['busy'] = False; table.setRowCount(0); save.setEnabled(False)
                    status.setText('La sesión cambió. Cierra y vuelve a consultar.'); return
                state.update(busy=False, page=data['page'], total=data['total'], rows=data['items'])
                table.setRowCount(len(state['rows']))
                for index, row in enumerate(state['rows']):
                    compatible = row.get('kind') == resource.get('kind') and row.get('component') == resource.get('component')
                    name = row['name'] if compatible else row['name'] + ' (no corresponde)'
                    for column, value in enumerate((name, display(row['component']), row['version'])):
                        cell = QTableWidgetItem(str(value))
                        if column == 0: cell.setToolTip(row['name'])
                        if not compatible:
                            cell.setFlags(cell.flags() & ~Qt.ItemIsSelectable)
                            cell.setToolTip((row['name'] + '. ' if column == 0 else '') + 'El producto o tipo no corresponde a esta unidad.')
                        table.setItem(index, column, cell)
                page_label.setText(f"Página {state['page']} · {state['total']} registros")
                previous.setEnabled(state['page'] > 1); following.setEnabled(state['page'] * 20 < state['total'])
                save.setEnabled(True); status.setText('Selecciona el perfil de la unidad.' if state['rows'] else 'No hay perfiles en esta página.')
            def failed(_error):
                window._request_workers.remove(worker)
                if not state['alive']: return
                if not same_session():
                    state['busy'] = False; table.setRowCount(0); save.setEnabled(False)
                    status.setText('La sesión cambió. Cierra y vuelve a consultar.'); return
                state['busy'] = False; previous.setEnabled(state['page'] > 1); following.setEnabled(state['page'] * 20 < state['total'])
                status.setText('No se pudieron consultar los perfiles. Usa Actualizar para volver a intentar.')
            worker.signals.done.connect(done); worker.signals.failed.connect(failed); window.pool.start(worker)
        previous.clicked.connect(lambda: fetch(state['page'] - 1)); following.clicked.connect(lambda: fetch(state['page'] + 1))
        refresh.clicked.connect(lambda: fetch(state['page']))
        QTimer.singleShot(0, lambda: fetch(1))
    def submit():
        if not same_session():
            status.setText('La sesión cambió. Cierra y vuelve a consultar.'); return
        profile = None
        if not release:
            index = table.currentRow()
            if 0 <= index < len(state['rows']): profile = state['rows'][index]
            if profile and (profile.get('kind') != resource.get('kind') or profile.get('component') != resource.get('component')): profile = None
        if (not release and not profile) or len(reason.text().strip()) < 6 or not confirm.isChecked():
            QMessageBox.warning(dialog, 'Datos incompletos', 'Selecciona el perfil si corresponde, escribe el motivo y confirma la decisión.'); return
        body = {'version': resource['version'], 'reason': reason.text().strip(), 'human_confirmation': 'true'}
        if profile:
            body.update(lab_profile_id=profile['id'], cold_equipment_id=controls.get('cold_equipment_id'), cold_profile_id=controls.get('cold_profile_id'))
        state['body'] = body; dialog.accept()
    save.clicked.connect(submit)
    accepted = dialog.exec(); state['alive'] = False
    return state['body'] if accepted == QDialog.Accepted else None
