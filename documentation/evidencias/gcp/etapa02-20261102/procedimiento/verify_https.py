import ast,base64,hashlib,hmac,json,os,struct,sys,time
from pathlib import Path
from uuid import uuid4
from datetime import datetime,timezone,timedelta
import requests
from jsonschema import Draft202012Validator,FormatChecker
root=Path.cwd();sys.path.insert(0,str(root/'apps/services'))
from redhouse.xml_response import validate_response
out=root/'documentation/evidencias/gcp/etapa02-20261102'
private=root/'.local/gcp-update-20261102'
old=json.loads((root/'.local/gcp-update-20261031/demo-input.json').read_text())
factors={v['username']:v['secret'] for v in old['accounts'].values() if 'secret' in v}
base='https://34.18.186.116';tokens={};checks=[]
def totp(secret):
 raw=hmac.new(base64.b32decode(secret),struct.pack('>Q',int(time.time())//30),hashlib.sha1).digest();i=raw[-1]&15
 return str((struct.unpack('>I',raw[i:i+4])[0]&0x7fffffff)%1000000).zfill(6)
def call(service,path,body=None,user='medical1',fmt='json'):
 headers={'Accept':'application/'+fmt,'Idempotency-Key':uuid4().hex}
 if user:headers['Authorization']='Bearer '+tokens[user]
 r=requests.request('POST' if body is not None else 'GET',base+'/services/'+service.replace('_','-')+path,headers=headers,json=body,timeout=45)
 assert r.ok,(service,path,r.status_code)
 if body is not None and '/auth/' not in path:
  with (private/'mutations.jsonl').open('a') as log:log.write(json.dumps({'service':service,'path':path,'data':r.json()['data']})+'\n')
 return r
services=['identidad_acceso','donantes','receptores','inventario','compatibilidad','priorizacion_geografia','transporte','custodia','alertas','auditoria','monitoreo','documentos']
health=[]
for s in services:
 module='servicio_monitoreo' if s=='monitoreo' else 'ms_'+s
 tree=ast.parse((root/'apps/services'/module/'__init__.py').read_text())
 expected=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='VERSION' for t in n.targets))
 for endpoint in ['live','ready']:
  r=requests.get(base+'/services/'+s.replace('_','-')+'/health/'+endpoint,timeout=45);assert r.ok,(s,endpoint,r.status_code)
  d=r.json();assert d['data']['version']==expected,(s,'version',expected)
  health.append({'service':s,'endpoint':endpoint,'status':r.status_code,'response':d})
(out/'health-final.json').write_text(json.dumps(health,indent=2)+'\n')
for user in ['admin1','medical1','medical2','coordinator1','operator1','transport1','auditor1']:
 data={'username':user,'password':old['password']}
 if user in factors:data['otp']=totp(factors[user])
 tokens[user]=call('identidad_acceso','/api/v1/auth/login',data,user=None).json()['data']['access_token']
metadata=json.loads((root/'documentation/evidencias/gcp/correccion-20261031/browser-summary.json').read_text())
# Use an authorized existing shipment from the owner, never a credential-bearing log.
ships=call('transporte','/api/v1/shipments',user='coordinator1').json()['data']['items'];assert ships
paths={'identidad_acceso':('/api/v1/users','admin1'),'donantes':('/api/v1/campaigns','operator1'),'receptores':('/api/v1/requests','medical2'),'inventario':('/api/v1/resources','operator1'),'compatibilidad':('/api/v1/evaluations','medical2'),'priorizacion_geografia':('/api/v1/routes','coordinator1'),'transporte':('/api/v1/shipments','coordinator1'),'custodia':('/api/v1/chains/{identifier}','transport1'),'alertas':('/api/v1/alerts','operator1'),'auditoria':('/api/v1/events','auditor1'),'monitoreo':('/api/v1/status','admin1'),'documentos':('/api/v1/export-jobs','medical2')}
paths.update({'compatibilidad_sources':('/api/v1/laboratory/reference-sources','medical1'),'priorizacion_geografia_sources':('/api/v1/regional-graph-sources','medical1')})
for label,(path,user) in paths.items():
 service=label.removesuffix('_sources');module='servicio_monitoreo' if service=='monitoreo' else 'ms_'+service
 contracts=root/'apps/services'/module/'contracts';spec=json.loads((contracts/'openapi.json').read_text());op=spec['paths'][path]['get']['operationId'];schema=json.loads((contracts/(op+'.response.json')).read_text())
 for fmt in ['json','xml']:
  r=call(service,path.replace('{identifier}',ships[0]['id']),user=user,fmt=fmt)
  if fmt=='xml':validate_response(r.content,schema)
  else:Draft202012Validator(schema,format_checker=FormatChecker()).validate(r.json())
  checks.append({'operation':op,'format':fmt,'status':'passed'})
sources=call('compatibilidad','/api/v1/laboratory/reference-sources').json()['data'];assert sources['catalogues'][0]['available']
now=lambda delta=0:(datetime.now(timezone.utc)+timedelta(minutes=delta)).isoformat()
profile=call('compatibilidad','/api/v1/laboratory/profiles',{'name':'Comprobación académica GCP 0.4.4','kind':'ORGAN','component':'KIDNEY','version':1,'required_tests':['HLA'],'required_loci':['A'],'source':'IPD público; datos ficticios para comprobar despliegue','synthetic':True,'effective_at':now(-10),'evidence_rules':['HLA-NAMING-2010-SYNTAX2'],'policy':{'require_hla_catalogue':True}}).json()['data']
recipient=call('receptores','/api/v1/recipients',{'folio':'GCP044-'+uuid4().hex[:12],'display_name':'Receptor ficticio de comprobación técnica','kind':'ORGAN','organ_type':'KIDNEY','blood_group':'O+','studies':'Datos ficticios, sin evaluación clínica'}).json()['data']
sample=call('compatibilidad','/api/v1/laboratory/samples',{'recipient_id':recipient['id'],'profile_id':profile['id'],'identifier':'GCP044-'+uuid4().hex,'collected_at':now(-5)}).json()['data']
call('compatibilidad','/api/v1/laboratory/samples/'+sample['id']+'/receive',{'version':1,'decision':'RECEIVED','human_confirmation':True,'reason':'Verificación técnica autorizada, datos ficticios'})
result=call('compatibilidad','/api/v1/laboratory/results',{'sample_id':sample['id'],'test_code':'HLA','result_state':'REPORTED','method':'Declaración ficticia','laboratory':'Laboratorio ficticio','reference':'Verificación técnica GCP','measured_at':now(-2),'issued_at':now(-1),'hla':{'nomenclature':'HLA-colon-2010','nomenclature_version':'2010:syntax-2','resolution':'Cuatro campos','catalogue_version':'3.66.0','loci':[{'locus':'A','alleles':['A*01:01:01:01']} ]}}).json()['data']
assert result['catalogue_check']['entries'][0]['allele_id']=='HLA00001';assert result['catalogue_check']['clinical_approval'] is False
read=call('compatibilidad','/api/v1/laboratory/results/'+result['id']).json()['data'];assert read['catalogue_check']==result['catalogue_check']
complete=call('compatibilidad','/api/v1/laboratory/samples/'+sample['id']+'/completeness').json()['data'];assert not complete['clinical_approval']
graph=call('priorizacion_geografia','/api/v1/regional-graphs/from-reference',{'reference_id':'NL-OSRM-20261102'}).json()['data']
run=call('priorizacion_geografia','/api/v1/decision-runs',{'branch':'ALG-02-GEO','graph_id':graph['id'],'origin':'MONTERREY','destination':'GUADALUPE'}).json()['data']
replay=call('priorizacion_geografia','/api/v1/decision-runs/'+run['id']+'/reproduce').json()['data']
assert 'OpenStreetMap' in json.dumps(replay);assert 'REGIONAL-OSM-DIJKSTRA-3.0' in json.dumps(run)
report={'passed':True,'contracts':checks,'new_fictitious_records':{'profile':profile['id'],'recipient':recipient['id'],'sample':sample['id'],'result':result['id'],'graph':graph['id'],'run':run['id']},'hla_persisted':True,'clinical_approval':False,'road_reproduced':True}
(out/'api-final.json').write_text(json.dumps(report,indent=2)+'\n')
old.update(tokens=tokens,output=str(out),stage02=report['new_fictitious_records'])
(private/'browser-input.json').write_text(json.dumps(old)+'\n');(private/'browser-input.json').chmod(0o600)
print(json.dumps({'passed':True,'contracts':len(checks),'health_checks':len(health),'clinical_approval':False}))
