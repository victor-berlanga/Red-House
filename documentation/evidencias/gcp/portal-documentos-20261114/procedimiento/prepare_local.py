"""Package the three reviewed web sources locally. No network, builds or services."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

from deploy import BASELINE_REF, FILES, TARGET


def package(root, output):
    root = root.resolve(strict=True)
    output = output.resolve()
    if not output.is_relative_to(root / '.local') or output.exists():
        raise ValueError('Use a new directory under the repository .local/')
    output.mkdir(mode=0o700, parents=True)
    manifest = {}
    baseline = {}
    for name in FILES:
        source = root / name
        if source.is_symlink() or not source.is_file():
            raise ValueError('Source missing or symlink')
        content = source.read_bytes()
        if name.endswith('.py'):
            compile(content, name, 'exec')
        destination = output / 'payload' / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
        manifest[name] = hashlib.sha256(content).hexdigest()
        previous = subprocess.check_output(['git', '-C', str(root), 'show', BASELINE_REF + ':' + name])
        baseline[name] = hashlib.sha256(previous).hexdigest()
    for name in ('deploy.py',):
        shutil.copy2(Path(__file__).with_name(name), output / name)
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    head = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
    (output / 'source.json').write_text(json.dumps({
        'head': head, 'target': TARGET, 'state': 'PREPARED_LOCALLY_NOT_DEPLOYED',
        'baseline_ref': BASELINE_REF,
        'baseline_commit': subprocess.check_output(
            ['git', '-C', str(root), 'rev-parse', BASELINE_REF], text=True).strip(),
        'baseline_hashes': baseline,
        'files': manifest, 'deploy_sha256': hashlib.sha256((output / 'deploy.py').read_bytes()).hexdigest()
    }, indent=2) + '\n')
    diff = subprocess.check_output(['git', '-C', str(root), 'diff', BASELINE_REF, '--', *FILES])
    (output / 'reviewed-source.diff').write_bytes(diff)
    print(json.dumps({'package': str(output), 'files': manifest, 'remote_actions': 0}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    os.umask(0o077)
    package(args.root, args.output)
