import sys,json,shutil
from pathlib import Path
from types import SimpleNamespace as NS
from jinja2 import FileSystemLoader
ROOT=Path.cwd();sys.path[:0]=[str(ROOT/'apps/web'),str(ROOT/'apps/services')]
from src import create_app
from src.integration import PERMISSIONS,ROLES
from flask import g,render_template
app=create_app({'MICROSERVICES_CONFIG':ROOT/'.local/runtime/web-client.json','BACKEND_MODE':'microservices'})
base=ROOT/'.local/uiux-quality-20261110'
for phase in ['before','after']:
 source=base/'before/apps/web/src/presentation' if phase=='before' else ROOT/'apps/web/src/presentation'
 target=base/'preview'/phase;target.mkdir(parents=True,exist_ok=True)
 shutil.copytree(source/'static',target/'static',dirs_exist_ok=True)
 app.jinja_env.loader=FileSystemLoader(str(source/'templates'));app.jinja_env.cache.clear()
 for role in ROLES:
  with app.test_request_context('/campanas'):
   g.principal=NS(role_code=role,role_name=ROLES[role],party_name='Cuenta de prueba',account_id='synthetic',institution_id='synthetic',institution_name='Institución de prueba',region_name='Nuevo León',can=lambda permission:role in PERMISSIONS.get(permission,set()))
   def save(name,template,**context):
    text=render_template(template,**context).replace('/static/',f'/{phase}/static/')
    (target/f'{role}-{name}.html').write_text(text)
   for kind,title,active in [('campaigns','Campañas','campanas'),('alerts','Notificaciones','alertas'),('operations','Inventario','inventario')]:
    rows=[dict(name=f'{"Campaña" if kind=="campaigns" else "Aviso" if kind=="alerts" else "Unidad"} de prueba {i:02}',status='OPEN' if kind=='alerts' else 'ACTIVE',created_at='2026-11-10T10:00:00Z',_href=f'/record-{i}',_action_key=f'synthetic-{i}',_actions=[('Marcar como leída',f'/ack-{i}','read')] if kind=='alerts' else [('Editar',f'/edit-{i}','pencil'),('Cancelar',f'/cancel-{i}','cancel'),('Consultar historial',f'/history-{i}','history')] if kind=='operations' else []) for i in range(1,21)]
    save(kind,'integration/list.html',title=title,active=active,columns=[('name','Nombre'),('status','Estado'),('created_at','Fecha')],rows=rows,total=31,page=1,pages=2,has_actions=True,filters=[],filter_options={},new=None,note=None,refresh_enabled=True,export='/export')
   save('documents','integration/documents.html',title='Documentos privados',kinds=[('donor','Donante')],kind='donor',subjects=[NS(id='synthetic',folio='D-001',name='Prueba')],identifier='',documents=None)
   principal=g.principal;g.principal=None
   save('login','login.html',error=None,field_errors=[])
   g.principal=principal
   save('workspace','integration/workspace.html',title='Operaciones',links=[('Consultar inventario','/inventory'),('Conservación','/conservation')])
   save('label','integration/label.html',title='Etiqueta',unit=NS(folio='UN-001',component='Eritrocitos',blood_group='O+',status='QUARANTINE',expires_at='2026-11-20T10:00:00Z',id='synthetic'),barcode='')
   save('decision','integration/decision_support.html',title='Apoyo a decisiones')
print('Fixtures before/after: 7 roles × 8 families; same dataset, templates and assets isolated.')
