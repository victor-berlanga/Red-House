"""Restore the preceding web presentation and image; never restore databases."""
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

assert os.geteuid() == 0
root = Path('/opt/redhouse')
backup = root/'.local/deploy-uiux-quality-20261110'
cfg = root/'.local/compose'
expected = json.loads((backup/'expected-before.json').read_text())
for name, sha in expected.items():
    assert name.startswith('apps/web/src/presentation/') and '..' not in Path(name).parts
    if sha is None:
        (root/name).unlink(missing_ok=True)
    else:
        source = backup/'sources'/name
        assert hashlib.sha256(source.read_bytes()).hexdigest() == sha
        shutil.copy2(source, root/name)
shutil.copy2(backup/'gcs.compose.yaml', cfg/'gcs.compose.yaml')
subprocess.run(['docker', 'compose', '-f', str(root/'compose.yaml'), '-f', str(cfg/'gcs.compose.yaml'), '-f', str(cfg/'public.compose.yaml'), 'up', '-d', '--no-deps', '--no-build', '--wait', '--wait-timeout', '180', 'web'], cwd=root, check=True)
before = json.loads((backup/'runtime-before.json').read_text())
current = subprocess.check_output(['docker', 'inspect', '--format={{.Image}}', 'redhouse-parcial2-web-1'], text=True).strip()
assert current == before['redhouse-parcial2-web-1']['image']
print('Previous web image restored; other services and databases untouched')
