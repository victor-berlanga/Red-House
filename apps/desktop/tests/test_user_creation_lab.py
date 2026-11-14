"""Alta de cuenta y recuperación de respuesta perdida en laboratorio aislado."""
import os
import uuid
from pathlib import Path

from cryptography.fernet import Fernet
from PySide6.QtCore import QTimer
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QComboBox, QLineEdit, QPushButton

from tests.conftest import platform
from test_real_lab import gateway
from redhouse_desktop.journal import Journal
from redhouse_desktop.client import ApiError, Client
from redhouse_desktop.user_creation import prepare_user, submit_user
import redhouse_desktop.app as desktop
import pytest


def wait_until(predicate):
    for _ in range(2000):
        QTest.qWait(20)
        if predicate(): return True
    return False


def test_account_creation_recovers_lost_response_through_qt(platform,gateway,monkeypatch,tmp_path):
    principal=platform.ok('identidad_acceso','GET','/api/v1/auth/me',user='admin1')
    administrator='desktop-admin-'+uuid.uuid4().hex[:10]
    platform.ok('identidad_acceso','POST','/api/v1/users',user='admin1',data={
        'username':administrator,'password':platform.env.state['password'],
        'tenant_id':principal['tenant_id'],'role':'ADMIN',
    })
    class Keys:
        def __init__(self): self.key=Fernet.generate_key()
        def get(self,identifier,exists): return self.key
    keys=Keys()
    monkeypatch.setattr(desktop,'Journal',lambda _root,base,user,tenant:Journal(tmp_path,base,user,tenant,keys))
    monkeypatch.setattr(desktop,'USER_CREATION_ENABLED',True)
    monkeypatch.setenv('REDHOUSE_BASE_URL',gateway)
    original=desktop.Client.authorized; dropped=[]
    def lose_once(client,service,path,operation,*args,**kwargs):
        result=original(client,service,path,operation,*args,**kwargs)
        if operation=='user_create' and not dropped:
            dropped.append(True)
            raise ConnectionError('Respuesta sintética perdida después del commit')
        return result
    monkeypatch.setattr(desktop.Client,'authorized',lose_once)
    app=QApplication.instance() or QApplication([]); app.setStyleSheet(desktop.STYLE)
    window=desktop.Window(); window.show(); window.username.setText(administrator); window.password.setText(platform.env.state['password']); window.login()
    assert wait_until(lambda:window.stack.currentIndex()==1 and not window.busy)
    username='desktop-account-'+uuid.uuid4().hex[:10]; captured=[]
    def fill():
        modal=QApplication.activeModalWidget()
        if not modal: QTimer.singleShot(50,fill); return
        fields=modal.findChildren(QLineEdit); fields[0].setText(username)
        roles=modal.findChild(QComboBox); roles.setCurrentIndex(roles.findData('OPERATOR'))
        app.processEvents(); out=Path(os.environ['DESKTOP_CAPTURE_DIR']); out.mkdir(parents=True,exist_ok=True)
        assert modal.grab().save(str(out/'alta-qt.png')); captured.append(True)
        fields[1].setText(platform.env.state['password']); fields[2].setText(platform.env.state['password'])
        next(button for button in modal.findChildren(QPushButton) if button.text()=='Registrar cuenta').click()
    QTimer.singleShot(50,fill); window.create_user()
    assert wait_until(lambda:dropped and not window.busy)
    pending=window.journal.list()[0]
    assert captured and pending['state']=='PREPARED' and 'password' not in pending['body']
    original_key=pending['key']
    window.journal=Journal(tmp_path,window.client.base,window.client.user['id'],window.client.user['tenant_id'],keys)
    window.recover_operation(window.journal.list())
    assert wait_until(lambda:not window.busy and window.journal.list()[0]['state']=='DONE')
    assert window.journal.list()[0]['key']==original_key
    found=window.client.authorized('identidad-acceso','/api/v1/users','user_list',params={'q':username,'page':1,'page_size':20})
    assert len([row for row in found['items'] if row['username']==username])==1
    window.close()


def test_duplicate_account_releases_journal_for_new_attempt(platform,gateway,tmp_path):
    principal=platform.ok('identidad_acceso','GET','/api/v1/auth/me',user='admin1')
    administrator='desktop-admin-'+uuid.uuid4().hex[:10]
    platform.ok('identidad_acceso','POST','/api/v1/users',user='admin1',data={
        'username':administrator,'password':platform.env.state['password'],
        'tenant_id':principal['tenant_id'],'role':'ADMIN',
    })
    class Keys:
        def __init__(self): self.key=Fernet.generate_key()
        def get(self,identifier,exists): return self.key
    client=Client(gateway); user=client.login(administrator,platform.env.state['password'],'')
    journal=Journal(tmp_path,gateway,user['id'],user['tenant_id'],Keys())
    duplicate=prepare_user(journal,user,administrator,'OPERATOR',platform.env.state['password'])
    with pytest.raises(ApiError) as error:
        submit_user(client,journal,duplicate,platform.env.state['password'],fresh=True)
    assert error.value.status==409 and error.value.code=='conflict'
    assert journal.list()[0]['state']=='DONE' and journal.list()[0]['status']=='FAILED'
    name='desktop-new-'+uuid.uuid4().hex[:10]
    retry=prepare_user(journal,user,name,'OPERATOR',platform.env.state['password'])
    result=submit_user(client,journal,retry,platform.env.state['password'],fresh=True)
    assert result['username']==name and journal.list()[-1]['state']=='DONE'
    client.logout()
