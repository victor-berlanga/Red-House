"""Administración XML/Qt con identidades sintéticas del laboratorio aislado."""
import os
import uuid
from pathlib import Path

from cryptography.fernet import Fernet
from PySide6.QtCore import QTimer
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QCheckBox, QLineEdit, QPushButton

from tests.conftest import platform
from test_real_lab import gateway
from redhouse_desktop.journal import Journal
import redhouse_desktop.app as desktop


def wait_until(predicate):
    for _ in range(2000):
        QTest.qWait(20)
        if predicate(): return True
    return False


def test_admin_registers_and_revokes_device(platform,gateway,monkeypatch,tmp_path):
    principal=platform.ok('identidad_acceso','GET','/api/v1/auth/me',user='admin1')
    username='admin-desktop-'+uuid.uuid4().hex[:10]
    platform.ok('identidad_acceso','POST','/api/v1/users',user='admin1',data={
        'username':username,'password':platform.env.state['password'],
        'tenant_id':principal['tenant_id'],'role':'ADMIN',
    })
    class Keys:
        def __init__(self): self.key=Fernet.generate_key()
        def get(self,identifier,exists): return self.key
    keys=Keys()
    monkeypatch.setattr(desktop,'Journal',lambda _root,base,user,tenant:Journal(tmp_path,base,user,tenant,keys))
    monkeypatch.setenv('REDHOUSE_BASE_URL',gateway)
    app=QApplication.instance() or QApplication([]); app.setStyleSheet(desktop.STYLE)
    window=desktop.Window(); window.show(); window.username.setText(username); window.password.setText(platform.env.state['password']); window.login()
    assert wait_until(lambda:window.stack.currentIndex()==1 and not window.busy)
    target=next(i for i,row in enumerate(window.rows) if row['username']=='transport1')
    window.table.selectRow(target)
    title='Equipo sintético '+uuid.uuid4().hex[:6]
    out=Path(os.environ['DESKTOP_CAPTURE_DIR']); out.mkdir(parents=True,exist_ok=True)
    def fill_create():
        modal=QApplication.activeModalWidget()
        if not modal: QTimer.singleShot(50,fill_create); return
        modal.findChild(QLineEdit).setText(title); modal.findChild(QCheckBox).setChecked(True)
        app.processEvents(); assert modal.grab().save(str(out/'registro-qt.png'))
        next(button for button in modal.findChildren(QPushButton) if button.text()=='Registrar').click()
    QTimer.singleShot(50,fill_create); window.create_device()
    assert wait_until(lambda:not window.busy and window.journal.list() and window.journal.list()[-1]['state']=='DONE')
    window.switch('devices'); assert wait_until(lambda:not window.busy and any(row['label']==title for row in window.rows))
    app.processEvents(); assert window.grab().save(str(out/'dispositivos-qt.png'))
    target=next(i for i,row in enumerate(window.rows) if row['label']==title); window.table.selectRow(target)
    def fill_revoke():
        modal=QApplication.activeModalWidget()
        if not modal: QTimer.singleShot(50,fill_revoke); return
        modal.findChild(QLineEdit).setText('Revocación sintética'); modal.findChild(QCheckBox).setChecked(True)
        next(button for button in modal.findChildren(QPushButton) if button.text()=='Revocar').click()
    QTimer.singleShot(50,fill_revoke); window.revoke_device()
    assert wait_until(lambda:not window.busy and any(row['label']==title and not row['active'] for row in window.rows))
    window.close()
