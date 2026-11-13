"""Preparación de emisión auditada. No conecta la interfaz hasta validar contrato."""
from uuid import uuid4
from .journal import JournalError

def prepare_label(journal, resource, action, reason):
    if action not in ('EXPORT_PDF','PRINT') or len(reason.strip())<6:
        raise JournalError('Indica el destino y un motivo de al menos seis caracteres.')
    record={
        'key':str(uuid4()), 'kind':'LABEL', 'target':resource['id'],
        'body':{'version':resource['version'],'action':action,'reason':reason.strip(),'human_confirmation':'true'},
        'state':'UNCERTAIN','operation_id':None,'status':None,
    }
    journal.prepare(record)
    return record

def submit_label(client, journal, record):
    """Reutiliza exactamente el cuerpo y la clave conservados en el diario."""
    if record.get('kind')!='LABEL' or record.get('state')!='UNCERTAIN':
        raise JournalError('No hay emisión pendiente de recuperar.')
    result=client.authorized('inventario','/api/v1/resources/'+record['target']+'/label-issuances',
        'label_issue',method='POST',body=record['body'],request_schema='label_issue.xsd',key=record['key'])
    if result['resource_id']!=record['target'] or result['resource_version']!=record['body']['version'] or result['action']!=record['body']['action']:
        raise JournalError('La emisión recibida no corresponde a la solicitud.')
    journal.update(record['key'],{'operation_id':result['issuance_id'],'status':'AUTHORIZED'})
    return result
