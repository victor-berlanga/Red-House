"""Consulta modal, edición protegida y conservación del ámbito institucional."""
import os
import json
import re
import subprocess
from pathlib import Path
from threading import Thread

from werkzeug.serving import make_server
import pytest

from conftest import csrf
from test_regional import actors, case, reserve

MODAL = {'X-Detail-Modal':'1'}


def test_full_details_and_edit_permissions(app, actors, db, sign_in):
    c=case(app,actors)
    aid=reserve(app,actors,c)
    route=db.execute('SELECT route_id FROM regional_route LIMIT 1').fetchone()['route_id']
    operator=app.test_client(); sign_in(operator)
    for path,expected in [(f"/inventario/{c['resource']}",'Historial de movimientos'),
                          (f"/sangre/personas/donor/{c['donor']}",'SECRETO-CLINICO-ANTECEDENTES'),
                          (f"/sangre/donaciones/{c['donation']}",'Procesamiento ficticio')]:
        response=operator.get(path,headers=MODAL)
        html=response.get_data(as_text=True)
        assert response.status_code==200
        assert 'data-detail-content' in html and expected in html
        assert '<form' not in html and '<input' not in html and '<script' not in html
        assert response.headers['Cache-Control']=='no-store'
    # Un expediente histórico no ofrece edición al operador ni acepta URL manual.
    listing=operator.get('/sangre/personas/donor').get_data(as_text=True)
    assert f"/sangre/personas/donor/{c['donor']}/editar" not in listing
    assert operator.get(f"/sangre/personas/donor/{c['donor']}/editar").status_code==409
    assert operator.get(f"/inventario/{c['resource']}/editar").status_code==409
    outsider=app.test_client(); sign_in(outsider,'operador.valle')
    response=outsider.get(f"/sangre/personas/donor/{c['donor']}",headers=MODAL)
    assert response.status_code==404 and b'SECRETO-CLINICO' not in response.data
    assert outsider.get(f"/inventario/{c['resource']}/editar").status_code==404
    auditor=app.test_client(); sign_in(auditor,'auditor')
    for path in [f"/inventario/{c['resource']}/editar", f"/sangre/personas/donor/{c['donor']}/editar",
                 f"/sangre/donaciones/{c['donation']}/editar", f"/sangre/solicitudes/{c['request']}/editar",
                 f'/sangre/traslados/{aid}/editar', f'/sangre/rutas/{route}/editar', '/administracion/users']:
        response=auditor.get(path)
        assert response.status_code==403,path
        assert b'data-access-error' in response.data
        assert 'No tienes los permisos requeridos' in response.get_data(as_text=True)
        modal=auditor.get(path,headers=MODAL)
        assert modal.status_code==403 and b'data-detail-content' in modal.data
        assert b'<form' not in modal.data
    for path in [f"/sangre/solicitudes/{c['request']}",f'/sangre/traslados/{aid}']:
        response=auditor.get(path,headers=MODAL)
        assert response.status_code==200
        assert b'SECRETO-CLINICO' not in response.data and b'<form' not in response.data
    response=auditor.post(f"/inventario/{c['resource']}/editar",data={'csrf_token':csrf(auditor,'/panel')})
    assert response.status_code==403
    assert db.execute("SELECT count(*) AS n FROM audit_event WHERE outcome='DENIED'").fetchone()['n']>=9


def test_admin_detail_allowlist_and_scoped_edit(app,db,sign_in):
    client=app.test_client(); sign_in(client,'admin')
    for entity,table,key in [('users','user_account','account_id'),('institutions','institution','institution_id'),('sites','site','site_id'),('locations','storage_location','location_id'),('components','blood_component','component_id')]:
        identifier=db.execute(f'SELECT {key} FROM {table} LIMIT 1').fetchone()[key]
        response=client.get(f'/administracion/{entity}/{identifier}',headers=MODAL)
        assert response.status_code==200
        assert b'<form' not in response.data and b'password' not in response.data and b'scrypt:' not in response.data
        assert client.get(f'/administracion/{entity}/{identifier}/editar').status_code==200
    # El administrador institucional puede consultar el catálogo regional, pero no editarlo.
    institution=db.execute("SELECT institution_id FROM institution WHERE institution_code='DEMO-NORTE'").fetchone()['institution_id']
    db.execute("UPDATE account_role SET institution_id=%s,region_name=NULL WHERE account_id=(SELECT account_id FROM user_account WHERE login_email='admin@red-house.test')",(institution,)); db.commit()
    sign_in(client,'admin')
    assert client.get(f'/administracion/components/{identifier}',headers=MODAL).status_code==200
    assert client.get(f'/administracion/components/{identifier}/editar').status_code==403
    assert client.get('/administracion/components/nuevo').status_code==403
    audit=app.test_client(); sign_in(audit,'auditor')
    event=db.execute('SELECT event_id FROM audit_event LIMIT 1').fetchone()['event_id']
    response=audit.get(f'/auditoria/{event}',headers=MODAL)
    assert response.status_code==200 and b'Correlaci' in response.data and b'<form' not in response.data
    assert client.get(f'/auditoria/{event}',headers=MODAL).status_code==403


def test_details_browser(app,actors,db,sign_in,request,tmp_path):
    if not request.config.getoption('--browser'):
        pytest.skip('Usa --browser con Chrome y Playwright.')
    c=case(app,actors)
    server=make_server('127.0.0.1',0,app,threaded=True)
    thread=Thread(target=server.serve_forever,daemon=True); thread.start()
    try:
        result=subprocess.run(['node',str(Path(__file__).with_name('details_browser.cjs'))],env={**os.environ,
            'BASE_URL':f'http://127.0.0.1:{server.server_port}','DEMO_PASSWORD':app.config['DEMO_TEST_PASSWORD'],
            'DETAIL_DATA':json.dumps({k:str(v) for k,v in c.items()}),
            'BROWSER_ARTIFACTS':os.getenv('BROWSER_ARTIFACTS',str(tmp_path))},capture_output=True,text=True,timeout=120)
        assert result.returncode==0,result.stdout+result.stderr
    finally:
        server.shutdown();thread.join(timeout=5);server.server_close()


def test_route_edit_preserves_identity_and_stale_form(app,actors,db,sign_in):
    case(app,actors)
    row=db.execute('SELECT * FROM regional_route LIMIT 1').fetchone()
    client=app.test_client();sign_in(client,'coordinador')
    path=f"/sangre/rutas/{row['route_id']}/editar"
    assert client.get(path).status_code==200
    assert b'<form' not in client.get(f"/sangre/rutas/{row['route_id']}",headers=MODAL).data
    data={'audit_reason':'Actualizar estimación de prueba','version_no':row['version_no'],'distance_km':42,'travel_minutes':60,'source_reference':'Referencia actualizada',
          'origin_id':str(row['destination_id']),'destination_id':str(row['origin_id']),'csrf_token':csrf(client,path)}
    assert client.post(path,data=data).status_code==302
    saved=db.execute('SELECT * FROM regional_route WHERE route_id=%s',(row['route_id'],)).fetchone()
    assert saved['origin_id']==row['origin_id'] and saved['destination_id']==row['destination_id']
    assert saved['distance_km']==42 and saved['version_no']==row['version_no']+1
    response=client.post(path,data={**data,'distance_km':99})
    assert response.status_code==409
    assert f'action="{path}"' in response.get_data(as_text=True)
    assert 'value="99"' in response.get_data(as_text=True)
    assert db.execute('SELECT distance_km FROM regional_route WHERE route_id=%s',(row['route_id'],)).fetchone()['distance_km']==42
