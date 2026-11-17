"""Destino documentado de una unidad; conserva antecedentes y revisión humana."""
from datetime import datetime
from uuid import UUID

from PySide6.QtCore import QDateTime, Qt
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDateTimeEdit, QDialog, QFormLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QScrollArea, QVBoxLayout, QWidget,
)

from .client import ContractError
from .session_context import OperationContext, SessionChanged


DESTINATIONS = {
    'TRANSFUSED': 'Transfusión documentada',
    'TRANSPLANTED': 'Trasplante documentado',
    'DISCARDED': 'Descarte documentado',
    'RETURNED': 'Devolución documentada',
    'RESEARCH': 'Destino a investigación autorizado',
}


def validate_destination_result(client, record, result):
    """Cotejar respuesta antes de cerrar el comando durable."""
    body=record['body']
    try:
        if str(UUID(result['id']))!=result['id']: raise ValueError()
        if (result['resource_id']!=record['target']['identifier']
                or result['tenant_id']!=client.user['tenant_id']
                or result['author_id']!=client.user['id']): raise ValueError()
        if any(result.get(k)!=body.get(k) for k in ('destination','reference','reason','supersedes')): raise ValueError()
        version=result['version']
        if type(version) is not int or (version!=1 if not body.get('supersedes') else version<2): raise ValueError()
        expected=datetime.fromisoformat(body['occurred_at'].replace('Z','+00:00'))
        received=datetime.fromisoformat(result['occurred_at'].replace('Z','+00:00'))
        if expected.tzinfo is None or received.tzinfo is None or expected!=received: raise ValueError()
    except (KeyError,ValueError,TypeError,AttributeError) as exc:
        raise ContractError('El destino confirmado no corresponde al intento registrado.') from exc


def destination_context(binding, identifier):
    """XML paginado; nunca elegir antecedente de una lista parcial o ajena."""
    binding.check()
    client=binding.client
    resource=client.authorized('inventario','/api/v1/resources/'+identifier,'resource_detail')
    binding.check()
    if resource.get('id')!=identifier or resource.get('current_institution_id')!=binding.actor[1]:
        raise ContractError('La unidad no pertenece a la institución activa.')
    previous=None; seen=set(); total=None; page=1
    while True:
        binding.check()
        result=client.authorized('inventario','/api/v1/resource-destinations','resource_destinations_list',
                                 params={'resource_id':identifier,'page':page,'page_size':100})
        binding.check()
        if result['page']!=page or (total is not None and total!=result['total']):
            raise ContractError('La historia cambió durante la consulta. Vuelve a consultar.')
        total=result['total']
        for row in result['items']:
            if row['resource_id']!=identifier or row['tenant_id']!=binding.actor[1] or row['id'] in seen:
                raise ContractError('La historia recibida no corresponde a esta unidad.')
            seen.add(row['id'])
            if previous is None or row['version']>previous['version']: previous=row
        if len(seen)==total: break
        if not result['items'] or len(seen)>total:
            raise ContractError('No se pudo obtener la historia completa.')
        page+=1
    return resource,previous


def destination_dialog(window, binding, resource, previous, display=str):
    if not binding.current(): return None
    dialog=QDialog(window); dialog.setWindowTitle('Corregir destino' if previous else 'Registrar destino')
    dialog.resize(720,620); outer=QVBoxLayout(dialog); outer.setContentsMargins(24,20,24,20);outer.setSpacing(12)
    heading=QLabel(dialog.windowTitle());heading.setObjectName('title');outer.addWidget(heading)
    summary=QLabel('Unidad '+resource['folio']+' · '+display(resource['component'])+' · '+resource['blood_group'])
    summary.setWordWrap(True);outer.addWidget(summary)
    note=QLabel('Registra un hecho respaldado por documentación autorizada. La recepción logística y el uso clínico son hechos distintos. El registro retira la unidad del inventario disponible y conserva su historia.')
    note.setWordWrap(True);outer.addWidget(note)
    scroll=QScrollArea();scroll.setWidgetResizable(True);panel=QWidget();form=QFormLayout(panel)
    form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow);scroll.setWidget(panel);outer.addWidget(scroll,1)
    if previous:
        prior=QLabel(f"Versión {previous['version']} · {DESTINATIONS.get(previous['destination'],previous['destination'])}")
        prior.setWordWrap(True);form.addRow('Antecedente conservado',prior)
    choice=QComboBox();choice.setObjectName('destination');choice.addItem('Selecciona el hecho documentado','')
    for code,title in DESTINATIONS.items():
        if (code=='TRANSFUSED' and resource['kind']!='BLOOD') or (code=='TRANSPLANTED' and resource['kind']!='ORGAN'): continue
        choice.addItem(title,code)
    form.addRow('Destino',choice)
    date=QDateTimeEdit(QDateTime.currentDateTime());date.setObjectName('occurred_at');date.setCalendarPopup(True);date.setDisplayFormat('dd/MM/yyyy HH:mm:ss')
    if previous:
        choice.setCurrentIndex(choice.findData(previous['destination']))
        old=datetime.fromisoformat(previous['occurred_at'].replace('Z','+00:00'))
        date.setDateTime(QDateTime.fromMSecsSinceEpoch(int(old.timestamp()*1000)).toLocalTime())
    date_state={'changed':False}
    date.dateTimeChanged.connect(lambda _:date_state.update(changed=True))
    form.addRow('Fecha del hecho · hora local',date)
    documented=QCheckBox('Confirmo la fecha y hora de la documentación.');documented.setObjectName('confirm_time');form.addRow(documented)
    reference=QLineEdit(previous['reference'] if previous else '');reference.setObjectName('reference');reference.setMaxLength(200);form.addRow('Referencia autorizada',reference)
    reason=QLineEdit();reason.setObjectName('reason');reason.setMaxLength(1000);form.addRow('Motivo del registro o corrección',reason)
    confirmed=QCheckBox('Revisé la documentación y autorizo registrar este destino.');confirmed.setObjectName('confirm_destination');form.addRow(confirmed)
    error=QLabel();error.setWordWrap(True);error.setAccessibleName('Resultado de validación');outer.addWidget(error)
    buttons=QHBoxLayout();cancel=QPushButton('Cancelar');save=QPushButton(dialog.windowTitle());save.setObjectName('primary')
    buttons.addWidget(cancel);buttons.addWidget(save);outer.addLayout(buttons);cancel.clicked.connect(dialog.reject)
    result={'body':None}
    def submit():
        if not binding.current(): error.setText('La sesión cambió. Cierra y vuelve a consultar.');save.setEnabled(False);return
        if not choice.currentData(): error.setText('Selecciona el destino documentado.');choice.setFocus();return
        if not documented.isChecked() or not date.dateTime().isValid() or date.dateTime()>QDateTime.currentDateTime():
            error.setText('Confirma una fecha documentada que no sea futura.');date.setFocus();return
        if not reference.text().strip(): error.setText('Escribe la referencia autorizada.');reference.setFocus();return
        if len(reason.text().strip())<6: error.setText('Describe el motivo con al menos seis caracteres.');reason.setFocus();return
        if not confirmed.isChecked(): error.setText('Confirma la revisión de la documentación.');confirmed.setFocus();return
        occurred=previous['occurred_at'] if previous and not date_state['changed'] else date.dateTime().toUTC().toString(Qt.ISODate)
        result['body']={'version':resource['version'],'destination':choice.currentData(),'reference':reference.text().strip(),
                        'occurred_at':occurred,'reason':reason.text().strip(),
                        'human_confirmation':'true','supersedes':previous['id'] if previous else None}
        dialog.accept()
    save.clicked.connect(submit)
    return result['body'] if dialog.exec()==QDialog.Accepted and binding.current() else None


def open_destination(window,display=str):
    try: binding=OperationContext(window)
    except SessionChanged: window.status.setText('Inicia sesión para consultar la unidad.');return
    if binding.actor[2]!='MEDICAL': window.status.setText('El registro requiere personal médico autorizado.');return
    selected=window.selected()
    if not selected: window.status.setText('Selecciona una unidad.');return
    identifier=selected['id']
    def ready(context):
        resource,previous=context
        if resource['status'] not in ('QUARANTINE','AVAILABLE','RECEIVED','WITHDRAWN'):
            window.status.setText('Concluye la reserva o el traslado antes de documentar el destino.');return
        body=destination_dialog(window,binding,resource,previous,display)
        if body is None or not binding.current():return
        def completed(_result):
            if binding.current():window.status.setText('Destino registrado. La historia anterior se conserva. Actualiza la lista para consultar el estado vigente.')
        window.secure_command('resource_destination',identifier,body,completed)
    window.run_in_context(binding,lambda:destination_context(binding,identifier),ready,'Consultando unidad e historia de destinos…')
