"""Integración del diario institucional con el transporte de comandos."""
from uuid import uuid4

import pytest
from cryptography.fernet import Fernet
from redhouse_desktop.client import ContractError
from redhouse_desktop.durable_commands import prepare_command, submit_command
from redhouse_desktop.journal import Journal


class Keys:
    def __init__(self): self.key = Fernet.generate_key()
    def get(self, identifier, exists): return self.key


def test_site_edit_reuses_key_and_rejects_wrong_tenant(tmp_path):
    tenant, identifier = str(uuid4()), str(uuid4())
    body = {'name': 'Sede', 'municipality': 'Monterrey', 'address': 'Dirección sintética',
            'active': True, 'version': 3, 'reason': 'Corrección documentada', 'human_confirmation': 'true'}
    journal = Journal(tmp_path, 'https://lab', 'user', tenant, Keys())
    record = prepare_command(journal, 'sites_edit', identifier, body)
    sent = []
    class API:
        def __init__(self): self.user = {'tenant_id': tenant}
        def authorized(self, _service, _path, _operation, **kwargs):
            sent.append(kwargs['key'])
            assert kwargs['method'] == 'PATCH' and kwargs['body'] == body
            if len(sent) == 1: raise ConnectionError('respuesta perdida')
            return dict(body, id=identifier, tenant_id=str(uuid4()) if len(sent) == 2 else tenant,
                        kind='sites', version=4, parent_id=None)
    api = API()
    with pytest.raises(ConnectionError): submit_command(api, journal, record, fresh=True)
    with pytest.raises(ContractError): submit_command(api, journal, journal.list()[0])
    assert journal.list()[0]['state'] == 'PREPARED'
    submit_command(api, journal, journal.list()[0])
    assert sent == [record['key']] * 3 and journal.list()[0]['state'] == 'DONE'
