"""Captura documental de resultados; la validación clínica pertenece al servicio."""
import re
from datetime import datetime

from PySide6.QtCore import QDateTime, Qt
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDateTimeEdit, QDialog, QFormLayout,
    QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMessageBox, QPushButton, QScrollArea,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

from .client import ContractError
from .session_context import OperationContext



def validate_result_confirmation(result, body, user):
    if (result.get('tenant_id')!=user.get('tenant_id') or result.get('author_id')!=user.get('id')
            or result.get('sample_id')!=body['sample_id'] or result.get('test_code')!=body['test_code']
            or result.get('status')!='CAPTURED'):
        raise ContractError('El resultado confirmado no corresponde al intento.')
    for field,default in (('result_state','REPORTED'),('value',None),('document_id',None),('supersedes',None),('method',None),('laboratory',None),('reference',None)):
        if result.get(field,default)!=body.get(field,default): raise ContractError('El resultado confirmado no corresponde al intento.')
    for field in ('measured_at','issued_at'):
        expected=body.get(field); actual=result.get(field)
        if expected is None and actual is None: continue
        try:
            left=datetime.fromisoformat(expected.replace('Z','+00:00')); right=datetime.fromisoformat(actual.replace('Z','+00:00'))
            if left.tzinfo is None or right.tzinfo is None or left!=right: raise ValueError()
        except (AttributeError,TypeError,ValueError) as error:
            raise ContractError('La fecha confirmada no corresponde al intento.') from error
    expected=body.get('hla'); actual=result.get('hla')
    if expected is None:
        if actual is not None: raise ContractError('La tipificación no corresponde al intento.')
    else:
        if not isinstance(actual,dict) or any(actual.get(key)!=expected.get(key) for key in ('nomenclature','nomenclature_version','resolution','catalogue_version','loci')):
            raise ContractError('La tipificación no corresponde al intento.')


def verified_document(value, prior, tenant):
    if (value.get('tenant_id') != tenant or value.get('subject_kind') != 'RESULT'
            or value.get('subject_id') != prior['id'] or value.get('analysis') != 'CLEAN'
            or value.get('file_status') != 'VERIFIED' or not value.get('generation')
            or not re.fullmatch(r'[0-9a-f]{64}', str(value.get('sha256','')))):
        raise ContractError('El documento no corresponde al resultado o aún no está verificado.')
    return value


def document_selector(window, prior, worker_type):
    binding=OperationContext(window); dialog=QDialog(window); dialog.setWindowTitle('Documento del resultado'); dialog.resize(780,440)
    layout=QVBoxLayout(dialog); title=QLabel('Seleccionar documento verificado'); title.setObjectName('title'); layout.addWidget(title)
    note=QLabel('Documentos privados del resultado anterior. Selecciona una fila para comprobar su estado.'); note.setWordWrap(True); layout.addWidget(note)
    table=QTableWidget(0,3); table.setHorizontalHeaderLabels(['Categoría','Registro','Referencia']); table.setSelectionBehavior(QTableWidget.SelectRows); table.setEditTriggers(QTableWidget.NoEditTriggers); table.horizontalHeader().setSectionResizeMode(0,QHeaderView.Stretch); table.horizontalHeader().setSectionResizeMode(1,QHeaderView.ResizeToContents); table.horizontalHeader().setSectionResizeMode(2,QHeaderView.Stretch); layout.addWidget(table)
    status=QLabel(''); status.setWordWrap(True); layout.addWidget(status); nav=QHBoxLayout(); previous=QPushButton('Anterior'); following=QPushButton('Siguiente'); refresh=QPushButton('Actualizar'); page_label=QLabel()
    for w in (previous,page_label,following,refresh): nav.addWidget(w)
    nav.addStretch(); choose=QPushButton('Comprobar documento'); choose.setObjectName('primary'); choose.setEnabled(False); cancel=QPushButton('Cancelar'); nav.addWidget(cancel); nav.addWidget(choose); layout.addLayout(nav)
    state={'alive':True,'busy':False,'rows':[],'page':1,'total':0,'value':None}
    def run(work,done):
        worker=worker_type(work)
        if not hasattr(window,'_request_workers'): window._request_workers=[]
        window._request_workers.append(worker)
        def finish(value,error=False):
            window._request_workers.remove(worker)
            if not state['alive']: return
            state['busy']=False
            if not binding.current(): table.setRowCount(0); status.setText('La sesión cambió. Cierra y vuelve a ingresar.'); return
            refresh.setEnabled(True)
            if error: status.setText('No se pudo comprobar el documento. Actualiza y vuelve a intentarlo.'); return
            try: done(value)
            except (ContractError,KeyError,TypeError,ValueError): status.setText('La respuesta no corresponde al documento. Actualiza y vuelve a intentar.')
        worker.signals.done.connect(finish); worker.signals.failed.connect(lambda error:finish(error,True)); window.pool.start(worker)
    def load(page):
        if state['busy'] or not binding.current(): return
        state.update(busy=True,rows=[]); table.setRowCount(0); choose.setEnabled(False)
        for w in (previous,following,refresh): w.setEnabled(False)
        status.setText('Consultando documentos…')
        def fetch():
            binding.check(); return binding.client.authorized('documentos','/api/v1/documents','document_list',params={'subject_kind':'RESULT','subject_id':prior['id'],'page':page,'page_size':10})
        def loaded(data):
            if data.get('page')!=page or not isinstance(data.get('items'),list) or type(data.get('total')) is not int: raise ContractError('Página documental inválida.')
            rows=data['items']
            if any(r.get('tenant_id')!=binding.actor[1] or r.get('subject_kind')!='RESULT' or r.get('subject_id')!=prior['id'] for r in rows): raise ContractError('Documento ajeno.')
            state.update(rows=rows,page=page,total=data['total']); table.setRowCount(len(rows))
            for index,row in enumerate(rows):
                for col,value in enumerate((row.get('category',''),row.get('created_at',''),row.get('id',''))): table.setItem(index,col,QTableWidgetItem(str(value)))
            page_label.setText('Página '+str(page)); previous.setEnabled(page>1); following.setEnabled(page*10<data['total']); status.setText('Selecciona un documento.' if rows else 'No hay documentos para este resultado.')
        run(fetch,loaded)
    def select():
        index=table.currentRow()
        if state['busy'] or not 0<=index<len(state['rows']) or not binding.current(): return
        row=state['rows'][index]; state['busy']=True; choose.setEnabled(False); status.setText('Comprobando verificación…')
        def fetch():
            binding.check(); value=binding.client.authorized('documentos','/api/v1/documents/'+row['id']+'/verified','document_verified')
            binding.check()
            if value.get('id')!=row['id']: raise ContractError('Documento distinto.')
            return verified_document(value,prior,binding.actor[1])
        def chosen(value): state.update(value=value); dialog.accept()
        run(fetch,chosen)
    table.itemSelectionChanged.connect(lambda:choose.setEnabled(table.currentRow()>=0 and not state['busy'] and binding.current()))
    previous.clicked.connect(lambda:load(state['page']-1)); following.clicked.connect(lambda:load(state['page']+1)); refresh.clicked.connect(lambda:load(state['page'])); choose.clicked.connect(select); cancel.clicked.connect(dialog.reject)
    load(1); result=dialog.exec(); state['alive']=False
    return state['value'] if result==QDialog.Accepted and binding.current() else None


def result_dialog(window, sample, prior, worker_type, draft=None, locked=False, notice=None):
    binding=OperationContext(window); dialog=QDialog(window); dialog.setWindowTitle('Corregir resultado' if prior else 'Capturar resultado'); dialog.resize(780,680)
    outer=QVBoxLayout(dialog); title=QLabel(dialog.windowTitle()); title.setObjectName('title'); outer.addWidget(title)
    scroll=QScrollArea(); scroll.setWidgetResizable(True); panel=QWidget(); form=QFormLayout(panel); form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow); scroll.setWidget(panel); outer.addWidget(scroll,1)
    form.addRow('Muestra',QLabel(sample.get('identifier') or 'Muestra seleccionada'))
    if prior: form.addRow('Antecedente',QLabel('Resultado anterior · versión '+str(prior['version'])))
    code=QLineEdit(prior['test_code'] if prior else ''); code.setObjectName('result_code'); code.setMaxLength(60); code.setReadOnly(bool(prior)); form.addRow('Código de prueba',code)
    state=QComboBox(); state.setObjectName('result_state'); state.addItem('Selecciona un estado','')
    if prior: state.addItem('Corrección documentada','CORRECTED')
    else:
        state.addItem('Pendiente','PENDING'); state.addItem('Informado','REPORTED')
    form.addRow('Estado',state)
    fields={}
    for key,title_text,maximum in [('value','Resultado escrito · opcional para HLA',2000),('method','Método',200),('laboratory','Laboratorio',200),('reference','Referencia',200)]:
        fields[key]=QLineEdit(); fields[key].setObjectName('result_'+key); fields[key].setMaxLength(maximum); form.addRow(title_text,fields[key])
    measured=QDateTimeEdit(QDateTime.currentDateTime()); measured.setObjectName('measured_time'); measured.setCalendarPopup(True); measured.setDisplayFormat('dd/MM/yyyy HH:mm:ss'); form.addRow('Medición documentada · hora local',measured)
    confirm_measured=QCheckBox('Confirmo la fecha y hora documentadas de medición.'); confirm_measured.setObjectName('confirm_measured'); form.addRow(confirm_measured)
    use_hla=QCheckBox('Registrar tipificación HLA declarada'); use_hla.setObjectName('use_hla'); form.addRow(use_hla)
    hla_panel=QWidget(); hla_form=QFormLayout(hla_panel); hla_form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow); hla_form.addRow('Nomenclatura',QLabel('HLA-colon-2010'))
    syntax=QComboBox(); syntax.setObjectName('hla_syntax'); syntax.addItem('Selecciona una versión',''); syntax.addItem('2010','2010'); syntax.addItem('2010 · sintaxis 2','2010:syntax-2'); hla_form.addRow('Versión de nomenclatura',syntax)
    resolution=QLineEdit(); resolution.setObjectName('hla_resolution'); resolution.setMaxLength(200); hla_form.addRow('Resolución documentada',resolution)
    catalogue=QComboBox(); catalogue.addItem('Sin catálogo declarado',''); hla_form.addRow('Catálogo de referencia',catalogue)
    hla_note=QLabel('Separa alelos y grupos con comas. La tipificación es declarada y requiere revisión profesional.'); hla_note.setWordWrap(True); hla_form.addRow(hla_note)
    loci=QTableWidget(0,5); loci.setObjectName('hla_loci'); loci.setHorizontalHeaderLabels(['Locus','Alelos','Grupos','Ambigua','Parcial']); loci.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); loci.setMinimumHeight(150); hla_form.addRow(loci)
    actions=QHBoxLayout(); add=QPushButton('Añadir locus'); remove=QPushButton('Quitar locus'); actions.addWidget(add); actions.addWidget(remove); hla_form.addRow(actions); form.addRow(hla_panel)
    def add_locus():
        if loci.rowCount()>=80: return
        row=loci.rowCount(); loci.insertRow(row)
        for col in (0,1,2): loci.setItem(row,col,QTableWidgetItem(''))
        for col in (3,4):
            item=QTableWidgetItem(''); item.setFlags(item.flags()|Qt.ItemIsUserCheckable); item.setCheckState(Qt.Unchecked); loci.setItem(row,col,item)
    add.clicked.connect(add_locus); remove.clicked.connect(lambda:loci.removeRow(loci.currentRow()) if loci.currentRow()>=0 else None)
    use_issued=QCheckBox('Registrar fecha de emisión documentada'); use_issued.setObjectName('use_issued'); form.addRow(use_issued)
    issued=QDateTimeEdit(QDateTime.currentDateTime()); issued.setObjectName('issued_time'); issued.setCalendarPopup(True); issued.setDisplayFormat('dd/MM/yyyy HH:mm:ss'); form.addRow('Emisión documentada · hora local',issued)
    issued_confirm=QCheckBox('Confirmo la fecha y hora documentadas de emisión.'); issued_confirm.setObjectName('confirm_issued'); form.addRow(issued_confirm)
    document={'value':None}; document_label=QLabel('Sin documento seleccionado.'); document_label.setWordWrap(True); document_button=QPushButton('Seleccionar documento verificado'); document_button.setEnabled(bool(prior)); form.addRow(document_button); form.addRow(document_label)
    def choose_document():
        if not prior or not binding.current(): return
        selected=document_selector(window,prior,worker_type)
        if selected and binding.current():
            document['value']=selected; document_label.setText('Verificado · '+selected['category']+' · generación '+str(selected['generation'])+'\nSHA-256 '+selected['sha256'])
    document_button.clicked.connect(choose_document)
    note=QLabel('Si el perfil exige documento, registra primero un resultado pendiente y vincula el archivo verificado a su corrección.'); note.setWordWrap(True); form.addRow(note)
    def change_state():
        pending=state.currentData()=='PENDING'; fields['value'].setEnabled(not pending); use_hla.setEnabled(not pending)
        if pending:
            fields['value'].clear(); use_hla.setChecked(False); use_issued.setChecked(False); document['value']=None; document_label.setText('Sin documento seleccionado.')
        document_button.setEnabled(bool(prior) and not pending); hla_panel.setEnabled(use_hla.isChecked() and not pending)
    state.currentIndexChanged.connect(change_state); use_hla.toggled.connect(change_state); use_issued.toggled.connect(lambda checked:(issued.setEnabled(checked),issued_confirm.setEnabled(checked)))
    change_state(); issued.setEnabled(False); issued_confirm.setEnabled(False)
    if draft:
        body, saved_document=draft
        code.setText(body['test_code']); state.setCurrentIndex(max(0,state.findData(body['result_state'])))
        for key in fields: fields[key].setText(body.get(key) or '')
        measured.setDateTime(QDateTime.fromString(body['measured_at'],Qt.ISODate).toLocalTime()); confirm_measured.setChecked(True)
        if body.get('issued_at'):
            use_issued.setChecked(True); issued.setDateTime(QDateTime.fromString(body['issued_at'],Qt.ISODate).toLocalTime()); issued_confirm.setChecked(True)
        if body.get('hla'):
            use_hla.setChecked(True); typing=body['hla']; syntax.setCurrentIndex(max(0,syntax.findData(typing['nomenclature_version']))); resolution.setText(typing['resolution'])
            for entry in typing['loci']:
                add_locus(); row=loci.rowCount()-1
                loci.item(row,0).setText(entry['locus']); loci.item(row,1).setText(', '.join(entry['alleles'])); loci.item(row,2).setText(', '.join(entry.get('groups',[])))
                loci.item(row,3).setCheckState(Qt.Checked if entry.get('ambiguous') else Qt.Unchecked); loci.item(row,4).setCheckState(Qt.Checked if entry.get('partial') else Qt.Unchecked)
            catalogue.addItem(typing.get('catalogue_version') or 'Sin catálogo declarado',typing.get('catalogue_version') or ''); catalogue.setCurrentIndex(catalogue.count()-1)
        if saved_document:
            document['value']=saved_document; document_label.setText('Verificado · '+saved_document['category']+' · generación '+str(saved_document['generation'])+'\nSHA-256 '+saved_document['sha256'])
    buttons=QHBoxLayout(); cancel=QPushButton('Cancelar'); save=QPushButton('Guardar resultado'); save.setObjectName('primary'); buttons.addStretch(); buttons.addWidget(cancel); buttons.addWidget(save); outer.addLayout(buttons); cancel.clicked.connect(dialog.reject); save.clicked.connect(dialog.accept)
    if notice: note.setText(notice)
    if locked:
        panel.setStyleSheet('QWidget:disabled { color: #354553; } QLineEdit:disabled, QComboBox:disabled, QDateTimeEdit:disabled, QTableWidget:disabled { color: #354553; background: #f4f6f7; }')
        panel.setEnabled(False); save.setEnabled(False)
        explanation=QLabel(notice or 'Este intento requiere revisión o recuperación. Actualiza el resultado antes de iniciar otra operación.')
        explanation.setWordWrap(True); outer.insertWidget(1,explanation)
    holder={'catalogue_worker':None,'alive':True}
    def catalogue_work(): binding.check(); return binding.client.authorized('compatibilidad','/api/v1/laboratory/reference-sources','reference_sources')
    worker=worker_type(catalogue_work); holder['catalogue_worker']=worker
    if not hasattr(window,'_request_workers'): window._request_workers=[]
    window._request_workers.append(worker)
    def catalogues(data,error=False):
        window._request_workers.remove(worker)
        if not holder['alive'] or not binding.current(): return
        if error: hla_note.setText('No fue posible consultar el catálogo. Puedes continuar sin declararlo.'); return
        for row in data.get('catalogues',[]):
            if row.get('available') and row.get('version'): catalogue.addItem(str(row['version']),str(row['version']))
    worker.signals.done.connect(catalogues); worker.signals.failed.connect(lambda e:catalogues(e,True)); window.pool.start(worker)
    result=None
    while dialog.exec()==QDialog.Accepted:
        if not binding.current(): break
        values={k:v.text().strip() for k,v in fields.items()}; status=state.currentData(); test=code.text().strip()
        if not re.fullmatch(r'[A-Z0-9_.-]{1,60}',test) or not status or not all(values[k] for k in ('method','laboratory','reference')) or not confirm_measured.isChecked():
            QMessageBox.warning(dialog,'Datos incompletos','Completa prueba, estado, método, laboratorio, referencia y confirma la medición.'); continue
        body={'sample_id':sample['id'],'test_code':test,'result_state':status,'method':values['method'],'laboratory':values['laboratory'],'reference':values['reference'],'measured_at':measured.dateTime().toUTC().toString(Qt.ISODate)}
        if values['value'] and status!='PENDING': body['value']=values['value']
        if prior: body['supersedes']=prior['id']
        if use_issued.isChecked():
            if not issued_confirm.isChecked() or issued.dateTime()<measured.dateTime() or issued.dateTime()>QDateTime.currentDateTime():
                QMessageBox.warning(dialog,'Emisión documentada','Confirma una emisión posterior a la medición y que no sea futura.'); continue
            body['issued_at']=issued.dateTime().toUTC().toString(Qt.ISODate)
        if use_hla.isChecked():
            rows=[]
            for row in range(loci.rowCount()):
                locus=loci.item(row,0).text().strip(); alleles=[x.strip() for x in loci.item(row,1).text().split(',') if x.strip()]; groups=[x.strip() for x in loci.item(row,2).text().split(',') if x.strip()]
                rows.append({'locus':locus,'alleles':alleles,'groups':groups,'ambiguous':loci.item(row,3).checkState()==Qt.Checked,'partial':loci.item(row,4).checkState()==Qt.Checked})
            if not body.get('issued_at') or not syntax.currentData() or not resolution.text().strip() or not rows:
                QMessageBox.warning(dialog,'Tipificación incompleta','Documenta emisión, versión, resolución y al menos un locus.'); continue
            body['hla']={'nomenclature':'HLA-colon-2010','nomenclature_version':syntax.currentData(),'resolution':resolution.text().strip(),'loci':rows}
            if catalogue.currentData(): body['hla']['catalogue_version']=catalogue.currentData()
        if status in ('REPORTED','CORRECTED') and not body.get('value') and not body.get('hla'):
            QMessageBox.warning(dialog,'Resultado incompleto','Documenta el resultado o la tipificación.'); continue
        if document['value']: body['document_id']=document['value']['id']
        result=(body,document['value']); break
    holder['alive']=False
    return result if binding.current() else None
