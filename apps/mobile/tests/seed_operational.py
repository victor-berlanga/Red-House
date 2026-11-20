"""Synthetic, nonclinical fixtures for native operator and medical journeys, through JSON only."""
import json, sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
from uuid import uuid4
import requests

path=Path(sys.argv[1]);lab=json.loads(path.read_text());tokens={}
def date(minutes=0):return (datetime.now(timezone.utc)+timedelta(minutes=minutes)).isoformat()
def call(service,route,body=None,user='medical1'):
    headers={'Accept':'application/json','Idempotency-Key':str(uuid4())}
    if user:headers['Authorization']='Bearer '+tokens[user]
    if body and 'password' in body:headers['X-RedHouse-Client']='web'  # acceso por aplicación
    response=requests.request('POST' if body is not None else 'GET',lab['gateway']+'/services/'+service+route,json=body,headers=headers,verify=lab['ca'],timeout=30)
    if response.status_code>=300:raise RuntimeError(f'{service} {route}: {response.status_code} '+response.json().get('error',{}).get('code',''))
    return response.json()['data']
for user in ['operator1','medical1']:
    tokens[user]=call('identidad-acceso','/api/v1/auth/login',{'username':user,'password':lab['password']},None)['access_token']
folio='MOB-COLD-'+uuid4().hex[:12]
unit=call('inventario','/api/v1/resources',{'folio':folio,'kind':'BLOOD','component':'RBC','blood_group':'O-','expires_at':date(2880)},'operator1')
profile=call('compatibilidad','/api/v1/laboratory/profiles',{'name':'Prueba móvil '+uuid4().hex[:8],'kind':'BLOOD','component':'RBC','version':1,'required_tests':['ABO'],'source':'Fixture sintético de interfaz; sin aplicación clínica','synthetic':True,'effective_at':date(-1)})
equipment=call('inventario','/api/v1/cold/equipment',{'label':'Equipo ficticio '+uuid4().hex[:8],'location':'Laboratorio aislado','calibration_reference':'CAL-SINTETICA'},'operator1')
# Arbitrary test interval, explicitly synthetic; never a clinical conservation recommendation.
cold=call('inventario','/api/v1/cold/profiles',{'kind':'BLOOD','component':'RBC','minimum_c':0,'maximum_c':10,'max_gap_seconds':3600,'source':'Intervalo arbitrario solo para probar captura de interfaz','synthetic':True,'version':1,'effective_at':date(-1)})
call('inventario',f"/api/v1/resources/{unit['id']}/controls",{'version':unit['version'],'lab_profile_id':profile['id'],'cold_equipment_id':equipment['id'],'cold_profile_id':cold['id'],'human_confirmation':True,'reason':'Vinculación sintética para verificar formularios; no liberar'})
identifier='MUESTRA-MOVIL-'+uuid4().hex[:12]
sample=call('compatibilidad','/api/v1/laboratory/samples',{'resource_id':unit['id'],'profile_id':profile['id'],'identifier':identifier,'collected_at':date(-1)})
result=call('compatibilidad',f"/api/v1/laboratory/samples/{sample['id']}/completeness")
assert result['synthetic'] and not result['complete'] and 'ABO' in result['missing'] and not result['clinical_enabled']
lab.update(operational_resource_id=unit['id'],operational_folio=folio,operational_sample_id=sample['id'],operational_sample_identifier=identifier)
path.write_text(json.dumps(lab));path.chmod(0o600)
print('Synthetic controlled unit and incomplete sample prepared through real JSON APIs.')
