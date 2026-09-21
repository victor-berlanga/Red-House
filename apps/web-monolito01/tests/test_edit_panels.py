"""Motivos obligatorios, persistencia atómica y recuperación de formularios."""
import pytest
from werkzeug.datastructures import MultiDict

from conftest import csrf
from test_regional import actors, case, reserve
from src.business.access import BusinessError
from src.business.services import administration, regional, logistics
from src.data_access.repositories import network


@pytest.mark.parametrize('entity', ['institutions', 'sites', 'locations', 'components', 'users'])
def test_admin_edit_requires_audited_reason(app, actors, db, entity):
    actor=actors['admin']
    table,key,_=network.ENTITIES[entity]
    identifier=db.execute(f'SELECT {key} FROM {table} LIMIT 1').fetchone()[key]
    before=network.one(db,entity,actor,identifier)
    data=MultiDict(before)
    if entity=='institutions':
        details=network.institution_details(db,identifier)
        data.update({k:v for k,v in details.items() if k!='capabilities'})
        data.setlist('capabilities',details['capabilities'])
    if entity in ('locations','components'): data['is_active']='on'
    if entity=='users':
        data['scope']=str(before['institution_id']) if before['institution_id'] else 'REGIONAL'
        data['password']=''
    db.commit()
    with app.app_context():
        for reason in ('', '   ', 'x'*241):
            with pytest.raises(BusinessError) as error:
                administration.save(entity,actor,MultiDict([*data.items(multi=True),('audit_reason',reason)]),identifier)
            assert error.value.field=='audit_reason'
            assert db.execute(f'SELECT version_no FROM {table} WHERE {key}=%s',(identifier,)).fetchone()['version_no']==before['version_no']
        data['audit_reason']='Corrección administrativa\nRevisada por responsable'
        administration.save(entity,actor,data,identifier)
    event=db.execute("SELECT reason FROM audit_event WHERE entity_reference=%s AND action='UPDATE' ORDER BY occurred_at DESC LIMIT 1",(str(identifier),)).fetchone()
    assert event['reason']==data['audit_reason']


@pytest.mark.parametrize('kind,role', [('donor','operador'),('recipient','medico.valle')])
def test_person_reason_and_sensitive_data_not_duplicated(app,actors,db,kind,role):
    actor=actors[role]
    data=dict(institution_id=actor.institution_id,record_code='EDIT-TEST',display_name='Prueba reservada',
              blood_group='O-',restrictions='Contenido clínico reservado',background='Antecedentes reservados',
              donation_kind='VOLUNTARY',consent_reference='CONSENT-TEST',consent_at='2020-01-01',
              requirement='Requerimiento reservado',studies='Estudios reservados',current_status='ACTIVE')
    with app.app_context():
        identifier=regional.save_person(actor,kind,data)
        changed={**data,'version_no':1,'display_name':'Corrección reservada'}
        with pytest.raises(BusinessError) as error: regional.save_person(actor,kind,changed,identifier)
        assert error.value.field=='audit_reason'
        assert db.execute(f'SELECT version_no FROM {kind} WHERE {kind}_id=%s',(identifier,)).fetchone()['version_no']==1
        regional.save_person(actor,kind,{**changed,'audit_reason':'Corrección autorizada'},identifier)
    event=db.execute("SELECT * FROM audit_event WHERE entity_reference=%s AND action='UPDATE'",(str(identifier),)).fetchone()
    assert event['reason']=='Corrección autorizada'
    assert 'reservad' not in str(event)


def test_parameter_reason_rollback_and_stale_version(client,sign_in,db):
    sign_in(client,'admin')
    path='/administracion/configuracion/parametros'
    payload={'version_no':1,'hours':36,'csrf_token':csrf(client,path)}
    response=client.post(path,data=payload)
    assert response.status_code==400
    assert b'value="36"' in response.data
    assert db.execute('SELECT count(*) AS n FROM parameter_version').fetchone()['n']==1
    payload['audit_reason']='Aviso anticipado autorizado'
    assert client.post(path,data=payload).status_code==302
    response=client.post(path,data={**payload,'hours':40})
    assert response.status_code==409
    assert b'name="version_no" value="1"' in response.data
    assert b'value="40"' in response.data
    assert b'Aviso anticipado autorizado' in response.data


def test_route_and_planning_require_reason_atomically(app,actors,db):
    c=case(app,actors)
    aid=reserve(app,actors,c)
    route=db.execute('SELECT * FROM regional_route LIMIT 1').fetchone()
    with app.app_context():
        with pytest.raises(BusinessError) as error:
            regional.save_route(actors['coordinador'],{**route,'distance_km':99},route['route_id'])
        assert error.value.field=='audit_reason'
        # La ruta alternativa de registro/actualización tampoco permite omitir el motivo.
        with pytest.raises(BusinessError): regional.save_route(actors['coordinador'],{**route,'distance_km':99})
        assert db.execute('SELECT distance_km FROM regional_route WHERE route_id=%s',(route['route_id'],)).fetchone()['distance_km']==route['distance_km']
        from datetime import timedelta
        departure=regional.now()+timedelta(minutes=1)
        payload=dict(version_no=1,transport_id=actors['traslado'].account_id,vehicle='DEMO',
                     departure_at=departure.isoformat(),eta=(departure+timedelta(minutes=45)).isoformat())
        with pytest.raises(BusinessError) as error: logistics.plan(actors['coordinador'],aid,payload)
        assert error.value.field=='audit_reason'
        assert not db.execute('SELECT 1 FROM shipment WHERE allocation_id=%s',(aid,)).fetchone()
        assert db.execute('SELECT current_status FROM blood_allocation WHERE allocation_id=%s',(aid,)).fetchone()['current_status']=='RESERVED'
        logistics.plan(actors['coordinador'],aid,{**payload,'audit_reason':'Programación autorizada'})
    assert db.execute("SELECT reason FROM audit_event WHERE entity_reference=%s AND action='ASSIGN'",(str(aid),)).fetchone()['reason']=='Programación autorizada'
