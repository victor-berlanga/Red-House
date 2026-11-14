"""Alta recuperable sin persistir contraseñas ni derivados."""
from uuid import UUID, uuid4

from .client import ApiError, ContractError, request_xml
from .journal import JournalError


def prepare_user(journal, user, username, role, password):
    if user.get('role')!='ADMIN' or not user.get('tenant_id'):
        raise JournalError('Solo administración puede registrar cuentas de su institución.')
    body={'username':username,'tenant_id':user['tenant_id'],'role':role}
    request_xml(dict(body,password=password),'user_create.xsd')
    record={'key':str(uuid4()),'kind':'USER_CREATE','target':'user_create','body':body,
            'state':'PREPARED','operation_id':None,'status':None}
    journal.prepare(record)
    return record


def _check_record(record,client):
    if record.get('kind')!='USER_CREATE' or record.get('target')!='user_create' or record.get('state') not in ('PREPARED','UNCERTAIN'):
        raise JournalError('El alta pendiente requiere revisión.')
    body=record.get('body')
    if not isinstance(body,dict) or set(body)!={'username','role','tenant_id'}:
        raise JournalError('El alta pendiente no tiene un formato válido.')
    if not client.user or client.user.get('role')!='ADMIN' or client.user.get('tenant_id')!=body['tenant_id']:
        raise JournalError('El alta pertenece a otra institución o requiere administración.')
    return body


def _complete(journal,record,result):
    body=record['body']
    if not isinstance(result,dict) or result.get('username')!=body['username'] or result.get('role')!=body['role'] or not result.get('id'):
        raise ContractError('El alta confirmada no corresponde al intento registrado.')
    try:
        if str(UUID(result['id']))!=result['id'] or ('tenant_id' in result and result['tenant_id']!=body['tenant_id']): raise ValueError()
    except (ValueError,TypeError,AttributeError) as exc:
        raise ContractError('El alta confirmada no corresponde al ámbito registrado.') from exc
    journal.update(record['key'],{'operation_id':result['id'],'status':'COMPLETED'})
    return result


def lookup_user(client,journal,record):
    _check_record(record,client)
    try:
        result=client.authorized('identidad-acceso','/api/v1/user-creation-receipt','user_creation_receipt',key=record['key'],fresh_identity=True)
    except ApiError as exc:
        if exc.status==404: return None
        raise
    return _complete(journal,record,result)


def submit_user(client,journal,record,password,proof=None,*,fresh=False):
    body=dict(_check_record(record,client),password=password)
    request_xml(body,'user_create.xsd')
    try:
        result=client.authorized('identidad-acceso','/api/v1/users','user_create',method='POST',body=body,request_schema='user_create.xsd',key=record['key'],fresh_identity=True,proof=proof)
    except ApiError as exc:
        if fresh and (exc.status,exc.code) in ((409,'conflict'),(422,'validation')):
            journal.update(record['key'],{'operation_id':None,'status':'FAILED'})
        raise
    return _complete(journal,record,result)
