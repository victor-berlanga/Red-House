import hashlib,json
from pathlib import Path
base=Path('/opt/redhouse/.local');old=base/'deploy-20261102/configuration-before';new=base/'compose'
checks=[]
for name in ('postgres-password','mongo-password','redis-password'):
 assert hashlib.sha256((old/name).read_bytes()).digest()==hashlib.sha256((new/name).read_bytes()).digest();checks.append(name)
keys={'DATABASE_URL','REDIS_URL','MONGODB_URL','JWT_PRIVATE_KEY','JWT_PUBLIC_KEY','SERVICE_PRIVATE_KEY','SERVICE_PUBLIC_KEYS','SECRET_KEY','JWT_SECRET_KEY','password','accounts','database_owners'}
for p in list((old/'apps').glob('*.json'))+[old/'state.json',old/'web.json']:
 q=new/p.relative_to(old)
 if not q.exists():continue
 a=json.loads(p.read_text());b=json.loads(q.read_text())
 for k in keys & a.keys():
  assert a[k]==b.get(k),(str(p.relative_to(old)),k)
  checks.append(str(p.relative_to(old))+':'+k)
result={'preserved_secret_fields':len(checks),'checks':checks,'values_redacted':True,'passed':True}
(base/'deploy-20261102/configuration-preservation.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'preserved_secret_fields':len(checks),'passed':True}))
