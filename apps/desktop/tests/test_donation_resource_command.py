"""La procedencia confirmada debe corresponder a la seleccionada."""
from uuid import uuid4

import pytest
from cryptography.fernet import Fernet
from redhouse_desktop.client import ContractError
from redhouse_desktop.durable_commands import prepare_command, submit_command
from redhouse_desktop.journal import Journal


class Keys:
    def __init__(self): self.key = Fernet.generate_key()
    def get(self, identifier, exists): return self.key


def test_donation_resource_rejects_other_origin(tmp_path):
    journal = Journal(tmp_path, 'https://lab', 'user', 'tenant', Keys())
    body = {'folio': 'UNIT-001', 'kind': 'BLOOD', 'component': 'RBC', 'blood_group': 'O-',
            'expires_at': '2026-11-16T12:00:00Z', 'collected_at': '2026-11-14T10:00:01.123456Z', 'donation_id': str(uuid4())}
    record = prepare_command(journal, 'resource_create', None, body)
    class API:
        def authorized(self, *_args, **_kwargs):
            return dict(body, id=str(uuid4()), donation_id=str(uuid4()))
    with pytest.raises(ContractError): submit_command(API(), journal, record, fresh=True)
    assert journal.list()[0]['state'] == 'PREPARED'
