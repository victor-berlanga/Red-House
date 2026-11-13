import json
import threading
import pytest
from redhouse_desktop.client import Client, ContractError, decode, read_xml, request_xml


def example(service,path,method,status='200'):
    from redhouse_desktop.client import CONTRACTS
    spec=json.loads((CONTRACTS/(service+'.json')).read_text())
    return spec['paths'][path][method]['responses'][status]['content']['application/xml']['example'].encode()


def test_login_and_list_examples_validate_against_operation_dto():
    login=decode(example('identidad','/api/v1/auth/login','post'),'identidad','login',True)
    assert 'access_token' in login['data']
    result=decode(example('inventario','/api/v1/resources','get'),'inventario','resources_list',True)
    assert isinstance(result['data']['items'],list)
    alerts=decode(example('alertas','/api/v1/alerts','get'),'alertas','alerts_list',True)
    assert isinstance(alerts['data']['items'],list)
    with pytest.raises(ContractError):
        decode(example('inventario','/api/v1/resources','get'),'identidad','login',True)


def test_request_xsd_and_xml_escape():
    raw=request_xml({'username':'abc','password':'abcdefghijk<>&'},'login.xsd')
    assert b'&lt;&gt;&amp;' in raw
    with pytest.raises(ContractError): request_xml({'username':'x','password':'short'},'login.xsd')
    with pytest.raises(ContractError): request_xml({'decision':'RECEIVED','reason':'ok','version':1,'human_confirmation':'true'},'lab_sample_receive.xsd')


def test_xml_attacks_and_wrong_content():
    with pytest.raises(ContractError): read_xml(b'<!DOCTYPE x [<!ENTITY x SYSTEM "file:///etc/passwd">]><response>&x;</response>')
    with pytest.raises(ContractError): read_xml('<?xml version="1.0" encoding="UTF-16"?><!DOCTYPE x><x/>'.encode('utf-16'))
    with pytest.raises(ContractError): read_xml(b'x'*2_000_001)
    with pytest.raises(ContractError): read_xml(b'{"data":{}}')
    with pytest.raises(ValueError): Client('http://localhost')
    with pytest.raises(ValueError): Client('https://user:pass@example.com')


def test_refresh_failure_clears_tokens_and_is_not_replayed():
    client=Client('https://example.com'); client.access='expired'; client.refresh='secret'; client.user={'role':'OPERATOR'}
    calls=[]
    from redhouse_desktop.client import ApiError
    def fail(service,path,*args,**kwargs):
        calls.append(path)
        if path.endswith('/refresh'): raise ConnectionError('lost')
        raise ApiError(401,'expired','expired')
    client.call=fail
    with pytest.raises(ConnectionError): client.authorized('inventario','/api/v1/resources','resources_list')
    assert calls==['/api/v1/auth/me','/api/v1/auth/refresh']
    assert client.access is None and client.refresh is None and client.user is None


def test_parallel_expired_requests_rotate_only_once():
    from concurrent.futures import ThreadPoolExecutor
    from redhouse_desktop.client import ApiError
    c=Client('https://example.com'); c.access='old'; c.refresh='refresh'; c.user={'id':'u','tenant_id':'t','region_id':'r','role':'OPERATOR','active':True}
    refreshes=[]
    def call(service,path,*args,**kwargs):
        if path.endswith('/refresh'):
            refreshes.append(1)
            return {'access_token':'new','refresh_token':'rotated'}
        if c.access=='old': raise ApiError(401,'expired','expired')
        if path.endswith('/auth/me'): return dict(c.user)
        return {'items':[]}
    c.call=call
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(c.authorized,'inventario','/api/v1/resources','resources_list') for _ in range(2)]
        assert [f.result() for f in futures]==[{'items':[]},{'items':[]}]
    assert len(refreshes)==1 and c.refresh=='rotated'


def test_rejects_incompatible_server_contract_version():
    raw=example('inventario','/api/v1/resources','get')
    with pytest.raises(ContractError): decode(raw.replace(b'0.4.1',b'0.5.0'),'inventario','resources_list',True)


def test_process_version_policy_is_independent_of_openapi_info(tmp_path, monkeypatch):
    import shutil
    import redhouse_desktop.client as client_module
    raw=example('inventario','/api/v1/resources','get')
    target=tmp_path/'contracts'; shutil.copytree(client_module.CONTRACTS,target)
    spec=target/'inventario.json'; document=json.loads(spec.read_text()); document['info']['version']='documentation-version'; spec.write_text(json.dumps(document))
    monkeypatch.setattr(client_module,'CONTRACTS',target)
    assert decode(raw,'inventario','resources_list',True)['meta']['version']=='0.4.1'
    with pytest.raises(ContractError): decode(raw.replace(b'0.4.1',b'0.4.4'),'inventario','resources_list',True)


def test_nested_custody_xml_escapes_and_validates():
    body={'human_confirmation':True,'reason':'Recepción autorizada','state':'ACCEPTED','version':3,
          'custody':{'scanned_resource_id':'00000000-0000-4000-8000-000000000001','seal':'Sello <ficticio>',
                     'captured_at':'2030-01-01T00:00:00Z','reported_handover_user_id':'00000000-0000-4000-8000-000000000002','electronic_acceptance':True}}
    raw=request_xml(body,'shipment_transition.xsd')
    assert b'&lt;ficticio&gt;' in raw and b'<electronic_acceptance>true</electronic_acceptance>' in raw
    with pytest.raises(ContractError): request_xml(dict(body,custody={'seal':'incompleto'}),'shipment_transition.xsd')


def test_scope_change_blocks_business_request():
    from redhouse_desktop.client import ApiError
    c=Client('https://example.com'); c.access='token'; c.refresh='refresh'; c.user={'id':'u','tenant_id':'old','region_id':'r','role':'MEDICAL','active':True}
    seen=[]
    def call(service,path,*args,**kwargs):
        seen.append(path)
        return {'id':'u','tenant_id':'new','region_id':'r','role':'MEDICAL','active':True}
    c.call=call
    with pytest.raises(ApiError) as failure: c.authorized('inventario','/api/v1/resources','resources_list')
    assert failure.value.code=='identity_changed' and seen==['/api/v1/auth/me'] and c.access is None


def test_xml_scalars_and_containers_reject_ambiguous_values():
    from lxml import etree
    from redhouse_desktop.client import value
    invalid=['<response type="number">NaN</response>','<response type="number">Infinity</response>',
             '<response type="integer">+1</response>','<response type="integer">1_0</response>',
             '<response type="object">texto<field name="x" type="string">a</field></response>',
             '<response type="array"><item type="integer">1</item>texto</response>']
    for raw in invalid:
        with pytest.raises(ContractError): value(etree.fromstring(raw.encode()))


def test_reads_share_brief_check_but_mutation_rechecks_scope():
    from redhouse_desktop.client import ApiError
    c=Client('https://example.com'); c.access='token'; c.refresh='refresh'
    c.user={'id':'u','tenant_id':'old','region_id':'r','role':'MEDICAL','active':True}
    state={'tenant':'old'}; calls=[]
    def call(service,path,*args,**kwargs):
        calls.append(path)
        if path=='/api/v1/auth/me': return dict(c.user,tenant_id=state['tenant'])
        return {'items':[]}
    c.call=call
    c.authorized('inventario','/api/v1/resources','resources_list')
    c.authorized('inventario','/api/v1/resources','resources_list')
    assert calls.count('/api/v1/auth/me')==1
    state['tenant']='new'
    with pytest.raises(ApiError): c.authorized('inventario','/api/v1/resources','resource_create',method='POST')
    assert calls.count('/api/v1/auth/me')==2 and calls.count('/api/v1/resources')==2 and c.access is None


def test_invalid_reauthentication_is_not_replayed():
    from redhouse_desktop.client import ApiError
    c=Client('https://example.com'); c.access='access'; c.refresh='refresh'
    c.user={'id':'u','tenant_id':'t','region_id':'r','role':'MEDICAL','active':True}; calls=[]
    def call(service,path,*args,**kwargs):
        calls.append(path)
        if path=='/api/v1/auth/me': return dict(c.user)
        if path=='/api/v1/auth/reauthentication-proofs': raise ApiError(401,'unauthorized','Credenciales inválidas.')
        raise AssertionError('No debe renovar ni reenviar el desafío.')
    c.call=call
    with pytest.raises(ApiError): c.authorized('identidad-acceso','/api/v1/auth/reauthentication-proofs','reauthenticate',method='POST')
    assert calls==['/api/v1/auth/me','/api/v1/auth/reauthentication-proofs']


def test_reauthentication_proof_is_only_sent_as_header(monkeypatch):
    import requests
    raw=example('inventario','/api/v1/resources','get'); captured={}
    class Response:
        status_code=200; headers={'Content-Type':'application/xml'}
        def __enter__(self): return self
        def __exit__(self,*args): pass
        def iter_content(self,size): yield raw
    def fake_request(method,url,**kwargs): captured.update(kwargs); return Response()
    monkeypatch.setattr(requests,'request',fake_request)
    c=Client('https://example.com'); c.access='access'
    c.call('inventario','/api/v1/resources','resources_list',proof='proof-in-memory')
    assert captured['headers']['X-Reauthentication-Proof']=='proof-in-memory'
    assert captured['data'] is None and captured.get('params') is None


def test_cold_reading_xsd_rejects_nonfinite_or_out_of_range():
    valid={'temperature_c':4.2,'captured_at':'2030-01-01T00:00:00Z','source':'Termómetro ficticio'}
    assert b'<temperature_c>4.2</temperature_c>' in request_xml(valid,'cold_reading_create.xsd')
    with pytest.raises(ContractError): request_xml(dict(valid,temperature_c=200),'cold_reading_create.xsd')
    with pytest.raises(ContractError): request_xml(dict(valid,temperature_c=float('nan')),'cold_reading_create.xsd')
