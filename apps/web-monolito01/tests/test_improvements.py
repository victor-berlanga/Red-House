"""Regresiones de captura, filtros parciales, ámbito, horario y coste de consultas."""
import json
import os
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from time import perf_counter

import psycopg
import pytest

from conftest import csrf
from test_regional import actors, case, reserve
from src.business import validators as v
from src.business.access import BusinessError
from src.business.services import regional as r, logistics, regional_reporting


def test_timezone_and_multiline_validation():
    assert v.timestamp({'at':'2026-09-14T08:30','_timezone':'America/Monterrey'},'at') == datetime(2026,9,14,14,30,tzinfo=timezone.utc)
    assert v.timestamp({'at':'2026-09-14T08:30+02:00','_timezone':'America/Monterrey'},'at').hour == 6
    for at,zone in [('2026-09-14T08:30','Invalid/Zone'),('2021-10-31T01:30','America/Monterrey'),('2021-04-04T02:30','America/Monterrey')]:
        with pytest.raises(BusinessError): v.timestamp({'at':at,'_timezone':zone},'at')
    assert v.paragraph({'note':'Primera línea\nSegunda línea'},'note','nota') == 'Primera línea\nSegunda línea'
    with pytest.raises(BusinessError): v.text({'note':'Primera\nSegunda'},'note','nombre')
    with pytest.raises(BusinessError): v.paragraph({'note':'Dato\x00'},'note','nota')


def test_regional_validation_keeps_fields_and_locked_details(app,actors,db,sign_in):
    client=app.test_client();sign_in(client)
    data=dict(institution_id=actors['operador'].institution_id,record_code='!',display_name='<Persona de prueba>',blood_group='O-',
        restrictions='Primera línea\nSegunda línea',background='Antecedentes conservados',donation_kind='VOLUNTARY',
        consent_reference='CONSENT-TEST',consent_at='2020-01-01T08:00',_timezone='America/Monterrey')
    response=client.post('/sangre/personas/donor',data={**data,'csrf_token':csrf(client)})
    assert response.status_code==400
    html=response.get_data(as_text=True)
    assert 'name="display_name" type="text" value="&lt;Persona de prueba&gt;"' in html
    assert 'Primera línea\nSegunda línea</textarea>' in html
    assert 'action="/sangre/personas/donor"' in html
    assert 'name="_timezone" value="America/Monterrey"' in html
    response=client.post('/sangre/personas/donor',data={**data,'record_code':'NEW-OK','csrf_token':csrf(client)})
    assert response.status_code==302
    row=db.execute("SELECT consent_at,restrictions FROM donor WHERE record_code='NEW-OK'").fetchone()
    assert row['consent_at'].hour==14 and '\n' in row['restrictions']
    c=case(app,actors)
    html=client.get(f"/sangre/personas/donor/{c['donor']}").get_data(as_text=True)
    assert 'Expediente de consulta' in html and 'Actualizar expediente' not in html
    med=app.test_client();sign_in(med,'medico.valle')
    html=med.get(f"/sangre/personas/recipient/{c['recipient']}").get_data(as_text=True)
    assert 'Expediente de consulta' in html and 'Actualizar expediente' not in html
    # Error en una acción hija vuelve a su detalle; nunca cambia la versión enviada.
    response=med.post(f"/sangre/solicitudes/{c['request']}/reservar",data={'candidate_id':c['candidate'],'reason':'Conservar motivo','human_confirmation':'on','version_no':999,'csrf_token':csrf(med)})
    html=response.get_data(as_text=True)
    assert response.status_code==409 and 'Conservar motivo</textarea>' in html
    assert 'name="version_no" value="999"' in html
    assert f'action="/sangre/solicitudes/{c["request"]}/reservar"' in html
    assert not db.execute('SELECT 1 FROM blood_allocation WHERE request_id=%s',(c['request'],)).fetchone()
    auditor=app.test_client();sign_in(auditor,'auditor')
    denied=auditor.get(f"/sangre/personas/recipient/{c['recipient']}")
    assert denied.status_code==403 and b'SECRETO-CLINICO' not in denied.data


def test_filters_options_permissions_and_dashboard_links(app,actors,db,sign_in):
    c=case(app,actors);aid=reserve(app,actors,c)
    op=app.test_client();sign_in(op)
    # Solo donantes con revisión favorable; nombres restringidos al operador institucional.
    with app.app_context():
        pending=r.save_person(actors['operador'],'donor',dict(institution_id=actors['operador'].institution_id,record_code='PENDING-X',display_name='Pendiente',blood_group='O-',restrictions='Ninguna',background='Antecedentes',donation_kind='VOLUNTARY',consent_reference='REF-X',consent_at='2020-01-01'))
    html=op.get('/sangre/donaciones').get_data(as_text=True)
    assert f'<option value="{pending}"' not in html
    assert f'<option value="{c["donor"]}"' in html and 'DON-01 · Persona ficticia' in html
    med=app.test_client();sign_in(med,'medico.valle')
    for route,term in [('/sangre/solicitudes?urgency=ROUTINE','SOL-01'),('/sangre/donaciones?status=REGISTERED','DONA-01')]:
        response=(med if 'solicitudes' in route else op).get(route,headers={'X-Filter-Fragment':'1'})
        assert response.status_code==200 and term.encode() not in response.data
        assert b'data-filter-results' in response.data and b'<html' not in response.data and b'<form' not in response.data
    assert op.get('/sangre/donaciones?status=INVALID').status_code==400
    assert med.get('/sangre/solicitudes?urgency=INVALID').status_code==400
    assert op.get('/sangre/traslados?q=NO-MATCH',headers={'X-Filter-Fragment':'1'}).data.count(b'data-result-count="0"')==1
    transport=app.test_client();sign_in(transport,'traslado')
    assert str(aid).encode() not in transport.get('/sangre/traslados',headers={'X-Filter-Fragment':'1'}).data
    assert b'SECRETO-CLINICO' not in op.get('/sangre/panel-regional').data
    # El KPI de reservas del origen es cero; el destino tiene una.
    assert b'data-result-count="0"' in op.get('/sangre/traslados?status=ACTIVE&direction=destination',headers={'X-Filter-Fragment':'1'}).data
    assert b'data-result-count="1"' in med.get('/sangre/traslados?status=ACTIVE&direction=destination',headers={'X-Filter-Fragment':'1'}).data
    anon=app.test_client();assert anon.get('/inventario',headers={'X-Filter-Fragment':'1'}).status_code==302


def test_fragment_cost_and_batched_alerts(app,actors,db,sign_in,monkeypatch,tmp_path):
    c=case(app,actors)
    original=psycopg.Connection.execute
    calls=[]
    def counted(conn,query,*args,**kwargs):
        calls.append(1)
        return original(conn,query,*args,**kwargs)
    monkeypatch.setattr(psycopg.Connection,'execute',counted)
    client=app.test_client();sign_in(client)
    calls.clear();start=perf_counter();full=client.get('/inventario');full_ms=(perf_counter()-start)*1000;full_queries=len(calls)
    calls.clear();start=perf_counter();partial=client.get('/inventario',headers={'X-Filter-Fragment':'1'});partial_ms=(perf_counter()-start)*1000;partial_queries=len(calls)
    assert full.status_code==partial.status_code==200
    assert len(partial.data)<len(full.data) and partial_queries<full_queries
    assert b'data-filter-summary' in partial.data and b'<html' not in partial.data
    with app.app_context():
        calls.clear();start=perf_counter();one=regional_reporting.dashboard(actors['coordinador']);one_ms=(perf_counter()-start)*1000;one_queries=len(calls)
        for n in range(2,21):
            r.create_request(actors['medico.valle'],dict(request_code=f'PERF-{n:02}',recipient_id=c['recipient'],component_id=c['component'],quantity=1,urgency='URGENT',justification='Prueba de volumen de consultas'))
        calls.clear();start=perf_counter();many=regional_reporting.dashboard(actors['coordinador']);many_ms=(perf_counter()-start)*1000;many_queries=len(calls)
    assert one_queries==many_queries
    assert len(many['trends'])==7 and sum(x['requests'] for x in many['trends'])==20
    assert len(many['opportunities'])==10
    assert all(x['traceability_code']=='UNIT-01' for x in many['opportunities'])
    result=dict(inventory=dict(full_bytes=len(full.data),fragment_bytes=len(partial.data),full_queries=full_queries,fragment_queries=partial_queries,full_ms=round(full_ms,2),fragment_ms=round(partial_ms,2)),dashboard=dict(one_request_queries=one_queries,twenty_request_queries=many_queries,one_ms=round(one_ms,2),twenty_ms=round(many_ms,2)),note='Muestra local, sin carga concurrente; tiempos orientativos, no benchmark de producción.')
    output=Path(os.getenv('BROWSER_ARTIFACTS',str(tmp_path)));output.mkdir(parents=True,exist_ok=True)
    (output/'Performance.json').write_text(json.dumps(result,indent=2)+'\n')


def test_timezone_preference_and_local_audit_day(app,actors,db,sign_in):
    client=app.test_client();sign_in(client,'auditor')
    response=client.post('/preferencias/horario',data={'timezone':'America/Monterrey','next':'/auditoria','csrf_token':csrf(client)})
    assert response.status_code==302
    html=client.get('/auditoria').get_data(as_text=True)
    assert 'Fecha America/Monterrey' in html
    # 02 UTC del día siguiente pertenece al día anterior de Monterrey.
    db.execute("INSERT INTO audit_event(action,entity_type,entity_reference,region_name,reason,occurred_at,correlation_id,outcome) VALUES ('READ','TIME_TEST','ZONE-CHECK','DEMO-NORTE','Prueba de horario','2026-09-15 02:00+00',gen_random_uuid(),'SUCCESS')")
    db.commit()
    assert b'ZONE-CHECK' in client.get('/auditoria?q=ZONE-CHECK&date=2026-09-14').data
    assert b'data-result-count="0"' in client.get('/auditoria?q=ZONE-CHECK&date=2026-09-15').data
    response=client.post('/preferencias/horario',data={'timezone':'UTC','next':'https://example.org','csrf_token':csrf(client)})
    assert response.location=='/panel'
    assert client.post('/preferencias/horario',data={'timezone':'Invalid','csrf_token':csrf(client)}).status_code==400
