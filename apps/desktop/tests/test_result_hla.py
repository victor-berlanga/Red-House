"""Contratos y formularios HLA sintéticos, sin red ni inferencias clínicas."""
from copy import deepcopy
import os
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest
from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtWidgets import QApplication, QCheckBox, QComboBox, QDateTimeEdit, QDialog, QLineEdit, QPushButton, QTableWidget, QScrollArea

from redhouse_desktop.client import ContractError, request_xml
from redhouse_desktop.laboratory_result import result_dialog, validate_result_confirmation, verified_document

app=QApplication.instance() or QApplication([])
if os.environ.get('HLA_PRODUCT_STYLE')=='1':
    from redhouse_desktop.app import STYLE
    app.setStyleSheet(STYLE)


def body_hla():
    return {'sample_id':str(uuid4()),'test_code':'HLA','result_state':'CORRECTED','method':'Técnica sintética','laboratory':'Laboratorio sintético','reference':'Informe sintético','measured_at':'2026-11-16T12:00:00Z','issued_at':'2026-11-16T12:01:00Z','supersedes':str(uuid4()),'document_id':str(uuid4()),'hla':{'nomenclature':'HLA-colon-2010','nomenclature_version':'2010','resolution':'Dos campos','loci':[{'locus':'A','alleles':['A*01:01'],'groups':[],'ambiguous':False,'partial':False}]}}


def test_hla_and_pending_requests_validate_xsd():
    body=body_hla(); assert b'<supersedes>' in request_xml(body,'lab_result_create.xsd')
    pending={k:v for k,v in body.items() if k not in ('hla','issued_at','supersedes','document_id')}; pending['result_state']='PENDING'
    payload=request_xml(pending,'lab_result_create.xsd'); assert b'<hla>' not in payload and b'<value>' not in payload


@pytest.mark.parametrize('field', ['document_id','supersedes','result_state','sample_id','test_code'])
def test_foreign_confirmation_rejected(field):
    body=body_hla(); user={'id':str(uuid4()),'tenant_id':str(uuid4())}; response={**deepcopy(body),'tenant_id':user['tenant_id'],'author_id':user['id'],'status':'CAPTURED'}
    validate_result_confirmation(response,body,user)
    response[field]='PENDING' if field=='result_state' else str(uuid4())
    with pytest.raises(ContractError): validate_result_confirmation(response,body,user)


def test_unverified_or_foreign_document_rejected():
    prior={'id':str(uuid4())}; tenant=str(uuid4()); value={'tenant_id':tenant,'subject_kind':'RESULT','subject_id':prior['id'],'analysis':'CLEAN','file_status':'VERIFIED','generation':'1','sha256':'a'*64}
    assert verified_document(value,prior,tenant)==value
    for field,foreign in [('tenant_id',str(uuid4())),('subject_id',str(uuid4())),('file_status','PENDING'),('analysis','INFECTED'),('sha256','bad')]:
        invalid=dict(value); invalid[field]=foreign
        with pytest.raises(ContractError): verified_document(invalid,prior,tenant)


class Signals(QObject):
    done=Signal(object); failed=Signal(object)


class Worker:
    def __init__(self,work): self.work=work; self.signals=Signals()


class Pool:
    def start(self,worker):
        try: worker.signals.done.emit(worker.work())
        except Exception as error: worker.signals.failed.emit(error)


def window():
    w=QDialog(); w.client=SimpleNamespace(user={'id':str(uuid4()),'tenant_id':str(uuid4()),'role':'MEDICAL'},session_id=str(uuid4()),authorized=lambda *a,**k:{'catalogues':[]})
    w.journal=object(); w.pool=Pool(); return w


def test_pending_clears_hidden_value_and_hla():
    w=window(); sample={'id':str(uuid4()),'identifier':'MUESTRA'}
    def fill():
        d=app.activeModalWidget(); d.findChild(QLineEdit,'result_code').setText('HLA')
        state=d.findChild(QComboBox,'result_state'); state.setCurrentIndex(state.findData('REPORTED'))
        d.findChild(QLineEdit,'result_value').setText('Dato previo'); d.findChild(QCheckBox,'use_hla').setChecked(True)
        state.setCurrentIndex(state.findData('PENDING'))
        for field in ('method','laboratory','reference'): d.findChild(QLineEdit,'result_'+field).setText('Dato sintético')
        d.findChild(QCheckBox,'confirm_measured').setChecked(True)
        if os.environ.get('HLA_CAPTURE_DIR'): d.grab().save(str(Path(os.environ['HLA_CAPTURE_DIR'])/'pendiente.png'))
        d.accept()
    QTimer.singleShot(0,fill); result=result_dialog(w,sample,None,Worker); body,_=result
    assert body['result_state']=='PENDING' and 'value' not in body and 'hla' not in body


def test_changed_sid_prevents_submission():
    w=window(); sample={'id':str(uuid4()),'identifier':'MUESTRA'}
    def change():
        d=app.activeModalWidget(); w.client.session_id=str(uuid4()); d.accept()
    QTimer.singleShot(0,change); assert result_dialog(w,sample,None,Worker) is None


def test_correction_records_hla_dates_document_and_fixed_predecessor(monkeypatch):
    import redhouse_desktop.laboratory_result as module
    w=window(); sample={'id':str(uuid4()),'identifier':'MUESTRA'}
    prior={'id':str(uuid4()),'sample_id':sample['id'],'test_code':'HLA','version':1}
    doc={'id':str(uuid4()),'tenant_id':w.client.user['tenant_id'],'subject_kind':'RESULT','subject_id':prior['id'],'analysis':'CLEAN','file_status':'VERIFIED','generation':'1','sha256':'a'*64,'category':'INFORME'}
    monkeypatch.setattr(module,'document_selector',lambda *args:verified_document(doc,prior,w.client.user['tenant_id']))
    def fill():
        d=app.activeModalWidget(); state=d.findChild(QComboBox,'result_state'); state.setCurrentIndex(state.findData('CORRECTED'))
        for field in ('method','laboratory','reference'): d.findChild(QLineEdit,'result_'+field).setText('Dato sintético')
        measured=d.findChild(QDateTimeEdit,'measured_time'); measured.setDateTime(measured.dateTime().addSecs(-10)); d.findChild(QCheckBox,'confirm_measured').setChecked(True)
        d.findChild(QCheckBox,'use_issued').setChecked(True); d.findChild(QCheckBox,'confirm_issued').setChecked(True)
        d.findChild(QCheckBox,'use_hla').setChecked(True); syntax=d.findChild(QComboBox,'hla_syntax'); syntax.setCurrentIndex(syntax.findData('2010'))
        d.findChild(QLineEdit,'hla_resolution').setText('Dos campos')
        next(b for b in d.findChildren(QPushButton) if b.text()=='Añadir locus').click()
        table=d.findChild(QTableWidget,'hla_loci'); table.item(0,0).setText('A'); table.item(0,1).setText('A*01:01')
        next(b for b in d.findChildren(QPushButton) if b.text()=='Seleccionar documento verificado').click()
        if os.environ.get('HLA_CAPTURE_DIR'):
            d.grab().save(str(Path(os.environ['HLA_CAPTURE_DIR'])/'correccion.png'))
            app.processEvents(); bar=d.findChild(QScrollArea).verticalScrollBar(); bar.setValue(bar.maximum()); app.processEvents(); bar.setValue(bar.maximum()); app.processEvents()
            d.grab().save(str(Path(os.environ['HLA_CAPTURE_DIR'])/'correccion-baja.png'))
        d.accept()
    QTimer.singleShot(0,fill); result=result_dialog(w,sample,prior,Worker); body,selected=result
    assert body['supersedes']==prior['id'] and body['document_id']==doc['id'] and selected==doc
    assert body['issued_at'].endswith('Z') and body['measured_at'].endswith('Z') and body['hla']['loci'][0]['alleles']==['A*01:01']
    request_xml(body,'lab_result_create.xsd')


def test_412_preserves_draft_without_second_command(monkeypatch):
    import redhouse_desktop.app as desktop
    import redhouse_desktop.laboratory_result as module
    from redhouse_desktop.client import ApiError
    w=desktop.Window(); w.client=SimpleNamespace(user={'id':str(uuid4()),'tenant_id':str(uuid4()),'role':'MEDICAL'},session_id=str(uuid4()),access=None); w.journal=object()
    prior={'id':str(uuid4()),'version':1}; sample={'id':str(uuid4())}; body=body_hla(); draft=(body,None); dialogs=[]; commands=[]
    def show(_window,_sample,_prior,_worker,**kwargs):
        dialogs.append(kwargs)
        return draft if len(dialogs)==1 else None
    monkeypatch.setattr(module,'result_dialog',show)
    def send(operation,identifier,payload,**kwargs):
        commands.append((operation,identifier,payload)); kwargs['failure_callback'](ApiError(412,'stale_version','cambió'),'submit')
    monkeypatch.setattr(w,'secure_command',send)
    w.edit_laboratory_result(sample,prior,desktop.OperationContext(w))
    assert len(commands)==1 and dialogs[1]['locked'] is True and dialogs[1]['draft']==draft
    w.close()


@pytest.mark.parametrize('error_code, status, editable', [('validation',422,True),('stale_version',412,False),('unexpected',422,False)])
def test_actual_secure_command_reopens_draft_without_automatic_retry(tmp_path,monkeypatch,error_code,status,editable):
    from cryptography.fernet import Fernet
    from redhouse_desktop.app import Window
    from redhouse_desktop.client import ApiError
    from redhouse_desktop.journal import Journal
    from redhouse_desktop.session_context import OperationContext
    import redhouse_desktop.laboratory_result as module
    class Keys:
        def __init__(self): self.key=Fernet.generate_key()
        def get(self,*_): return self.key
    user={'id':str(uuid4()),'tenant_id':str(uuid4()),'role':'MEDICAL'}; sent=[]
    def reject(*_args,**kwargs): sent.append(kwargs['key']); raise ApiError(status,error_code,'rechazo')
    w=Window(); w.client=SimpleNamespace(user=user,session_id=str(uuid4()),access=None,authorized=reject); w.journal=Journal(tmp_path,'https://lab',user['id'],user['tenant_id'],Keys())
    jobs=[]; w.run=lambda work,done,label,failure=None:jobs.append((work,done,failure))
    body=body_hla(); sample={'id':body['sample_id']}; prior={'id':body['supersedes'],'version':1}; dialogs=[]
    def show(*_args,**kwargs): dialogs.append(kwargs); return (body,None) if len(dialogs)==1 else None
    monkeypatch.setattr(module,'result_dialog',show)
    def fire():
        work,done,failure=jobs.pop(0)
        try: value=work()
        except Exception as error: failure(error)
        else: done(value)
    w.edit_laboratory_result(sample,prior,OperationContext(w)); fire(); fire()
    assert len(sent)==1 and not jobs and len(dialogs)==2
    assert dialogs[1]['locked'] is (not editable) and dialogs[1]['draft'][0]['supersedes']==prior['id']
    assert w.journal.list()[0]['status']=='FAILED'
    w.close()


@pytest.mark.parametrize('change_sid', [False,True])
def test_actual_reauth_cancel_or_changed_session_never_resends(tmp_path,monkeypatch,change_sid):
    from cryptography.fernet import Fernet
    from redhouse_desktop.app import Window
    from redhouse_desktop.client import ApiError
    from redhouse_desktop.journal import Journal
    from redhouse_desktop.session_context import OperationContext
    import redhouse_desktop.laboratory_result as module
    class Keys:
        def __init__(self): self.key=Fernet.generate_key()
        def get(self,*_): return self.key
    user={'id':str(uuid4()),'tenant_id':str(uuid4()),'role':'MEDICAL'}; sent=[]
    def challenge(*_args,**kwargs):
        sent.append(kwargs['key']); raise ApiError(403,'reauthentication_required','confirmación',[{'field':'reauthentication','code':'challenge','challenge':'x'*60}])
    w=Window(); w.client=SimpleNamespace(user=user,session_id=str(uuid4()),access=None,authorized=challenge); w.journal=Journal(tmp_path,'https://lab',user['id'],user['tenant_id'],Keys())
    jobs=[]; w.run=lambda work,done,label,failure=None:jobs.append((work,done,failure))
    body=body_hla(); dialogs=[]
    monkeypatch.setattr(module,'result_dialog',lambda *a,**k:(dialogs.append(k) or ((body,None) if len(dialogs)==1 else None)))
    def cancel(_dialog):
        if change_sid: w.client.session_id=str(uuid4())
        return QDialog.Rejected
    monkeypatch.setattr(QDialog,'exec',cancel)
    def fire():
        work,done,failure=jobs.pop(0)
        try: value=work()
        except Exception as error: failure(error)
        else: done(value)
    w.edit_laboratory_result({'id':body['sample_id']},{'id':body['supersedes'],'version':1},OperationContext(w)); fire(); fire()
    assert len(sent)==1 and not jobs and w.journal.list()[0]['state']=='PREPARED'
    assert len(dialogs)==(1 if change_sid else 2)
    if not change_sid: assert dialogs[1]['locked'] is True
    w.close()


def test_normalized_hla_defaults_and_equivalent_utc_in_response():
    body=body_hla(); user={'id':str(uuid4()),'tenant_id':str(uuid4())}
    response={**deepcopy(body),'tenant_id':user['tenant_id'],'author_id':user['id'],'status':'CAPTURED'}
    response['issued_at']='2026-11-16T12:01:00+00:00'; response['hla']['catalogue_version']=None
    validate_result_confirmation(response,body,user)


def test_locked_draft_is_read_only_and_close_remains_available():
    w=window(); sample={'id':str(uuid4()),'identifier':'MUESTRA'}; body=body_hla(); sample['id']=body['sample_id']; prior={'id':body['supersedes'],'test_code':'HLA','version':1}
    def inspect():
        d=app.activeModalWidget(); assert not d.findChild(QLineEdit,'result_method').isEnabled()
        assert not next(b for b in d.findChildren(QPushButton) if b.text()=='Guardar resultado').isEnabled()
        assert next(b for b in d.findChildren(QPushButton) if b.text()=='Cancelar').isEnabled()
        if os.environ.get('HLA_CAPTURE_DIR'): d.grab().save(str(Path(os.environ['HLA_CAPTURE_DIR'])/'revision-bloqueada.png'))
        d.reject()
    QTimer.singleShot(0,inspect); assert result_dialog(w,sample,prior,Worker,draft=(body,None),locked=True) is None
