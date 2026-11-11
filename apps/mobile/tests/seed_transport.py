"""Add a fresh synthetic journey to an already running private lab through real APIs only."""
import json,sys
from pathlib import Path
from datetime import datetime,timezone,timedelta
from uuid import uuid4
import requests
path=Path(sys.argv[1]);lab=json.loads(path.read_text());tokens={}
def date(minutes=0):return (datetime.now(timezone.utc)+timedelta(minutes=minutes)).isoformat()
def call(service,path,body=None,user='coordinator1'):
    headers={'Accept':'application/json','Idempotency-Key':str(uuid4())}
    if user:headers['Authorization']='Bearer '+tokens[user]
    r=requests.request('POST' if body is not None else 'GET',lab['gateway']+'/services/'+service+path,json=body,headers=headers,verify=lab['ca'],timeout=30)
    if r.status_code>=300:raise RuntimeError(f'{service} {path}: {r.status_code} '+r.json().get('error',{}).get('code',''))
    return r.json()['data']
for user in ['operator1','medical1','medical2','coordinator1']:
    tokens[user]=call('identidad-acceso','/api/v1/auth/login',{'username':user,'password':lab['password']},None)['access_token']
unit=call('inventario','/api/v1/resources',{'folio':'MOB-'+uuid4().hex[:15],'kind':'BLOOD','component':'RBC','blood_group':'O-','expires_at':date(2880)},'operator1')
unit=call('inventario',f"/api/v1/resources/{unit['id']}/release",{'version':unit['version'],'human_confirmation':True,'reason':'Liberación humana sintética en laboratorio'},'medical1')
recipient=call('receptores','/api/v1/recipients',{'folio':'MOB-'+uuid4().hex[:15],'display_name':'Paciente sintético móvil','kind':'BLOOD','blood_group':'A+','studies':'Estudios sintéticos para integración'},'medical2')
demand=call('receptores','/api/v1/requests',{'recipient_id':recipient['id'],'component':'RBC','quantity':1,'urgency':3},'medical2')
evaluation=call('compatibilidad','/api/v1/evaluations',{'request_id':demand['id']},'medical2')
call('compatibilidad',f"/api/v1/evaluations/{evaluation['id']}/reviews",{'resource_id':unit['id'],'decision':'FAVORABLE','human_confirmation':True,'reason':'Dictamen sintético autorizado para laboratorio'},'medical2')
allocation=call('inventario','/api/v1/reservations',{'evaluation_id':evaluation['id'],'resource_id':unit['id'],'human_confirmation':True,'reason':'Asignación humana sintética para integración'},'medical2')
if '--planning-only' in sys.argv:
    lab.update(planning_reservation_id=allocation['reservation']['id'])
    path.write_text(json.dumps(lab));path.chmod(0o600)
    print('Fresh synthetic reservation ready for native planning.')
    sys.exit(0)
shipment=call('transporte','/api/v1/shipments',{'reservation_id':allocation['reservation']['id'],'transport_user_id':lab['accounts']['transport1'],'departure_at':date(1),'eta':date(30),'human_confirmation':True,'reason':'Programación sintética de laboratorio'})
shipment=call('transporte',f"/api/v1/shipments/{shipment['id']}/transitions",{'state':'PREPARED','version':shipment['version'],'human_confirmation':True,'reason':'Preparación sintética para prueba móvil'},'operator1')
lab.update(shipment_id=shipment['id'],resource_id=unit['id']);path.write_text(json.dumps(lab));path.chmod(0o600)
print('Fresh synthetic task prepared through JSON APIs.')
