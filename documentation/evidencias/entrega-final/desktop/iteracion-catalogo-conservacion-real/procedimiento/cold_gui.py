"""Secuencia Qt académica sobre unidad propia; no inicia servicios ni inicia sesión."""
from pathlib import Path
import time
from uuid import uuid4
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication,QCheckBox,QComboBox,QDateTimeEdit,QDialog,QLineEdit,QPushButton,QTableWidget
import redhouse_desktop.cold_catalogue as catalog


def run(operator,medical,resource,lab_profile_id,output,wait_until):
    app=QApplication.instance();output=Path(output);errors=[]; label='Equipo-E2EB-'+uuid4().hex[:8]; source='Perfil sintético-E2EB-'+uuid4().hex[:8]
    if not app or operator.client.user['role']!='OPERATOR' or medical.client.user['role']!='MEDICAL' or operator.client.user['tenant_id']!=medical.client.user['tenant_id']:
        raise RuntimeError('Actores no corresponden')
    if resource['current_institution_id']!=medical.client.user['tenant_id'] or resource['status'] not in ('AVAILABLE','QUARANTINE'):
        raise RuntimeError('Unidad no disponible')
    def require(value,message):
        if not value:raise RuntimeError(message)
    def modal(title,callback):
        deadline=time.monotonic()+15
        def visit():
            dialog=app.activeModalWidget()
            if not dialog or dialog.windowTitle()!=title:dialog=next((x for x in app.topLevelWidgets() if isinstance(x,QDialog) and x.isVisible() and x.windowTitle()==title),None)
            if time.monotonic()>deadline:
                errors.append('modal_timeout')
                if dialog:dialog.reject()
                return
            if not dialog:QTimer.singleShot(50,visit);return
            try:callback(dialog)
            except LookupError:QTimer.singleShot(50,visit)
            except Exception as error:  # noqa: BLE001 - registrar solo clase
                errors.append(type(error).__name__);dialog.reject()
        QTimer.singleShot(0,visit)
    def click(dialog,title):next(x for x in dialog.findChildren(QPushButton) if x.text()==title).click()
    def completed(window,operation):
        records=[x for x in window.journal.list() if x.get('target',{}).get('operation')==operation and x.get('state')=='DONE' and x.get('status')=='COMPLETED']
        return records[0] if len(records)==1 else None
    def wait(window,operation):
        require(wait_until(lambda:bool(errors) or (not window.busy and completed(window,operation) is not None)),'operación pendiente')
        require(not errors,'error en formulario')
        return completed(window,operation)['operation_id']
    def switch(window,mode):
        window.switch(mode);require(wait_until(lambda:not window.busy),'vista pendiente')
    switch(operator,'cold_equipment')
    def equipment(dialog):
        fields=dialog.findChildren(QLineEdit)
        for field,value in zip(fields,(label,'Área sintética E2EB','Calibración sintética')):field.setText(value)
        app.processEvents();require(dialog.grab().save(str(output/'equipo.png')),'captura');click(dialog,'Guardar')
    modal('Registrar equipo de conservación',equipment);operator.cold_catalogue_action(False)
    equipment_id=wait(operator,'cold_equipment_create')
    switch(medical,'cold_profiles')
    def profile(dialog):
        choice=dialog.findChild(QComboBox);choice.setCurrentIndex(choice.findData((resource['kind'],resource['component'])))
        fields=[x for x in dialog.findChildren(QLineEdit) if not isinstance(x.parent(),QDateTimeEdit)]
        for field,value in zip(fields,('1','2','300',source)):field.setText(value)
        dialog.findChild(QCheckBox).setChecked(True);app.processEvents();require(dialog.grab().save(str(output/'perfil.png')),'captura');click(dialog,'Guardar')
    modal('Registrar perfil térmico académico',profile);medical.cold_catalogue_action(False)
    profile_id=wait(medical,'cold_profile_create')
    switch(medical,'inventory')
    for _ in range(100):
        index=next((i for i,row in enumerate(medical.rows) if row.get('id')==resource['id']),None)
        if index is not None:medical.table.selectRow(index);break
        require(medical.next.isEnabled(),'unidad no visible');medical.next.click();require(wait_until(lambda:not medical.busy),'página pendiente')
    else:raise RuntimeError('límite de páginas')
    original=catalog.bind_dialog
    def adapted(*args,**kwargs):
        def select(dialog):
            tables=dialog.findChildren(QTableWidget)
            if len(tables)!=2 or not all(table.rowCount() for table in tables):raise LookupError()
            equipment_rows=[i for i in range(tables[0].rowCount()) if tables[0].item(i,0) and tables[0].item(i,0).text()==label]
            profile_rows=[i for i in range(tables[1].rowCount()) if tables[1].item(i,1) and tables[1].item(i,1).text()==source]
            if not equipment_rows or not profile_rows:raise LookupError()
            require(len(equipment_rows)==len(profile_rows)==1,'selección no inequívoca')
            tables[0].selectRow(equipment_rows[0]);tables[1].selectRow(profile_rows[0]);dialog.findChild(QLineEdit).setText('Vinculación académica sintética');dialog.findChild(QCheckBox).setChecked(True)
            app.processEvents();require(dialog.grab().save(str(output/'vinculo.png')),'captura');click(dialog,'Vincular conservación')
        modal('Vincular conservación',select);return original(*args,**kwargs)
    catalog.bind_dialog=adapted
    try:
        medical.bind_cold_controls();wait(medical,'resource_controls_create')
    finally:catalog.bind_dialog=original
    controls=medical.client.authorized('inventario','/api/v1/resources/'+resource['id']+'/controls','resource_controls_detail')
    require(controls.get('id')==resource['id'] and controls.get('lab_profile_id')==lab_profile_id and controls.get('cold_equipment_id')==equipment_id and controls.get('cold_profile_id')==profile_id,'vínculo no corresponde')
    return {'resource_id':resource['id'],'lab_profile_id':lab_profile_id,'equipment_id':equipment_id,'profile_id':profile_id}
