"""One isolated cold control and one candidate; no service/image mutations."""
import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from uuid import uuid4

IMAGE = 'sha256:8693ff8ffafc6fe92079f0dc9a5e73530f6bede32cb61b5bbde0aab66a8446fd'
BASE = '64eb84e46ea78f3715f4ed504b644f54c13af48142abaf91490ee54529934220'
CANDIDATE = '964c65b1982e0dcadccb0080b47bfcb68cdd4975a9ef06bbb3814417e705fe30'


def main():
    root = Path(__file__).resolve().parent
    output = Path(sys.argv[1]).resolve()
    os.umask(0o077)
    output.mkdir(mode=0o700, parents=False, exist_ok=False)
    for name in ('probe.py', 'codec.py'):
        assert not (root / name).is_symlink() and (root / name).stat().st_mode & 0o004
        ast.parse((root / name).read_text())
    assert hashlib.sha256((root / 'codec.py').read_bytes()).hexdigest() == CANDIDATE
    image = json.loads(subprocess.check_output(['docker', 'image', 'inspect', IMAGE], text=True))[0]
    assert image['Id'] == IMAGE and image['Config']['User'] == '10001:10001'
    run_id = uuid4().hex
    report = {'image_id': IMAGE, 'user': image['Config']['User'],
              'probe_sha256': hashlib.sha256((root / 'probe.py').read_bytes()).hexdigest(),
              'runner_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'runs': [], 'own_containers_closed': False,
              'scope': 'Two ephemeral containers only; existing runtime and configuration untouched'}
    try:
        for label, digest in (('control', BASE), ('candidate', CANDIDATE)):
            name = 'rh-codec-compile-' + run_id + '-' + label
            command = ['docker', 'run', '--rm', '--name', name,
                       '--label', 'redhouse.codec-discriminant=' + run_id,
                       '--network', 'none', '--read-only', '--entrypoint', 'python',
                       '--mount', f'type=bind,src={root / "probe.py"},dst=/tmp/codec-probe.py,readonly']
            if label == 'candidate':
                command += ['--mount', f'type=bind,src={root / "codec.py"},dst=/app/apps/services/redhouse/codec.py,readonly']
            command += [IMAGE, '-B', '/tmp/codec-probe.py', digest]
            row = {'label': label, 'source_sha256': digest, 'container_closed': False}
            report['runs'].append(row)
            started = time.monotonic()
            try:
                process = subprocess.run(command, text=True, capture_output=True, timeout=35)
                row['exit_code'] = process.returncode
                (output / (label + '.stdout.private.json')).write_text(process.stdout)
                (output / (label + '.stderr.private.log')).write_text(process.stderr)
                try:
                    row['result'] = json.loads(process.stdout)
                except ValueError:
                    row['error_type'] = 'InvalidProbeOutput'
            except subprocess.TimeoutExpired:
                row['error_type'] = 'TimeoutExpired'
            finally:
                row['elapsed_seconds'] = time.monotonic() - started
                inspected = subprocess.run(['docker', 'container', 'inspect', name], text=True, capture_output=True)
                if inspected.returncode == 0:
                    owned = json.loads(inspected.stdout)[0]
                    assert owned['Image'] == IMAGE and owned['Config']['Labels']['redhouse.codec-discriminant'] == run_id
                    subprocess.run(['docker', 'rm', '-f', name], check=True, capture_output=True, timeout=15)
                    row['forced_cleanup'] = True
                else:
                    assert 'No such' in inspected.stderr
                    row['forced_cleanup'] = False
                remaining = subprocess.check_output(['docker', 'ps', '-aq', '--filter', 'name=^/' + name + '$'], text=True)
                assert not remaining.strip()
                row['container_closed'] = True
                (output / 'comparison.private.json').write_text(json.dumps(report, indent=2) + '\n')
        report['own_containers_closed'] = all(row['container_closed'] for row in report['runs'])
        report['candidate_passed'] = report['runs'][1].get('exit_code') == 0 and report['runs'][1].get('result', {}).get('passed') is True
        report['control_reproduced'] = any(
            error.get('type') == 'XMLSchemaParseError' and error.get('builtin_type_failure') is True
            for error in report['runs'][0].get('result', {}).get('errors', [])
        )
    finally:
        (output / 'comparison.private.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'output': str(output), 'candidate_passed': report['candidate_passed'],
                      'control_reproduced': report['control_reproduced'], 'own_containers_closed': report['own_containers_closed']}))
    raise SystemExit(0 if report['candidate_passed'] and report['own_containers_closed'] else 1)


if __name__ == '__main__':
    main()
