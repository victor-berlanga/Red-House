"""Correlación y recuperación de acuse sin acceso a servicios."""
from uuid import uuid4

import pytest
from cryptography.fernet import Fernet
from redhouse_desktop.client import ContractError
from redhouse_desktop.durable_commands import prepare_command, submit_command
from redhouse_desktop.journal import Journal


class Keys:
    def __init__(self): self.key = Fernet.generate_key()
    def get(self, identifier, exists): return self.key


def test_ack_retries_same_key_and_rejects_other_response(tmp_path):
    tenant, actor, alert = (str(uuid4()) for _ in range(3))
    journal = Journal(tmp_path, 'https://lab', actor, tenant, Keys())
    record = prepare_command(journal, 'alert_ack', alert, None)
    sent = []
    class Client:
        user = {'id': actor, 'tenant_id': tenant}
        def authorized(self, *_args, **kwargs):
            sent.append(kwargs['key'])
            if len(sent) == 1: raise ConnectionError('respuesta perdida')
            return {'id': str(uuid4()) if len(sent) == 2 else alert, 'tenant_id': tenant,
                    'status': 'ACKNOWLEDGED', 'acknowledged_by': actor}
    with pytest.raises(ConnectionError): submit_command(Client(), journal, record, fresh=True)
    with pytest.raises(ContractError): submit_command(Client(), journal, journal.list()[0])
    assert journal.list()[0]['state'] == 'PREPARED'
    submit_command(Client(), journal, journal.list()[0])
    assert sent == [record['key']] * 3 and journal.list()[0]['state'] == 'DONE'
