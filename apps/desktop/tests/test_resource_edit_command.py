"""Control de versión y recuperación del intento de corrección de unidad."""
from uuid import uuid4

import pytest
from cryptography.fernet import Fernet
from redhouse_desktop.client import ContractError
from redhouse_desktop.durable_commands import prepare_command, submit_command
from redhouse_desktop.journal import Journal


class Keys:
    def __init__(self): self.key = Fernet.generate_key()
    def get(self, identifier, exists): return self.key


def test_resource_edit_preserves_intent_after_lost_response(tmp_path):
    keys = Keys()
    journal = Journal(tmp_path, 'https://lab', 'user', 'tenant', keys)
    identifier, location = str(uuid4()), str(uuid4())
    body = {'folio': 'UNIT-001', 'kind': 'BLOOD', 'component': 'RBC', 'blood_group': 'O-',
            'expires_at': '2026-11-16T12:00:00Z', 'collected_at': None, 'location_id': location,
            'donation_id': None, 'version': 3, 'reason': 'Corrección documentada', 'human_confirmation': 'true'}
    record = prepare_command(journal, 'resource_edit', identifier, body)
    sent = []
    class API:
        def authorized(self, service, path, operation, **kwargs):
            sent.append(kwargs['key'])
            assert kwargs['method'] == 'PATCH' and kwargs['body'] == body
            if len(sent) == 1: raise ConnectionError('respuesta perdida')
            return dict(body, id=identifier, version=4)
    with pytest.raises(ConnectionError): submit_command(API(), journal, record, fresh=True)
    restored = Journal(tmp_path, 'https://lab', 'user', 'tenant', keys)
    submit_command(API(), restored, restored.list()[0])
    assert sent == [record['key'], record['key']]
    assert restored.list()[0]['state'] == 'DONE'
    other = prepare_command(restored, 'resource_edit', identifier, body)
    class Wrong:
        def authorized(self, *_args, **_kwargs): return dict(body, id=identifier, version=4, location_id=str(uuid4()))
    with pytest.raises(ContractError): submit_command(Wrong(), restored, other, fresh=True)
    assert restored.list()[1]['state'] == 'PREPARED'
