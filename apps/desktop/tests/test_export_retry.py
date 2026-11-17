from types import SimpleNamespace
from uuid import uuid4

import pytest
from cryptography.fernet import Fernet
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QCheckBox, QDialog, QLineEdit

from redhouse_desktop.app import Window
from redhouse_desktop.client import ContractError
from redhouse_desktop.durable_commands import prepare_command, submit_command
from redhouse_desktop.journal import Journal

app = QApplication.instance() or QApplication([])

class Keys:
    def __init__(self): self.key=Fernet.generate_key()
    def get(self, identifier, exists): return self.key

def setup_command(tmp_path):
    tenant, user, target = (str(uuid4()) for _ in range(3))
    journal=Journal(tmp_path,'https://lab',user,tenant,Keys())
    body={'human_confirmation':True,'reason':'Corrección documentada'}
    record=prepare_command(journal,'export_retry',target,body)
    api=SimpleNamespace(user={'id':user,'tenant_id':tenant})
    return tenant,user,target,journal,record,api

def test_retry_response_correlates_and_replays_same_key(tmp_path):
    tenant,user,target,journal,record,api=setup_command(tmp_path)
    keys=[]
    def send(*args,**kwargs):
        keys.append(kwargs['key'])
        if len(keys)==1: raise ConnectionError('respuesta perdida')
        return {'id':target,'tenant_id':tenant,'user_id':user,'status':'PENDING'}
    api.authorized=send
    with pytest.raises(ConnectionError): submit_command(api,journal,record,fresh=True)
    submit_command(api,journal,journal.list()[0])
    assert keys==[record['key'],record['key']]
    assert journal.list()[0]['state']=='DONE'

@pytest.mark.parametrize('field',['id','tenant_id','user_id','status'])
def test_foreign_response_does_not_complete(tmp_path,field):
    tenant,user,target,journal,record,api=setup_command(tmp_path)
    result={'id':target,'tenant_id':tenant,'user_id':user,'status':'PENDING'}
    result[field]='other'
    api.authorized=lambda *a,**k:result
    with pytest.raises(ContractError): submit_command(api,journal,record,fresh=True)
    assert journal.list()[0]['state']=='PREPARED'

def test_invalid_status_never_opens_dialog_or_sends():
    w=Window(); w.client=SimpleNamespace(user={'id':'u','tenant_id':'t','role':'MEDICAL'},session_id='sid',access=None); w.journal=object(); w.uncertain=False; w.mode='reports'
    sent=[]; w.secure_command=lambda *args: sent.append(args)
    w.selected=lambda:{'id':str(uuid4()),'status':'COMPLETE'}
    w.retry_report()
    assert not sent and 'requiera reintento' in w.status.text()
    w.client=None; w.close()

@pytest.mark.parametrize('action',['cancel','switch','accept'])
def test_modal_controls_and_session(action):
    w=Window(); w.client=SimpleNamespace(user={'id':'u','tenant_id':'t','role':'MEDICAL'},session_id='sid',access=None); w.journal=object(); w.uncertain=False; w.mode='reports'
    target=str(uuid4());w.selected=lambda:{'id':target,'status':'RETRYABLE','report':'INVENTORY','format':'CSV'}
    sent=[];w.secure_command=lambda *args:sent.append(args)
    def handle():
        dialog=next(d for d in w.findChildren(QDialog) if d.isVisible())
        if action=='cancel': dialog.reject();return
        dialog.findChild(QLineEdit).setText('Motivo de prueba')
        dialog.findChild(QCheckBox).setChecked(True)
        if action=='switch': w.client=SimpleNamespace(user={'id':'other','tenant_id':'t','role':'MEDICAL'},session_id='new',access=None)
        dialog.accept()
    QTimer.singleShot(0,handle);w.retry_report()
    if action=='accept': assert sent==[('export_retry',target,{'human_confirmation':True,'reason':'Motivo de prueba'})]
    else: assert not sent
    w.client=None;w.close()


def test_refresh_hides_retry_when_selected_job_is_complete():
    w=Window();w.client=SimpleNamespace(user={'id':'u','tenant_id':'t','role':'MEDICAL'},session_id='sid',access=None);w.journal=object();w.mode='reports'
    w.stack.setCurrentIndex(1); w.show(); item={'id':str(uuid4()),'status':'RETRYABLE','report':'INVENTORY','format':'CSV','created_at':'2026-11-16T12:00:00Z'}
    data={'items':[item],'total':1,'page':1}; w.show_rows(data);w.table.selectRow(0);app.processEvents()
    assert w.report_retry_button.isVisible()
    w.show_rows({'items':[{**item,'status':'COMPLETE'}],'total':1,'page':1});app.processEvents()
    assert w.table.currentRow()==0 and not w.report_retry_button.isVisible()
    w.client=None;w.close()

def test_other_area_never_sends():
    w=Window();w.client=SimpleNamespace(user={'id':'u','tenant_id':'t','role':'MEDICAL'},session_id='sid',access=None);w.journal=object();w.uncertain=False;w.mode='inventory'
    w.selected=lambda:{'id':str(uuid4()),'status':'RETRYABLE'}
    sent=[];w.secure_command=lambda *args:sent.append(args)
    w.retry_report();assert not sent
    w.client=None;w.close()
