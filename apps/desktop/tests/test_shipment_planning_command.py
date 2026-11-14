"""Estados durables de planificación; dobles, sin red ni motores."""
from uuid import uuid4

import pytest
from cryptography.fernet import Fernet
from redhouse_desktop.client import ContractError
from redhouse_desktop.durable_commands import prepare_command, submit_command, update_shipment_command
from redhouse_desktop.journal import Journal


class Keys:
    def __init__(self):
        self.key = Fernet.generate_key()

    def get(self, identifier, exists):
        return self.key


def body():
    return {'reservation_id': str(uuid4()), 'transport_user_id': str(uuid4()),
            'departure_at': '2026-11-14T12:00:00Z', 'eta': '2026-11-14T13:00:00Z',
            'reason': 'Traslado autorizado', 'human_confirmation': 'true'}


def test_response_lost_reuses_key_and_pending_requires_authorized_poll(tmp_path):
    keys = Keys()
    journal = Journal(tmp_path, 'https://lab', 'user', 'tenant', keys)
    intent = body()
    record = prepare_command(journal, 'shipment_create', None, intent)
    shipment = {'id': str(uuid4()), 'reservation_id': intent['reservation_id'],
                'transport_user_id': intent['transport_user_id'],
                'inventory_pending': True, 'status': 'PLANNED'}
    sent = []

    class API:
        def authorized(self, service, path, operation, **kwargs):
            sent.append(kwargs['key'])
            assert kwargs['body'] == intent
            if len(sent) == 1: raise ConnectionError('respuesta perdida')
            return shipment

    with pytest.raises(ConnectionError):
        submit_command(API(), journal, record, fresh=True)
    reopened = Journal(tmp_path, 'https://lab', 'user', 'tenant', keys)
    submit_command(API(), reopened, reopened.list()[0])
    saved = reopened.list()[0]
    assert sent == [record['key'], record['key']]
    assert saved['state'] == 'PENDING' and saved['operation_id'] == shipment['id']
    with pytest.raises(ContractError):
        update_shipment_command(reopened, saved, dict(shipment, id=str(uuid4()), inventory_pending=False))
    assert reopened.list()[0]['state'] == 'PENDING'
    assert update_shipment_command(reopened, saved, dict(shipment, inventory_pending=False)) == 'COMPLETED'
    assert reopened.list()[0]['state'] == 'DONE'


def test_mismatched_shipment_or_unexpected_status_never_completes(tmp_path):
    journal = Journal(tmp_path, 'https://lab', 'user', 'tenant', Keys())
    intent = body()
    record = prepare_command(journal, 'shipment_create', None, intent)
    shipment = {'id': str(uuid4()), 'reservation_id': intent['reservation_id'],
                'transport_user_id': intent['transport_user_id'],
                'inventory_pending': False, 'status': 'PLANNED'}
    with pytest.raises(ContractError):
        update_shipment_command(journal, record, dict(shipment, transport_user_id=str(uuid4())))
    assert journal.list()[0]['state'] == 'PREPARED'
    assert update_shipment_command(journal, record, dict(shipment, status='CANCELLED')) == 'CONFLICT'
    assert journal.list()[0]['state'] == 'PENDING'
