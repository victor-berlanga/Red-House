"""Reintento de objeto local sintético, con ClamD real y misma idempotencia."""
import base64
import hashlib
import json
import os
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from urllib.parse import urlsplit
from uuid import uuid4

import pytest
import requests
from cryptography.fernet import Fernet
from PIL import Image
from redhouse.document_contracts import Prepared
from redhouse.examples import request_xml
from redhouse.extension_contracts import schema
from redhouse.xml_response import validate_response

from .helpers import iso
from .test_final_quality import api


@pytest.mark.skipif(not os.environ.get('REDHOUSE_TEST_CLAMD_PORT'),reason='Requiere ClamD real')
@pytest.mark.parametrize('fmt',['json','xml'])
def test_missing_retry_same_document_and_immutable_object(p,tmp_path,monkeypatch,fmt):
    app=p.apps['documentos']; root=tmp_path/'files'; root.mkdir(mode=0o700)
    for name,value in {'STORAGE_PROVIDER':'local','STORAGE_LOCAL_ROOT':str(root),'STORAGE_PUBLIC_BASE_URL':'https://example.test','CLAMD_HOST':'127.0.0.1','CLAMD_PORT':int(os.environ['REDHOUSE_TEST_CLAMD_PORT'])}.items(): monkeypatch.setitem(app.config,name,value)
    owner='medical2'; recipient=p.ok('receptores','POST','/api/v1/recipients',user=owner,data={'folio':'REC-'+uuid4().hex[:10],'display_name':'Paciente sintético','kind':'ORGAN','organ_type':'KIDNEY','blood_group':'A+','studies':'Sin uso clínico'})
    profile=p.ok('compatibilidad','POST','/api/v1/laboratory/profiles',user=owner,data={'name':'Perfil sintético','kind':'ORGAN','component':'KIDNEY','version':1,'required_tests':['HLA'],'required_loci':['A'],'source':'Ensayo sintético','synthetic':True,'effective_at':iso()})
    sample=p.ok('compatibilidad','POST','/api/v1/laboratory/samples',user=owner,data={'recipient_id':recipient['id'],'profile_id':profile['id'],'identifier':'SYN-'+uuid4().hex,'collected_at':iso(minutes=-5)})
    p.ok('compatibilidad','POST',f"/api/v1/laboratory/samples/{sample['id']}/receive",user=owner,data={'human_confirmation':True,'reason':'Recepción sintética','version':1,'decision':'RECEIVED'})
    result=p.ok('compatibilidad','POST','/api/v1/laboratory/results',user=owner,data={'sample_id':sample['id'],'test_code':'HLA','result_state':'PENDING','method':'Método sintético','laboratory':'Laboratorio sintético','reference':'Informe sintético','measured_at':iso(minutes=-2)})
    image=BytesIO(); Image.new('RGB',(8,8),'red').save(image,format='PNG'); content=image.getvalue(); digest=hashlib.sha256(content).hexdigest()
    body={'subject_kind':'RESULT','subject_id':result['id'],'category':'LAB_RESULT','mime_type':'image/png','size':len(content),'sha256':digest,'policy_reference':'Política sintética'}
    def prepare(key):
        headers={'Authorization':'Bearer '+p.tokens[owner],'Accept':'application/'+fmt,'Content-Type':'application/'+fmt,'Idempotency-Key':key}
        raw=request_xml(body).encode() if fmt=='xml' else json.dumps(body).encode()
        response=requests.post(p.urls['documentos']+'/api/v1/documents',headers=headers,data=raw,timeout=20)
        assert response.status_code==201
        return (validate_response(response.content,{'type':'object','properties':{'data':schema(Prepared)}}) if fmt=='xml' else response.json())['data']
    key=uuid4().hex; first=prepare(key); document=first['id']; path=urlsplit(first['upload_url']).path
    missing=p.request('documentos','POST',f'/api/v1/files/{document}/verify',user=owner,key=uuid4().hex)
    assert missing.status_code==404 and missing.json()['error']['code']=='object_missing'
    same=prepare(key); assert same['id']==document
    def as_user(token,user):
        cipher=Fernet(base64.urlsafe_b64encode(hashlib.sha256(('private-storage-v1:'+app.config['SERVICE_PRIVATE_KEY']).encode()).digest()))
        data=json.loads(cipher.decrypt(token.encode())); data['authorization']='Bearer '+p.tokens[user]
        return '/storage/v1/objects/'+cipher.encrypt(json.dumps(data,separators=(',',':')).encode()).decode()
    token=urlsplit(same['upload_url']).path.rsplit('/',1)[-1]
    with app.test_client() as client:
        assert client.put(as_user(token,'medical1'),data=content,content_type='image/png').status_code==403
        assert client.put(as_user(token,'operator2'),data=content,content_type='image/png').status_code==409
    def put():
        with app.test_client() as client: return client.put(urlsplit(same['upload_url']).path,data=content,content_type='image/png').status_code
    with ThreadPoolExecutor(max_workers=2) as pool: assert sorted(pool.map(lambda _:put(),range(2)))==[201,412]
    verified=p.ok('documentos','POST',f'/api/v1/files/{document}/verify',user=owner,key=key+'-verify')
    assert verified['id']==document and verified['status']=='VERIFIED' and verified['sha256']==digest and verified['generation']
    metadata=api(p,'documentos',f'/api/v1/documents/{document}/verified',user=owner,fmt=fmt,method='GET')
    assert metadata['subject_id']==result['id'] and metadata['sha256']==digest and metadata['generation']==verified['generation'] and metadata['analysis']=='CLEAN'
    with app.test_client() as client: assert client.put(urlsplit(same['upload_url']).path,data=content,content_type='image/png').status_code==409
    with p.owner('documentos') as conn:
        for forbidden in ('ERROR','REJECTED'):
            extra=prepare(uuid4().hex); conn.execute('UPDATE files SET status=%s WHERE id=%s',(forbidden,extra['id'])); conn.commit()
            with app.test_client() as client: assert client.put(urlsplit(extra['upload_url']).path,data=content,content_type='image/png').status_code==409
        events=conn.execute("SELECT event->>'action',count(*) FROM activity_events WHERE event->>'resource_id'=%s AND event->>'action' IN ('FILE_MISSING','FILE_VERIFIED') GROUP BY 1",(document,)).fetchall()
    assert dict(events)=={'FILE_MISSING':1,'FILE_VERIFIED':1}
