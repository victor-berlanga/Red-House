"""Rollback manual de presentación; ejecutar solo por decisión autorizada."""
from pathlib import Path
import json,os,shutil,subprocess
assert os.geteuid()==0
root=Path('/opt/redhouse');backup=root/'.local/deploy-uiux-20261110';cfg=root/'.local/compose'
for name in json.loads((backup/'manifest.json').read_text()):shutil.copy2(backup/'sources'/name,root/name)
shutil.copy2(backup/'gcs.compose.yaml',cfg/'gcs.compose.yaml')
subprocess.run(['docker','compose','-f',str(root/'compose.yaml'),'-f',str(cfg/'gcs.compose.yaml'),'-f',str(cfg/'public.compose.yaml'),'up','-d','--no-deps','--no-build','--wait','web'],cwd=root,check=True)
