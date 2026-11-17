"""Destino durable: contrato real, diario cifrado y transporte simulado."""
from copy import deepcopy
from types import SimpleNamespace
from uuid import uuid4

import pytest
from cryptography.fernet import Fernet
from redhouse_desktop.client import ApiError, ContractError
from redhouse_desktop.durable_commands import prepare_command, submit_command
from redhouse_desktop.journal import Journal, JournalError


class Keys:
    def __init__(self): self.key = Fernet.generate_key()
    def get(self, identifier, exists): return self.key


@pytest.fixture
def case(tmp_path):
    actor, tenant, resource, previous, destination = [str(uuid4()) for _ in range(5)]
    keys = Keys()
    journal = Journal(tmp_path, 'https://fixture.invalid', actor, tenant, keys)
    body = {'version': 8, 'destination': 'TRANSPLANTED', 'reference': 'Referencia sintética',
            'occurred_at': '2026-11-16T15:00:00.123456+00:00', 'reason': 'Corrección documental sintética',
            'human_confirmation': 'true', 'supersedes': previous}
    result = {name: value for name, value in body.items() if name not in ('version', 'human_confirmation')}
    result.update(id=destination, resource_id=resource, tenant_id=tenant, author_id=actor, version=3)
    return SimpleNamespace(actor=actor, tenant=tenant, resource=resource, keys=keys, journal=journal,
                           body=body, result=result, user={'id': actor, 'tenant_id': tenant, 'role': 'MEDICAL'})


def test_destination_replay_uses_persisted_key_body_and_route(case, tmp_path):
    record = prepare_command(case.journal, 'resource_destination', case.resource, case.body)
    calls = []
    def authorized(service, path, operation, **kwargs):
        calls.append((service, path, operation, deepcopy(kwargs)))
        persisted = case.journal.list()[0]
        assert kwargs['key'] == persisted['key'] and kwargs['body'] == persisted['body']
        if len(calls) == 1: raise ConnectionError('respuesta perdida')
        return case.result
    client = SimpleNamespace(user=case.user, authorized=authorized)
    with pytest.raises(ConnectionError): submit_command(client, case.journal, record, fresh=True)
    case.journal.mark_uncertain(record['key'])
    reopened = Journal(tmp_path, 'https://fixture.invalid', case.actor, case.tenant, case.keys)
    recovered = reopened.list()[0]
    assert recovered['state'] == 'UNCERTAIN'
    submit_command(client, reopened, recovered)
    assert calls[0] == calls[1]
    assert calls[1][0:3] == ('inventario', '/api/v1/resources/'+case.resource+'/destination', 'resource_destination')
    assert calls[1][3]['method'] == 'POST' and calls[1][3]['request_schema'] == 'resource_destination.xsd'
    assert reopened.list()[0]['state'] == 'DONE' and reopened.list()[0]['operation_id'] == case.result['id']


@pytest.mark.parametrize('field', ['resource_id', 'tenant_id', 'author_id'])
def test_foreign_destination_never_closes_journal(case, field):
    record = prepare_command(case.journal, 'resource_destination', case.resource, case.body)
    result = dict(case.result, **{field: str(uuid4())})
    client = SimpleNamespace(user=case.user, authorized=lambda *a, **k: result)
    with pytest.raises(ContractError): submit_command(client, case.journal, record, fresh=True)
    assert case.journal.list()[0]['state'] == 'PREPARED'
    assert case.journal.list()[0]['operation_id'] is None


def test_reauthentication_preserves_original_attempt(case):
    record = prepare_command(case.journal, 'resource_destination', case.resource, case.body)
    calls = []
    def authorized(*args, **kwargs):
        calls.append(deepcopy(kwargs))
        if not kwargs['proof']:
            raise ApiError(403, 'reauthentication_required', 'Confirmación necesaria',
                           [{'field': 'reauthentication', 'code': 'challenge', 'challenge': 'synthetic-challenge'}])
        return case.result
    client = SimpleNamespace(user=case.user, authorized=authorized)
    with pytest.raises(ApiError) as caught: submit_command(client, case.journal, record, fresh=True)
    assert caught.value.challenge() == 'synthetic-challenge'
    assert case.journal.list()[0]['state'] == 'PREPARED'
    submit_command(client, case.journal, case.journal.list()[0], proof='synthetic-proof', fresh=True)
    assert calls[0]['key'] == calls[1]['key'] and calls[0]['body'] == calls[1]['body']
    assert calls[1]['proof'] == 'synthetic-proof' and case.journal.list()[0]['state'] == 'DONE'


def test_stale_recovery_requires_review_without_another_send(case):
    record = prepare_command(case.journal, 'resource_destination', case.resource, case.body)
    count = []
    def authorized(*args, **kwargs):
        count.append(kwargs['key']); raise ApiError(412, 'stale_version', 'Antecedente cambiado')
    client = SimpleNamespace(user=case.user, authorized=authorized)
    with pytest.raises(ApiError): submit_command(client, case.journal, record)
    pending = case.journal.list()[0]
    assert pending['state'] == 'PENDING' and pending['status'] == 'CONFLICT'
    with pytest.raises(JournalError): submit_command(client, case.journal, pending)
    assert count == [record['key']]


def test_destination_xsd_rejects_invalid_value_before_journal(case):
    with pytest.raises(ContractError):
        prepare_command(case.journal, 'resource_destination', case.resource, dict(case.body, destination='INVALID'))
    assert case.journal.list() == []


def test_destination_button_scope_and_busy_state():
    from PySide6.QtWidgets import QApplication
    from redhouse_desktop.app import Window
    application = QApplication.instance() or QApplication([])
    window = Window()
    try:
        for role, mode, visible in [('MEDICAL', 'inventory', True), ('OPERATOR', 'inventory', False),
                                    ('COORDINATOR', 'inventory', False), ('MEDICAL', 'results', False)]:
            window.client = SimpleNamespace(user={'role': role})
            window.mode = mode
            window.show_rows({'items': [], 'total': 0, 'page': 1})
            window.set_controls(True)
            assert (not window.resource_destination_button.isHidden()) == visible
            assert window.resource_destination_button.isEnabled() == visible
            window.set_controls(False)
            assert not window.resource_destination_button.isEnabled()
    finally:
        window.client = None
        window.close()
        application.processEvents()
