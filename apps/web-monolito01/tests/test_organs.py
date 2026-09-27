from datetime import timedelta
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import pytest
import psycopg
from conftest import csrf
from test_regional import actors
from src.business.services import organs as o, regional as r
from src.business.access import BusinessError, Principal
from src.data_access.repositories import audit
from src.data_access.connection import transaction


def organ_case(app,actors,typ='KIDNEY',suffix='001'):
    with app.app_context():
        d=o.create_person(actors['medico'],'donor',dict(record_code='OD-'+suffix,display_name='Donante ficticio',abo='O',donation_kind='DECEASED',consent_reference='CONSENTIMIENTO-FICTICIO',studies='ESTUDIO-PRIVADO-DONANTE',hla='HLA A*01:01 B*08:01 DRB1*03:01 — ficticio',clinical_reference='REVISIÓN-FICTICIA',human_confirmation='on'))
        p=o.create_person(actors['medico.valle'],'recipient',dict(record_code='OR-'+suffix,display_name='Receptor ficticio',abo='O',organ_type=typ,studies='ESTUDIO-PRIVADO-RECEPTOR',hla='HLA A*01:01 B*08:01 DRB1*03:01 — ficticio',clinical_reference='COMITÉ-FICTICIO',urgency='URGENT',waiting_since=(r.now()-timedelta(days=20)).isoformat(),human_confirmation='on'))
        oid=o.create_offer(actors['medico'],dict(donor_id=d,record_code='ORG-'+suffix,organ_type=typ,anatomical_description='Órgano de ejercicio completo',recovered_at=(r.now()-timedelta(minutes=5)).isoformat(),preservation_until=(r.now()+timedelta(hours=4)).isoformat(),preservation_reference='LÍMITE-FICTICIO-CAPTURADO',human_confirmation='on'))
        r.save_route(actors['coordinador'],dict(origin_id=actors['medico'].institution_id,destination_id=actors['medico.valle'].institution_id,distance_km=30,travel_minutes=45,audit_reason='Estimación del ejercicio'))
        eid=o.evaluate(actors['coordinador'],oid)
        with transaction() as conn:
            c=conn.execute('SELECT candidate_id FROM organ_candidate WHERE evaluation_id=%s AND recipient_id=%s',(eid,p)).fetchone()['candidate_id']
        return dict(donor=d,recipient=p,offer=oid,candidate=c)


def approve(app,actors,c):
    with app.app_context():
        rev=o.review(actors['medico.valle'],c['candidate'],dict(decision='FAVORABLE',hla_assessment='Interpretación ficticia registrada por médico; no validación real',size_assessment='Evaluación ficticia de tamaño',crossmatch_reference='ESTUDIO-PAREJA-FICTICIO',clinical_reference='DICTAMEN-FICTICIO',human_confirmation='on'))
        return o.reserve(actors['medico.valle'],c['candidate'],dict(review_id=rev,authorization_reference='AUTORIZACIÓN-FICTICIA',human_confirmation='on'))


def event_data(version,status):
    return dict(version_no=version,status=status,location_description='Ubicación ficticia',observation='Evento del ejercicio',evidence_reference='ACTA-FICTICIA')


@pytest.mark.parametrize('typ',['KIDNEY','LIVER','HEART'])
def test_complete_organ_flow(app,actors,db,sign_in,typ):
    c=organ_case(app,actors,typ);aid=approve(app,actors,c)
    with app.app_context():
        departure=r.now()+timedelta(minutes=1)
        o.plan(actors['coordinador'],aid,dict(version_no=1,transport_id=actors['traslado'].account_id,vehicle='VEHÍCULO-FICTICIO',departure_at=departure.isoformat(),eta=(departure+timedelta(minutes=45)).isoformat(),evidence_reference='ORDEN-FICTICIA'))
        for version,(role,status) in enumerate([('operador','PREPARED'),('traslado','COLLECTED'),('traslado','IN_TRANSIT'),('traslado','DELIVERED'),('medico.valle','ACCEPTED')],2):
            o.step(actors[role],aid,event_data(version,status))
    assert db.execute('SELECT current_status FROM organ_recipient WHERE recipient_id=%s',(c['recipient'],)).fetchone()['current_status']=='CLOSED'
    assert db.execute('SELECT current_status FROM organ_offer WHERE offer_id=%s',(c['offer'],)).fetchone()['current_status']=='RECEIVED'
    assert db.execute('SELECT count(*) AS n FROM organ_custody_event WHERE allocation_id=%s',(aid,)).fetchone()['n']==7
    for role,paths in [('medico',['/organos','/organos/personas/donor','/organos/registrar',f"/organos/personas/donor/{c['donor']}"]),('medico.valle',[f"/organos/candidatos/{c['candidate']}"]),('auditor',['/organos',f'/organos/traslados/{aid}']),('traslado',[f'/organos/traslados/{aid}'])]:
        client=app.test_client();sign_in(client,role)
        for path in paths:
            response=client.get(path)
            assert response.status_code==200,(path,response.data[:2000])
            if role in ('auditor','traslado'):assert b'ESTUDIO-PRIVADO' not in response.data
    with pytest.raises(psycopg.Error):
        with db.transaction():db.execute('DELETE FROM organ_custody_event WHERE allocation_id=%s',(aid,))


def test_clinical_authorization_scope_and_stale_candidate(app,actors,db,sign_in):
    c=organ_case(app,actors)
    with app.app_context():
        with pytest.raises(BusinessError):o.reserve(actors['medico.valle'],c['candidate'],dict(human_confirmation='on'))
        with pytest.raises(BusinessError):o.clinical_candidate(actors['medico'],c['candidate'])
        with pytest.raises(BusinessError):o.clinical_candidate(actors['auditor'],c['candidate'])
        with pytest.raises(BusinessError):o.person_detail(actors['medico.valle'],'donor',c['donor'])
        r.save_route(actors['coordinador'],dict(origin_id=actors['medico'].institution_id,destination_id=actors['medico.valle'].institution_id,distance_km=31,travel_minutes=46,audit_reason='Cambio posterior'))
        with pytest.raises(BusinessError,match='obsoleta'):approve(app,actors,c)
    client=app.test_client();sign_in(client,'auditor')
    assert client.get('/organos/personas/donor').status_code==403
    assert client.post('/organos/personas/donor',data={}).status_code==400
    assert db.execute('SELECT count(*) AS n FROM organ_allocation').fetchone()['n']==0


def test_no_cross_region_and_no_clinical_leak(app,actors,db):
    c=organ_case(app,actors)
    alien=Principal(**{**actors['coordinador'].__dict__,'region_name':'OTHER'})
    with app.app_context():
        with pytest.raises(BusinessError):o.detail(alien,c['offer'])
        with pytest.raises(BusinessError):o.evaluate(actors['auditor'],c['offer'])
    for row in db.execute("SELECT reason FROM audit_event WHERE entity_type LIKE 'ORGAN_%'"):
        assert 'ESTUDIO-PRIVADO' not in row['reason']


def test_concurrent_reservation_and_rollback(app,actors,db,monkeypatch):
    c=organ_case(app,actors)
    with app.app_context():
        rev=o.review(actors['medico.valle'],c['candidate'],dict(decision='FAVORABLE',hla_assessment='Ficticio',size_assessment='Ficticio',crossmatch_reference='Ficticio',clinical_reference='Ficticio',human_confirmation='on'))
    data=dict(review_id=rev,authorization_reference='Ficticia',human_confirmation='on')
    old=audit.record
    def fail(*a,**kw): raise RuntimeError('audit failed')
    monkeypatch.setattr(audit,'record',fail)
    with app.app_context(),pytest.raises(RuntimeError):o.reserve(actors['medico.valle'],c['candidate'],data)
    monkeypatch.setattr(audit,'record',old)
    assert db.execute('SELECT count(*) AS n FROM organ_allocation').fetchone()['n']==0
    barrier=Barrier(2)
    def reserve():
        with app.app_context():
            barrier.wait()
            try:return o.reserve(actors['medico.valle'],c['candidate'],data)
            except BusinessError:return None
    with ThreadPoolExecutor(2) as pool: results=list(pool.map(lambda _:reserve(),range(2)))
    assert sum(x is not None for x in results)==1
    assert db.execute('SELECT count(*) AS n FROM organ_allocation').fetchone()['n']==1


def test_cancel_releases_and_forbidden_events(app,actors,db):
    c=organ_case(app,actors);aid=approve(app,actors,c)
    with app.app_context():
        with pytest.raises(BusinessError):o.step(actors['auditor'],aid,event_data(1,'INCIDENT'))
        with pytest.raises(BusinessError):o.step(actors['medico.valle'],aid,event_data(1,'ACCEPTED'))
        o.step(actors['coordinador'],aid,event_data(1,'CANCELLED'))
        with pytest.raises(BusinessError):o.step(actors['coordinador'],aid,event_data(1,'CANCELLED'))
        with pytest.raises(BusinessError):o.reserve(actors['medico.valle'],c['candidate'],dict(human_confirmation='on'))
    assert db.execute('SELECT current_status FROM organ_offer WHERE offer_id=%s',(c['offer'],)).fetchone()['current_status']=='AVAILABLE'
    assert db.execute('SELECT current_status FROM organ_recipient WHERE recipient_id=%s',(c['recipient'],)).fetchone()['current_status']=='ACTIVE'


def test_expiry_and_abo_exclusion(app,actors,db):
    c=organ_case(app,actors)
    db.execute("UPDATE organ_recipient SET abo='A' WHERE recipient_id=%s",(c['recipient'],));db.commit()
    with app.app_context():eid=o.evaluate(actors['coordinador'],c['offer'])
    assert db.execute('SELECT count(*) AS n FROM organ_candidate WHERE evaluation_id=%s',(eid,)).fetchone()['n']==0
    db.execute("UPDATE organ_recipient SET abo='O' WHERE recipient_id=%s",(c['recipient'],))
    db.execute("UPDATE organ_offer SET preservation_until=now()+interval '1 minute' WHERE offer_id=%s",(c['offer'],));db.commit()
    with app.app_context():eid=o.evaluate(actors['coordinador'],c['offer'])
    assert db.execute('SELECT count(*) AS n FROM organ_candidate WHERE evaluation_id=%s',(eid,)).fetchone()['n']==0


def test_organs_browser(app,actors,request,tmp_path):
    if not request.config.getoption('--browser'):pytest.skip('Requiere --browser y Chrome.')
    import os,json,subprocess
    from pathlib import Path
    from threading import Thread
    from werkzeug.serving import make_server
    cases=[organ_case(app,actors,typ,str(i)+'00') for i,typ in enumerate(o.TYPES,1)]
    data={**{k:str(v) for k,v in cases[0].items()},'transport':str(actors['traslado'].account_id)}
    app.config['HIGHCHARTS_ENABLED']=True
    server=make_server('127.0.0.1',0,app,threaded=True);thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        result=subprocess.run(['node',str(Path(__file__).with_name('organs_browser.cjs'))],env={**os.environ,'BASE_URL':f'http://127.0.0.1:{server.server_port}','DEMO_PASSWORD':app.config['DEMO_TEST_PASSWORD'],'ORGAN_DATA':json.dumps(data),'BROWSER_ARTIFACTS':str(Path(os.getenv('BROWSER_ARTIFACTS',str(tmp_path)))/'organos')},capture_output=True,text=True,timeout=180)
        assert result.returncode==0,result.stdout+result.stderr
        print(result.stdout)
    finally:
        server.shutdown();thread.join(5);server.server_close()


def test_rejected_form_preserves_capture_and_returns_error(app,actors,sign_in):
    client=app.test_client();sign_in(client,'medico')
    response=client.post('/organos/personas/donor',data={'csrf_token':csrf(client,'/organos/personas/donor'),'record_code':'DON-ERROR','display_name':'Borrador conservado','abo':'O'})
    assert response.status_code==400
    assert b'Borrador conservado' in response.data
    assert 'Confirma la evaluación humana'.encode() in response.data
