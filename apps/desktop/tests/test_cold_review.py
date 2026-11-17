"""Revisión de conservación: alcance, versión vigente y sesión sin servidores."""
from types import SimpleNamespace
from uuid import uuid4

import pytest
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QCheckBox, QDialog, QLineEdit, QPushButton
from redhouse_desktop import cold_review
from redhouse_desktop.app import Window
from redhouse_desktop.client import ApiError, ContractError
from redhouse_desktop.durable_commands import prepare_command, submit_command
from redhouse_desktop.journal import Journal
from redhouse_desktop.session_context import OperationContext
from test_resource_quality_commands import Keys


@pytest.fixture
def window():
    app = QApplication.instance() or QApplication([])
    value = Window()
    value.client = SimpleNamespace(user={'id':str(uuid4()),'tenant_id':str(uuid4()),'role':'MEDICAL'}, session_id=str(uuid4()))
    value.journal = object()
    value.run_in_context = lambda binding, work, done, *_: done(work())
    yield value
    value.client = None
    value.close()
    app.processEvents()


def case(window):
    resource = {'id':str(uuid4()),'folio':'SINTETICO-01','current_institution_id':window.client.user['tenant_id'],'status':'QUARANTINE','version':8}
    controls = {'id':resource['id'],'blocked':True,'version':12}
    window.client.authorized = lambda _service,_path,operation: resource if operation=='resource_detail' else controls
    return resource,controls


@pytest.mark.parametrize('changed',[False,True])
def test_review_uses_current_controls_and_checks_modal_session(window, monkeypatch, changed):
    resource, controls = case(window)
    sent = []
    def form(owner,row,current,binding):
        assert row is resource and current is controls and current['version']==12
        if changed: window.client.session_id=str(uuid4())
        return {'version':12,'reason':'Incidente sintético revisado','human_confirmation':'true'}
    monkeypatch.setattr(cold_review,'review_dialog',form)
    window.secure_command=lambda *args:sent.append(args)
    cold_review.open_review(window,dict(resource,version=1))
    assert sent == ([] if changed else [('quality_review',resource['id'],{'version':12,'reason':'Incidente sintético revisado','human_confirmation':'true'})])


@pytest.mark.parametrize('foreign',['resource','controls'])
def test_foreign_tenant_or_controls_never_opens_review(window,monkeypatch,foreign):
    resource, controls=case(window)
    if foreign=='resource':resource['current_institution_id']=str(uuid4())
    else:controls['id']=str(uuid4())
    monkeypatch.setattr(cold_review,'review_dialog',lambda *_:pytest.fail('foreign dialog'))
    with pytest.raises(ContractError):cold_review.open_review(window,resource)


@pytest.mark.parametrize('role',['OPERATOR','COORDINATOR'])
def test_nonmedical_never_reads_or_submits(window,role):
    resource,_=case(window);window.client.user['role']=role
    window.client.authorized=lambda *_:pytest.fail('unauthorized read')
    window.secure_command=lambda *_:pytest.fail('unauthorized write')
    cold_review.open_review(window,resource)


def test_unblocked_never_opens_review(window,monkeypatch):
    resource,controls=case(window);controls['blocked']=False
    monkeypatch.setattr(cold_review,'review_dialog',lambda *_:pytest.fail('unblocked dialog'))
    cold_review.open_review(window,resource)


def test_dialog_requires_reason_and_confirmation(window):
    resource,controls=case(window)
    def inspect():
        dialog=QApplication.activeModalWidget()
        reason=dialog.findChild(QLineEdit);confirm=dialog.findChild(QCheckBox)
        save=next(b for b in dialog.findChildren(QPushButton) if b.text()=='Registrar revisión')
        save.click();assert dialog.isVisible()
        reason.setText('Revisión sintética explícita');save.click();assert dialog.isVisible()
        confirm.setChecked(True);save.click()
    QTimer.singleShot(0,inspect)
    assert cold_review.review_dialog(window,resource,controls,OperationContext(window))=={'version':12,'reason':'Revisión sintética explícita','human_confirmation':'true'}


@pytest.mark.parametrize('mismatch',['id','version','blocked','stale'])
def test_command_preserves_intent_on_rejected_confirmation(tmp_path,mismatch):
    resource,tenant=str(uuid4()),str(uuid4())
    journal=Journal(tmp_path,'https://lab','user',tenant,Keys())
    record=prepare_command(journal,'quality_review',resource,{'version':12,'reason':'Revisión documentada','human_confirmation':'true'})
    class API:
        user={'tenant_id':tenant}
        def authorized(self,*args,**kwargs):
            assert kwargs['key']==record['key'] and kwargs['body']['version']==12
            if mismatch=='stale':raise ApiError(412,'stale_version','Versión obsoleta')
            return dict({'id':resource,'version':13,'blocked':False},**{mismatch:{'id':str(uuid4()),'version':12,'blocked':True}[mismatch]})
    with pytest.raises(ApiError if mismatch=='stale' else ContractError):submit_command(API(),journal,record,fresh=True)
    saved=journal.list()[0]
    assert saved['key']==record['key'] and saved['body']==record['body']
    assert saved['status']==('FAILED' if mismatch=='stale' else None)


def test_command_confirms_only_review_without_release(tmp_path):
    resource,tenant=str(uuid4()),str(uuid4());journal=Journal(tmp_path,'https://lab','user',tenant,Keys())
    record=prepare_command(journal,'quality_review',resource,{'version':12,'reason':'Revisión documentada','human_confirmation':'true'})
    calls=[]
    class API:
        user={'tenant_id':tenant}
        def authorized(self,*args,**kwargs):
            calls.append(args)
            return {'id':resource,'version':13,'blocked':False}
    submit_command(API(),journal,record,fresh=True)
    assert calls==[('inventario','/api/v1/resources/'+resource+'/quality-review','quality_review')]
    assert journal.list()[0]['status']=='COMPLETED'
