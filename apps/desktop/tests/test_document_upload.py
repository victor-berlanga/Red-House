"""Carga documental sintética: origen, diario y recuperación sin credenciales."""
from types import SimpleNamespace
from uuid import uuid4
import hashlib

import pytest
from cryptography.fernet import Fernet
from redhouse_desktop.client import ApiError, ContractError
from redhouse_desktop.document_upload import prepare_document, prepare_remote, read_document, upload_bytes, verify_remote
from redhouse_desktop.journal import Journal, JournalError
from redhouse_desktop.download import DownloadError
from redhouse_desktop.session_context import OperationContext, SessionChanged


class Keys:
    def __init__(self): self.key=Fernet.generate_key()
    def get(self,*_): return self.key


def setup(tmp_path):
    tenant,user,subject=(str(uuid4()) for _ in range(3)); keys=Keys(); base='https://lab.example'
    journal=Journal(tmp_path,base,user,tenant,keys); content=b'%PDF-synthetic-document'; details={'size':len(content),'mime_type':'application/pdf','sha256':hashlib.sha256(content).hexdigest()}
    record=prepare_document(journal,subject,details,'Referencia sintética'); client=SimpleNamespace(user={'id':user,'tenant_id':tenant,'role':'MEDICAL'},session_id=str(uuid4()),base=base)
    window=SimpleNamespace(client=client,journal=journal); context=OperationContext(window); doc_id=str(uuid4())
    metadata={'id':doc_id,'tenant_id':tenant,'subject_kind':'RESULT','subject_id':subject,'category':'LAB_RESULT','policy_reference':'Referencia sintética','privacy':'PRIVATE'}
    prepared={'id':doc_id,'metadata':metadata,'upload_url':'https://lab.example/storage/v1/objects/abcd','upload_headers':{'Content-Type':'application/pdf'}}
    return journal,record,client,window,context,content,prepared,keys


def test_journal_rejects_secrets_and_extra_fields(tmp_path):
    journal,record,*_=setup(tmp_path); invalid=dict(record,key=str(uuid4()),body=dict(record['body'],token='secret'))
    with pytest.raises(JournalError): journal.prepare(invalid)


def test_read_document_checks_magic_size_and_hash(tmp_path):
    path=tmp_path/'file'; path.write_bytes(b'%PDF-synthetic'); content,meta=read_document(path)
    assert meta['sha256']==hashlib.sha256(content).hexdigest()
    path.write_bytes(b'not a document')
    with pytest.raises(JournalError): read_document(path)


def test_prepare_response_lost_reuses_key_and_never_stores_url(tmp_path):
    journal,record,client,window,context,content,prepared,keys=setup(tmp_path); calls=[]
    def server(*a,**kw):
        calls.append(kw['key'])
        if len(calls)==1: raise ConnectionError('lost')
        return prepared
    client.authorized=server
    with pytest.raises(ConnectionError): context.submit(record,lambda:prepare_remote(context,record))
    pending=journal.list()[0]; assert pending['state']=='PREPARED'
    response=prepare_remote(context,pending); assert response['id']==prepared['id'] and calls==[record['key']]*2
    persisted=journal.list()[0]; assert persisted['status']=='ASSIGNED' and 'upload_url' not in str(persisted) and 'abcd' not in str(persisted)
    restored=Journal(tmp_path,client.base,client.user['id'],client.user['tenant_id'],keys)
    assert restored.list()[0]['key']==record['key']


@pytest.mark.parametrize('malice',['origin','headers','hash'])
def test_upload_rejects_altered_destination_headers_or_file(tmp_path,malice):
    journal,record,client,window,context,content,prepared,keys=setup(tmp_path)
    journal.document_transition(record['key'],prepared['id'],'assign'); record=journal.list()[0]
    if malice=='origin': prepared['upload_url']='https://evil.example/storage/v1/objects/abcd'
    elif malice=='headers': prepared['upload_headers']['Authorization']='secret'
    else: content+=b'changed'
    with pytest.raises((ContractError,JournalError,DownloadError,ValueError)): upload_bytes(context,record,prepared,content)
    assert journal.list()[0]['status']=='ASSIGNED'


def test_lost_put_preserves_state_and_never_reissues(tmp_path,monkeypatch):
    import redhouse_desktop.document_upload as module
    journal,record,client,window,context,content,prepared,keys=setup(tmp_path)
    journal.document_transition(record['key'],prepared['id'],'assign'); record=journal.list()[0]; sends=[]
    class Session:
        trust_env=True
        def put(self,*a,**k): sends.append(1); raise module.requests.ConnectionError('lost')
        def close(self): pass
    monkeypatch.setattr(module.requests,'Session',Session)
    with pytest.raises(ConnectionError): upload_bytes(context,record,prepared,content)
    assert sends==[1] and journal.list()[0]['status']=='PUT_UNCERTAIN'
    with pytest.raises(JournalError): upload_bytes(context,record,prepared,content)
    assert sends==[1]


def test_changed_sid_does_not_transfer(tmp_path):
    journal,record,client,window,context,content,prepared,keys=setup(tmp_path)
    journal.document_transition(record['key'],prepared['id'],'assign'); record=journal.list()[0]
    client.session_id=str(uuid4())
    with pytest.raises(SessionChanged): upload_bytes(context,record,prepared,content)
    assert journal.list()[0]['status']=='ASSIGNED'


def test_missing_then_verified_keeps_id_and_verify_key(tmp_path):
    journal,record,client,window,context,content,prepared,keys=setup(tmp_path)
    identifier=prepared['id']; journal.document_transition(record['key'],identifier,'assign'); journal.document_transition(record['key'],identifier,'start'); record=journal.list()[0]; keys_used=[]
    def missing(*a,**k): keys_used.append(k['key']); raise ApiError(404,'object_missing','no existe')
    client.authorized=missing
    with pytest.raises(ApiError): verify_remote(context,record)
    assert journal.list()[0]['status']=='MISSING'
    journal.document_transition(record['key'],identifier,'start'); journal.document_transition(record['key'],identifier,'uploaded'); record=journal.list()[0]
    response={'id':identifier,'status':'VERIFIED','sha256':record['body']['sha256'],'size':record['body']['size'],'mime_type':record['body']['mime_type'],'generation':'77'}
    metadata={**prepared['metadata'],'id':identifier,'analysis':'CLEAN','file_status':'VERIFIED','sha256':record['body']['sha256'],'generation':'77'}
    def verified(*a,**k):
        if a[2]=='file_verify': keys_used.append(k['key']); return response
        return metadata
    client.authorized=verified
    assert verify_remote(context,record)==metadata and journal.list()[0]['state']=='DONE'
    assert keys_used==[record['key']+'-verify']*2


@pytest.mark.parametrize('remote_status',[201,412])
def test_put_once_no_proxy_no_auth_and_existing_is_verified(tmp_path,monkeypatch,remote_status):
    import redhouse_desktop.document_upload as module
    journal,record,client,window,context,content,prepared,keys=setup(tmp_path)
    journal.document_transition(record['key'],prepared['id'],'assign'); record=journal.list()[0]; calls=[]
    class Response:
        status_code=remote_status
        def close(self): pass
    class Session:
        trust_env=True
        def put(self,url,**kwargs): calls.append((self.trust_env,kwargs)); return Response()
        def close(self): pass
    monkeypatch.setattr(module.requests,'Session',Session)
    upload_bytes(context,record,prepared,content)
    assert len(calls)==1 and calls[0][0] is False and calls[0][1]['allow_redirects'] is False
    assert set(calls[0][1]['headers'])=={'Content-Type'} and journal.list()[0]['status']=='UPLOADED'


def test_gcs_destination_must_match_exact_tenant_and_document(tmp_path,monkeypatch):
    import redhouse_desktop.document_upload as module
    journal,record,client,window,context,content,prepared,keys=setup(tmp_path); monkeypatch.setenv('REDHOUSE_GCS_BUCKET','synthetic-bucket')
    journal.document_transition(record['key'],prepared['id'],'assign'); record=journal.list()[0]
    prepared['upload_url']='https://storage.googleapis.com/synthetic-bucket/documents/'+context.actor[1]+'/'+prepared['id']+'?signature=test'
    prepared['upload_headers']['x-goog-if-generation-match']='0'
    class Response:
        status_code=200
        def close(self): pass
    class Session:
        trust_env=True
        def put(self,*a,**k): return Response()
        def close(self): pass
    monkeypatch.setattr(module.requests,'Session',Session)
    upload_bytes(context,record,prepared,content)
    assert journal.list()[0]['status']=='UPLOADED'


def test_mismatched_verified_generation_does_not_close_journal(tmp_path):
    journal,record,client,window,context,content,prepared,keys=setup(tmp_path); identifier=prepared['id']
    journal.document_transition(record['key'],identifier,'assign'); journal.document_transition(record['key'],identifier,'start'); journal.document_transition(record['key'],identifier,'uploaded'); record=journal.list()[0]
    response={'id':identifier,'status':'VERIFIED','sha256':record['body']['sha256'],'size':record['body']['size'],'mime_type':record['body']['mime_type'],'generation':'77'}
    metadata={**prepared['metadata'],'analysis':'CLEAN','file_status':'VERIFIED','sha256':record['body']['sha256'],'generation':'78'}
    client.authorized=lambda *a,**k: response if a[2]=='file_verify' else metadata
    with pytest.raises(ContractError): verify_remote(context,record)
    assert journal.list()[0]['state']=='PENDING'


def test_restart_other_account_cannot_read_pending_document(tmp_path):
    journal,record,client,window,context,content,prepared,keys=setup(tmp_path)
    restarted=Journal(tmp_path,client.base,str(uuid4()),client.user['tenant_id'],keys)
    assert restarted.list()==[]
    original=Journal(tmp_path,client.base,client.user['id'],client.user['tenant_id'],keys)
    assert original.list()[0]['key']==record['key']


@pytest.mark.parametrize('field,value',[('path','/tmp/private.pdf'),('password','secret'),('proof','secret')])
def test_journal_rejects_private_fields(tmp_path,field,value):
    journal,record,*_=setup(tmp_path)
    invalid=dict(record,key=str(uuid4()),body=dict(record['body'],**{field:value}))
    with pytest.raises(JournalError): journal.prepare(invalid)


def test_put_changed_account_keeps_original_journal_and_explicit_ca(tmp_path,monkeypatch):
    import redhouse_desktop.document_upload as module
    journal,record,client,window,context,content,prepared,keys=setup(tmp_path)
    journal.document_transition(record['key'],prepared['id'],'assign'); record=journal.list()[0]
    monkeypatch.setenv('REQUESTS_CA_BUNDLE','/private/test-ca.pem'); observed=[]
    class Response:
        status_code=201
        def close(self): pass
    class Session:
        trust_env=True
        def put(self,*a,**k):
            observed.append((self.trust_env,self.verify))
            window.client=SimpleNamespace(user={'id':str(uuid4())},session_id=str(uuid4()))
            return Response()
        def close(self): pass
    monkeypatch.setattr(module.requests,'Session',Session)
    upload_bytes(context,record,prepared,content)
    assert observed==[(False,'/private/test-ca.pem')]
    assert journal.list()[0]['status']=='UPLOADED'


def test_verify_changed_account_never_uses_new_session_or_closes_journal(tmp_path):
    journal,record,client,window,context,content,prepared,keys=setup(tmp_path); identifier=prepared['id']
    journal.document_transition(record['key'],identifier,'assign'); journal.document_transition(record['key'],identifier,'start'); journal.document_transition(record['key'],identifier,'uploaded'); record=journal.list()[0]; calls=[]
    def response(*a,**k):
        calls.append(a[2]); window.client=SimpleNamespace(user={'id':str(uuid4())},session_id=str(uuid4()))
        return {'id':identifier,'status':'VERIFIED','sha256':record['body']['sha256'],'size':record['body']['size'],'mime_type':record['body']['mime_type'],'generation':'1'}
    client.authorized=response
    with pytest.raises(SessionChanged): verify_remote(context,record)
    assert calls==['file_verify'] and journal.list()[0]['status']=='UPLOADED'


def test_missing_restart_reuses_same_document_and_key(tmp_path):
    journal,record,client,window,context,content,prepared,keys=setup(tmp_path); identifier=prepared['id']
    journal.document_transition(record['key'],identifier,'assign'); journal.document_transition(record['key'],identifier,'start'); journal.document_transition(record['key'],identifier,'missing')
    restarted=Journal(tmp_path,client.base,client.user['id'],client.user['tenant_id'],keys); window.journal=restarted; context=OperationContext(window); record=restarted.list()[0]; calls=[]
    def response(*a,**k): calls.append(k['key']); return prepared
    client.authorized=response
    assert prepare_remote(context,record)['id']==identifier
    assert calls==[record['key']] and restarted.list()[0]['status']=='MISSING'
