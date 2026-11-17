"""Revisión médica de un incidente; no libera ni modifica lecturas históricas."""
from PySide6.QtWidgets import QCheckBox, QDialog, QFormLayout, QLabel, QLineEdit, QPushButton

from .client import ContractError
from .session_context import OperationContext


def review_dialog(window, resource, controls, binding):
    if not binding.current():
        return None
    dialog = QDialog(window)
    dialog.setWindowTitle('Revisar incidente de conservación')
    dialog.resize(800, 330)
    form = QFormLayout(dialog)
    form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
    form.addRow('Unidad', QLabel(str(resource['folio'])))
    form.addRow('Controles vigentes', QLabel('Versión '+str(controls['version'])+' · Bloqueados'))
    note = QLabel('Documenta la revisión humana del incidente y sus antecedentes. Las lecturas y alertas se conservan. Esta revisión desbloquea controles; no libera la unidad ni autoriza uso clínico.')
    note.setWordWrap(True)
    form.addRow(note)
    reason = QLineEdit()
    reason.setMaxLength(1000)
    form.addRow('Motivo de revisión', reason)
    confirmed = QCheckBox('Confirmo que revisé el incidente y su documentación.')
    form.addRow(confirmed)
    status = QLabel()
    status.setWordWrap(True)
    form.addRow(status)
    save = QPushButton('Registrar revisión')
    cancel = QPushButton('Cancelar')
    form.addRow(save)
    form.addRow(cancel)
    result = {'body': None}

    def submit():
        if not binding.current():
            status.setText('La sesión cambió. Cierra y vuelve a consultar.')
            save.setEnabled(False)
            return
        if len(reason.text().strip()) < 6 or not confirmed.isChecked():
            status.setText('Escribe un motivo de al menos seis caracteres y confirma la revisión.')
            return
        result['body'] = {'version': controls['version'], 'reason': reason.text().strip(), 'human_confirmation': 'true'}
        dialog.accept()

    save.clicked.connect(submit)
    cancel.clicked.connect(dialog.reject)
    accepted = dialog.exec()
    return result['body'] if accepted == QDialog.Accepted and binding.current() else None


def open_review(window, item):
    if window.uncertain or not window.client or not window.client.user or window.client.user.get('role') != 'MEDICAL':
        window.status.setText('La revisión requiere personal médico y operaciones conciliadas.')
        return
    binding = OperationContext(window)
    client = binding.client

    def fetch():
        binding.check()
        resource = client.authorized('inventario', '/api/v1/resources/'+item['id'], 'resource_detail')
        controls = client.authorized('inventario', '/api/v1/resources/'+item['id']+'/controls', 'resource_controls_detail')
        binding.check()
        if resource.get('id') != item['id'] or resource.get('current_institution_id') != client.user.get('tenant_id') or controls.get('id') != item['id']:
            raise ContractError('La unidad o los controles no pertenecen a esta institución.')
        return resource, controls

    def ready(value):
        if not binding.current():
            return
        resource, controls = value
        if not controls.get('blocked') or resource.get('status') == 'WITHDRAWN':
            window.status.setText('No hay un incidente bloqueado disponible para revisión.')
            return
        body = review_dialog(window, resource, controls, binding)
        if body is not None and binding.current():
            window.secure_command('quality_review', resource['id'], body)

    window.run_in_context(binding, fetch, ready, 'Consultando incidente y controles vigentes…')
