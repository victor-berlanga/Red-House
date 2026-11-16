from types import SimpleNamespace
from uuid import uuid4

from PySide6.QtWidgets import QApplication, QDialog, QFileDialog, QLineEdit, QMessageBox

from redhouse_desktop.app import Window
from redhouse_desktop.session_context import OperationContext, SessionChanged

app = QApplication.instance() or QApplication([])


def setup():
    window = Window()
    client = SimpleNamespace(user={'id': str(uuid4()), 'tenant_id': str(uuid4()), 'role': 'OPERATOR'}, session_id=str(uuid4()), access=None)
    journal = SimpleNamespace()
    window.client = client; window.journal = journal
    jobs=[]
    window.run=lambda work, done, message, failure=None: jobs.append((work, done, failure))
    def switch():
        window.client=SimpleNamespace(user={'id':str(uuid4()),'tenant_id':client.user['tenant_id'],'role':'OPERATOR'},session_id=str(uuid4()),access=None)
        window.journal=SimpleNamespace()
    return window,client,journal,jobs,switch


def test_resume_modal_switch_never_sends(monkeypatch):
    w,client,journal,jobs,switch=setup()
    w.last_operation='op'; sent=[]; client.authorized=lambda *a,**k:sent.append(1)
    def confirm(*args): switch(); return QMessageBox.Yes
    monkeypatch.setattr(QMessageBox,'question',confirm)
    w.resume_pending([{'operation_id':'op','state':'PENDING','key':'key'}])
    assert not jobs and not sent


def test_resume_switch_before_worker_never_sends(monkeypatch):
    w,client,journal,jobs,switch=setup(); w.last_operation='op'; sent=[]
    client.authorized=lambda *a,**k:sent.append(1)
    monkeypatch.setattr(QMessageBox,'question',lambda *a:QMessageBox.Yes)
    w.resume_pending([{'operation_id':'op','state':'PENDING','key':'key'}])
    switch()
    try: jobs[0][0]()
    except SessionChanged: pass
    else: raise AssertionError('expected session change')
    assert not sent


def test_label_dialog_switch_never_prepares(monkeypatch):
    w,client,journal,jobs,switch=setup()
    def execute(dialog):
        dialog.findChild(QLineEdit).setText('Motivo suficiente'); switch(); return 1
    monkeypatch.setattr(QDialog,'exec',execute)
    w.show_label({'id':str(uuid4()),'folio':'unidad','version':1})
    assert not jobs


def test_pdf_dialog_switch_never_outputs(monkeypatch):
    w,client,journal,jobs,switch=setup()
    monkeypatch.setattr(QMessageBox,'information',lambda *a:QMessageBox.Ok)
    def save(*a): switch(); return ('/tmp/test.pdf','PDF')
    monkeypatch.setattr(QFileDialog,'getSaveFileName',save)
    w.label_authorized({'id':str(uuid4())},{'body':{'action':'EXPORT_PDF'},'key':'key'},'issuance')
    assert not jobs


def test_shipment_detail_response_after_switch_is_not_shown():
    w,client,journal,jobs,switch=setup(); w.mode='shipments'; w.selected=lambda:{'id':'shipment'}
    seen=[]; client.authorized=lambda *a,**k:{'id':'shipment'}
    w.shipment_detail=lambda *a:seen.append(a)
    w.open_selected(); work,done,_=jobs.pop(); result=work(); switch(); done(result)
    assert not seen


def test_label_recovery_modal_switch_never_resends(monkeypatch):
    w,client,journal,jobs,switch=setup(); sent=[]
    client.authorized=lambda *a,**k:sent.append(1)
    def confirm(*a): switch(); return QMessageBox.Yes
    monkeypatch.setattr(QMessageBox,'question',confirm)
    w.recover_operation([{'kind':'LABEL','state':'UNCERTAIN','status':'PENDING','key':'key'}],OperationContext(w))
    assert not jobs and not sent


def test_print_already_dispatched_records_old_journal_without_new_callback(monkeypatch):
    import redhouse_desktop.app as module
    w,client,journal,jobs,switch=setup(); transitions=[]; shown=[]
    journal.print_transition=lambda key,issuance,state:transitions.append(state)
    monkeypatch.setattr(QMessageBox,'information',lambda *a:QMessageBox.Ok)
    monkeypatch.setattr(module,'QPrinter',lambda *a:object())
    module.QPrinter.HighResolution=0
    monkeypatch.setattr(module,'QPrintDialog',lambda *a:SimpleNamespace(exec=lambda:QDialog.Accepted))
    monkeypatch.setattr(module,'draw_label',lambda *a:switch())
    w.status.setText('espera')
    w.label_authorized({'id':str(uuid4())},{'body':{'action':'PRINT'},'key':'key'},'issuance')
    work,done,_=jobs.pop(); result=work(); done(result)
    assert transitions==['start','sent'] and w.status.text()=='espera' and not shown


def test_resume_confirmed_after_switch_updates_original_journal(monkeypatch):
    import redhouse_desktop.app as module
    w,client,journal,jobs,switch=setup(); w.last_operation='op'; updates=[]; shown=[]
    journal.update=lambda key,result:updates.append((key,result))
    def send(*a,**k): switch(); return {'status':'COMPLETED'}
    client.authorized=send
    monkeypatch.setattr(module,'validate_operation',lambda *a:None)
    monkeypatch.setattr(QMessageBox,'question',lambda *a:QMessageBox.Yes)
    w.reservation_result=lambda result:shown.append(result)
    w.resume_pending([{'operation_id':'op','state':'PENDING','key':'key'}])
    work,done,_=jobs.pop(); result=work(); done(result)
    assert updates==[('key',{'status':'COMPLETED'})] and not shown


def test_same_client_invalidated_before_success_clears_view():
    w,client,journal,jobs,switch=setup(); w.stack.setCurrentIndex(1); w.rows=[{'id':'old'}]; w.table.setRowCount(1)
    w.run_in_context(OperationContext(w),lambda:'response',lambda _:None,'consulta')
    _,done,_=jobs.pop(); client.user=None; client.access=None; done('response')
    assert w.client is None and w.journal is None and not w.rows and w.table.rowCount()==0
