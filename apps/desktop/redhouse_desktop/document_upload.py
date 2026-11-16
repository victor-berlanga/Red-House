"""Carga documental durable; nunca persiste capacidades, archivos ni rutas."""
import hashlib
import os
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit
from uuid import uuid4

import requests

from .client import ApiError, ContractError, request_xml
from .download import approved_url
from .journal import JournalError

LIMIT=10*1024*1024
MIMES={'application/pdf':b'%PDF-','image/png':b'\x89PNG\r\n\x1a\n','image/jpeg':b'\xff\xd8\xff'}


def read_document(path):
    """Captura bytes en memoria para evitar cambios entre huella y transmisión."""
    try:
        with Path(path).open('rb') as stream:
            content=stream.read(LIMIT+1)
    except OSError as exc: raise JournalError('No se pudo leer el archivo elegido.') from exc
    if not 1<=len(content)<=LIMIT: raise JournalError('El archivo debe medir entre 1 byte y 10 MiB.')
    mime=next((kind for kind,signature in MIMES.items() if content.startswith(signature)),None)
    if not mime: raise JournalError('Selecciona un archivo PDF, PNG o JPEG.')
    return content,{'mime_type':mime,'size':len(content),'sha256':hashlib.sha256(content).hexdigest()}


def prepare_document(journal,subject,details,reference):
    body={'subject_kind':'RESULT','subject_id':subject,'category':'LAB_RESULT',**details,'policy_reference':reference.strip()}
    request_xml(body,'document_prepare.xsd')
    record={'key':str(uuid4()),'kind':'DOCUMENT','target':subject,'body':body,'state':'PREPARED','status':None,'operation_id':None}
    journal.prepare(record); return record


def validate_prepared(result,record,tenant):
    meta=result.get('metadata') or {}; identifier=result.get('id')
    if (meta.get('id')!=identifier or meta.get('tenant_id')!=tenant or meta.get('subject_kind')!='RESULT'
            or meta.get('subject_id')!=record['target'] or meta.get('category')!='LAB_RESULT'
            or meta.get('policy_reference')!=record['body']['policy_reference'] or meta.get('privacy')!='PRIVATE'):
        raise ContractError('El documento preparado no corresponde al resultado seleccionado.')
    if record.get('operation_id') and record['operation_id']!=identifier:
        raise ContractError('El intento preparado apunta a otro documento.')
    return identifier


def prepare_remote(context,record,proof=None):
    context.check()
    result=context.client.authorized('documentos','/api/v1/documents','document_prepare',method='POST',body=record['body'],request_schema='document_prepare.xsd',key=record['key'],proof=proof)
    identifier=validate_prepared(result,record,context.actor[1])
    if not record.get('operation_id'): context.journal.document_transition(record['key'],identifier,'assign')
    return result


def _headers_and_url(result,record,tenant,base):
    identifier=result['id']; url=result.get('upload_url'); headers=result.get('upload_headers')
    approved_url(url,base)
    if not isinstance(headers,dict) or any(not isinstance(k,str) or not isinstance(v,str) for k,v in headers.items()): raise ContractError('Las cabeceras de carga no son válidas.')
    lowered={k.lower():v for k,v in headers.items()}
    if len(lowered)!=len(headers) or lowered.get('content-type')!=record['body']['mime_type']: raise ContractError('El tipo del archivo no corresponde a la carga.')
    target=urlsplit(url)
    if target.hostname=='storage.googleapis.com':
        bucket=os.environ.get('REDHOUSE_GCS_BUCKET','')
        if unquote(target.path)!=f'/'+bucket+'/documents/'+tenant+'/'+identifier or set(lowered)!={'content-type','x-goog-if-generation-match'} or lowered['x-goog-if-generation-match']!='0':
            raise ContractError('El destino de carga no corresponde al documento.')
    elif set(lowered)!={'content-type'}:
        raise ContractError('Las cabeceras de carga no están permitidas.')
    return url,headers


def upload_bytes(context,record,prepared,content):
    if len(content)!=record['body']['size'] or hashlib.sha256(content).hexdigest()!=record['body']['sha256']:
        raise JournalError('El archivo elegido no coincide con la intención conservada.')
    context.check(); identifier=validate_prepared(prepared,record,context.actor[1]); url,headers=_headers_and_url(prepared,record,context.actor[1],context.client.base)
    context.journal.document_transition(record['key'],identifier,'start')
    context.check()
    session=requests.Session(); session.trust_env=False
    # Igual que requests.request del cliente XML, pero sin proxies ni credenciales implícitas.
    session.verify=os.environ.get('REQUESTS_CA_BUNDLE') or os.environ.get('CURL_CA_BUNDLE') or True
    try:
        try: response=session.put(url,data=content,headers=headers,timeout=(5,30),allow_redirects=False)
        except requests.RequestException as exc: raise ConnectionError('No se confirmó la transferencia. Consulta la operación antes de repetir.') from exc
        try:
            if response.status_code not in (200,201,412): raise ConnectionError('No se confirmó la transferencia. Consulta la operación antes de repetir.')
        finally: response.close()
    finally: session.close()
    context.journal.document_transition(record['key'],identifier,'uploaded')


def verify_remote(context,record,proof=None):
    context.check(); identifier=record['operation_id']
    try:
        response=context.client.authorized('documentos','/api/v1/files/'+identifier+'/verify','file_verify',method='POST',key=record['key']+'-verify',proof=proof)
    except ApiError as exc:
        if exc.status==404 and exc.code=='object_missing': context.journal.document_transition(record['key'],identifier,'missing')
        raise
    if (response.get('id')!=identifier or response.get('status')!='VERIFIED'
            or response.get('sha256')!=record['body']['sha256'] or response.get('size')!=record['body']['size']
            or response.get('mime_type')!=record['body']['mime_type']): raise ContractError('La verificación no corresponde al archivo.')
    context.check()
    metadata=context.client.authorized('documentos','/api/v1/documents/'+identifier+'/verified','document_verified')
    if (metadata.get('id')!=identifier or metadata.get('tenant_id')!=context.actor[1] or metadata.get('subject_kind')!='RESULT'
            or metadata.get('subject_id')!=record['target'] or metadata.get('category')!='LAB_RESULT' or metadata.get('analysis')!='CLEAN'
            or metadata.get('file_status')!='VERIFIED' or metadata.get('sha256')!=record['body']['sha256']
            or not metadata.get('generation') or str(metadata['generation'])!=str(response.get('generation'))):
        raise ContractError('El documento verificado no corresponde al intento.')
    context.journal.document_transition(record['key'],identifier,'verified'); return metadata
