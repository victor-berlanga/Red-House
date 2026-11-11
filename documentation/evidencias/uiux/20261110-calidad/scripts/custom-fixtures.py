exec(open('.local/uiux-quality-20261110/render.py').read().split("for phase in ['before','after']:")[0])
from src.integration.routes.common import field
out=base/'preview/after'
with app.test_request_context('/review'):
 g.principal=NS(role_code='MEDICAL',role_name='Médico',party_name='Cuenta de prueba',account_id='synthetic',institution_id='synthetic',institution_name='Institución de prueba',region_name='Nuevo León',can=lambda permission:'MEDICAL' in PERMISSIONS.get(permission,set()))
 def save(name,template,**context):(out/f'custom-{name}.html').write_text(render_template(template,**context).replace('/static/','/after/static/'))
 unit={'id':'synthetic','folio':'UN-001','donation_id':'DON-001'}
 save('conservation','integration/conservation.html',title='Conservación',unit=unit,control={'blocked':False},actions=[('Registrar lectura','/read')],readings=[{'captured_at':'2026-11-10T10:00:00Z','temperature_c':'4.0','source':'DEMO','calibration_reference':'TEST','excursion':False,'gap':False}])
 save('lineage','integration/lineage.html',title='Linaje',unit=unit,children=[dict(unit,component='Eritrocitos',status='QUARANTINE',expires_at='2026-11-20T10:00:00Z')])
 save('evaluation','integration/evaluation.html',back='/requests',ranking_url='/ranking',rankings=[],evaluation={'created_at':'2026-11-10T10:00:00Z','snapshot':{'clinical_notice':'Fixture de composición; sin evaluación clínica.','missing_data':{'route':0,'expired':0,'other_component':0}},'validity':None},candidates=[{'resource_folio':'UN-001','origin_id':'Institución de prueba','expires_at':'2026-11-20T10:00:00Z','distance_km':10,'travel_minutes':20,'review':None,'review_url':'/review'},{'resource_folio':'UN-002','origin_id':'Institución de prueba','expires_at':'2026-11-20T10:00:00Z','distance_km':10,'travel_minutes':20,'review':{'decision':'FAVORABLE'},'reserve_url':'/reserve'}])
 fields=[field('name','Nombre'),field('status','Estado','select',options=[('ACTIVE','Activo')]),field('reason','Motivo','textarea')]
 for f in fields:f.update(hint='',errors=[],attrs={})
 save('form','integration/form.html',title='Formulario de prueba',fields=fields,error=None,field_errors=[],idempotency_key='fixture',submit_label='Guardar',back='/back')
 save('upload','integration/document_upload.html',title='Cargar documento',kind='DONOR',identifier='synthetic',idempotency_key='fixture',error=None)
 save('detail','integration/detail.html',title='Recurso de prueba',record={'status':'QUARANTINE'},back='/back',actions=[],fact_groups=[('Identificación',[('Folio','UN-001'),('Estado','QUARANTINE')])],sections=[])
 save('empty','integration/list.html',title='Notificaciones',active='alertas',columns=[('name','Nombre')],rows=[],total=0,page=1,pages=1,has_actions=False,filters=[],filter_options={},new=None,note=None,refresh_enabled=True,export='/export')
 save('error','error.html',title='Servicio temporalmente no disponible',code=503,message='No fue posible completar la operación. Conserva el identificador de referencia.')
print('Eight additional synthetic family/state fixtures rendered')
