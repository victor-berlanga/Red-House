"""Explicit deployment phases; never prints private configuration or credentials."""
import hashlib,json,os,shutil,subprocess,sys,tarfile
from pathlib import Path
os.umask(0o077)
root=Path('/opt/redhouse');private=root/'.local/deploy-20261102';directory=root/'.local/compose'
def run(args):subprocess.run(args,cwd=root,check=True)
def capture(args):return subprocess.check_output(args,cwd=root,text=True)
def compose():
 args=['docker','compose','-f',str(root/'compose.yaml')]
 for name in ('gcs.compose.yaml','public.compose.yaml'):
  if (directory/name).exists():args+=['-f',str(directory/name)]
 return args
def sql(query):
 return json.loads(capture(['docker','exec','redhouse-parcial2-postgres-1','psql','-U','rh_bootstrap','-d','red_house','-qAt','-v','ON_ERROR_STOP=1','-c',query]))
def state(columns=None):
 if columns is None:
  columns=sql("SELECT json_object_agg(t,cols) FROM (SELECT table_name t,json_agg(column_name ORDER BY ordinal_position) cols FROM information_schema.columns WHERE table_schema='red_house' GROUP BY table_name) x")
 result={}
 for name,cols in columns.items():
  assert name.replace('_','').isalnum() and all(c.replace('_','').isalnum() for c in cols)
  projection=','.join('"'+c+'"' for c in cols)
  result[name]=sql("SELECT json_build_object('rows',count(*),'digest',md5(coalesce(string_agg(md5(row_to_json(t)::text),'' ORDER BY md5(row_to_json(t)::text)),''))) FROM (SELECT "+projection+' FROM red_house."'+name+'") t')
 return {'columns':columns,'tables':result}
def save(name,data):(private/name).write_text(json.dumps(data,indent=2)+'\n')
phase=sys.argv[1]
if phase=='prepare':
 assert shutil.disk_usage(root).free>2_000_000_000,'Insufficient free disk for preservation'
 private.mkdir(exist_ok=False)
 with tarfile.open(private/'source-before.tar.gz','w:gz') as out:
  for p in root.iterdir():
   if p.name not in {'.local','.git','.codegraph'}:out.add(p,arcname=p.name)
 shutil.copytree(directory,private/'configuration-before',ignore=shutil.ignore_patterns('backups','demo-20261021','labels-20261021'))
 images=capture(['docker','image','ls','--no-trunc','--format','json']);(private/'images-before.jsonl').write_text(images)
 for line in images.splitlines():
  row=json.loads(line)
  if row['Repository'].startswith('redhouse') and row['Tag']!='<none>' and not row['Tag'].startswith('before-'):
   run(['docker','tag',row['ID'],row['Repository']+':before-20261102-'+row['Tag']])
 run(['systemctl','stop','redhouse'])
 run(compose()+['up','-d','--wait','postgres','mongodb','redis'])
 run(['python3','deployment/backup.py','--verify','--leave-stopped','--output',str(private/'backup-report.json')])
 report=json.loads((private/'backup-report.json').read_text());assert report['restore']=='passed'
 save('data-before.json',state())
 manifest=json.loads(Path('/tmp/source-manifest.json').read_text())
 with tarfile.open('/tmp/project.tar.gz') as archive:
  for m in archive.getmembers():
   assert m.isfile() and m.name in manifest and not Path(m.name).is_absolute() and '..' not in Path(m.name).parts
   raw=archive.extractfile(m).read();assert hashlib.sha256(raw).hexdigest()==manifest[m.name]
   p=root/m.name;p.parent.mkdir(parents=True,exist_ok=True,mode=0o755);p.write_bytes(raw);p.chmod(m.mode)
 for name,digest in manifest.items():
  p=root/name;assert hashlib.sha256(p.read_bytes()).hexdigest()==digest
  for parent in p.parents:
   if parent==root:break
   parent.chmod(0o755)
 save('source-manifest.json',manifest)
 raw=Path('/tmp/Allelelist.txt').read_bytes();assert hashlib.sha256(raw).hexdigest()=='1913c5f748e6d649017996686e135dc6ffedc53215d4da7efad8f9165f3d2f35'
 target=directory/'reference-data/hla/3.66.0/Allelelist.txt';target.parent.mkdir(parents=True,exist_ok=False);target.write_bytes(raw);target.chmod(0o644)
 target.parent.chmod(0o755);target.parent.parent.chmod(0o755)
 print(json.dumps({'backup':report['backup'],'restore':report['restore'],'tables_before':len(report['before']['postgres']),'source_files':len(manifest),'disk_free':shutil.disk_usage(root).free}),flush=True)
elif phase=='retag':
 old=(root/'compose.yaml').read_bytes();new=Path('/tmp/compose-stage02.json').read_bytes()
 assert old.replace(b'${REDHOUSE_TAG:-0.4.1}',b'${REDHOUSE_TAG:-0.4.4}')==new
 cfg=json.loads(old)
 for image in sorted({x.get('image','') for x in cfg['services'].values()}):
  if '${REDHOUSE_TAG:-0.4.1}' in image:
   run(['docker','tag',image.replace('${REDHOUSE_TAG:-0.4.1}','0.4.1'),image.replace('${REDHOUSE_TAG:-0.4.1}','0.4.4')])
 (root/'compose.yaml').write_bytes(new)
 manifest=json.loads((private/'source-manifest.json').read_text());manifest['compose.yaml']=hashlib.sha256(new).hexdigest();save('source-manifest-final.json',manifest)
 save('deployment-delta.json',{'file':'compose.yaml','before':hashlib.sha256(old).hexdigest(),'after':hashlib.sha256(new).hexdigest(),'change':'Image tags 0.4.1 to 0.4.4; identical built image IDs'})
 print('Images tagged0.4.4; Compose default updated, no application logic change.')
elif phase=='build':
 assert (private/'backup-report.json').exists()
 run(['docker','compose','--parallel','1','--profile','install','build'])
elif phase=='migrate':
 report=json.loads((private/'backup-report.json').read_text());assert report['restore']=='passed'
 backup=Path(report['private_path'])/'postgres.dump'
 run(['docker','compose','--profile','install','run','--rm','--entrypoint','python','bootstrap','/app/apps/services/scripts/upgrade_compose.py','--backup',str(Path('/run/install')/backup.relative_to(directory))])
 before=json.loads((private/'data-before.json').read_text());after=state(before['columns']);save('data-after.json',after)
 differences=[t for t,v in before['tables'].items() if after['tables'][t]!=v]
 assert differences==['schema_migration'],differences
 save('data-preservation.json',{'compared_tables':len(before['tables']),'unchanged_tables':len(before['tables'])-1,'expected_change':'schema_migration','unexpected_changes':[],'schema':sql('SELECT max(version) FROM red_house.schema_migration')})
 for path in (directory/'apps').glob('*.json'):
  if path.name=='state.json':continue
  cfg=json.loads(path.read_text());cfg['VERSION']='0.4.4';cfg['OPERATION_SCOPE']='ACADEMIC';cfg['HLA_REFERENCE_DIR']='/run/hla-reference'
  # Add new critical actions without removing any existing security setting.
  cfg['REAUTH_REQUIRED_OPERATIONS']=list(dict.fromkeys(cfg.get('REAUTH_REQUIRED_OPERATIONS',[])+['resource_release','lab_result_review','evaluation_review','rule_transition','anomaly_resolve','reservation_create','resource_destination']))
  cfg['REQUIRE_LAB_PROFILE']=True;cfg['REQUIRE_ORGAN_AUTHORIZATION']=True
  path.write_text(json.dumps(cfg,indent=2)+'\n');path.chmod(0o644)
 override_path=directory/'gcs.compose.yaml';override=json.loads(override_path.read_text())
 for name in ('compatibilidad-a','compatibilidad-b','web'):
  spec=override.setdefault('services',{}).setdefault(name,{})
  spec.setdefault('volumes',[]).append({'type':'bind','source':str(directory/'reference-data/hla'),'target':'/run/hla-reference','read_only':True})
 override_path.write_text(json.dumps(override,indent=2)+'\n')
 run(['python3','deployment/gcp/configure_public.py','--ip','34.18.186.116'])
 run(compose()+['config','--quiet'])
 save('runtime-settings.json',{'version':'0.4.4','scope':'ACADEMIC','catalogue':'3.66.0','read_only_mounts':['compatibilidad-a','compatibilidad-b','web'],'clinical_approval_granted':False})
 run(['systemctl','start','--no-block','redhouse'])
 print('Schema16 migrated; historical data preserved; bounded startup initiated.',flush=True)
elif phase=='status':
 rows=[json.loads(x) for x in capture(['docker','ps','-a','--filter','label=com.docker.compose.project=redhouse-parcial2','--format','json']).splitlines()]
 print(json.dumps({'systemd':capture(['systemctl','is-active','redhouse']).strip(),'containers':[{'name':x['Names'],'status':x['Status']} for x in rows],'disk_free':shutil.disk_usage(root).free},indent=2))
else:raise ValueError('Unknown phase')
