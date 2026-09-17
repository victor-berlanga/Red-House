"""Flujo regional real, privacidad, concurrencia e integridad histórica."""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
import re

import psycopg
import pytest

from conftest import csrf
from src.business.access import BusinessError,Principal
from src.business.services import regional as r,matching,logistics
from src.data_access.repositories import accounts,audit
from src.data_access.repositories.common import insert
from src.data_access.connection import transaction
from src.data_access.migrations import migrate


@pytest.fixture
def actors(app,db):
    institutions={x['institution_code']:x['institution_id'] for x in db.execute('SELECT * FROM institution')}
    hashed=db.execute("SELECT password_hash FROM user_account WHERE login_email='admin@red-house.test'").fetchone()['password_hash']
    for name,role,scope in [('medico','MEDICAL','DEMO-NORTE'),('medico.valle','MEDICAL','DEMO-VALLE'),('coordinador','COORDINATOR',None),('traslado','TRANSPORT','DEMO-NORTE')]:
        party=insert(db,'party',{'party_name':name+' DEMO'},'party_id')
        account=insert(db,'user_account',{'party_id':party['party_id'],'login_email':name+'@red-house.test','password_hash':hashed},'account_id')
        insert(db,'account_role',{'account_id':account['account_id'],'role_code':role,'institution_id':institutions[scope] if scope else None,'region_name':None if scope else 'DEMO-NORTE'},'account_id')
    db.commit()
    return {name:Principal.from_row(accounts.by_email(db,name+'@red-house.test')) for name in ('medico','medico.valle','coordinador','traslado','operador','operador.valle','auditor','admin')}


def case(app,actors,suffix='01'):
    with app.app_context():
        donor=r.save_person(actors['operador'],'donor',dict(institution_id=actors['operador'].institution_id,
            record_code='DON-'+suffix,display_name='Persona ficticia',blood_group='O-',donation_kind='VOLUNTARY',
            background='SECRETO-CLINICO-ANTECEDENTES',restrictions='Ninguna registrada DEMO',consent_reference='CONSENT-'+suffix,
            consent_at=(r.now()-timedelta(minutes=5)).isoformat()))
        r.review_donor(actors['medico'],donor,dict(version_no=1,decision='ELIGIBLE',reason='Revisión médica ficticia',human_confirmation='on'))
        donation=r.create_donation(actors['operador'],dict(donor_id=donor,donation_code='DONA-'+suffix))
        r.progress_donation(actors['operador'],donation,dict(version_no=1,status='COLLECTED',observation='Recolección ficticia'))
        r.progress_donation(actors['operador'],donation,dict(version_no=2,status='PROCESSED',observation='Procesamiento ficticio'))
        with transaction() as conn:
            component=conn.execute("SELECT component_id FROM blood_component WHERE component_code='RBC-DEMO'").fetchone()['component_id']
            location=conn.execute('SELECT location_id FROM blood_inventory WHERE institution_id=%s LIMIT 1',(actors['operador'].institution_id,)).fetchone()['location_id']
        rid=r.produce_unit(actors['medico'],donation,dict(traceability_code='UNIT-'+suffix,component_id=component,location_id=location,
            expires_at=(r.now()+timedelta(hours=24)).isoformat(),release_reference='LAB-DEMO-'+suffix,human_confirmation='on'))
        recipient=r.save_person(actors['medico.valle'],'recipient',dict(institution_id=actors['medico.valle'].institution_id,record_code='REC-'+suffix,
            display_name='Receptor ficticio',blood_group='O-',requirement='SECRETO-CLINICO-REQUERIMIENTO',studies='SECRETO-CLINICO-ESTUDIOS',
            restrictions='Ninguna registrada DEMO',current_status='ACTIVE'))
        request=r.create_request(actors['medico.valle'],dict(request_code='SOL-'+suffix,recipient_id=recipient,component_id=component,
            quantity=1,urgency='URGENT',justification='SECRETO-CLINICO-JUSTIFICACION'))
        r.save_route(actors['coordinador'],dict(origin_id=actors['operador'].institution_id,destination_id=actors['medico.valle'].institution_id,
            distance_km=30,travel_minutes=45,source_reference='Supuesto académico de prueba, no ruta real'))
        eid=matching.evaluate(actors['coordinador'],request)
        with transaction() as conn:
            candidate=conn.execute('SELECT candidate_id FROM blood_candidate WHERE evaluation_id=%s AND resource_id=%s',(eid,rid)).fetchone()['candidate_id']
        return dict(donor=donor,donation=donation,resource=rid,recipient=recipient,request=request,candidate=candidate,component=component)


def reserve(app,actors,c):
    with app.app_context():
        return matching.reserve(actors['medico.valle'],c['request'],dict(candidate_id=c['candidate'],version_no=1,
            reason='Referencia de revisión humana DEMO',human_confirmation='on'))


def deliver(app,actors,c,aid):
    with app.app_context():
        departure=r.now()+timedelta(minutes=1)
        sid=logistics.plan(actors['coordinador'],aid,dict(version_no=1,transport_id=actors['traslado'].account_id,
            vehicle='VEHICULO-DEMO',departure_at=departure.isoformat(),eta=(departure+timedelta(minutes=45)).isoformat()))
        for version,(role,target) in enumerate([('operador','PREPARED'),('traslado','COLLECTED'),('traslado','IN_TRANSIT'),('traslado','DELIVERED'),('operador.valle','ACCEPTED')],1):
            data=dict(version_no=version,status=target,location_description='Ubicación ficticia del evento',observation='Evidencia de '+target,evidence_reference='ACTA-DEMO-'+target)
            if target=='ACCEPTED':
                with transaction() as conn:
                    data['location_id']=conn.execute('SELECT l.location_id FROM storage_location l JOIN site s USING(site_id) WHERE institution_id=%s LIMIT 1',(actors[role].institution_id,)).fetchone()['location_id']
            logistics.step(actors[role],aid,data)
        return sid


@pytest.mark.parametrize('recipient,permitted',[
    ('O-',{'O-'}),('O+',{'O-','O+'}),('A-',{'O-','A-'}),('A+',{'O-','O+','A-','A+'}),
    ('B-',{'O-','B-'}),('B+',{'O-','O+','B-','B+'}),('AB-',{'O-','A-','B-','AB-'}),
    ('AB+',{'O-','O+','A-','A+','B-','B+','AB-','AB+'})])
def test_demonstrative_rbc_table(recipient,permitted):
    for donor in ('O-','O+','A-','A+','B-','B+','AB-','AB+'):
        assert matching.compatible(donor,recipient)==(donor in permitted)
    assert not matching.compatible('UNKNOWN',recipient)


def test_complete_cross_institution_flow(app,actors,db,sign_in):
    c=case(app,actors)
    aid=reserve(app,actors,c)
    sid=deliver(app,actors,c,aid)
    with app.app_context():
        r.close_request(actors['medico.valle'],c['request'],dict(version_no=2,status='CLOSED',observation='Recepción completa verificada'))
        with pytest.raises(BusinessError) as exc:
            r.save_person(actors['medico.valle'],'recipient',dict(version_no=1,institution_id=actors['medico.valle'].institution_id,
                record_code='REC-01',display_name='Nombre cambiado',blood_group='AB+',restrictions='Ninguna',
                requirement='Cambio retrospectivo',studies='Cambiar estudios',current_status='ACTIVE'),c['recipient'])
        assert exc.value.status==409
    row=db.execute('SELECT * FROM blood_inventory WHERE resource_id=%s',(c['resource'],)).fetchone()
    assert row['institution_id']==actors['medico.valle'].institution_id
    assert row['effective_status']=='DELIVERED' and not row['is_available']
    assert db.execute('SELECT current_status FROM blood_request WHERE request_id=%s',(c['request'],)).fetchone()['current_status']=='CLOSED'
    assert [x['status'] for x in db.execute('SELECT status FROM custody_event WHERE shipment_id=%s ORDER BY sequence',(sid,))]==['SCHEDULED','PREPARED','COLLECTED','IN_TRANSIT','DELIVERED','ACCEPTED']
    assert db.execute('SELECT count(*) AS n FROM donation_unit WHERE resource_id=%s',(c['resource'],)).fetchone()['n']==1
    actions={x['action'] for x in db.execute('SELECT action FROM audit_event')}
    assert {'AUTHORIZE','RESERVE','ASSIGN','IN_TRANSIT','ACCEPTED','CLOSED'}<=actions
    # Renderizar cada pantalla real con el perfil correspondiente.
    for role,paths in {
        'operador':['/sangre/personas/donor',f"/sangre/personas/donor/{c['donor']}",'/sangre/donaciones',f"/sangre/donaciones/{c['donation']}"],
        'medico.valle':['/sangre/personas/recipient',f"/sangre/personas/recipient/{c['recipient']}",f"/sangre/solicitudes/{c['request']}"],
        'coordinador':['/sangre/panel-regional','/sangre/rutas','/sangre/solicitudes','/sangre/traslados',f'/sangre/traslados/{aid}'],
        'traslado':[f'/sangre/traslados/{aid}'],
        'auditor':['/sangre/panel-regional','/auditoria',f'/sangre/traslados/{aid}']}.items():
        client=app.test_client();sign_in(client,role)
        for path in paths:
            response=client.get(path)
            assert response.status_code==200,(path,response.status_code)
            expected = next(base for base in ('/sangre/personas/donor', '/sangre/personas/recipient',
                '/sangre/donaciones', '/sangre/solicitudes', '/sangre/rutas', '/sangre/traslados',
                '/sangre/panel-regional', '/auditoria') if path == base or path.startswith(base+'/'))
            selected = re.findall(rb'<a class="nav-link active"[^>]*href="([^"]+)"[^>]*aria-current="page"', response.data)
            assert selected == [expected.encode()], (role, path, selected)
            if '/sangre/traslados' in path:
                assert ('Trazabilidad regional' if role == 'auditor' else 'Traslados y custodia').encode() in response.data
            if role in ('coordinador','traslado','auditor'):
                assert b'SECRETO-CLINICO' not in response.data


def test_authorization_and_scope_are_enforced(app,actors,sign_in):
    c=case(app,actors)
    with app.app_context():
        for role in ('operador','auditor','coordinador','admin','traslado'):
            with pytest.raises(BusinessError) as exc:
                matching.reserve(actors[role],c['request'],dict(candidate_id=c['candidate'],version_no=1,human_confirmation='on',reason='Intento'))
            assert exc.value.status==403
        with pytest.raises(BusinessError) as exc:
            r.person_detail(actors['medico'],'recipient',c['recipient'])
        assert exc.value.status==404
        with pytest.raises(BusinessError):
            matching.reserve(actors['medico.valle'],c['request'],dict(candidate_id=c['candidate'],version_no=1,reason='Sin confirmar'))
    for role in ('auditor','coordinador','traslado','admin'):
        client=app.test_client();sign_in(client,role)
        assert client.get('/sangre/personas/donor').status_code==403
        assert client.get('/sangre/personas/recipient').status_code==403


def test_donor_requires_human_review_and_cannot_skip_processing(app,actors):
    with app.app_context():
        donor=r.save_person(actors['operador'],'donor',dict(institution_id=actors['operador'].institution_id,
            record_code='PENDING-DONOR',display_name='Ficticio',blood_group='A+',donation_kind='VOLUNTARY',background='Ficticio',
            restrictions='Ninguna registrada',consent_reference='CONSENT',consent_at=(r.now()-timedelta(minutes=1)).isoformat()))
        with pytest.raises(BusinessError) as exc:
            r.create_donation(actors['operador'],dict(donor_id=donor,donation_code='DONA-PENDING'))
        assert exc.value.status==409
        with pytest.raises(BusinessError) as exc:
            r.review_donor(actors['operador'],donor,dict(version_no=1,decision='ELIGIBLE',reason='Sin autorización',human_confirmation='on'))
        assert exc.value.status==403
        r.review_donor(actors['medico'],donor,dict(version_no=1,decision='ELIGIBLE',reason='Revisión humana DEMO',human_confirmation='on'))
        donation=r.create_donation(actors['operador'],dict(donor_id=donor,donation_code='DONA-PENDING'))
        with pytest.raises(BusinessError) as exc:
            r.progress_donation(actors['operador'],donation,dict(version_no=1,status='PROCESSED',observation='Salto de recolección'))
        assert exc.value.status==409


def test_quantity_bound_and_reserved_unit_cannot_be_changed_locally(app,actors,db):
    from src.business.services import inventory as inv
    c=case(app,actors);reserve(app,actors,c)
    row=db.execute('SELECT * FROM blood_unit WHERE resource_id=%s',(c['resource'],)).fetchone();db.commit()
    with app.app_context():
        with pytest.raises(BusinessError) as exc:
            matching.reserve(actors['medico.valle'],c['request'],dict(candidate_id=c['candidate'],version_no=2,reason='Exceso',human_confirmation='on'))
        assert exc.value.status==409
        with pytest.raises(BusinessError) as exc:
            inv.change(actors['operador'],c['resource'],dict(version_no=row['version_no'],current_status='QUARANTINED',location_id=row['location_id'],reason='Cambio local'))
        assert exc.value.status==409


def test_concurrent_reservation_only_one_request_wins(app,actors,db):
    c=case(app,actors)
    with app.app_context():
        second=r.create_request(actors['medico.valle'],dict(request_code='SOL-SECOND',recipient_id=c['recipient'],component_id=c['component'],quantity=1,urgency='URGENT',justification='Solicitud ficticia distinta'))
        eid=matching.evaluate(actors['coordinador'],second)
    candidate=db.execute('SELECT candidate_id FROM blood_candidate WHERE evaluation_id=%s AND resource_id=%s',(eid,c['resource'])).fetchone()['candidate_id'];db.commit()
    barrier=Barrier(2)
    def run(req,candidate):
        with app.app_context():
            barrier.wait(timeout=10)
            try:
                matching.reserve(actors['medico.valle'],req,dict(candidate_id=candidate,version_no=1,reason='Autorización concurrente ficticia',human_confirmation='on'))
                return 'reserved'
            except BusinessError as exc:
                return exc.status
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(run,c['request'],c['candidate']),pool.submit(run,second,candidate)]
        results=[f.result(timeout=20) for f in futures]
    assert sorted(results,key=str)==sorted(['reserved',409],key=str)
    assert db.execute("SELECT count(*) AS n FROM blood_allocation WHERE resource_id=%s AND current_status<>'CANCELLED'",(c['resource'],)).fetchone()['n']==1


def test_reservation_audit_failure_rolls_back(app,actors,db,monkeypatch):
    c=case(app,actors)
    def fail(*a,**kw): raise RuntimeError('Test audit failure')
    monkeypatch.setattr(audit,'record',fail)
    with pytest.raises(RuntimeError): reserve(app,actors,c)
    assert db.execute('SELECT current_status FROM blood_unit WHERE resource_id=%s',(c['resource'],)).fetchone()['current_status']=='AVAILABLE'
    assert db.execute('SELECT count(*) AS n FROM blood_allocation WHERE resource_id=%s',(c['resource'],)).fetchone()['n']==0


def test_stale_route_and_expired_units_are_rejected(app,actors,db):
    c=case(app,actors)
    with app.app_context():
        r.save_route(actors['coordinador'],dict(origin_id=actors['operador'].institution_id,destination_id=actors['medico.valle'].institution_id,distance_km=50,travel_minutes=60,source_reference='Nuevo supuesto'))
        with pytest.raises(BusinessError) as exc: reserve(app,actors,c)
        assert exc.value.status==409
    db.execute("UPDATE blood_unit SET collected_at=now()-interval '2 days',expires_at=now()-interval '1 minute' WHERE resource_id=%s",(c['resource'],));db.commit()
    with app.app_context(): eid=matching.evaluate(actors['coordinador'],c['request'])
    assert not db.execute('SELECT 1 FROM blood_candidate WHERE evaluation_id=%s AND resource_id=%s',(eid,c['resource'])).fetchone()


def test_custody_states_append_only_and_foreign_transport(app,actors,db):
    c=case(app,actors);aid=reserve(app,actors,c)
    with app.app_context():
        departure=r.now()+timedelta(minutes=1)
        sid=logistics.plan(actors['coordinador'],aid,dict(version_no=1,transport_id=actors['traslado'].account_id,vehicle='DEMO',departure_at=departure.isoformat(),eta=(departure+timedelta(minutes=45)).isoformat()))
        for role,target in [('traslado','PREPARED'),('operador.valle','PREPARED'),('operador','ACCEPTED')]:
            with pytest.raises(BusinessError): logistics.step(actors[role],aid,dict(version_no=1,status=target))
        with pytest.raises(BusinessError): r.close_request(actors['medico.valle'],c['request'],dict(version_no=2,status='CLOSED',observation='Prematuro'))
    with pytest.raises(psycopg.errors.CheckViolation):
        db.execute('UPDATE custody_event SET observation=%s WHERE shipment_id=%s',('Reescritura',sid))
    db.rollback()
    with pytest.raises(psycopg.errors.CheckViolation):
        db.execute('DELETE FROM blood_candidate WHERE candidate_id=%s',(c['candidate'],))
    db.rollback()


def test_cancel_releases_resource_and_preserves_audit(app,actors,db):
    c=case(app,actors);aid=reserve(app,actors,c)
    with app.app_context(): logistics.cancel(actors['coordinador'],aid,dict(version_no=1,observation='Cancelación documentada'))
    assert db.execute('SELECT is_available FROM blood_inventory WHERE resource_id=%s',(c['resource'],)).fetchone()['is_available']
    assert db.execute('SELECT current_status FROM blood_allocation WHERE allocation_id=%s',(aid,)).fetchone()['current_status']=='CANCELLED'
    with app.app_context():
        with pytest.raises(BusinessError): reserve(app,actors,c)


def test_migration_is_idempotent_and_preserves_counts(app,db):
    before=db.execute('SELECT count(*) AS n FROM blood_unit').fetchone()['n']
    db.commit()
    with app.app_context(),transaction() as conn: assert migrate(conn)==[]
    assert db.execute('SELECT count(*) AS n FROM blood_unit').fetchone()['n']==before


def test_unsupported_component_requires_manual_review(app,actors,db):
    c=case(app,actors)
    plasma=db.execute("SELECT component_id FROM blood_component WHERE component_code='PLASMA-DEMO'").fetchone()['component_id'];db.commit()
    with app.app_context():
        req=r.create_request(actors['medico.valle'],dict(request_code='SOL-PLASMA',recipient_id=c['recipient'],component_id=plasma,quantity=1,urgency='ROUTINE',justification='Ejercicio de componente no soportado'))
        with pytest.raises(BusinessError) as exc: matching.evaluate(actors['coordinador'],req)
        assert exc.value.status==409


@pytest.mark.parametrize('script', ['regional_browser.cjs', 'filters_browser.cjs', 'improvements_browser.cjs'])
def test_regional_browser(app,actors,db,request,tmp_path,script):
    if not request.config.getoption('--browser'):
        pytest.skip('Requiere --browser, Chrome y Playwright mediante NODE_PATH.')
    import json,os,subprocess
    from pathlib import Path
    from threading import Thread
    from werkzeug.serving import make_server
    app.config['HIGHCHARTS_ENABLED']=True
    def location(iid):
        return str(db.execute('SELECT location_id FROM storage_location JOIN site USING(site_id) WHERE institution_id=%s LIMIT 1',(iid,)).fetchone()['location_id'])
    data=dict(north=str(actors['operador'].institution_id),valley=str(actors['operador.valle'].institution_id),
        northLocation=location(actors['operador'].institution_id),valleyLocation=location(actors['operador.valle'].institution_id),
        transport=str(actors['traslado'].account_id),component=str(db.execute("SELECT component_id FROM blood_component WHERE component_code='RBC-DEMO'").fetchone()['component_id']))
    db.commit()
    if script in ('filters_browser.cjs','improvements_browser.cjs'):
        case(app, actors)
    server=make_server('127.0.0.1',0,app,threaded=True)
    thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        result=subprocess.run(['node',str(Path(__file__).with_name(script))],env={**os.environ,
            'BASE_URL':f'http://127.0.0.1:{server.server_port}','DEMO_PASSWORD':app.config['DEMO_TEST_PASSWORD'],
            'REGIONAL_DATA':json.dumps(data),'BROWSER_ARTIFACTS':str(Path(os.getenv('BROWSER_ARTIFACTS',str(tmp_path)))/script.removesuffix('_browser.cjs'))},
            capture_output=True,text=True,timeout=200)
        assert result.returncode==0,result.stdout+result.stderr
        print(result.stdout)
    finally:
        server.shutdown();thread.join(timeout=5);server.server_close()
