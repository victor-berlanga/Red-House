"""Formularios académicos de conservación; reglas y decisiones son del servicio."""
from datetime import datetime
import math
from PySide6.QtCore import QDateTime, Qt
from PySide6.QtWidgets import QCheckBox,QComboBox,QDateTimeEdit,QDialog,QFormLayout,QLabel,QLineEdit,QMessageBox,QPushButton
from redhouse_desktop.client import ContractError
from redhouse_desktop.session_context import OperationContext

COMMANDS={
    'cold_equipment_create':('inventario','/api/v1/cold/equipment','cold_equipment_create.xsd',False),
    'cold_profile_create':('inventario','/api/v1/cold/profiles','cold_profile_create.xsd',False),
}
SCHEMAS=('cold_equipment_create','cold_profile_create')


def validate_result(operation,body,result,user):
    if result.get('tenant_id')!=user.get('tenant_id') or not result.get('id'):
        raise ContractError('La respuesta no corresponde a la institución.')
    if operation=='cold_equipment_create':
        if any(result.get(k)!=body.get(k) for k in ('label','location','calibration_reference')) or result.get('active') is not True or result.get('version')!=1:
            raise ContractError('El equipo confirmado no corresponde al registro.')
    elif operation=='cold_profile_create':
        if result.get('author_id')!=user.get('id') or any(result.get(k)!=body.get(k) for k in ('kind','component','minimum_c','maximum_c','max_gap_seconds','source','synthetic','version','supersedes')):
            raise ContractError('El perfil confirmado no corresponde al registro.')
        try:
            expected=datetime.fromisoformat(body['effective_at'].replace('Z','+00:00')); actual=datetime.fromisoformat(result['effective_at'].replace('Z','+00:00'))
            if expected.tzinfo is None or actual.tzinfo is None or expected!=actual: raise ValueError()
        except (KeyError,TypeError,ValueError,AttributeError) as error: raise ContractError('La fecha del perfil no corresponde.') from error
    else: raise ContractError('Operación de conservación desconocida.')


def dialog(window,kind,prior=None):
    binding=OperationContext(window); role=binding.actor[2]
    if (kind=='equipment' and (role!='OPERATOR' or prior)) or (kind=='profile' and role!='MEDICAL') or kind not in ('equipment','profile'):
        raise ContractError('Esta operación requiere personal autorizado.')
    form_dialog=QDialog(window); form_dialog.setWindowTitle('Registrar equipo de conservación' if kind=='equipment' else 'Corregir perfil térmico' if prior else 'Registrar perfil térmico académico'); form_dialog.resize(700,560)
    form=QFormLayout(form_dialog); form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
    title=QLabel(form_dialog.windowTitle()); title.setObjectName('title'); form.addRow(title)
    fields={}
    def line(key,title):
        value=QLineEdit(); value.setMaxLength(200); fields[key]=value; form.addRow(title,value); return value
    if kind=='equipment':
        line('label','Nombre documentado'); line('location','Ubicación documentada'); line('calibration_reference','Referencia de calibración · opcional')
    else:
        note=QLabel('Perfil sintético de ensayo académico; no autoriza uso clínico. Documenta valores y fuente autorizados.'); note.setWordWrap(True); form.addRow(note)
        product=QComboBox(); product.addItem('Selecciona un producto',None)
        for title_text,value in (('Eritrocitos',('BLOOD','RBC')),('Plasma',('BLOOD','PLASMA')),('Plaquetas',('BLOOD','PLATELETS')),('Riñón',('ORGAN','KIDNEY')),('Hígado',('ORGAN','LIVER')),('Corazón',('ORGAN','HEART'))): product.addItem(title_text,value)
        if prior:
            product.setCurrentIndex(product.findData((prior['kind'],prior['component']))); product.setEnabled(False)
        form.addRow('Producto',product)
        line('minimum_c','Temperatura mínima documentada · °C'); line('maximum_c','Temperatura máxima documentada · °C'); line('max_gap_seconds','Intervalo máximo documentado · segundos'); line('source','Fuente documentada')
        effective=QDateTimeEdit(QDateTime.currentDateTime()); effective.setCalendarPopup(True); effective.setDisplayFormat('dd/MM/yyyy HH:mm:ss'); form.addRow('Vigencia documentada · hora local',effective)
        confirmed=QCheckBox('Confirmo la fecha y hora documentadas de vigencia.'); form.addRow(confirmed)
    save=QPushButton('Guardar'); save.setObjectName('primary'); save.clicked.connect(form_dialog.accept); cancel=QPushButton('Cancelar'); cancel.clicked.connect(form_dialog.reject); form.addRow(save); form.addRow(cancel)
    while form_dialog.exec()==QDialog.Accepted:
        if not binding.current(): return None
        values={key:value.text().strip() for key,value in fields.items()}
        if kind=='equipment':
            if values['label'] and values['location']:
                return {'label':values['label'],'location':values['location'],'calibration_reference':values['calibration_reference'] or None}
        else:
            try:
                low=float(values['minimum_c']); high=float(values['maximum_c']); gap=int(values['max_gap_seconds'])
                if not (math.isfinite(low) and math.isfinite(high) and -273.15<=low<high<=100 and 1<=gap<=86400): raise ValueError()
                if not product.currentData() or not values['source'] or not confirmed.isChecked() or effective.dateTime()>QDateTime.currentDateTime(): raise ValueError()
                resource_kind,component=product.currentData()
                return {'kind':resource_kind,'component':component,'minimum_c':low,'maximum_c':high,'max_gap_seconds':gap,'source':values['source'],'synthetic':True,'version':prior['version']+1 if prior else 1,'effective_at':effective.dateTime().toUTC().toString(Qt.ISODate),'supersedes':prior['id'] if prior else None}
            except (ValueError,OverflowError): pass
        QMessageBox.warning(form_dialog,'Datos incompletos','Revisa los datos documentados y confirma la vigencia cuando corresponda.')
    return None


def bind_dialog(window,resource,controls,work_type):
    """Selecciona equipo y perfil existentes sin pedir identificadores manuales."""
    from PySide6.QtWidgets import QHBoxLayout,QHeaderView,QTableWidget,QTableWidgetItem,QVBoxLayout
    binding=OperationContext(window)
    if binding.actor[2]!='MEDICAL' or resource.get('current_institution_id')!=binding.actor[1] or controls.get('id')!=resource.get('id') or not controls.get('lab_profile_id'):
        raise ContractError('La unidad requiere personal médico y perfil de laboratorio vigente.')
    window_dialog=QDialog(window); window_dialog.setWindowTitle('Vincular conservación'); window_dialog.resize(850,700)
    layout=QVBoxLayout(window_dialog); title=QLabel('Vincular equipo y perfil térmico'); title.setObjectName('title'); layout.addWidget(title)
    note=QLabel('Elige un equipo activo y un perfil académico del mismo producto. Se conserva el perfil de laboratorio actual.'); note.setWordWrap(True); layout.addWidget(note)
    panels={}; alive={'value':True}; result={'body':None}
    for key,heading,headers in (('equipment','Equipos',['Nombre','Ubicación']),('profile','Perfiles térmicos',['Producto','Fuente','Versión'])):
        layout.addWidget(QLabel(heading)); table=QTableWidget(0,len(headers)); table.setHorizontalHeaderLabels(headers); table.setAccessibleName(heading); table.setSelectionBehavior(QTableWidget.SelectRows); table.setSelectionMode(QTableWidget.SingleSelection); table.setEditTriggers(QTableWidget.NoEditTriggers); table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); layout.addWidget(table)
        nav=QHBoxLayout(); prev=QPushButton('Anterior'); next_button=QPushButton('Siguiente'); refresh=QPushButton('Actualizar'); page_label=QLabel()
        for item in (prev,page_label,next_button,refresh):nav.addWidget(item)
        nav.addStretch(); layout.addLayout(nav); panels[key]={'table':table,'prev':prev,'next':next_button,'refresh':refresh,'page_label':page_label,'rows':[],'page':1,'total':0,'busy':False}
    reason=QLineEdit(); reason.setMaxLength(1000); reason.setPlaceholderText('Motivo documentado'); layout.addWidget(reason)
    confirmed=QCheckBox('Confirmo la decisión documentada.'); layout.addWidget(confirmed); status=QLabel(''); status.setWordWrap(True); layout.addWidget(status)
    controls_row=QHBoxLayout(); save=QPushButton('Vincular conservación'); save.setObjectName('primary'); cancel=QPushButton('Cancelar'); controls_row.addWidget(cancel); controls_row.addWidget(save); layout.addLayout(controls_row)
    def selected(key):
        panel=panels[key]; index=panel['table'].currentRow()
        return panel['rows'][index] if not panel['busy'] and 0<=index<len(panel['rows']) else None
    def selected_status():
        status.setText('Equipo y perfil seleccionados. Confirma la decisión.' if selected('equipment') and selected('profile') else 'Selecciona equipo y perfil.')
    for panel in panels.values():panel['table'].itemSelectionChanged.connect(selected_status)
    def fetch(key,page):
        panel=panels[key]
        if panel['busy'] or not binding.current(): return
        panel.update(busy=True,rows=[]); panel['table'].setRowCount(0)
        for widget in (panel['prev'],panel['next'],panel['refresh']):widget.setEnabled(False)
        status.setText('Consultando '+('equipos' if key=='equipment' else 'perfiles')+'…')
        def query():
            binding.check()
            path='/api/v1/cold/equipment' if key=='equipment' else '/api/v1/cold/profiles'
            operation='cold_equipment_list' if key=='equipment' else 'cold_profiles_list'
            return binding.client.authorized('inventario',path,operation,params={'page':page,'page_size':20})
        worker=work_type(query)
        if not hasattr(window,'_request_workers'):window._request_workers=[]
        window._request_workers.append(worker)
        def done(value,error=False):
            window._request_workers.remove(worker)
            if not alive['value']:return
            panel['busy']=False
            if not binding.current():panel['table'].setRowCount(0);status.setText('La sesión cambió. Cierra y vuelve a ingresar.');return
            panel['refresh'].setEnabled(True)
            if error or not isinstance(value,dict) or value.get('page')!=page or not isinstance(value.get('items'),list) or type(value.get('total')) is not int:
                status.setText('No se pudo consultar. Usa Actualizar para volver a intentar.');return
            rows=value['items']
            if any(row.get('tenant_id')!=binding.actor[1] for row in rows):status.setText('La respuesta no corresponde a esta institución.');return
            panel.update(rows=rows,page=page,total=value['total']); panel['table'].setRowCount(len(rows))
            for index,row in enumerate(rows):
                valid=(row.get('active') is True) if key=='equipment' else (row.get('kind')==resource.get('kind') and row.get('component')==resource.get('component'))
                product={'RBC':'Eritrocitos','PLASMA':'Plasma','PLATELETS':'Plaquetas','KIDNEY':'Riñón','LIVER':'Hígado','HEART':'Corazón'}.get(row.get('component'),'Otro producto')
                values=(row.get('label'),row.get('location')) if key=='equipment' else (product,row.get('source'),row.get('version'))
                for column,cell_value in enumerate(values):
                    cell=QTableWidgetItem(str(cell_value or '')); cell.setToolTip(str(cell_value or ''))
                    if not valid:cell.setFlags(cell.flags() & ~Qt.ItemIsSelectable);cell.setToolTip('No disponible para esta unidad.')
                    panel['table'].setItem(index,column,cell)
            panel['page_label'].setText('Página '+str(page));panel['prev'].setEnabled(page>1);panel['next'].setEnabled(page*20<value['total']);status.setText('Selecciona equipo y perfil.' if rows else 'No hay registros en esta página.')
        worker.signals.done.connect(done);worker.signals.failed.connect(lambda error:done(error,True));window.pool.start(worker)
    def submit():
        equipment,profile=selected('equipment'),selected('profile')
        valid=binding.current() and equipment and equipment.get('active') is True and profile and profile.get('kind')==resource.get('kind') and profile.get('component')==resource.get('component')
        if not valid or len(reason.text().strip())<6 or not confirmed.isChecked():
            status.setText('Selecciona equipo y perfil, escribe el motivo y confirma.');return
        result['body']={'version':resource['version'],'lab_profile_id':controls['lab_profile_id'],'cold_equipment_id':equipment['id'],'cold_profile_id':profile['id'],'reason':reason.text().strip(),'human_confirmation':'true'};window_dialog.accept()
    for key,panel in panels.items():
        panel['prev'].clicked.connect(lambda _=False,k=key:fetch(k,panels[k]['page']-1));panel['next'].clicked.connect(lambda _=False,k=key:fetch(k,panels[k]['page']+1));panel['refresh'].clicked.connect(lambda _=False,k=key:fetch(k,panels[k]['page']))
    save.clicked.connect(submit);cancel.clicked.connect(window_dialog.reject)
    for key in panels:fetch(key,1)
    accepted=window_dialog.exec();alive['value']=False
    return result['body'] if accepted==QDialog.Accepted and binding.current() else None


CATALOGUES={
    'cold_equipment':('equipment','Equipos de conservación','/api/v1/cold/equipment','cold_equipment_list','cold_equipment_detail',
                      [('label','Nombre'),('location','Ubicación'),('calibration_reference','Calibración'),('active','Activo')]),
    'cold_profiles':('profile','Perfiles térmicos académicos','/api/v1/cold/profiles','cold_profiles_list','cold_profiles_detail',
                     [('component','Producto'),('source','Fuente'),('version','Versión'),('effective_at','Vigencia')]),
}


def _context(window):
    from .session_context import SessionChanged
    try:
        binding=OperationContext(window)
        if binding.actor[2] not in ('OPERATOR','MEDICAL'):raise ContractError('Consulta disponible para personal de laboratorio y médico.')
        return binding
    except (SessionChanged,ContractError) as error:
        window.status.setText(str(error));return None


def _detail(binding,mode,identifier):
    binding.check();spec=CATALOGUES[mode]
    row=binding.client.authorized('inventario',spec[2]+'/'+identifier,spec[4])
    binding.check()
    if row.get('id')!=identifier or row.get('tenant_id')!=binding.actor[1]:
        raise ContractError('El registro no corresponde al catálogo de esta institución.')
    return row


def load_catalogue(window,display):
    from PySide6.QtWidgets import QTableWidgetItem
    binding=_context(window)
    if binding is None:return
    mode=window.mode;spec=CATALOGUES[mode];page=window.page
    window.heading.setText(spec[1]);window.description.setText('Consulta paginada de registros autorizados. Los perfiles son sintéticos y no sustituyen una decisión clínica.')
    window.table.setColumnCount(len(spec[5]));window.table.setHorizontalHeaderLabels([title for _,title in spec[5]])
    def fetch():
        binding.check();result=binding.client.authorized('inventario',spec[2],spec[3],params={'page':page,'page_size':20});binding.check()
        if result.get('page')!=page or any(row.get('tenant_id')!=binding.actor[1] for row in result['items']):
            raise ContractError('El listado no corresponde a la institución o página solicitada.')
        return result
    def ready(result):
        if not binding.current() or window.mode!=mode:return
        window.rows=result['items'];window.total=result['total'];window.table.setRowCount(len(window.rows));window.uncertain=False
        for index,row in enumerate(window.rows):
            for column,(key,_) in enumerate(spec[5]):
                value=('Sí' if row[key] else 'No') if key=='active' else display('occurred_at' if key=='effective_at' else key,row.get(key))
                window.table.setItem(index,column,QTableWidgetItem(str(value)))
        window.page_label.setText(f'Página {page} · {window.total} registros')
        window.cold_create_button.setText('Registrar equipo' if mode=='cold_equipment' else 'Registrar perfil térmico')
        window.cold_create_button.setVisible(binding.actor[2]==('OPERATOR' if mode=='cold_equipment' else 'MEDICAL'))
        window.cold_correct_button.setVisible(mode=='cold_profiles' and binding.actor[2]=='MEDICAL')
        window.set_controls(True)
    window.run_in_context(binding,fetch,ready,'Consultando catálogo de conservación…')


def open_catalogue_detail(window,display):
    binding=_context(window);item=window.selected()
    if binding is None:return
    if not item:window.status.setText('Selecciona un registro del catálogo.');return
    mode=window.mode
    def ready(row):
        if not binding.current():return
        detail=QDialog(window);detail.setWindowTitle(CATALOGUES[mode][1]);form=QFormLayout(detail)
        fields=CATALOGUES[mode][5]+([('minimum_c','Mínima °C'),('maximum_c','Máxima °C'),('max_gap_seconds','Intervalo máximo · segundos'),('synthetic','Sintético')] if mode=='cold_profiles' else [])
        for key,title in fields:
            value=row.get(key);text=('Sí' if value else 'No') if isinstance(value,bool) else display('occurred_at' if key=='effective_at' else key,value)
            label=QLabel(str(text));label.setWordWrap(True);form.addRow(title,label)
        close=QPushButton('Cerrar');close.clicked.connect(detail.reject);form.addRow(close);detail.exec()
    window.run_in_context(binding,lambda:_detail(binding,mode,item['id']),ready,'Consultando registro de conservación…')


def edit_catalogue(window,correction=False):
    binding=_context(window)
    if binding is None:return
    mode=window.mode
    if mode not in CATALOGUES:return
    kind=CATALOGUES[mode][0]
    if binding.actor[2]!=('OPERATOR' if kind=='equipment' else 'MEDICAL') or (correction and kind!='profile'):
        window.status.setText('Esta operación requiere personal autorizado.');return
    def ready(prior=None):
        if not binding.current():return
        body=dialog(window,kind,prior)
        if body is not None and binding.current():
            window.secure_command('cold_equipment_create' if kind=='equipment' else 'cold_profile_create',None,body)
    if correction:
        item=window.selected()
        if not item:window.status.setText('Selecciona el perfil que requiere corrección.');return
        window.run_in_context(binding,lambda:_detail(binding,mode,item['id']),ready,'Consultando antecedente térmico…')
    else:ready()


def bind_selected(window,work_type):
    binding=_context(window)
    if binding is None:return
    if window.mode!='inventory' or binding.actor[2]!='MEDICAL':
        window.status.setText('La vinculación corresponde al personal médico desde Inventario.');return
    item=window.selected()
    if not item:window.status.setText('Selecciona una unidad.');return
    identifier=item['id']
    def fetch():
        binding.check();resource=binding.client.authorized('inventario','/api/v1/resources/'+identifier,'resource_detail');binding.check()
        if resource.get('id')!=identifier or resource.get('current_institution_id')!=binding.actor[1]:
            raise ContractError('La unidad no pertenece a la institución activa.')
        if resource.get('status') not in ('QUARANTINE','AVAILABLE'):
            raise ContractError('La vinculación requiere una unidad en cuarentena o disponible.')
        controls=binding.client.authorized('inventario','/api/v1/resources/'+identifier+'/controls','resource_controls_detail');binding.check()
        if controls.get('id')!=identifier or not controls.get('lab_profile_id'):
            raise ContractError('La unidad requiere su perfil de laboratorio vigente antes de vincular conservación.')
        return resource,controls
    def ready(result):
        if not binding.current():return
        resource,controls=result;body=bind_dialog(window,resource,controls,work_type)
        if body is not None and binding.current():window.secure_command('resource_controls_create',identifier,body)
    window.run_in_context(binding,fetch,ready,'Consultando unidad y controles vigentes…')
