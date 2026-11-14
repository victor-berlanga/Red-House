"""Future explicit OS Login add/remove commands; never run by prepare_local.py.

Adapted from clientes-20261113 access.py and cleanup_access.py. All credentials
and cloud responses are stored outside this versioned procedure.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess

from deploy import TARGET, require

GCLOUD = '/Users/victorberlanga/Downloads/google-cloud-sdk/bin/gcloud'


def cloud(directory, args):
    result = subprocess.run([GCLOUD, *args, '--project=' + TARGET['project'], '--format=json'],
                            capture_output=True, text=True, timeout=90)
    if result.returncode:
        (directory / 'access-error.private.log').write_text(result.stderr)
        raise RuntimeError('gcloud failed; inspect private diagnostic')
    return json.loads(result.stdout) if result.stdout.strip() else {}


def save(directory, name, value):
    (directory / name).write_text(json.dumps(value, indent=2) + '\n')


def add(directory):
    require(not directory.exists(), 'Access directory already exists; preserve earlier keys')
    directory.mkdir(mode=0o700, parents=True)
    vm = cloud(directory, ['compute', 'instances', 'describe', TARGET['instance'],
                           '--zone=' + TARGET['zone']])
    require(str(vm['id']) == TARGET['id'] and vm['name'] == TARGET['instance'] and
            vm['zone'].endswith('/zones/' + TARGET['zone']) and vm['status'] == 'RUNNING' and
            vm['networkInterfaces'][0]['accessConfigs'][0]['natIP'] == TARGET['ip'],
            'Wrong VM target')
    before = cloud(directory, ['compute', 'os-login', 'describe-profile'])
    old = before.get('sshPublicKeys', {})
    require(len(old) == 2, 'Expected the two previously retained OS Login keys')
    save(directory, 'oslogin-before.private.json', before)
    subprocess.run(['ssh-keygen', '-q', '-t', 'ed25519', '-f', str(directory / 'ssh_key'),
                    '-N', '', '-C', 'redhouse-portal-documentos-20261114'],
                   check=True, capture_output=True)
    added = cloud(directory, ['compute', 'os-login', 'ssh-keys', 'add',
                             '--key-file=' + str(directory / 'ssh_key.pub'), '--ttl=30m'])
    save(directory, 'oslogin-add.private.json', added)
    after = cloud(directory, ['compute', 'os-login', 'describe-profile'])
    save(directory, 'oslogin-active.private.json', after)
    current = after.get('sshPublicKeys', {})
    candidates = set(current) - set(old)
    public = (directory / 'ssh_key.pub').read_text().split()[:2]
    own = [key for key in candidates if current[key]['key'].split()[:2] == public]
    require(len(own) == 1 and all(current.get(k) == v for k, v in old.items()),
            'Key addition not isolated')
    username = next(a['username'] for a in after['posixAccounts'] if a.get('primary'))
    require(username == 'victor_berlangam_gmail_com', 'Unexpected OS Login identity')
    save(directory, 'access.json', {'fingerprint': own[0], 'username': username,
                                    'target': TARGET, 'previous_keys': 2, 'ttl': '30m'})
    print(json.dumps({'temporary_key_added': True, 'previous_keys_preserved': 2}))


def remove(directory, receipt):
    require(receipt is not None, 'Provide downloaded validation.json or rollback.json')
    validation = json.loads(receipt.read_text())
    require(validation.get('status') == 'passed' and validation.get('target') == TARGET,
            'Successful validation for the exact target is required')
    record = json.loads((directory / 'access.json').read_text())
    old = json.loads((directory / 'oslogin-before.private.json').read_text()).get('sshPublicKeys', {})
    require(len(old) == 2 and record['target'] == TARGET, 'Access record mismatch')
    current = cloud(directory, ['compute', 'os-login', 'describe-profile']).get('sshPublicKeys', {})
    fingerprint = record['fingerprint']
    require(fingerprint not in old and all(current.get(k) == v for k, v in old.items()),
            'Previous keys changed; do not remove unrelated keys')
    if fingerprint in current:
        require(current[fingerprint]['key'].split()[:2] ==
                (directory / 'ssh_key.pub').read_text().split()[:2], 'Temporary key identity mismatch')
        cloud(directory, ['compute', 'os-login', 'ssh-keys', 'remove',
                          '--key=' + fingerprint, '--quiet'])
    after = cloud(directory, ['compute', 'os-login', 'describe-profile']).get('sshPublicKeys', {})
    require(fingerprint not in after and all(after.get(k) == v for k, v in old.items()),
            'Key cleanup verification failed')
    for name in ('ssh_key', 'ssh_key.pub'):
        (directory / name).unlink(missing_ok=True)
    report = {'temporary_key_removed': True, 'prior_keys_preserved': 2,
              'private_key_deleted': True, 'validation_action': validation['action']}
    save(directory, 'access-cleanup.json', report)
    print(json.dumps(report))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('add', 'remove'))
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--receipt', type=Path)
    args = parser.parse_args()
    os.umask(0o077)
    directory = args.directory.resolve()
    require('.local' in directory.parts, 'Access material must remain in private .local/')
    if args.action == 'add':
        add(directory)
    else:
        remove(directory, args.receipt)
