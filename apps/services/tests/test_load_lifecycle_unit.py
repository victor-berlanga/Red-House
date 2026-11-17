"""Pure owner-version and failed-startup compensation regressions."""
import json
import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
import sys
import pytest
from flask import Flask
SERVICES=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(SERVICES),str(SERVICES/'tests')]
os.environ['LOCUST_SKIP_MONKEY_PATCH']='1'
from scripts import load_client
from redhouse.codec import respond
from tests import locust_transactions as workload
from tests.load_cleanup import cleanup_for

@pytest.mark.parametrize('service,version',[('inventario','0.4.1'),('compatibilidad','0.4.4')])
@pytest.mark.parametrize('mime',['application/json','application/xml'])
def test_declared_owner_version(service,version,mime):
    app=Flask('owner-contract')
    payload=dict(error=dict(code='reauthentication_required',message='Confirm identity',details=[dict(field='reauthentication',code='challenge',challenge='synthetic-challenge-'*6)]),meta=dict(correlation_id='00000000-0000-4000-8000-000000000001',service=service,version=version))
    def reply():
        with app.test_request_context('/',headers={'Accept':mime}):response=respond(payload,403)
        return SimpleNamespace(headers=response.headers,content=response.data,json=lambda:payload)
    assert load_client.reauthentication_challenge(reply(),service,mime)=='synthetic-challenge-'*6
    payload['meta']['version']='0.0.0'
    with pytest.raises(ValueError,match='invalid_challenge_owner'):load_client.reauthentication_challenge(reply(),service,mime)

def environment():
    return SimpleNamespace(events=SimpleNamespace(request=SimpleNamespace(fire=Mock()),test_stop=SimpleNamespace(add_listener=Mock())),runner=SimpleNamespace(quit=Mock()),process_exit_code=0)

def test_close_failure_preserves_original_error():
    env=environment();cleanup=cleanup_for(env)
    api=SimpleNamespace(user={'id':'actor'},refresh='synthetic',close=Mock(side_effect=RuntimeError('private close detail')))
    client=SimpleNamespace(close=Mock());cleanup.add(api,client);original=load_client.LoadFailure('original_business_error')
    with pytest.raises(load_client.LoadFailure) as observed:
        try:raise original
        finally:cleanup.close_entry(api,client,preserve_error=True)
    assert observed.value is original and str(env.events.request.fire.call_args.kwargs['exception'])=='cleanup_RuntimeError'
    cleanup.close_entry(api,client,preserve_error=True);api.close.assert_called_once();client.close.assert_called_once()

@pytest.mark.parametrize('close_fails',[False,True])
def test_failed_on_start_closes_without_preflight_done(monkeypatch,tmp_path,close_fails):
    account=dict(id='actor',tenant_id='tenant',role='TRANSPORT',username='transport1',mime='application/json')
    (tmp_path/'state.json').write_text(json.dumps(dict(directory=str(tmp_path),urls={'transporte':'http://127.0.0.1:1234'},password='synthetic')))
    (tmp_path/'fixture.json').write_text(json.dumps({'cases':{'TRANSPORT':[dict(case_id='case')]*3}}))
    for key,value in {'REDHOUSE_LOAD_FINITE_ROLES':'1','REDHOUSE_LOAD_ISOLATED':'1','REDHOUSE_LOAD_USERS':'3','REDHOUSE_LOAD_MEASURE_SECONDS':'120','REDHOUSE_LOAD_STATE':str(tmp_path/'state.json'),'REDHOUSE_LOAD_FINITE_MANIFEST':str(tmp_path/'fixture.json'),'REDHOUSE_LOAD_MARKER':str(tmp_path/'phase.json')}.items():monkeypatch.setenv(key,value)
    monkeypatch.setattr(workload,'finite_manifest',lambda *_:[account]);monkeypatch.setattr(workload.timing,'ephemeral_factors',lambda:{})
    api=SimpleNamespace(user=account,refresh='synthetic',login=Mock(),close=Mock(side_effect=RuntimeError('close') if close_fails else None))
    monkeypatch.setattr(workload,'LoadSession',lambda *a,**kw:api);original=load_client.LoadFailure('original_preflight_error')
    class User:
        issued=0
        def run_case(self,case):raise original
    user=User();user.client=SimpleNamespace(close=Mock());user.environment=environment()
    with pytest.raises(workload.StopUser) as observed:workload.FiniteRoleUser.on_start(user)
    import gevent
    gevent.sleep(0)
    assert observed.value.__context__ is original and not user.preflight_done and user.environment.process_exit_code==1
    api.close.assert_called_once();user.client.close.assert_called_once();workload.FiniteRoleUser.on_stop(user);api.close.assert_called_once()

def test_challenge_diagnostic_keeps_metadata_and_never_secret_value():
    app=Flask('diagnostic');secret='never-persist-this-challenge-'*5
    payload=dict(error=dict(code='reauthentication_required',message='Confirm identity',details=[dict(field='reauthentication',code='challenge',challenge=secret)]),meta=dict(correlation_id='00000000-0000-4000-8000-000000000001',service='inventario',version='0.4.4'))
    with app.test_request_context('/',headers={'Accept':'application/xml'}):response=respond(payload,403)
    fake=SimpleNamespace(headers=response.headers,content=response.data,status_code=403)
    diagnostic={}
    with pytest.raises(ValueError,match='invalid_challenge_owner'):load_client.reauthentication_challenge(fake,'inventario','application/xml',diagnostic=diagnostic)
    assert diagnostic['status']==403 and diagnostic['version_matches'] is False
    assert diagnostic['details'][0]['challenge_type']=='str' and diagnostic['details'][0]['challenge_length']==len(secret)
    assert secret not in json.dumps(diagnostic) and 'proof' not in diagnostic


def test_actor_cancellation_does_not_cancel_owned_cleanup_greenlet():
    import gevent
    from gevent.event import Event
    from gevent.pool import Group
    env=environment();env.runner.user_greenlets=Group();cleanup=cleanup_for(env)
    started,release,closed=Event(),Event(),Event()
    def close():
        started.set();release.wait(timeout=2);closed.set()
    api=SimpleNamespace(user={'id':'actor'},refresh='synthetic',close=close)
    client=SimpleNamespace(close=Mock());cleanup.add(api,client)
    def actor():
        cleanup.schedule_close(api,client)
        started.wait(timeout=2)
        gevent.sleep(10)
    user=gevent.spawn(actor);assert started.wait(timeout=2)
    user.kill(block=True)
    assert not closed.is_set() and not cleanup.closers[id(api)].ready()
    release.set();cleanup.finish()
    assert closed.is_set() and all(g.ready() for g in cleanup.closers.values())
    assert cleanup.failure_codes==[] and cleanup.entries==[]
    client.close.assert_called_once()
