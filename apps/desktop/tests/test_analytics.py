from types import SimpleNamespace
from redhouse_desktop import analytics
from redhouse_desktop.client import ApiError


def payload(title,values):
    return {'scope':'Institución','from_at':'2026-01-01T00:00:00+00:00',
            'until_at':'2026-02-01T00:00:00+00:00','updated_at':'2026-02-01T01:00:00+00:00',
            'series':[{'title':title,'population':'Población real de prueba','denominator':2,'unit':'registros','values':values}]}


def test_series_preserves_population_scope_and_null():
    values=[{'label':'Abierta','value':None}]
    data={'receptores':payload('Solicitudes por estado',values)}
    selected=analytics.select_series('MEDICAL',data)
    request=next(s for s in selected if s[1]=='Solicitudes por estado')
    assert request[2]['values']==values and request[2]['denominator']==2
    assert request[2]['scope']=='Institución' and request[2]['population']=='Población real de prueba'
    assert next(s for s in selected if s[0]=='inventario')[2] is None


def test_restricted_role_does_not_see_unpermitted_data():
    data={'receptores':payload('Solicitudes por estado',[{'label':'OPEN','value':12}])}
    selected=analytics.select_series('COORDINATOR',data)
    request=next(s for s in selected if s[0]=='receptores')
    assert request[2] is None and request[3]=='No disponible para este perfil.'
    assert [s[0] for s in analytics.select_series('TRANSPORT',data)]==['transporte']


def test_optional_series_fields_use_contract_defaults():
    data=payload('Inventario por estado',[{'label':'AVAILABLE','value':2}])
    del data['series'][0]['unit']
    selected=analytics.select_series('OPERATOR',{'inventario':data})[0][2]
    assert selected['unit']=='registros'
    assert selected['values']==[{'label':'AVAILABLE','value':2}]
    del data['series'][0]['values']
    selected=analytics.select_series('OPERATOR',{'inventario':data})[0][2]
    assert selected['values']==[] and selected['denominator']==2
    assert 'unit' not in data['series'][0] and 'values' not in data['series'][0]


def test_session_change_before_fetch_aborts(monkeypatch):
    user={'id':'a','tenant_id':'t','role':'OPERATOR'}
    first=SimpleNamespace(user=user,session_id='sid')
    window=SimpleNamespace(client=first,journal=object(),status=SimpleNamespace(setText=lambda _:None))
    calls=[]
    monkeypatch.setattr(analytics,'period_dialog',lambda _:(setattr(window,'client',SimpleNamespace(user=user,session_id='other')) or {'from_at':'x','until_at':'y'}))
    window.run_in_context=lambda *args:calls.append(args)
    analytics.open_analytics(window,lambda x:x)
    assert calls==[]


def test_coordinator_queries_only_authorized_owners(monkeypatch):
    user={'id':'a','tenant_id':'t','role':'COORDINATOR'};calls=[]
    def authorized(service,path,op,**kwargs):
        calls.append((service,path,op,kwargs['params']))
        if service=='transporte':raise ApiError(503,'unavailable','indisponible')
        return payload('Inventario por estado',[])
    client=SimpleNamespace(user=user,session_id='sid',authorized=authorized)
    window=SimpleNamespace(client=client,journal=object(),status=SimpleNamespace(setText=lambda _:None))
    period={'from_at':'2026-01-01T00:00:00Z','until_at':'2026-02-01T00:00:00Z'}
    monkeypatch.setattr(analytics,'period_dialog',lambda _:period)
    result=[];window.run_in_context=lambda ctx,fetch,done,message:result.append(fetch())
    analytics.open_analytics(window,lambda x:x)
    assert [c[0] for c in calls]==['inventario','transporte']
    assert all(c[1:3]==('/api/v1/portal-metrics','portal_metrics') and c[3]==period for c in calls)
    assert result[0]['transporte'] is None
