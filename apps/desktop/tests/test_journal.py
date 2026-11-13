from cryptography.fernet import Fernet
import pytest
from redhouse_desktop.journal import Journal, JournalError

class Keys:
    def __init__(self): self.values={}
    def get(self, identifier, exists):
        if identifier not in self.values:
            if exists: raise JournalError('missing')
            self.values[identifier]=Fernet.generate_key()
        return self.values[identifier]

def record():
    return {'key':'same-idempotency-key','body':{'evaluation_id':'private-eval','resource_id':'private-resource','reason':'motivo privado'},'state':'UNCERTAIN','operation_id':None,'status':None}

def test_restart_preserves_idempotency_and_isolates_accounts(tmp_path):
    keys=Keys(); first=Journal(tmp_path,'https://lab','user-a','tenant-a',keys); first.prepare(record())
    assert b'private-resource' not in first.file.read_bytes() and b'same-idempotency-key' not in first.file.read_bytes()
    restarted=Journal(tmp_path,'https://lab','user-a','tenant-a',keys)
    assert restarted.list()==[record()]
    assert Journal(tmp_path,'https://lab','user-b','tenant-a',keys).list()==[]
    assert Journal(tmp_path,'https://lab','user-a','tenant-b',keys).list()==[]
    assert Journal(tmp_path,'https://other','user-a','tenant-a',keys).list()==[]
    with pytest.raises(JournalError): restarted.prepare(dict(record(),key='different-key'))
    restarted.update('same-idempotency-key',{'operation_id':'op-id','status':'PENDING'})
    pending=Journal(tmp_path,'https://lab','user-a','tenant-a',keys).list()[0]
    assert pending['key']=='same-idempotency-key' and pending['operation_id']=='op-id' and pending['state']=='PENDING'
    restarted.update('same-idempotency-key',{'operation_id':'op-id','status':'COMPLETED'})
    restarted.prepare(dict(record(),key='next-key'))


def test_tamper_and_lock_fail_closed(tmp_path):
    keys=Keys(); journal=Journal(tmp_path,'https://lab','user','tenant',keys); journal.prepare(record())
    journal.file.write_bytes(b'tampered')
    with pytest.raises(JournalError): journal.list()
    journal.lock.touch()
    with pytest.raises(JournalError): journal.prepare(record())


def test_label_command_survives_restart_without_changing_key(tmp_path):
    keys=Keys(); journal=Journal(tmp_path,'https://lab','user','tenant',keys)
    label={'key':'label-key','kind':'LABEL','target':'resource-id','body':{'action':'EXPORT_PDF','version':2,'reason':'Etiqueta documentada','human_confirmation':'true'},'state':'UNCERTAIN','operation_id':None,'status':None}
    journal.prepare(label)
    assert Journal(tmp_path,'https://lab','user','tenant',keys).list()==[label]
    with pytest.raises(JournalError): journal.prepare(dict(label,key='new-key'))
    journal.update('label-key',{'operation_id':'issuance-id','status':'COMPLETED'})
    assert journal.list()[0]['state']=='DONE'


def test_label_issuance_recovery_uses_original_command(tmp_path):
    from redhouse_desktop.label_issuance import prepare_label, submit_label
    keys=Keys(); journal=Journal(tmp_path,'https://lab','user','tenant',keys)
    unit={'id':'unit-id','version':2}
    original=prepare_label(journal,unit,'EXPORT_PDF','Etiqueta necesaria')
    class API:
        def authorized(self,*args,**kwargs):
            assert kwargs['key']==original['key'] and kwargs['body']==original['body']
            return {'issuance_id':'issuance-id','resource_id':'unit-id','resource_version':2,'action':'EXPORT_PDF','issued_at':'2030-01-01T00:00:00Z','reissue':False}
    restored=Journal(tmp_path,'https://lab','user','tenant',keys)
    result=submit_label(API(),restored,restored.list()[0])
    assert result['issuance_id']=='issuance-id' and restored.list()[0]['state']=='PENDING' and restored.list()[0]['status']=='AUTHORIZED'


def test_critical_command_retries_same_key_after_restart(tmp_path):
    from redhouse_desktop.durable_commands import prepare_command, submit_command
    keys=Keys(); journal=Journal(tmp_path,'https://lab','user','tenant',keys)
    body={'folio':'SYN-1234','kind':'BLOOD','component':'RBC','blood_group':'O-','expires_at':'2030-01-01T00:00:00Z'}
    record=prepare_command(journal,'resource_create',None,body); sent=[]
    class API:
        def authorized(self,*args,**kwargs):
            sent.append(kwargs['key'])
            if len(sent)==1: raise ConnectionError('respuesta perdida')
            return {'id':'00000000-0000-4000-8000-000000000001'}
    api=API()
    with pytest.raises(ConnectionError): submit_command(api,journal,record)
    restored=Journal(tmp_path,'https://lab','user','tenant',keys)
    submit_command(api,restored,restored.list()[0])
    assert sent==[record['key'],record['key']] and restored.list()[0]['state']=='DONE'
    with pytest.raises(JournalError): prepare_command(restored,'unauthorized_operation',None,{})


def test_conflict_after_lost_reply_is_not_marked_failed(tmp_path):
    from redhouse_desktop.client import ApiError
    from redhouse_desktop.durable_commands import prepare_command, submit_command
    keys=Keys(); journal=Journal(tmp_path,'https://lab','user','tenant',keys)
    body={'folio':'SYN-1234','kind':'BLOOD','component':'RBC','blood_group':'O-','expires_at':'2030-01-01T00:00:00Z'}
    record=prepare_command(journal,'resource_create',None,body)
    class API:
        def authorized(self,*args,**kwargs): raise ApiError(409,'conflict','Cambió el estado.')
    with pytest.raises(ApiError): submit_command(API(),journal,record)
    assert journal.list()[0]['status']=='CONFLICT' and journal.list()[0]['state']=='PENDING'


def test_reservation_result_must_match_saved_attempt():
    from redhouse_desktop.reservation import validate_operation
    record={'body':{'resource_id':'resource-a','evaluation_id':'evaluation-a'},'operation_id':'op-a'}
    valid={'operation_id':'op-a','status':'COMPLETED','reservation':{'resource_id':'resource-a','evaluation_id':'evaluation-a'}}
    assert validate_operation(record,valid) is valid
    with pytest.raises(JournalError): validate_operation(record,dict(valid,operation_id='op-b'))
    with pytest.raises(JournalError): validate_operation(record,dict(valid,reservation={'resource_id':'resource-b','evaluation_id':'evaluation-a'}))
    with pytest.raises(JournalError): validate_operation(record,dict(valid,reservation=None))


def test_user_state_durable_uses_patch_and_never_stores_proof(tmp_path):
    from redhouse_desktop.durable_commands import prepare_command, submit_command
    keys=Keys(); journal=Journal(tmp_path,'https://lab','admin','tenant',keys)
    identifier='00000000-0000-4000-8000-000000000001'
    record=prepare_command(journal,'user_state',identifier,{'active':False,'version':3}); calls=[]
    class API:
        def authorized(self,*args,**kwargs): calls.append(kwargs); return {'id':identifier}
    submit_command(API(),journal,record,proof='temporary-proof')
    assert calls[0]['method']=='PATCH' and calls[0]['proof']=='temporary-proof'
    assert 'temporary-proof' not in str(journal.list())


def test_challenge_survives_restart_and_reuses_original_command(tmp_path):
    from redhouse_desktop.client import ApiError
    from redhouse_desktop.durable_commands import prepare_command, submit_command
    keys=Keys(); journal=Journal(tmp_path,'https://lab','admin','tenant',keys)
    identifier='00000000-0000-4000-8000-000000000001'
    record=prepare_command(journal,'user_state',identifier,{'active':False,'version':3}); calls=[]
    class API:
        def authorized(self,*args,**kwargs):
            calls.append(kwargs)
            if len(calls)==1: raise ApiError(403,'reauthentication_required','Confirma identidad.',[{'field':'reauthentication','code':'challenge','challenge':'opaque-secret'}])
            return {'id':identifier}
    api=API()
    with pytest.raises(ApiError) as raised: submit_command(api,journal,record,fresh=True)
    assert raised.value.challenge()=='opaque-secret'
    restored=Journal(tmp_path,'https://lab','admin','tenant',keys); pending=restored.list()[0]
    assert pending==record and 'opaque-secret' not in str(pending)
    submit_command(api,restored,pending,proof='proof-secret')
    assert calls[0]['key']==calls[1]['key'] and calls[0]['body']==calls[1]['body']
    assert calls[0]['method']==calls[1]['method']=='PATCH' and 'proof-secret' not in str(restored.list())


def test_saved_destination_must_still_match_allowed_contract(tmp_path):
    from redhouse_desktop.durable_commands import prepare_command, submit_command
    journal=Journal(tmp_path,'https://lab','admin','tenant',Keys())
    record=prepare_command(journal,'user_state','00000000-0000-4000-8000-000000000001',{'active':False,'version':3})
    changed=dict(record,target=dict(record['target'],path='/api/v1/other'))
    with pytest.raises(JournalError): submit_command(object(),journal,changed)
    assert journal.list()==[record]


def test_invalid_challenge_fails_closed_without_losing_command(tmp_path):
    from redhouse_desktop.client import ApiError, ContractError
    from redhouse_desktop.durable_commands import prepare_command, submit_command
    journal=Journal(tmp_path,'https://lab','admin','tenant',Keys())
    record=prepare_command(journal,'user_state','00000000-0000-4000-8000-000000000001',{'active':False,'version':3})
    class API:
        def authorized(self,*args,**kwargs): raise ApiError(403,'reauthentication_required','Confirmación requerida.',[])
    with pytest.raises(ContractError): submit_command(API(),journal,record,fresh=True)
    assert journal.list()==[record]


def test_print_dispatch_survives_restart_without_automatic_reprint(tmp_path):
    from redhouse_desktop.label_issuance import prepare_label
    keys=Keys(); journal=Journal(tmp_path,'https://lab','user','tenant',keys)
    record=prepare_label(journal,{'id':'unit','version':2},'PRINT','Impresión documentada')
    journal.update(record['key'],{'operation_id':'issuance-id','status':'AUTHORIZED'})
    journal.print_transition(record['key'],'issuance-id','start')
    restored=Journal(tmp_path,'https://lab','user','tenant',keys)
    assert restored.list()[0]['status']=='PRINT_UNCERTAIN'
    with pytest.raises(JournalError): restored.print_transition(record['key'],'issuance-id','start')
    with pytest.raises(JournalError): restored.print_transition(record['key'],'wrong-id','review')
    with pytest.raises(JournalError): restored.prepare(dict(record,key='new-key'))
    restored.print_transition(record['key'],'issuance-id','review')
    assert restored.list()[0]['status']=='PRINT_REVIEWED' and restored.list()[0]['state']=='DONE'
    with pytest.raises(JournalError): restored.print_transition(record['key'],'issuance-id','start')
    next_record=prepare_label(restored,{'id':'unit','version':2},'PRINT','Nueva emisión documentada')
    assert next_record['key']!=record['key']


def test_request_creation_after_lost_response_reuses_saved_command(tmp_path):
    from redhouse_desktop.durable_commands import prepare_command, submit_command
    keys=Keys(); journal=Journal(tmp_path,'https://lab','medical','tenant',keys)
    body={'recipient_id':'00000000-0000-4000-8000-000000000001','component':'RBC','quantity':2,'urgency':2}
    record=prepare_command(journal,'request_create',None,body); calls=[]
    class API:
        def authorized(self,*args,**kwargs):
            calls.append(kwargs)
            if len(calls)==1: raise ConnectionError('respuesta perdida')
            return dict(body,id='00000000-0000-4000-8000-000000000002')
    with pytest.raises(ConnectionError): submit_command(API(),journal,record,fresh=True)
    restarted=Journal(tmp_path,'https://lab','medical','tenant',keys); pending=restarted.list()[0]
    api=API(); api.authorized=lambda *args,**kwargs:(calls.append(kwargs) or dict(body,id='00000000-0000-4000-8000-000000000002'))
    submit_command(api,restarted,pending)
    assert calls[0]['key']==calls[1]['key'] and calls[0]['body']==calls[1]['body']==body
    assert restarted.list()[0]['state']=='DONE'


def test_request_response_must_match_original_intent(tmp_path):
    from redhouse_desktop.client import ContractError
    from redhouse_desktop.durable_commands import prepare_command, submit_command
    journal=Journal(tmp_path,'https://lab','medical','tenant',Keys())
    body={'recipient_id':'00000000-0000-4000-8000-000000000001','component':'RBC','quantity':2,'urgency':2}
    record=prepare_command(journal,'request_create',None,body)
    class API:
        def authorized(self,*args,**kwargs): return dict(body,id='00000000-0000-4000-8000-000000000002',quantity=3)
    with pytest.raises(ContractError): submit_command(API(),journal,record,fresh=True)
    assert journal.list()[0]['state']=='PREPARED'
