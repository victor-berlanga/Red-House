"""Comprobación Qt local; no ejecuta servicios ni envía documentos."""
from types import SimpleNamespace
from uuid import uuid4
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QDialog, QFileDialog, QLineEdit, QPushButton
from redhouse_desktop.app import STYLE, Window
from redhouse_desktop.session_context import OperationContext

app = QApplication.instance() or QApplication([])
app.setStyleSheet(STYLE)


def make_window():
    window=Window()
    window.client=SimpleNamespace(user={'id':str(uuid4()),'tenant_id':str(uuid4()),'role':'MEDICAL'},session_id=str(uuid4()),access=None)
    window.journal=object()
    return window


def test_upload_dialog_visible_and_cancelled(tmp_path):
    window=make_window(); window.show(); context=OperationContext(window); calls=[]
    window.run_in_context=lambda *args,**kwargs:calls.append(args)
    def inspect():
        modal=app.activeModalWidget(); assert isinstance(modal,QDialog)
        assert modal.windowTitle()=='Adjuntar documento al resultado'
        assert any(x.text()=='Seleccionar PDF o imagen' for x in modal.findChildren(QPushButton))
        assert modal.grab().save(str(tmp_path/'documento.png'))
        modal.reject()
    QTimer.singleShot(50,inspect)
    window.document_upload_form({'id':str(uuid4()),'test_code':'HLA'},None,context)
    assert not calls
    window.close()


def test_session_change_on_accept_never_starts_command(monkeypatch):
    window=make_window(); context=OperationContext(window); calls=[]
    window.run_in_context=lambda *args,**kwargs:calls.append(args)
    monkeypatch.setattr(QFileDialog,'getOpenFileName',lambda *args:('/tmp/archivo.pdf',''))
    def fill():
        modal=app.activeModalWidget(); fields=modal.findChildren(QLineEdit)
        next(x for x in modal.findChildren(QPushButton) if x.text()=='Seleccionar PDF o imagen').click()
        next(x for x in fields if not x.isReadOnly()).setText('Informe autorizado')
        window.client.session_id=str(uuid4())
        next(x for x in modal.findChildren(QPushButton) if x.text()=='Cargar y verificar').click()
    QTimer.singleShot(50,fill)
    window.document_upload_form({'id':str(uuid4()),'test_code':'HLA'},None,context)
    assert not calls
    window.close()


def test_verification_callback_keeps_result_status_and_refreshes_pending():
    window=make_window(); context=OperationContext(window); loads=[]
    window.load=lambda:loads.append(window.mode)
    window.secure_attempt=lambda record,operation,identifier,submit,success,context:success({})
    window.mode='results'; window.document_verify({'operation_id':str(uuid4())},context)
    assert not loads and 'Documento verificado' in window.status.text()
    window.mode='pending'; window.document_verify({'operation_id':str(uuid4())},context)
    assert loads==['pending']
    window.close()


def test_loading_another_area_hides_result_actions():
    window=make_window(); window.mode='results'
    window.document_upload_button.show(); window.correct_result_button.show()
    window.mode='audit'; window.run=lambda *args,**kwargs:None
    window.load()
    assert window.document_upload_button.isHidden() and window.correct_result_button.isHidden()
    window.close()
