"""Comandos de conservación con diario real y transporte simulado."""
from copy import deepcopy
from types import SimpleNamespace
from uuid import uuid4

import pytest
from cryptography.fernet import Fernet
from redhouse_desktop.client import ContractError
from redhouse_desktop.durable_commands import prepare_command, submit_command
from redhouse_desktop.journal import Journal


class Keys:
    def __init__(self): self.key=Fernet.generate_key()
    def get(self, identifier, exists): return self.key


def command(kind,tmp_path):
    user={'id':str(uuid4()),'tenant_id':str(uuid4()),'role':'MEDICAL' if kind=='profile' else 'OPERATOR'}
    body=({'kind':'ORGAN','component':'KIDNEY','minimum_c':1.0,'maximum_c':2.0,'max_gap_seconds':300,
           'source':'Fuente sintética','synthetic':True,'version':2,'effective_at':'2026-11-16T12:00:00Z','supersedes':str(uuid4())}
          if kind=='profile' else {'label':'Equipo sintético','location':'Sala sintética','calibration_reference':None})
    result=dict(body,id=str(uuid4()),tenant_id=user['tenant_id'])
    result.update(author_id=user['id']) if kind=='profile' else result.update(active=True,version=1)
    keys=Keys();journal=Journal(tmp_path,'https://fixture.invalid',user['id'],user['tenant_id'],keys)
    return user,body,result,keys,journal


@pytest.mark.parametrize('kind',['equipment','profile'])
def test_cold_replay_preserves_persisted_attempt(kind,tmp_path):
    user,body,result,keys,journal=command(kind,tmp_path);operation='cold_'+kind+'_create'
    record=prepare_command(journal,operation,None,body);calls=[]
    def authorized(service,path,name,**kwargs):
        calls.append((service,path,name,deepcopy(kwargs)))
        assert kwargs['key']==journal.list()[0]['key'] and kwargs['body']==journal.list()[0]['body']
        if len(calls)==1:raise ConnectionError('respuesta perdida')
        return result
    client=SimpleNamespace(user=user,authorized=authorized)
    with pytest.raises(ConnectionError):submit_command(client,journal,record,fresh=True)
    journal.mark_uncertain(record['key']);reopened=Journal(tmp_path,'https://fixture.invalid',user['id'],user['tenant_id'],keys)
    submit_command(client,reopened,reopened.list()[0])
    assert calls[0]==calls[1]
    assert calls[0][1]=='/api/v1/cold/'+('profiles' if kind=='profile' else 'equipment')
    assert calls[0][3]['request_schema']==operation+'.xsd'
    assert reopened.list()[0]['state']=='DONE' and reopened.list()[0]['operation_id']==result['id']


@pytest.mark.parametrize('kind',['equipment','profile'])
def test_cold_response_scope_cannot_close_journal(kind,tmp_path):
    user,body,result,_,journal=command(kind,tmp_path);record=prepare_command(journal,'cold_'+kind+'_create',None,body)
    client=SimpleNamespace(user=user,authorized=lambda *a,**k:dict(result,tenant_id=str(uuid4())))
    with pytest.raises(ContractError):submit_command(client,journal,record,fresh=True)
    assert journal.list()[0]['state']=='PREPARED'


def test_profile_invalid_synthetic_policy_fails_before_persistence(tmp_path):
    _,body,_,_,journal=command('profile',tmp_path)
    with pytest.raises(ContractError):prepare_command(journal,'cold_profile_create',None,dict(body,synthetic=False))
    assert journal.list()==[]
