"""Guardas del candidato privado ante una nueva sesión de la misma cuenta."""
import base64
import json
from types import SimpleNamespace
from uuid import uuid4

import pytest
from PySide6.QtWidgets import QApplication, QCheckBox, QDialog, QLineEdit, QMessageBox
import redhouse_desktop.app as desktop

app = QApplication.instance() or QApplication([])


def token(sid=None):
    payload = base64.urlsafe_b64encode(json.dumps({'sid': sid or str(uuid4())}).encode()).decode().rstrip('=')
    return 'header.' + payload + '.signature'


def window_for(role):
    window = desktop.Window()
    window.client = SimpleNamespace(user={'id': str(uuid4()), 'tenant_id': str(uuid4()), 'role': role}, access=token(), session_id=str(uuid4()))
    window.journal = object()
    return window


def swap_session(window): window.client.access = token(); window.client.session_id = str(uuid4())


@pytest.mark.parametrize('flow', ['cold', 'device'])
def test_new_session_after_modal_never_submits(flow, monkeypatch):
    window = window_for('OPERATOR' if flow == 'cold' else 'ADMIN')
    item = {'id': str(uuid4()), 'tenant_id': window.client.user['tenant_id'], 'role': 'TRANSPORT', 'active': True, 'username': 'synthetic'}
    monkeypatch.setattr(window, 'selected', lambda: item)
    commands = []; monkeypatch.setattr(window, 'secure_command', lambda *args: commands.append(args))
    def accept(dialog):
        if flow == 'cold':
            fields = dialog.findChildren(QLineEdit)
            next(field for field in fields if field.placeholderText() == 'Ejemplo: 4.2').setText('5')
            next(field for field in fields if field.maxLength() == 200).setText('Fuente sintética')
        else:
            dialog.findChild(QLineEdit).setText('Dispositivo sintético'); dialog.findChild(QCheckBox).setChecked(True)
        swap_session(window); return QDialog.Accepted
    monkeypatch.setattr(QDialog, 'exec', accept)
    if flow == 'cold': window.create_cold_reading(item)
    else: window.create_device()
    assert not commands and 'sesión cambió' in window.status.text().lower()


def test_new_session_after_state_confirmation_never_submits(monkeypatch):
    window = window_for('ADMIN'); item = {'id': str(uuid4()), 'active': True, 'username': 'other'}
    monkeypatch.setattr(window, 'administrable_user', lambda: item)
    commands = []; monkeypatch.setattr(window, 'secure_command', lambda *args: commands.append(args))
    def accept(*_args): swap_session(window); return QMessageBox.Yes
    monkeypatch.setattr(QMessageBox, 'question', accept)
    window.change_user_state()
    assert not commands and 'sesión cambió' in window.status.text().lower()


def test_new_session_after_planning_never_submits(monkeypatch):
    window = window_for('COORDINATOR'); commands = []
    monkeypatch.setattr(window, 'secure_command', lambda *args: commands.append(args))
    def plan(*_args): swap_session(window); return {'reservation_id': str(uuid4())}
    monkeypatch.setattr(desktop, 'planning_dialog', plan)
    window.plan_shipment()
    assert not commands and 'sesión cambió' in window.status.text().lower()


def test_refresh_same_session_during_state_confirmation_submits(monkeypatch):
    window = window_for('ADMIN'); item = {'id': str(uuid4()), 'active': True, 'username': 'other', 'version': 1}
    monkeypatch.setattr(window, 'administrable_user', lambda: item)
    commands = []; monkeypatch.setattr(window, 'secure_command', lambda *args: commands.append(args))
    def accept(*_args):
        window.client.access = token(window.client.session_id)  # La renovación conserva el SID estable del cliente.
        return QMessageBox.Yes
    monkeypatch.setattr(QMessageBox, 'question', accept)
    window.change_user_state()
    assert len(commands) == 1 and commands[0][0] == 'user_state'


def test_new_session_after_handover_modal_never_scans(monkeypatch):
    window = window_for('OPERATOR'); shipment, transport, unit = (str(uuid4()) for _ in range(3))
    item={'id':shipment,'version':3,'transport_user_id':transport}
    context={'shipment_version':3,'transport_user_id':transport}
    handover={'shipment_id':shipment,'shipment_version':3,'transport_user':{'id':transport,'name':'Cuenta sintética'}}
    jobs=[]; monkeypatch.setattr(window,'run',lambda *args:jobs.append(args))
    def accept(dialog):
        fields=dialog.findChildren(QLineEdit)
        fields[0].setText(unit); fields[1].setText('Sello'); fields[2].setText('Motivo sintético')
        dialog.findChild(QCheckBox).setChecked(True); swap_session(window); return QDialog.Accepted
    monkeypatch.setattr(QDialog,'exec',accept)
    window.accept_shipment(item,context,handover)
    assert not jobs and 'sesión cambió' in window.status.text().lower()


@pytest.mark.parametrize('operation', ['shipment_scan', 'shipment_transition', 'cold_reading_create', 'export_create'])
def test_mismatched_confirmation_does_not_close_journal(operation):
    from redhouse_desktop.client import ContractError
    from redhouse_desktop.durable_commands import submit_command
    actor, tenant, identifier, resource = (str(uuid4()) for _ in range(4))
    target={'operation':operation,'identifier':None if operation=='export_create' else identifier}
    if operation=='shipment_scan':
        body={'scanned_resource_id':resource}; response={'shipment_id':str(uuid4()),'resource_id':resource,'verified':True}
    elif operation=='shipment_transition':
        body={'version':3,'state':'ACCEPTED'}; response={'id':str(uuid4()),'version':4,'status':'ACCEPTED'}
    elif operation=='cold_reading_create':
        body={'temperature_c':5.0,'captured_at':'2026-11-16T15:00:00Z','source':'sensor'}
        response={'resource_id':str(uuid4()),'tenant_id':tenant,'author_id':actor,**body}
    else:
        body={'report':'INVENTORY','format':'PDF'}; response={'tenant_id':str(uuid4()),'user_id':actor,**body}
    client=SimpleNamespace(user={'id':actor,'tenant_id':tenant},authorized=lambda *a,**k:response)
    updates=[]; journal=SimpleNamespace(update=lambda *args:updates.append(args))
    record={'kind':'COMMAND','state':'PREPARED','target':target,'body':body,'key':str(uuid4())}
    with pytest.raises(ContractError): submit_command(client,journal,record)
    assert not updates


@pytest.mark.parametrize('operation', ['shipment_scan', 'shipment_transition', 'cold_reading_create', 'export_create'])
def test_matching_confirmation_closes_original_journal(operation):
    from redhouse_desktop.durable_commands import submit_command
    actor, tenant, identifier, resource = (str(uuid4()) for _ in range(4))
    target={'operation':operation,'identifier':None if operation=='export_create' else identifier}
    if operation=='shipment_scan':
        body={'scanned_resource_id':resource}; response={'shipment_id':identifier,'resource_id':resource,'verified':True}
    elif operation=='shipment_transition':
        body={'version':3,'state':'ACCEPTED'}; response={'id':identifier,'version':4,'status':'ACCEPTED'}
    elif operation=='cold_reading_create':
        body={'temperature_c':5.0,'captured_at':'2026-11-16T15:00:00Z','source':'sensor'}
        response={'id':str(uuid4()),'resource_id':identifier,'tenant_id':tenant,'author_id':actor,**body}
    else:
        body={'report':'INVENTORY','format':'PDF'}; response={'id':str(uuid4()),'tenant_id':tenant,'user_id':actor,**body}
    client=SimpleNamespace(user={'id':actor,'tenant_id':tenant},authorized=lambda *a,**k:response)
    updates=[]; journal=SimpleNamespace(update=lambda *args:updates.append(args))
    record={'kind':'COMMAND','state':'PREPARED','target':target,'body':body,'key':str(uuid4())}
    assert submit_command(client,journal,record)==response
    assert len(updates)==1 and updates[0][1]['status']=='COMPLETED'


@pytest.mark.parametrize('change', ['new_account', 'new_sid'])
def test_late_connection_error_does_not_mark_new_session_uncertain(change, monkeypatch):
    from redhouse_desktop.session_context import OperationContext
    window=window_for('MEDICAL'); binding=OperationContext(window); jobs=[]; failures=[]
    monkeypatch.setattr(window,'run',lambda work,done,message,failure:jobs.append((work,done,failure)))
    monkeypatch.setattr(window,'failed',lambda error:failures.append(error))
    window.run_in_context(binding,lambda:None,lambda _:None,'Consulta')
    if change=='new_sid': swap_session(window)
    else:
        window.client=SimpleNamespace(user={'id':str(uuid4()),'tenant_id':str(uuid4()),'role':'MEDICAL'},access=token(),session_id=str(uuid4()))
        window.journal=object()
    jobs[0][2](ConnectionError('conexión interrumpida'))
    assert not failures and not window.uncertain


def test_evaluation_response_after_session_change_never_opens(monkeypatch):
    window=window_for('MEDICAL'); jobs=[]; shown=[]
    monkeypatch.setattr(window,'selected',lambda:{'id':str(uuid4())})
    monkeypatch.setattr(QMessageBox,'question',lambda *args:QMessageBox.Yes)
    monkeypatch.setattr(window,'run',lambda work,done,message,failure:jobs.append((work,done,failure)))
    monkeypatch.setattr(window,'evaluation_detail',lambda value:shown.append(value))
    monkeypatch.setattr(window,'secure_command',lambda op,identifier,body,done:done({'id':str(uuid4())}))
    window.evaluate_request(); assert len(jobs)==1
    swap_session(window); jobs[0][1]({'id':'anterior'})
    assert not shown
