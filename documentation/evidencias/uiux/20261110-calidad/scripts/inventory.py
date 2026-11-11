import ast,json,csv,sys,inspect
from pathlib import Path
root=Path.cwd();sys.path[:0]=[str(root/'apps/web'),str(root/'apps/services')]
from src import create_app
from src.integration import NAV,PERMISSIONS
app=create_app({'MICROSERVICES_CONFIG':root/'.local/runtime/web-client.json','BACKEND_MODE':'microservices'})
out=root/'documentation/evidencias/uiux/20261110-calidad'
nav={}
for _,_,_,_,endpoint,_,permission,_ in NAV:nav.setdefault(endpoint,set()).update(PERMISSIONS[permission])
rows=[]
for rule in app.url_map.iter_rules():
 if rule.endpoint=='static':continue
 func=app.view_functions[rule.endpoint]
 try:
  src=inspect.getsource(func);tree=ast.parse(src);calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call)]
  family=[]
  for n in calls:
   name=getattr(n.func,'id','')
   if name in ('table','detail','submit'):family.append({'table':'list.html','detail':'detail.html','submit':'form.html'}[name])
   if name=='render_template' and n.args and isinstance(n.args[0],ast.Constant):family.append(str(n.args[0].value))
  guard='; '.join(ast.unparse(n) for n in ast.walk(tree) if isinstance(n,ast.Compare) and ('role_code' in ast.unparse(n) or '.can(' in ast.unparse(n)))
 except Exception:family=[];guard='Revisar función compuesta'
 for role in sorted(nav.get(rule.endpoint,{'PENDIENTE: autorización por recurso / función'})):
  rows.append({'route':str(rule),'methods':','.join(sorted(rule.methods-{'HEAD','OPTIONS'})),'endpoint':rule.endpoint,'role':role,'family':';'.join(sorted(set(family))) or 'delegada/JSON/redirección','additional_role_conditions':guard,'runtime_visual':'NO: inventario de fuente; fixtures de familia en chrome.json','states':'runtime pendiente; normal/vacío/error según familia','sizes':'runtime pendiente'})
with (out/'rutas.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
templates=[]
for p in sorted((root/'apps/web/src/presentation/templates/integration').glob('*.html')):
 s=p.read_text();templates.append({'template':p.name,'forms':s.count('<form'),'tables':s.count('<table'),'bare_card':s.count('class="card"'),'review':'fuente y compilación Jinja; ejecución solo si aparece en chrome.json'})
with (out/'plantillas.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=templates[0]);w.writeheader();w.writerows(templates)
print(len(rows),'route/role inventory rows;',len(templates),'integration templates')
