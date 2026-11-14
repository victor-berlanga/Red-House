"""Idempotencia y correlación de colecta y procesamiento."""
from uuid import uuid4

import pytest
from cryptography.fernet import Fernet
from redhouse_desktop.client import ContractError
from redhouse_desktop.durable_commands import prepare_command, submit_command
from redhouse_desktop.journal import Journal


class Keys:
    def __init__(self): self.key = Fernet.generate_key()
    def get(self, identifier, exists): return self.key


def test_collection_reuses_key_and_rejects_other_scope(tmp_path):
    tenant, donor, identifier = (str(uuid4()) for _ in range(3))
    body = {'donor_id': donor, 'kind': 'BLOOD', 'component': 'RBC', 'collected_at': '2026-11-14T12:00:00Z', 'reason': 'Colecta documentada', 'human_confirmation': 'true'}
    journal = Journal(tmp_path, 'https://lab', 'user', tenant, Keys())
    record = prepare_command(journal, 'donation_create', None, body)
    sent = []
    class API:
        def __init__(self): self.user = {'tenant_id': tenant}
        def authorized(self, _service, _path, _operation, **kwargs):
            sent.append(kwargs['key'])
            if len(sent) == 1: raise ConnectionError('respuesta perdida')
            return dict(body, id=identifier, status='COLLECTED', tenant_id=str(uuid4()) if len(sent) == 2 else tenant)
    api = API()
    with pytest.raises(ConnectionError): submit_command(api, journal, record, fresh=True)
    with pytest.raises(ContractError): submit_command(api, journal, journal.list()[0])
    assert journal.list()[0]['state'] == 'PREPARED'
    submit_command(api, journal, journal.list()[0])
    assert sent == [record['key']] * 3 and journal.list()[0]['state'] == 'DONE'


def test_processing_requires_same_version_state_and_scope(tmp_path):
    tenant, identifier = str(uuid4()), str(uuid4())
    body = {'version': 3, 'state': 'PROCESSED', 'reason': 'Proceso documentado', 'human_confirmation': 'true'}
    journal = Journal(tmp_path, 'https://lab', 'user', tenant, Keys())
    record = prepare_command(journal, 'donation_step', identifier, body)
    class API:
        def __init__(self): self.user = {'tenant_id': tenant}
        def authorized(self, *_args, **_kwargs): return {'id': identifier, 'tenant_id': tenant, 'version': 4, 'status': 'REJECTED'}
    with pytest.raises(ContractError): submit_command(API(), journal, record, fresh=True)
    assert journal.list()[0]['state'] == 'PREPARED'
