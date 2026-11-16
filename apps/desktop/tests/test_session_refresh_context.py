"""El contexto conserva SID durante refresh y falla cerrado si cambia."""
import base64
import json
from threading import Event, Thread
from types import SimpleNamespace
from uuid import uuid4

import pytest
from redhouse_desktop.client import Client, ContractError
from redhouse_desktop.session_context import OperationContext


def token(sid):
    payload = base64.urlsafe_b64encode(json.dumps({'sid': sid}).encode()).decode().rstrip('=')
    return 'header.' + payload + '.signature'


def client_and_context():
    client = Client('https://lab.invalid'); sid = str(uuid4())
    client.session_id = sid; client.access = token(sid); client.refresh = 'opaque'
    client.user = {'id': str(uuid4()), 'tenant_id': str(uuid4()), 'region_id': str(uuid4()), 'role': 'OPERATOR', 'active': True}
    return client, OperationContext(SimpleNamespace(client=client, journal=object())), sid


def test_refresh_in_flight_preserves_context_without_waiting_for_network():
    client, context, sid = client_and_context(); started, resume = Event(), Event(); errors = []
    def call(_service, path, *_args, **_kwargs):
        if path.endswith('/refresh'):
            started.set(); assert resume.wait(3)
            return {'access_token': token(sid), 'refresh_token': 'rotated'}
        return dict(client.user)
    client.call = call
    def rotate():
        try: client._rotate()
        except Exception as exc: errors.append(type(exc).__name__)
    worker = Thread(target=rotate); worker.start(); assert started.wait(3)
    assert client.access is None and context.current()
    resume.set(); worker.join(3)
    assert not worker.is_alive() and not errors and context.current()


def test_refresh_with_changed_sid_clears_client():
    client, context, _sid = client_and_context()
    client.call = lambda *_args, **_kwargs: {'access_token': token(str(uuid4())), 'refresh_token': 'rotated'}
    with pytest.raises(ContractError): client._rotate()
    assert client.user is None and client.session_id is None and not context.current()
