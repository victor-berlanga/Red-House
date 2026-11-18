"""Alta durable: el secreto no se guarda y el recibo no inventa resultados."""
from uuid import uuid4

from cryptography.fernet import Fernet
import pytest

from redhouse_desktop.client import ApiError, ContractError
from redhouse_desktop.journal import Journal, JournalError
from redhouse_desktop.user_creation import lookup_user, prepare_user, submit_user


class Keys:
    def __init__(self): self.key=Fernet.generate_key()
    def get(self,identifier,exists): return self.key


def test_user_creation_recovery_never_persists_password(tmp_path):
    keys=Keys(); tenant=str(uuid4()); user={'id':str(uuid4()),'tenant_id':tenant,'role':'ADMIN'}
    journal=Journal(tmp_path,'https://lab',user['id'],tenant,keys)
    record=prepare_user(journal,user,'cuenta.sintetica','OPERATOR','contraseña sintética segura')
    assert 'password' not in record['body'] and b'contrase' not in journal.file.read_bytes()
    restarted=Journal(tmp_path,'https://lab',user['id'],tenant,keys)
    class API:
        def __init__(self): self.user=user
        def authorized(self,service,path,operation,**kwargs):
            assert kwargs['key']==record['key']
            if operation=='user_creation_receipt': raise ApiError(404,'not_found','Sin recibo')
            assert kwargs['body']==dict(record['body'],password='contraseña sintética segura')
            return {'id':str(uuid4()),'username':record['body']['username'],'role':'OPERATOR','tenant_id':tenant}
    api=API(); pending=restarted.list()[0]
    assert lookup_user(api,restarted,pending) is None and restarted.list()[0]['state']=='PREPARED'
    submit_user(api,restarted,pending,'contraseña sintética segura')
    assert restarted.list()[0]['state']=='DONE' and 'password' not in restarted.list()[0]['body']


def test_user_receipt_rejects_other_scope_and_mismatched_result(tmp_path):
    keys=Keys(); tenant=str(uuid4()); user={'id':str(uuid4()),'tenant_id':tenant,'role':'ADMIN'}
    journal=Journal(tmp_path,'https://lab',user['id'],tenant,keys)
    record=prepare_user(journal,user,'cuenta.sintetica','OPERATOR','contraseña sintética segura')
    class API:
        def __init__(self): self.user=dict(user,tenant_id=str(uuid4()))
        def authorized(self,*args,**kwargs): return {'id':str(uuid4()),'username':'otra.cuenta','role':'OPERATOR'}
    api=API()
    with pytest.raises(JournalError): lookup_user(api,journal,record)
    api.user=user
    with pytest.raises(ContractError): lookup_user(api,journal,record)
    assert journal.list()[0]['state']=='PREPARED'


def test_conflicting_password_does_not_finish_or_replace_attempt(tmp_path):
    keys=Keys(); tenant=str(uuid4()); user={'id':str(uuid4()),'tenant_id':tenant,'role':'ADMIN'}
    journal=Journal(tmp_path,'https://lab',user['id'],tenant,keys)
    record=prepare_user(journal,user,'cuenta.sintetica','OPERATOR','contraseña sintética segura')
    class API:
        def __init__(self): self.user=user
        def authorized(self,*args,**kwargs):
            assert kwargs['key']==record['key']
            raise ApiError(409,'idempotency_conflict','Revisa la operación.')
    with pytest.raises(ApiError): submit_user(API(),journal,record,'contraseña diferente segura')
    pending=journal.list()[0]
    assert pending['state']=='PREPARED' and pending['key']==record['key'] and 'password' not in pending['body']


def test_lost_response_keeps_original_attempt(tmp_path):
    keys=Keys(); tenant=str(uuid4()); user={'id':str(uuid4()),'tenant_id':tenant,'role':'ADMIN'}
    journal=Journal(tmp_path,'https://lab',user['id'],tenant,keys)
    record=prepare_user(journal,user,'cuenta.sintetica','OPERATOR','contraseña sintética segura')
    class API:
        def __init__(self): self.user=user
        def authorized(self,*args,**kwargs): raise ConnectionError('respuesta perdida')
    with pytest.raises(ConnectionError): submit_user(API(),journal,record,'contraseña sintética segura',fresh=True)
    restarted=Journal(tmp_path,'https://lab',user['id'],tenant,keys)
    assert restarted.list()[0]['key']==record['key'] and restarted.list()[0]['state']=='PREPARED'


@pytest.mark.parametrize('extra,target', [({'password':'secreto'},'user_create'),({'proof':'comprobante'},'user_create'),({},'otro_destino')])
def test_journal_rejects_secrets_and_wrong_user_target(tmp_path,extra,target):
    keys=Keys(); tenant=str(uuid4()); journal=Journal(tmp_path,'https://lab',str(uuid4()),tenant,keys)
    body={'username':'cuenta.sintetica','role':'OPERATOR','tenant_id':tenant,**extra}
    record={'key':str(uuid4()),'kind':'USER_CREATE','target':target,'body':body,'state':'PREPARED','operation_id':None,'status':None}
    with pytest.raises(JournalError): journal.prepare(record)
    assert not journal.file.exists()


@pytest.mark.parametrize('status,code,fresh,expected',[(409,'conflict',True,'DONE'),(422,'validation',True,'DONE'),(409,'idempotency_conflict',True,'PREPARED'),(403,'reauthentication_required',True,'PREPARED'),(404,'not_found',True,'PREPARED'),(409,'conflict',False,'PREPARED'),(422,'validation',False,'PREPARED')])
def test_only_definitive_initial_rejection_finishes_attempt(tmp_path,status,code,fresh,expected):
    keys=Keys(); tenant=str(uuid4()); user={'id':str(uuid4()),'tenant_id':tenant,'role':'ADMIN'}
    journal=Journal(tmp_path,'https://lab',user['id'],tenant,keys)
    record=prepare_user(journal,user,'cuenta.sintetica','OPERATOR','contraseña sintética segura')
    class API:
        def __init__(self): self.user=user
        def authorized(self,*args,**kwargs): raise ApiError(status,code,'Resultado sintético.')
    with pytest.raises(ApiError): submit_user(API(),journal,record,'contraseña sintética segura',fresh=fresh)
    pending=journal.list()[0]
    assert pending['state']==expected and pending['key']==record['key'] and 'fresh' not in pending


def test_user_form_requires_explicit_profile(monkeypatch):
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication, QComboBox, QLineEdit
    import redhouse_desktop.app as desktop
    app=QApplication.instance() or QApplication([])
    monkeypatch.setattr(desktop,'USER_CREATION_ENABLED',True)
    class Client:
        user={'id':str(uuid4()),'tenant_id':str(uuid4()),'role':'ADMIN'}
        session_id=str(uuid4())
        access=None
    window=desktop.Window(); window.client=Client(); window.journal=object(); seen=[]; cleared=[]
    original_clear=QLineEdit.clear
    def clear(field):
        if field.echoMode()==QLineEdit.Password: cleared.append(True)
        original_clear(field)
    monkeypatch.setattr(QLineEdit,'clear',clear)
    def inspect():
        modal=app.activeModalWidget(); assert modal
        seen.append(modal.findChild(QComboBox).currentData()); fields=modal.findChildren(QLineEdit)[1:]; fields[0].setText('contraseña sintética segura'); fields[1].setText('contraseña sintética segura'); modal.reject()
    QTimer.singleShot(0,inspect); window.create_user()
    assert seen==[None] and len(cleared)==2
    window.close()
