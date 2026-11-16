"""Comandos idempotentes con diario cifrado; cada ruta se fija aquí."""
from uuid import UUID, uuid4
from datetime import datetime
from .client import ApiError, ContractError, request_xml
from .journal import JournalError
from .institutional_catalogue import COMMANDS as CATALOGUE_COMMANDS, PATCH_OPERATIONS, validate_catalogue_result

COMMANDS={
    'resource_controls_create':('inventario','/api/v1/resources/{id}/controls','resource_controls_create.xsd',True),
    'resource_release':('inventario','/api/v1/resources/{id}/release','resource_release.xsd',True),
    'donation_create':('donantes','/api/v1/donations','donation_create.xsd',False),
    'donation_step':('donantes','/api/v1/donations/{id}/steps','donation_step.xsd',True),
    'resource_fractionate':('inventario','/api/v1/resources/{id}/components','resource_fractionate.xsd',True),
    'resource_edit':('inventario','/api/v1/resources/{id}','resource_edit.xsd',True),
    'resource_create':('inventario','/api/v1/resources','resource_create.xsd',False),
    'lab_sample_create':('compatibilidad','/api/v1/laboratory/samples','lab_sample_create.xsd',False),
    'lab_sample_receive':('compatibilidad','/api/v1/laboratory/samples/{id}/receive','lab_sample_receive.xsd',True),
    'lab_result_create':('compatibilidad','/api/v1/laboratory/results','lab_result_create.xsd',False),
    'lab_result_review':('compatibilidad','/api/v1/laboratory/results/{id}/review','lab_result_review.xsd',True),
    'evaluation_create':('compatibilidad','/api/v1/evaluations','evaluation_create.xsd',False),
    'request_create':('receptores','/api/v1/requests','request_create.xsd',False),
    'recipient_create':('receptores','/api/v1/recipients','recipient_create.xsd',False),
    'recipient_edit':('receptores','/api/v1/recipients/{id}','recipient_edit.xsd',True),
    'request_edit':('receptores','/api/v1/requests/{id}','request_edit.xsd',True),
    'request_cancel':('receptores','/api/v1/requests/{id}/cancel','request_cancel.xsd',True),
    'evaluation_review':('compatibilidad','/api/v1/evaluations/{id}/reviews','evaluation_review.xsd',True),
    'alert_ack':('alertas','/api/v1/alerts/{id}/acknowledge',None,True),
    'cold_reading_create':('inventario','/api/v1/resources/{id}/cold-readings','cold_reading_create.xsd',True),
    'export_create':('documentos','/api/v1/export-jobs','export_create.xsd',False),
    'shipment_create':('transporte','/api/v1/shipments','shipment_create.xsd',False),
    'shipment_transition':('transporte','/api/v1/shipments/{id}/transitions','shipment_transition.xsd',True),
    'shipment_scan':('transporte','/api/v1/shipments/{id}/scan','shipment_scan.xsd',True),
    'user_state':('identidad-acceso','/api/v1/users/{id}','user_state.xsd',True),
    'user_role':('identidad-acceso','/api/v1/users/{id}/role','user_role.xsd',True),
    'device_create':('identidad-acceso','/api/v1/devices','device_create.xsd',False),
    'device_revoke':('identidad-acceso','/api/v1/devices/{id}/revoke','device_revoke.xsd',True),
}
COMMANDS.update(CATALOGUE_COMMANDS)

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
    method='PATCH' if operation in ('user_state','recipient_edit','request_edit','resource_edit') or operation in PATCH_OPERATIONS else 'POST'
    record={'key':str(uuid4()),'kind':'COMMAND','target':{'operation':operation,'identifier':identifier,'service':service,'path':path,'method':method,'schema':schema},
            'body':body,'state':'PREPARED','operation_id':None,'status':None}
    journal.prepare(record)
    return record

def submit_command(client,journal,record,*,fresh=False,proof=None):
    if record.get('kind')!='COMMAND' or record.get('state') not in ('PREPARED','UNCERTAIN'): raise JournalError('No hay comando pendiente.')
    target=record['target']; operation=target['operation']; service,path,schema=command_path(operation,target['identifier'])
    method='PATCH' if operation in ('user_state','recipient_edit','request_edit','resource_edit') or operation in PATCH_OPERATIONS else 'POST'
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
    if operation in CATALOGUE_COMMANDS:
        validate_catalogue_result(operation,target['identifier'],record['body'],result,client.user['tenant_id'])
    if operation=='alert_ack' and (result.get('id')!=target['identifier'] or result.get('tenant_id')!=client.user.get('tenant_id') or result.get('status')!='ACKNOWLEDGED' or result.get('acknowledged_by')!=client.user.get('id')):
        raise ContractError('El acuse confirmado no corresponde al aviso seleccionado.')
    if operation=='resource_controls_create' and (result.get('id')!=target['identifier'] or any(result.get(key)!=record['body'].get(key) for key in ('lab_profile_id','cold_equipment_id','cold_profile_id'))):
        raise ContractError('El perfil confirmado no corresponde a la unidad seleccionada.')
    if operation=='resource_release' and (result.get('id')!=target['identifier'] or result.get('tenant_id')!=client.user.get('tenant_id') or result.get('version')!=record['body']['version']+1 or result.get('status')!='AVAILABLE'):
        raise ContractError('La liberación confirmada no corresponde a la unidad seleccionada.')
    if operation=='shipment_scan' and (result.get('shipment_id')!=target['identifier'] or result.get('resource_id')!=record['body']['scanned_resource_id'] or result.get('verified') is not True):
        raise ContractError('La verificación confirmada no corresponde a la unidad seleccionada.')
    if operation=='shipment_transition' and (result.get('id')!=target['identifier'] or result.get('version')!=record['body']['version']+1 or (record['body']['state']!='INCIDENT' and result.get('status')!=record['body']['state'])):
        raise ContractError('El paso confirmado no corresponde al traslado seleccionado.')
    if operation=='cold_reading_create':
        if result.get('resource_id')!=target['identifier'] or result.get('tenant_id')!=client.user.get('tenant_id') or result.get('author_id')!=client.user.get('id') or any(result.get(field)!=record['body'].get(field) for field in ('temperature_c','source','calibration_reference')):
            raise ContractError('La lectura confirmada no corresponde a la unidad seleccionada.')
        try:
            expected=datetime.fromisoformat(record['body']['captured_at'].replace('Z','+00:00'))
            received=datetime.fromisoformat(result['captured_at'].replace('Z','+00:00'))
            if expected.tzinfo is None or received.tzinfo is None or expected!=received: raise ValueError()
        except (KeyError,TypeError,ValueError,AttributeError) as exc:
            raise ContractError('La fecha confirmada no corresponde a la lectura.') from exc
    if operation=='export_create' and (result.get('tenant_id')!=client.user.get('tenant_id') or result.get('user_id')!=client.user.get('id') or any(result.get(field)!=record['body'][field] for field in ('report','format'))):
        raise ContractError('El reporte confirmado no corresponde a la solicitud registrada.')
    if operation=='resource_fractionate':
        from .fractionation import validate_fractionation
        validate_fractionation(client,record,result)
        journal.update(record['key'],{'operation_id':target['identifier'],'status':'COMPLETED'})
        return result
    if operation=='request_create' and any(result.get(field)!=record['body'][field] for field in ('recipient_id','component','quantity','urgency')):
        raise ContractError('La solicitud confirmada no corresponde al intento registrado.')
    if operation=='donation_create':
        if result.get('tenant_id')!=client.user.get('tenant_id') or any(result.get(field)!=record['body'][field] for field in ('donor_id','kind','component')) or result.get('status')!='COLLECTED':
            raise ContractError('La colecta confirmada no corresponde al intento registrado.')
        try:
            expected=datetime.fromisoformat(record['body']['collected_at'].replace('Z','+00:00'))
            received=datetime.fromisoformat(result['collected_at'].replace('Z','+00:00'))
            if expected.tzinfo is None or received.tzinfo is None or expected!=received: raise ValueError()
        except (KeyError,TypeError,ValueError,AttributeError) as exc:
            raise ContractError('La fecha confirmada no corresponde a la colecta.') from exc
    if operation=='donation_step' and (result.get('id')!=target['identifier'] or result.get('tenant_id')!=client.user.get('tenant_id') or result.get('version')!=record['body']['version']+1 or result.get('status')!=record['body']['state']):
        raise ContractError('El procesamiento confirmado no corresponde al intento registrado.')
    if operation=='resource_edit':
        if result.get('id')!=target['identifier'] or result.get('version')!=record['body']['version']+1:
            raise ContractError('La versión de la unidad corregida no corresponde al intento.')
        if any(result.get(field)!=record['body'].get(field) for field in ('folio','kind','component','blood_group','location_id','donation_id')):
            raise ContractError('La unidad corregida no corresponde al intento registrado.')
        for field in ('expires_at','collected_at'):
            try:
                original=record['body'].get(field); confirmed=result.get(field)
                if original is None and confirmed is None: continue
                expected=datetime.fromisoformat(original.replace('Z','+00:00'))
                received=datetime.fromisoformat(confirmed.replace('Z','+00:00'))
                if expected.tzinfo is None or received.tzinfo is None or expected!=received: raise ValueError()
            except (TypeError,ValueError,AttributeError) as exc:
                raise ContractError('La fecha confirmada no corresponde a la corrección.') from exc
    if operation=='resource_create' and any(result.get(field)!=record['body'][field] for field in ('folio','kind','component','blood_group')):
        raise ContractError('La unidad confirmada no corresponde al intento registrado.')
    if operation=='resource_create' and record['body'].get('donation_id'):
        if result.get('donation_id')!=record['body']['donation_id']:
            raise ContractError('La procedencia confirmada no corresponde al intento registrado.')
        try:
            expected=datetime.fromisoformat(record['body']['collected_at'].replace('Z','+00:00'))
            received=datetime.fromisoformat(result['collected_at'].replace('Z','+00:00'))
            if expected.tzinfo is None or received.tzinfo is None or expected!=received: raise ValueError()
        except (KeyError,TypeError,ValueError,AttributeError) as exc:
            raise ContractError('La colecta confirmada no corresponde a la donación seleccionada.') from exc
    if operation=='lab_sample_create' and any(result.get(field)!=record['body'][field] for field in ('resource_id','profile_id','identifier')):
        raise ContractError('La muestra confirmada no corresponde al intento registrado.')
    if operation=='lab_sample_receive' and (result.get('id')!=target['identifier'] or result.get('tenant_id')!=client.user.get('tenant_id') or result.get('version')!=record['body']['version']+1 or result.get('status')!=record['body']['decision']):
        raise ContractError('La recepción confirmada no corresponde a la muestra seleccionada.')
    if operation=='lab_result_create':
        from .laboratory_result import validate_result_confirmation
        validate_result_confirmation(result,record['body'],client.user)
    if operation=='lab_result_review' and (result.get('id')!=target['identifier'] or result.get('tenant_id')!=client.user.get('tenant_id') or result.get('version')!=record['body']['version'] or result.get('status')!=record['body']['decision']):
        raise ContractError('La revisión confirmada no corresponde al resultado seleccionado.')
    if operation=='lab_sample_create':
        try:
            expected=datetime.fromisoformat(record['body']['collected_at'].replace('Z','+00:00'))
            received=datetime.fromisoformat(result['collected_at'].replace('Z','+00:00'))
            if expected.tzinfo is None or received.tzinfo is None or expected!=received: raise ValueError()
        except (KeyError,TypeError,ValueError,AttributeError) as exc:
            raise ContractError('La fecha de la muestra confirmada no corresponde al intento.') from exc
    if operation=='recipient_create' and any(result.get(field)!=record['body'][field] for field in ('folio','kind','blood_group')):
        raise ContractError('El receptor confirmado no corresponde al intento registrado.')
    if operation in ('recipient_edit','request_edit','request_cancel') and result.get('id')!=target['identifier']:
        raise ContractError('El resultado no corresponde al registro solicitado.')
    if operation in ('recipient_edit','request_edit','request_cancel') and result.get('version')!=record['body']['version']+1:
        raise ContractError('La versión confirmada no corresponde a la operación.')
    if operation=='recipient_edit' and any(result.get(field)!=record['body'][field] for field in ('folio','display_name','kind','blood_group','studies','status')):
        raise ContractError('El receptor confirmado no corresponde a la corrección.')
    if operation=='request_edit' and any(result.get(field)!=record['body'][field] for field in ('component','quantity','urgency')):
        raise ContractError('La solicitud confirmada no corresponde a la corrección.')
    if operation=='request_cancel' and result.get('status')!='CANCELLED':
        raise ContractError('La solicitud no aparece cancelada.')
    if operation=='device_create' and any(result.get(field)!=record['body'][field] for field in ('id','user_id','source')):
        raise ContractError('El dispositivo confirmado no corresponde al intento registrado.')
    if operation=='device_revoke' and (result.get('id')!=target['identifier'] or result.get('active') is not False):
        raise ContractError('La revocación confirmada no corresponde al dispositivo solicitado.')
    if operation=='shipment_create':
        update_shipment_command(journal,record,result)
    else:
        journal.update(record['key'],{'operation_id':result.get('id'),'status':'COMPLETED'})
    return result


def update_shipment_command(journal, record, result):
    """Correlaciona la planificación con el intento antes de cerrar su diario."""
    try:
        identifier=result['id']
        if str(UUID(identifier))!=identifier: raise ValueError()
        if record.get('operation_id') and record['operation_id']!=identifier: raise ValueError()
        if any(result.get(field)!=record['body'][field] for field in ('reservation_id','transport_user_id')): raise ValueError()
        pending=result['inventory_pending']
        if type(pending) is not bool: raise ValueError()
        status=result['status']
        if status=='REJECTED': outcome='FAILED'
        elif pending: outcome='PENDING'
        elif status in ('PLANNED','PREPARED','COLLECTED','IN_TRANSIT','DELIVERED','ACCEPTED'): outcome='COMPLETED'
        else: outcome='CONFLICT'
    except (KeyError,TypeError,ValueError,AttributeError) as exc:
        raise ContractError('El traslado no corresponde al intento registrado.') from exc
    journal.update(record['key'],{'operation_id':identifier,'status':outcome})
    return outcome
