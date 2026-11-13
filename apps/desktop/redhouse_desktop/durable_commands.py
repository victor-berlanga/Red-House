"""Comandos idempotentes con diario cifrado; cada ruta se fija aquí."""
from uuid import UUID, uuid4
from .client import ApiError, ContractError, request_xml
from .journal import JournalError

COMMANDS={
    'resource_create':('inventario','/api/v1/resources','resource_create.xsd',False),
    'lab_sample_receive':('compatibilidad','/api/v1/laboratory/samples/{id}/receive','lab_sample_receive.xsd',True),
    'lab_result_create':('compatibilidad','/api/v1/laboratory/results','lab_result_create.xsd',False),
    'lab_result_review':('compatibilidad','/api/v1/laboratory/results/{id}/review','lab_result_review.xsd',True),
    'evaluation_create':('compatibilidad','/api/v1/evaluations','evaluation_create.xsd',False),
    'request_create':('receptores','/api/v1/requests','request_create.xsd',False),
    'evaluation_review':('compatibilidad','/api/v1/evaluations/{id}/reviews','evaluation_review.xsd',True),
    'alert_ack':('alertas','/api/v1/alerts/{id}/acknowledge',None,True),
    'cold_reading_create':('inventario','/api/v1/resources/{id}/cold-readings','cold_reading_create.xsd',True),
    'export_create':('documentos','/api/v1/export-jobs','export_create.xsd',False),
    'shipment_transition':('transporte','/api/v1/shipments/{id}/transitions','shipment_transition.xsd',True),
    'shipment_scan':('transporte','/api/v1/shipments/{id}/scan','shipment_scan.xsd',True),
    'user_state':('identidad-acceso','/api/v1/users/{id}','user_state.xsd',True),
    'user_role':('identidad-acceso','/api/v1/users/{id}/role','user_role.xsd',True),
    'device_create':('identidad-acceso','/api/v1/devices','device_create.xsd',False),
    'device_revoke':('identidad-acceso','/api/v1/devices/{id}/revoke','device_revoke.xsd',True),
}

def command_path(operation,identifier):
    if operation not in COMMANDS: raise JournalError('Operación no reconocida.')
    service,path,schema,requires_id=COMMANDS[operation]
    if requires_id:
        try:
            if str(UUID(identifier))!=identifier: raise ValueError()
        except (ValueError,TypeError,AttributeError) as exc: raise JournalError('Identificador inválido.') from exc
        path=path.replace('{id}',identifier)
    elif identifier is not None: raise JournalError('Identificador inesperado.')
    return service,path,schema

def prepare_command(journal, operation, identifier, body):
    service,path,schema=command_path(operation,identifier)
    if schema: request_xml(body,schema)
    elif body is not None: raise JournalError('Esta operación no admite cuerpo.')
    method='PATCH' if operation=='user_state' else 'POST'
    record={'key':str(uuid4()),'kind':'COMMAND','target':{'operation':operation,'identifier':identifier,'service':service,'path':path,'method':method,'schema':schema},
            'body':body,'state':'PREPARED','operation_id':None,'status':None}
    journal.prepare(record)
    return record

def submit_command(client,journal,record,*,fresh=False,proof=None):
    if record.get('kind')!='COMMAND' or record.get('state') not in ('PREPARED','UNCERTAIN'): raise JournalError('No hay comando pendiente.')
    target=record['target']; operation=target['operation']; service,path,schema=command_path(operation,target['identifier'])
    method='PATCH' if operation=='user_state' else 'POST'
    if 'path' in target and any(target.get(k)!=v for k,v in {'service':service,'path':path,'method':method,'schema':schema}.items()): raise JournalError('El contrato de la operación pendiente cambió; solicita revisión.')
    try:
        result=client.authorized(service,path,operation,method=method,body=record['body'],request_schema=schema,key=record['key'],proof=proof)
    except ApiError as exc:
        if exc.status==403 and exc.code=='reauthentication_required':
            exc.challenge()
            raise
        if exc.status in (400,403,404,409,412,413,415,422):
            journal.update(record['key'],{'operation_id':None,'status':'FAILED' if fresh else 'CONFLICT'})
        raise
    if operation=='request_create' and any(result.get(field)!=record['body'][field] for field in ('recipient_id','component','quantity','urgency')):
        raise ContractError('La solicitud confirmada no corresponde al intento registrado.')
    if operation=='resource_create' and any(result.get(field)!=record['body'][field] for field in ('folio','kind','component','blood_group')):
        raise ContractError('La unidad confirmada no corresponde al intento registrado.')
    if operation=='device_create' and any(result.get(field)!=record['body'][field] for field in ('id','user_id','source')):
        raise ContractError('El dispositivo confirmado no corresponde al intento registrado.')
    if operation=='device_revoke' and (result.get('id')!=target['identifier'] or result.get('active') is not False):
        raise ContractError('La revocación confirmada no corresponde al dispositivo solicitado.')
    journal.update(record['key'],{'operation_id':result.get('id'),'status':'COMPLETED'})
    return result
