"""Comprobaciones de interacción local sin servidor ni datos clínicos."""
import os
import pytest
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from redhouse_desktop.app import STYLE, Window

app = QApplication.instance() or QApplication([])
app.setStyleSheet(STYLE)

class FakeClient:
    user={'username':'operador','role':'OPERATOR'}
    access=None
    calls=0
    def authorized(self,*args,**kwargs):
        self.calls+=1
        return {'items':[],'page':1,'page_size':20,'total':0}


def test_selection_is_read_only_and_pagination_reflects_server():
    w=Window(); w.client=FakeClient(); w.stack.setCurrentIndex(1); w.mode='inventory'; w.update_navigation()
    w.show_rows({'items':[{'id':'ficticio','folio':'RH-12345','component':'RBC','status':'QUARANTINE','blood_group':'O+','expires_at':'2030-01-01'}], 'page':1,'page_size':20,'total':1})
    w.show(); app.processEvents()
    point=w.table.visualItemRect(w.table.item(0,0)).center(); QTest.mouseClick(w.table.viewport(),Qt.LeftButton,pos=point)
    assert w.table.currentRow()==0 and w.client.calls==0
    assert w.table.item(0,1).text()=='Eritrocitos'
    assert w.table.item(0,3).text()=='En cuarentena'
    assert not w.prev.isEnabled() and not w.next.isEnabled()
    assert w.inventory_button.objectName()=='activeNav'
    assert not w.receive_button.isVisible()
    w.close()


def test_only_medical_can_review_result():
    w=Window(); w.client=FakeClient(); w.stack.setCurrentIndex(1); w.mode='results'; w.show()
    w.show_rows({'items':[],'page':1,'page_size':20,'total':0}); app.processEvents()
    assert w.review_button.isVisible() and not w.review_button.isEnabled()
    w.client.user={'username':'medico','role':'MEDICAL'}; w.set_controls(True)
    assert w.review_button.isEnabled()
    w.close()


def test_device_actions_restricted_to_administrator():
    w=Window(); w.client=FakeClient(); w.stack.setCurrentIndex(1); w.mode='devices'; w.show()
    data={'items':[{'id':'device','label':'Unidad móvil','source':'ANDROID','active':True,'expires_at':'2030-01-01T00:00:00+00:00','version':1}], 'page':1,'page_size':20,'total':1}
    w.show_rows(data); app.processEvents()
    assert w.device_revoke_button.isVisible() and not w.device_revoke_button.isEnabled()
    assert w.table.item(0,1).text()=='Teléfono Android'
    w.client.user={'username':'administradora','role':'ADMIN'}; w.set_controls(True)
    assert w.device_revoke_button.isEnabled() and w.device_create_button.isEnabled()
    assert not w.inventory_button.isVisible() and not w.samples_button.isVisible() and not w.results_button.isVisible()
    assert w.search.isEnabled() and w.search_button.isEnabled()
    w.mode='users'; w.show_rows({'items':[],'page':1,'page_size':20,'total':0})
    assert w.device_create_button.isVisible() and w.device_create_button.isEnabled()
    w.close()


def test_recovery_reuses_original_key_and_body(tmp_path,monkeypatch):
    from cryptography.fernet import Fernet
    from PySide6.QtWidgets import QMessageBox
    from redhouse_desktop.journal import Journal
    class Keys:
        def get(self,identifier,exists): return key
    key=Fernet.generate_key(); journal=Journal(tmp_path,'https://lab','user','tenant',Keys())
    body={'evaluation_id':'evaluation','resource_id':'resource','reason':'Motivo autorizado','human_confirmation':'true'}
    journal.prepare({'key':'original-key','body':body,'state':'UNCERTAIN','operation_id':None,'status':None})
    calls=[]
    class Client:
        user={'role':'MEDICAL'}; access=None
        def authorized(self,*args,**kwargs):
            from redhouse_desktop.client import ApiError
            calls.append((args,kwargs))
            if len(calls)==1: raise ApiError(403,'reauthentication_required','Confirma identidad.',[{'field':'reauthentication','code':'challenge','challenge':'opaque'}])
            return {'operation_id':'op','status':'PENDING','reservation':None}
    monkeypatch.setattr(QMessageBox,'question',lambda *args:QMessageBox.Yes)
    monkeypatch.setattr(QMessageBox,'information',lambda *args:QMessageBox.Ok)
    w=Window(); w.client=Client(); w.journal=journal
    monkeypatch.setattr(w,'reauthenticate',lambda operation,resource,challenge,continuation:continuation('proof-in-memory'))
    w.recover_operation(journal.list())
    for _ in range(1000):
        if not w.busy and len(calls)==2: break
        QTest.qWait(20)
    assert not w.busy and len(calls)==2
    assert all(call[1]['key']=='original-key' and call[1]['body']==body for call in calls)
    assert calls[0][1]['proof'] is None and calls[1][1]['proof']=='proof-in-memory'
    assert 'proof-in-memory' not in str(journal.list())
    assert journal.list()[0]['operation_id']=='op'
    w.close()


def test_uncertain_print_requires_review_without_sending_again(tmp_path,monkeypatch):
    from cryptography.fernet import Fernet
    from PySide6.QtWidgets import QMessageBox
    from redhouse_desktop.journal import Journal
    from redhouse_desktop.label_issuance import prepare_label
    class Keys:
        def __init__(self): self.key=Fernet.generate_key()
        def get(self,identifier,exists): return self.key
    journal=Journal(tmp_path,'https://lab','user','tenant',Keys())
    record=prepare_label(journal,{'id':'unit','version':1},'PRINT','Motivo documentado')
    journal.update(record['key'],{'operation_id':'issuance','status':'AUTHORIZED'})
    journal.print_transition(record['key'],'issuance','start')
    window=Window(); window.client=FakeClient(); window.journal=journal
    monkeypatch.setattr(QMessageBox,'question',lambda *args:QMessageBox.Yes)
    monkeypatch.setattr(window,'label_authorized',lambda *_:pytest.fail('No debe reimprimir.'))
    window.recover_operation(journal.list())
    for _ in range(500):
        QTest.qWait(20)
        if not window.busy: break
    assert journal.list()[0]['status']=='PRINT_REVIEWED' and window.client.calls==0
    window.close()


def test_summary_keeps_other_services_when_one_is_unavailable(monkeypatch):
    from redhouse_desktop.client import ApiError
    class SummaryClient:
        user={'role':'OPERATOR'}; access=None
        def authorized(self,service,*args,**kwargs):
            if service=='receptores': raise ApiError(503,'dependency_unavailable','No disponible.')
            return {'total':0,'statuses':[],'expiring':0}
    window=Window(); window.client=SummaryClient(); received=[]
    monkeypatch.setattr(window,'summary_dialog',received.append)
    window.open_summary()
    for _ in range(500):
        QTest.qWait(20)
        if received and not window.busy: break
    assert received and received[0]['receptores'] is None
    assert received[0]['inventario']['total']==received[0]['transporte']['total']==0
    window.close()


def test_request_creation_is_only_available_to_medical_role():
    window=Window(); window.client=FakeClient(); window.stack.setCurrentIndex(1); window.mode='requests'; window.show()
    window.show_rows({'items':[],'page':1,'total':0}); app.processEvents()
    assert window.request_create_button.isVisible() and not window.request_create_button.isEnabled()
    window.client.user={'role':'MEDICAL'}; window.set_controls(True)
    assert window.request_create_button.isEnabled()
    window.close()


def test_request_picker_reports_selected_recipient(tmp_path,monkeypatch):
    from pathlib import Path
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QLabel, QTableWidget
    class Client:
        user={'role':'MEDICAL'}; access=None
        def authorized(self,*args,**kwargs):
            return {'items':[{'id':'00000000-0000-4000-8000-000000000001','folio':'PACIENTE-FICTICIO','display_name':'Paciente ficticio','status':'ACTIVE','kind':'BLOOD'},
                             {'id':'00000000-0000-4000-8000-000000000002','folio':'ORGANO-FICTICIO','display_name':'Paciente ficticio','status':'ACTIVE','kind':'ORGAN','organ_type':'KIDNEY'}],'page':1,'total':2}
    window=Window(); window.client=Client(); seen=[]; limits=[]
    def inspect():
        modal=QApplication.activeModalWidget()
        table=modal.findChild(QTableWidget) if modal else None
        if not table or not table.rowCount(): QTimer.singleShot(50,inspect); return
        table.selectRow(0); app.processEvents()
        from PySide6.QtWidgets import QSpinBox
        quantity=modal.findChild(QSpinBox); quantity.setValue(5)
        table.selectRow(1); app.processEvents(); limits.append((quantity.maximum(),quantity.value()))
        output=Path(os.environ.get('DESKTOP_CAPTURE_DIR',str(tmp_path))); output.mkdir(parents=True,exist_ok=True)
        modal.grab().save(str(output/'solicitud-organo.png'))
        table.selectRow(0); app.processEvents(); limits.append((quantity.maximum(),quantity.value()))
        seen.extend(label.text() for label in modal.findChildren(QLabel))
        modal.grab().save(str(output/'solicitud-aviso-corregido.png')); modal.reject()
    QTimer.singleShot(50,inspect); window.request_form()
    assert 'Receptor seleccionado: PACIENTE-FICTICIO' in seen
    assert limits==[(1,1),(100,1)]
    window.close()


def test_resource_form_captures_organ_and_optional_collection(tmp_path,monkeypatch):
    from pathlib import Path
    from PySide6.QtCore import QDateTime, QTimer
    from PySide6.QtWidgets import QCheckBox, QComboBox, QDateTimeEdit, QLineEdit, QMessageBox, QPushButton
    window=Window(); window.client=FakeClient(); submitted=[]; warnings=[]
    monkeypatch.setattr(window,'durable',lambda operation,identifier,body:submitted.append((operation,body)))
    monkeypatch.setattr(window,'received',lambda:None)
    monkeypatch.setattr(QMessageBox,'warning',lambda *args:warnings.append(True))
    def fill():
        modal=QApplication.activeModalWidget()
        if not modal: QTimer.singleShot(50,fill); return
        modal.findChild(QLineEdit).setText('UNIDAD-FICTICIA')
        boxes=modal.findChildren(QComboBox); boxes[0].setCurrentIndex(boxes[0].findData('ORGAN'))
        boxes[1].setCurrentIndex(boxes[1].findData('KIDNEY')); boxes[2].setCurrentIndex(boxes[2].findData('O+'))
        checks=modal.findChildren(QCheckBox); checks[0].setChecked(True); dates=modal.findChildren(QDateTimeEdit)
        dates[0].setDateTime(QDateTime.currentDateTime().addDays(-1)); dates[1].setDateTime(QDateTime.currentDateTime().addDays(1))
        def confirm_date():
            checks[1].setChecked(True); app.processEvents()
            output=Path(os.environ.get('DESKTOP_CAPTURE_DIR',str(tmp_path))); output.mkdir(parents=True,exist_ok=True)
            modal.grab().save(str(output/'unidad-organo-sintetica.png'))
            next(button for button in modal.findChildren(QPushButton) if button.text()=='Registrar unidad').click()
        QTimer.singleShot(50,confirm_date)
        next(button for button in modal.findChildren(QPushButton) if button.text()=='Registrar unidad').click()
    QTimer.singleShot(50,fill); window.create_resource()
    for _ in range(500):
        QTest.qWait(20)
        if submitted and not window.busy: break
    assert warnings==[True] and submitted and submitted[0][0]=='resource_create'
    body=submitted[0][1]
    assert body['kind']=='ORGAN' and body['component']=='KIDNEY' and body['blood_group']=='O+' and body['collected_at']
    window.close()


def test_login_prompts_verification_only_when_required():
    from redhouse_desktop.client import ApiError
    w=Window(); w.show(); app.processEvents()
    assert not w.otp.isVisible()
    w.password.setText('contraseña-temporal')
    w.failed(ApiError(401,'mfa_required','Segundo factor inválido.'))
    assert w.otp.isVisible() and w.password.text()=='contraseña-temporal'
    assert w.otp_label.text()=='Código de verificación'
    w.failed(ApiError(401,'unauthorized','Credenciales inválidas.'))
    assert w.password.text()==''
    w.close()


def test_failed_navigation_does_not_keep_previous_account_rows():
    from redhouse_desktop.client import ApiError
    class Client:
        user={'role':'OPERATOR'}; access=None
        def authorized(self,*args,**kwargs): raise ApiError(403,'forbidden','Sin permiso.')
    w=Window(); w.client=Client(); w.stack.setCurrentIndex(1); w.mode='inventory'
    w.show_rows({'items':[{'id':'old','folio':'RH-ANTERIOR'}],'page':1,'page_size':20,'total':1})
    assert len(w.rows)==1
    w.switch('requests')
    for _ in range(1000):
        if not w.busy: break
        QTest.qWait(20)
    assert not w.busy and w.rows==[] and w.table.rowCount()==0
    w.close()


def test_accepted_reservation_is_not_presented_as_confirmed(monkeypatch):
    from PySide6.QtWidgets import QMessageBox
    messages=[]
    monkeypatch.setattr(QMessageBox,'information',lambda *args:messages.append(args[2]))
    w=Window(); w.reservation_result({'operation_id':'op-1','status':'PENDING','reservation':None})
    assert 'pendiente' in messages[0].lower() and 'confirmada' not in messages[0].lower()
    w.close()


def test_expired_session_hides_and_clears_previous_results():
    from redhouse_desktop.client import ApiError
    class Expired:
        user=None
    w=Window(); w.client=Expired(); w.stack.setCurrentIndex(1)
    w.rows=[{'id':'old'}]; w.table.setRowCount(1)
    w.failed(ApiError(401,'unauthorized','Sesión vencida.'))
    assert w.stack.currentIndex()==0 and w.rows==[] and w.table.rowCount()==0 and w.client is None
    w.close()
