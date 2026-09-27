"""Aceptación del primer parcial mejorado: estados, preservación y sesión."""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier

import pytest
from conftest import csrf
from test_regional import actors, case, reserve, deliver
from src.business.access import BusinessError
from src.business.services import auth, regional as r, logistics, matching
from src.data_access.connection import transaction
from src.data_access.repositories import audit


def test_session_rotation_expiry_revocation_and_csrf(app, client, sign_in, db):
    sign_in(client)
    token=client.get_cookie(app.config['JWT_COOKIE_NAME']).value
    assert client.get('/sesion/estado').status_code==200
    assert client.post('/sesion/continuar').status_code==400
    result=client.post('/sesion/continuar',headers={'X-CSRFToken':csrf(client,'/panel')})
    assert result.status_code==200
    assert result.json['expires_at']>result.json['server_time']
    assert result.json['csrf_token']
    new=client.get_cookie(app.config['JWT_COOKIE_NAME']).value
    assert token!=new
    with app.app_context():
        assert auth.authenticate(token)==(None,None)
        assert auth.authenticate(new)[0]
    db.execute('UPDATE web_session SET expires_at=now()-interval \'1 second\' WHERE revoked_at IS NULL');db.commit()
    assert client.get('/sesion/estado').status_code==401
    assert client.post('/sesion/continuar',headers={'X-CSRFToken':result.json['csrf_token']}).status_code==401


def test_session_renewal_denies_disabled_account_and_audit_rollback(app,client,sign_in,db,monkeypatch):
    sign_in(client)
    token=client.get_cookie(app.config['JWT_COOKIE_NAME']).value
    with app.app_context():
        actor,sid=auth.authenticate(token)
        def fail(*a,**kw):raise RuntimeError('audit failure')
        with monkeypatch.context() as m:
            m.setattr(audit,'record',fail)
            with pytest.raises(RuntimeError):auth.renew(actor,sid)
        assert auth.authenticate(token)[0]
    db.execute("UPDATE user_account SET account_status='INACTIVE' WHERE account_id=%s",(actor.account_id,));db.commit()
    assert client.get('/sesion/estado').status_code==401


def test_folio_and_urgency_new_and_historical(app,actors,db,client,sign_in):
    data=dict(institution_id=actors['medico.valle'].institution_id,record_code='AB',display_name='Prueba',blood_group='O-',restrictions='Ninguna',requirement='Prueba',studies='Referencia',current_status='ACTIVE',urgency='URGENT')
    with app.app_context():
        with pytest.raises(BusinessError,match='6 a 30'):r.save_person(actors['medico.valle'],'recipient',data)
        rid=r.save_person(actors['medico.valle'],'recipient',{**data,'record_code':'REC-ABC'})
    assert db.execute('SELECT legacy_urgency FROM recipient WHERE recipient_id=%s',(rid,)).fetchone()['legacy_urgency'] is None
    # Simula un folio legado: se permite conservarlo, no crear otro corto.
    db.execute("UPDATE recipient SET record_code='AB',legacy_urgency='PRIORITY' WHERE recipient_id=%s",(rid,));db.commit()
    with app.app_context():
        r.save_person(actors['medico.valle'],'recipient',{**data,'version_no':1,'audit_reason':'Corrección de prueba'},rid)
        with pytest.raises(BusinessError,match='6 a 30'):
            r.save_person(actors['medico.valle'],'recipient',{**data,'record_code':'CD','version_no':2,'audit_reason':'Prueba'},rid)
    row=db.execute('SELECT record_code,legacy_urgency FROM recipient WHERE recipient_id=%s',(rid,)).fetchone()
    assert row=={'record_code':'AB','legacy_urgency':'PRIORITY'}
    sign_in(client,'medico.valle')
    assert b'name="urgency"' not in client.get('/sangre/personas/recipient').data
    assert b'name="urgency"' in client.get('/sangre/solicitudes').data


def test_request_coverage_cancellation_and_automatic_close(app,actors,db,client,sign_in):
    c=case(app,actors);aid=reserve(app,actors,c)
    sign_in(client,'medico.valle')
    response=client.get(f"/sangre/solicitudes/{c['request']}/editar")
    assert response.status_code==200
    assert b'name="candidate_id"' not in response.data
    assert b'Cancelar solicitud</button>' not in response.data
    assert 'Cantidad cubierta' in response.text
    with app.app_context():
        with pytest.raises(BusinessError):r.close_request(actors['medico.valle'],c['request'],dict(version_no=2,status='CANCELLED',observation='No procede'))
    deliver(app,actors,c,aid)
    assert db.execute('SELECT current_status,closed_at FROM blood_request WHERE request_id=%s',(c['request'],)).fetchone()['current_status']=='CLOSED'
    assert db.execute("SELECT count(*) AS n FROM request_event WHERE request_id=%s AND action='CLOSED'",(c['request'],)).fetchone()['n']==1


@pytest.mark.parametrize('concurrent',[False,True])
def test_multiple_receipts_only_complete_when_all_received(app,actors,db,concurrent):
    c=case(app,actors)
    db.execute('UPDATE blood_request SET quantity=2 WHERE request_id=%s',(c['request'],));db.commit()
    first=reserve(app,actors,c)
    with app.app_context():
        r.produce_unit(actors['medico'],c['donation'],dict(traceability_code='UNIT-SECOND',component_id=c['component'],location_id=db.execute('SELECT location_id FROM blood_unit WHERE resource_id=%s',(c['resource'],)).fetchone()['location_id'],expires_at=(r.now()+timedelta(hours=24)).isoformat(),release_reference='LAB-SECOND',human_confirmation='on'))
        db.commit()
        eid=matching.evaluate(actors['coordinador'],c['request'])
        candidate=db.execute("SELECT c.candidate_id FROM blood_candidate c JOIN resource u USING(resource_id) WHERE evaluation_id=%s AND traceability_code='UNIT-SECOND'",(eid,)).fetchone()['candidate_id'];db.commit()
        second=matching.reserve(actors['medico.valle'],c['request'],dict(candidate_id=candidate,version_no=2,reason='Segunda unidad',human_confirmation='on'))
    deliver(app,actors,c,first,accept=not concurrent)
    assert db.execute('SELECT current_status FROM blood_request WHERE request_id=%s',(c['request'],)).fetchone()['current_status']=='IN_PROGRESS';db.commit()
    deliver(app,actors,c,second,accept=not concurrent)
    if concurrent:
        location=db.execute('SELECT location_id FROM storage_location JOIN site USING(site_id) WHERE institution_id=%s LIMIT 1',(actors['operador.valle'].institution_id,)).fetchone()['location_id'];db.commit()
        barrier=Barrier(2)
        def receive(aid):
            with app.app_context():
                barrier.wait(timeout=10)
                logistics.step(actors['operador.valle'],aid,dict(version_no=5,status='ACCEPTED',location_id=location,observation='Recepción concurrente',location_description='Destino de prueba',evidence_reference='ACTA-CONCURRENT'))
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures=[pool.submit(receive,aid) for aid in (first,second)]
            for future in futures:future.result(timeout=20)
    assert db.execute('SELECT current_status FROM blood_request WHERE request_id=%s',(c['request'],)).fetchone()['current_status']=='CLOSED'
    assert db.execute("SELECT count(*) AS n FROM request_event WHERE request_id=%s AND action='CLOSED'",(c['request'],)).fetchone()['n']==1


def test_navigation_routes_and_missing_route_explanation(app,actors,client,sign_in,db):
    c=case(app,actors)
    sign_in(client,'coordinador')
    page=client.get('/sangre/rutas').text
    assert 'name="source_reference"' not in page
    assert 'Panel principal' not in page
    db.execute('DELETE FROM regional_route');db.commit()
    with app.app_context(),transaction() as conn:
        row=r.request_row(conn,actors['coordinador'],c['request'])
        assert 'falta registrar' in matching.availability_message(conn,row)
    other=app.test_client();sign_in(other,'traslado')
    assert 'Panel principal' not in other.get('/sangre/traslados').text
    assert other.get('/panel').location.endswith('/sangre/traslados')


def test_feedback_session_browser(app,actors,request,tmp_path):
    if not request.config.getoption('--browser'):
        pytest.skip('Requiere --browser y Playwright/Chrome.')
    import os,subprocess
    from pathlib import Path
    from threading import Thread
    from werkzeug.serving import make_server
    app.config['JWT_LIFETIME_SECONDS']=330
    server=make_server('127.0.0.1',0,app,threaded=True)
    thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        result=subprocess.run(['node',str(Path(__file__).with_name('feedback_browser.cjs'))],env={**os.environ,
            'BASE_URL':f'http://127.0.0.1:{server.server_port}','DEMO_PASSWORD':app.config['DEMO_TEST_PASSWORD'],
            'BROWSER_ARTIFACTS':str(Path(os.getenv('BROWSER_ARTIFACTS',str(tmp_path)))/'session')},capture_output=True,text=True,timeout=120)
        assert result.returncode==0,result.stdout+result.stderr
    finally:
        server.shutdown();thread.join(timeout=5);server.server_close()


def test_automatic_close_audit_failure_rolls_back_receipt(app,actors,db,monkeypatch):
    c=case(app,actors);aid=reserve(app,actors,c)
    original=r.event
    def fail_close(*args,**kwargs):
        if args[2]=='CLOSED':raise RuntimeError('Closure audit unavailable')
        return original(*args,**kwargs)
    monkeypatch.setattr(r,'event',fail_close)
    with pytest.raises(RuntimeError,match='Closure audit'):deliver(app,actors,c,aid)
    assert db.execute('SELECT current_status FROM blood_request WHERE request_id=%s',(c['request'],)).fetchone()['current_status']=='IN_PROGRESS'
    assert db.execute('SELECT current_status FROM blood_allocation WHERE allocation_id=%s',(aid,)).fetchone()['current_status']=='IN_TRANSIT'
    assert db.execute('SELECT current_status FROM shipment WHERE allocation_id=%s',(aid,)).fetchone()['current_status']=='DELIVERED'
    assert not db.execute("SELECT 1 FROM request_event WHERE request_id=%s AND action='CLOSED'",(c['request'],)).fetchone()
