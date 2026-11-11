"""Run in the deployed web container; credentials on stdin, sanitized evidence only.

Creates/revokes two test phone registrations. Does not write clinical records,
change shipment state, publish positions, send push or touch GCS objects.
"""
import json, sys, uuid, ssl, socket
from datetime import datetime, timezone
import requests, websocket
from contextlib import closing

origin = 'https://34.18.186.116'
private = json.load(sys.stdin)
checks = []
tokens = {}

def call(service, path, user=None, body=None, expected=(200,201,202,204)):
    headers={'Accept':'application/json'}
    if user: headers['Authorization']='Bearer '+tokens[user]
    if body is not None: headers['Idempotency-Key']=str(uuid.uuid4())
    r=requests.request('POST' if body is not None else 'GET',origin+'/services/'+service+path,
                       headers=headers,json=body,timeout=30)
    assert r.status_code in expected, (service,path,r.status_code)
    if r.status_code == 204: return None
    assert 'application/json' in r.headers.get('Content-Type',''),(service,path,'non-JSON')
    data=r.json()
    checks.append({'service':service,'path':path,'status':r.status_code})
    return data.get('data',data)

result={'at':datetime.now(timezone.utc).isoformat(),'gateway':origin,'result':'failed'}
devices=[]
try:
    with socket.create_connection(('34.18.186.116',443),timeout=20) as raw:
        with ssl.create_default_context().wrap_socket(raw,server_hostname='34.18.186.116') as conn:
            cert=conn.getpeercert()
            result['tls']={'validated':True,'version':conn.version(),'expires':cert['notAfter'],'subject_alt_names':cert.get('subjectAltName',[])}
    services=['identidad-acceso','donantes','receptores','inventario','compatibilidad','priorizacion-geografia','transporte','custodia','alertas','auditoria','monitoreo','documentos']
    for service in services:
        for path in ['/health/live','/health/ready']: call(service,path)
        r=requests.get(origin+'/services/'+service+'/internal/v1/private',timeout=15)
        assert r.status_code==404,(service,'internal exposure',r.status_code)
    r=requests.get(origin+'/',timeout=30);assert r.status_code==200
    result['portal_http']=r.status_code
    for user in ['transport1','donor1','operator1']:
        auth=call('identidad-acceso','/api/v1/auth/login',body={'username':user,'password':private['password']})
        tokens[user]=auth['access_token']
        me=call('identidad-acceso','/api/v1/auth/me',user)
        assert me['username']==user
    for source in ['ANDROID','IOS']:
        row=call('identidad-acceso','/api/v1/mobile/devices','transport1',{'id':str(uuid.uuid4()),'source':source,'label':'Comprobación despliegue móvil 20261110'})
        devices.append(row)
        assert row['source']==source and 'token_hash' not in row
        call('identidad-acceso','/api/v1/mobile/devices','donor1',{'id':row['id'],'source':source,'label':'Comprobación de ámbito'},expected=(403,))
    shipments=call('transporte','/api/v1/shipments?page_size=20','transport1')['items']
    assert shipments,'No task available to verify authorized context'
    shipment=shipments[0]
    context=call('transporte','/api/v1/shipments/'+shipment['id']+'/operational-context','transport1')
    assert context['shipment_id']==shipment['id']
    call('transporte','/api/v1/shipments/'+shipment['id']+'/operational-context','donor1',expected=(403,))
    call('transporte','/api/v1/shipments/'+shipment['id']+'/scan','transport1',{'scanned_resource_id':str(uuid.uuid4())},expected=(409,))
    call('inventario','/api/v1/resources?page_size=2','operator1')
    call('donantes','/api/v1/campaigns?page_size=2','donor1')
    call('alertas','/api/v1/alerts?page_size=2','transport1')
    with closing(websocket.create_connection(origin.replace('https:','wss:')+'/services/transporte/ws/v1/tracking/json',timeout=15,suppress_origin=True,subprotocols=['redhouse.tracking.v1.json'])) as ws:
        ws.send(json.dumps({'type':'authenticate','credential_kind':'user','credential':tokens['transport1']}))
        assert json.loads(ws.recv())['type']=='authenticated'
        ws.send(json.dumps({'type':'heartbeat'}))
        assert json.loads(ws.recv())['type']=='heartbeat'
        ws.send(json.dumps({'type':'subscribe','shipment_id':shipment['id']}))
        event=json.loads(ws.recv())
        assert event['type']=='subscribed' or (event['type']=='error' and event['code']=='tracking_closed'), event.get('type')
        result['wss']={'authenticated':True,'heartbeat':True,'subscribed':event['type']=='subscribed','subscription_rejection':event.get('code'),'published_positions':0}
    result['device_sources_verified']=['ANDROID','IOS']
    result['result']='passed'
finally:
    for row in devices:
        call('identidad-acceso','/api/v1/mobile/devices/'+row['id']+'/revoke','transport1',{'version':row['version'],'reason':'Fin de comprobación del despliegue móvil','human_confirmation':True})
    for user in tokens:
        call('identidad-acceso','/api/v1/auth/logout',user,{})
    result['checks']=checks
    result['test_devices_revoked']=len(devices)
    print(json.dumps(result,indent=2))
