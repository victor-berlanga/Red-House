"""Correlación y recuperación de decisiones de calidad."""
from uuid import uuid4

import pytest
from cryptography.fernet import Fernet
from redhouse_desktop.client import ContractError
from redhouse_desktop.durable_commands import prepare_command, submit_command
from redhouse_desktop.journal import Journal


class Keys:
    def __init__(self): self.key = Fernet.generate_key()
    def get(self, identifier, exists): return self.key


def test_binding_preserves_cold_controls_and_reuses_key(tmp_path):
    tenant, resource, profile, equipment, cold = [str(uuid4()) for _ in range(5)]
    body = {'version': 2, 'reason': 'Perfil documentado', 'human_confirmation': 'true',
            'lab_profile_id': profile, 'cold_equipment_id': equipment, 'cold_profile_id': cold}
    journal = Journal(tmp_path, 'https://lab', 'user', tenant, Keys())
    record = prepare_command(journal, 'resource_controls_create', resource, body)
    sent = []
    class API:
        user = {'tenant_id': tenant}
        def authorized(self, *_args, **kwargs):
            sent.append(kwargs['key'])
            if len(sent) == 1: raise ConnectionError('respuesta perdida')
            return {'id': resource, **{key: body[key] for key in ('lab_profile_id', 'cold_equipment_id', 'cold_profile_id')}}
    with pytest.raises(ConnectionError): submit_command(API(), journal, record, fresh=True)
    submit_command(API(), journal, journal.list()[0])
    assert sent == [record['key'], record['key']]
    assert journal.list()[0]['state'] == 'DONE'


def test_release_cannot_complete_with_another_version_or_scope(tmp_path):
    tenant, resource = str(uuid4()), str(uuid4())
    body = {'version': 2, 'reason': 'Decisión documentada', 'human_confirmation': 'true'}
    journal = Journal(tmp_path, 'https://lab', 'user', tenant, Keys())
    record = prepare_command(journal, 'resource_release', resource, body)
    class API:
        user = {'tenant_id': tenant}
        def authorized(self, *_args, **_kwargs):
            return {'id': resource, 'tenant_id': tenant, 'version': 2, 'status': 'AVAILABLE'}
    with pytest.raises(ContractError): submit_command(API(), journal, record, fresh=True)
    assert journal.list()[0]['state'] == 'PREPARED'


def test_review_does_not_close_on_other_result(tmp_path):
    tenant, result = str(uuid4()), str(uuid4())
    journal = Journal(tmp_path, 'https://lab', 'user', tenant, Keys())
    body = {'version': 1, 'reason': 'Revisión documentada', 'human_confirmation': 'true', 'decision': 'AUTHORIZED'}
    record = prepare_command(journal, 'lab_result_review', result, body)
    class API:
        user = {'tenant_id': tenant}
        def authorized(self, *_args, **_kwargs):
            return {'id': str(uuid4()), 'tenant_id': tenant, 'version': 1, 'status': 'AUTHORIZED'}
    with pytest.raises(ContractError): submit_command(API(), journal, record, fresh=True)
    assert journal.list()[0]['state'] == 'PREPARED'
