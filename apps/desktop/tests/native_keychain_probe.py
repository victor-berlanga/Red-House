"""Prueba manual destructiva solo sobre una entrada sintética temporal del llavero."""
import os
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

import keyring
from redhouse_desktop.durable_commands import prepare_command, submit_command
from redhouse_desktop.journal import Journal, JournalError

BASE = 'https://isolated.invalid'
BODY = {'folio':'SYN-KEYCHAIN', 'kind':'BLOOD', 'component':'RBC', 'blood_group':'O-', 'expires_at':'2030-01-01T00:00:00Z'}


def journal(root, actor):
    return Journal(root, BASE, actor, actor)


def worker(root, actor):
    store = journal(root, actor)
    record = prepare_command(store, 'resource_create', None, BODY)
    class LostResponse:
        def authorized(self, *args, **kwargs):
            if kwargs['key'] != record['key'] or kwargs['body'] != BODY:
                raise AssertionError('El intento cambió.')
            raise ConnectionError('Respuesta sintética perdida.')
    try:
        submit_command(LostResponse(), store, record, fresh=True)
    except ConnectionError:
        os._exit(0)  # Simula interrupción abrupta antes de recuperar el resultado.
    raise AssertionError('No se simuló la interrupción.')


def main():
    if len(sys.argv) == 4 and sys.argv[1] == '--worker':
        worker(sys.argv[2], sys.argv[3])
        return
    actor = str(uuid.uuid4())
    with tempfile.TemporaryDirectory(prefix='redhouse-keychain-restart-') as directory:
        store = journal(directory, actor)
        try:
            subprocess.run([sys.executable, str(Path(__file__).resolve()), '--worker', directory, actor], check=True, timeout=30)
            pending = store.list()
            assert len(pending) == 1 and pending[0]['state'] == 'PREPARED' and pending[0]['body'] == BODY
            assert b'SYN-KEYCHAIN' not in store.file.read_bytes()
            other = journal(directory, str(uuid.uuid4()))
            try:
                assert other.list() == []
            finally:
                if keyring.get_password('RedHouse desktop journal', other.identifier) is not None:
                    keyring.delete_password('RedHouse desktop journal', other.identifier)
            class Replay:
                def authorized(self, *args, **kwargs):
                    assert kwargs['key'] == pending[0]['key'] and kwargs['body'] == BODY
                    return dict(BODY,id='00000000-0000-4000-8000-000000000001')
            submit_command(Replay(), store, pending[0])
            assert store.list()[0]['state'] == 'DONE'
            keyring.delete_password('RedHouse desktop journal', store.identifier)
            try:
                store.list()
            except JournalError:
                print('native_keychain=ok abrupt_restart=ok same_key=ok account_isolation=ok missing_key_fails_closed=ok')
            else:
                raise AssertionError('La ausencia de clave no bloqueó el diario.')
        finally:
            if keyring.get_password('RedHouse desktop journal', store.identifier) is not None:
                keyring.delete_password('RedHouse desktop journal', store.identifier)


if __name__ == '__main__':
    main()
