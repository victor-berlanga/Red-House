"""Fraccionamiento idempotente y correlación de vínculos con sus unidades."""
from uuid import uuid4

import pytest
from cryptography.fernet import Fernet
from redhouse_desktop.client import ContractError
from redhouse_desktop.durable_commands import prepare_command, submit_command
from redhouse_desktop.journal import Journal


class Keys:
    def __init__(self): self.key = Fernet.generate_key()
    def get(self, identifier, exists): return self.key


def test_fractionation_reuses_key_and_checks_each_child(tmp_path):
    parent, donation, child = (str(uuid4()) for _ in range(3))
    body = {'version': 2, 'reason': 'Procesamiento documentado', 'human_confirmation': 'true',
            'children': [{'folio': 'UNIT-001', 'component': 'RBC', 'expires_at': '2026-11-16T12:00:00Z'}]}
    journal = Journal(tmp_path, 'https://lab', 'user', 'tenant', Keys())
    record = prepare_command(journal, 'resource_fractionate', parent, body)
    keys = []
    class API:
        wrong = False
        def authorized(self, _service, path, operation, **kwargs):
            if operation == 'resource_fractionate':
                keys.append(kwargs['key'])
                assert kwargs['body'] == body
                if len(keys) == 1: raise ConnectionError('respuesta perdida')
                return [{'parent_id': parent, 'child_id': child, 'donation_id': donation}]
            if path.endswith(parent): return {'id': parent, 'donation_id': donation}
            return {'id': child, 'donation_id': donation, 'folio': 'WRONG' if self.wrong else 'UNIT-001',
                    'component': 'RBC', 'expires_at': '2026-11-16T12:00:00Z'}
    api = API()
    with pytest.raises(ConnectionError): submit_command(api, journal, record, fresh=True)
    api.wrong = True
    with pytest.raises(ContractError): submit_command(api, journal, journal.list()[0])
    assert journal.list()[0]['state'] == 'PREPARED'
    api.wrong = False
    submit_command(api, journal, journal.list()[0])
    assert keys == [record['key']] * 3
    assert journal.list()[0]['state'] == 'DONE'
