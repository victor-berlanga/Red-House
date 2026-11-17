from copy import deepcopy
from types import SimpleNamespace
from uuid import uuid4

import pytest
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QCheckBox, QDialog, QLineEdit, QPushButton, QWidget

from redhouse_desktop.client import ContractError
from redhouse_desktop.session_context import SessionChanged
from redhouse_desktop.resource_destination import destination_context, destination_dialog, validate_destination_result


@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])


def payload():
    actor={'id':str(uuid4()),'tenant_id':str(uuid4()),'role':'MEDICAL'}
    resource={'id':str(uuid4()),'tenant_id':str(uuid4()),'current_institution_id':actor['tenant_id'],
              'folio':'SYN-DESTINO','component':'KIDNEY','blood_group':'O+','kind':'ORGAN','version':8,'status':'WITHDRAWN'}
    prior={'id':str(uuid4()),'resource_id':resource['id'],'tenant_id':actor['tenant_id'],'version':2,
           'destination':'DISCARDED','reference':'Referencia sintética previa','occurred_at':'2026-11-16T15:00:00.123456+00:00'}
    return actor,resource,prior


def test_history_uses_current_institution_and_reads_last_page():
    actor,resource,prior=payload();early=deepcopy(prior);early.update(id=str(uuid4()),version=1)
    calls=[]
    def authorized(service,path,operation,**kwargs):
        calls.append((operation,kwargs))
        if operation=='resource_detail':return resource
        page=kwargs['params']['page'];return {'page':page,'total':2,'items':[early if page==1 else prior]}
    binding=SimpleNamespace(actor=tuple(actor.values()),client=SimpleNamespace(authorized=authorized),check=lambda:None)
    row,latest=destination_context(binding,resource['id'])
    assert row['tenant_id']!=actor['tenant_id'] and row['current_institution_id']==actor['tenant_id']
    assert latest['id']==prior['id'] and len(calls)==3


def test_history_stops_when_session_changes():
    actor,resource,_=payload();state={'checks':0}
    def check():
        state['checks']+=1
        if state['checks']==2:raise SessionChanged()
    binding=SimpleNamespace(actor=tuple(actor.values()),client=SimpleNamespace(authorized=lambda *a,**k:resource),check=check)
    with pytest.raises(SessionChanged):destination_context(binding,resource['id'])


def test_history_rejects_partial_or_foreign_results():
    actor,resource,prior=payload()
    for result in ({'page':1,'total':2,'items':[]}, {'page':1,'total':1,'items':[dict(prior,tenant_id=str(uuid4()))]}):
        binding=SimpleNamespace(actor=tuple(actor.values()),client=SimpleNamespace(authorized=lambda s,p,o,**k:resource if o=='resource_detail' else result),check=lambda:None)
        with pytest.raises(ContractError):destination_context(binding,resource['id'])


def test_response_matches_subject_author_dates_and_antecedent():
    actor,resource,prior=payload();body={'destination':'DISCARDED','reference':'Referencia corregida','reason':'Motivo documentado',
        'supersedes':prior['id'],'occurred_at':prior['occurred_at']}
    record={'target':{'identifier':resource['id']},'body':body}
    result=dict(body,id=str(uuid4()),resource_id=resource['id'],tenant_id=actor['tenant_id'],author_id=actor['id'],version=3)
    client=SimpleNamespace(user=actor);validate_destination_result(client,record,result)
    for change in ({'author_id':str(uuid4())},{'tenant_id':str(uuid4())},{'resource_id':str(uuid4())},{'supersedes':None},
                   {'occurred_at':'2026-11-16T15:00:00'},{'reference':'Otra referencia'},{'version':1}):
        with pytest.raises(ContractError):validate_destination_result(client,record,dict(result,**change))


def test_documentary_correction_preserves_precise_time_and_requires_confirmation(app):
    actor,resource,prior=payload();window=QWidget();binding=SimpleNamespace(current=lambda:True)
    seen={}
    def edit():
        dialog=QApplication.activeModalWidget();assert isinstance(dialog,QDialog)
        save=dialog.findChild(QPushButton,'primary');save.click()
        seen['blocked_without_confirmation']=dialog.isVisible()
        dialog.findChild(QLineEdit,'reference').setText('Referencia corregida')
        dialog.findChild(QLineEdit,'reason').setText('Corrección documental sintética')
        dialog.findChild(QCheckBox,'confirm_time').setChecked(True)
        dialog.findChild(QCheckBox,'confirm_destination').setChecked(True)
        save.click()
    QTimer.singleShot(0,edit);body=destination_dialog(window,binding,resource,prior)
    assert seen['blocked_without_confirmation'] and body['occurred_at']==prior['occurred_at']
    assert body['supersedes']==prior['id'] and body['version']==resource['version']
    assert body['destination']=='DISCARDED' and body['human_confirmation']=='true'
    window.close()


def test_modal_rejects_changed_identity_before_sending(app):
    _,resource,prior=payload();state={'current':True};window=QWidget();binding=SimpleNamespace(current=lambda:state['current'])
    def switch():
        dialog=QApplication.activeModalWidget();state['current']=False
        dialog.findChild(QPushButton,'primary').click()
        assert not dialog.findChild(QPushButton,'primary').isEnabled()
        dialog.reject()
    QTimer.singleShot(0,switch);assert destination_dialog(window,binding,resource,prior) is None
    window.close()
