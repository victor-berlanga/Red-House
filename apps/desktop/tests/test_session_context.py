"""Carreras de sesión del candidato privado; ningún servicio externo."""
from types import SimpleNamespace
import base64
import json
from uuid import uuid4

from cryptography.fernet import Fernet
from PySide6.QtWidgets import QApplication
from redhouse_desktop.app import Window
from redhouse_desktop.client import ApiError
from redhouse_desktop.journal import Journal

app = QApplication.instance() or QApplication([])


class Keys:
    def __init__(self): self.key = Fernet.generate_key()
    def get(self, identifier, exists): return self.key


class FakeClient:
    def __init__(self, user, tenant, behavior):
        self.user = {'id': user, 'tenant_id': tenant, 'role': 'OPERATOR'}
        self.session_id=str(uuid4())
        payload=base64.urlsafe_b64encode(json.dumps({'sid':self.session_id}).encode()).decode().rstrip('=')
        self.access='header.'+payload+'.signature'
        self.behavior = behavior; self.sent = []
    def authorized(self, _service, _path, _op, **kwargs):
        self.sent.append(kwargs['key'])
        if self.behavior == 'challenge':
            raise ApiError(403, 'reauthentication_required', 'confirmación', [{'field': 'reauthentication', 'code': 'challenge', 'challenge': 'x' * 60}])
        return {'id': self.target, 'tenant_id': self.user['tenant_id'], 'status': 'ACKNOWLEDGED', 'acknowledged_by': self.user['id']}


def setup(tmp_path):
    user, tenant, target = (str(uuid4()) for _ in range(3))
    client = FakeClient(user, tenant, 'ok'); client.target = target
    journal = Journal(tmp_path / 'old', 'https://lab', user, tenant, Keys())
    window = Window(); window.client = client; window.journal = journal
    jobs, callbacks = [], []
    window.run = lambda work, success, _message, failure=None: jobs.append((work, success, failure))
    window.received = lambda: callbacks.append('received')
    def switch():
        new_user = str(uuid4()); window.client = FakeClient(new_user, tenant, 'ok')
        window.journal = Journal(tmp_path / 'new', 'https://lab', new_user, tenant, Keys())
    def fire():
        work, success, failure = jobs.pop(0)
        try: value = work()
        except Exception as exc:
            if failure: failure(exc)
            else: raise
        else: success(value)
    return window, client, journal, target, jobs, callbacks, switch, fire


def test_change_before_prepare_never_creates_record(tmp_path):
    window, client, journal, target, jobs, callbacks, switch, fire = setup(tmp_path)
    window.secure_command('alert_ack', target, None); switch(); fire()
    assert not journal.list() and not client.sent and not callbacks


def test_change_before_send_keeps_prepared_original_key(tmp_path):
    window, client, journal, target, jobs, callbacks, switch, fire = setup(tmp_path)
    window.secure_command('alert_ack', target, None); fire()
    assert journal.list()[0]['state'] == 'PREPARED'
    switch(); fire()
    assert journal.list()[0]['state'] == 'PREPARED' and not client.sent and not callbacks


def test_change_during_challenge_does_not_retry(tmp_path, monkeypatch):
    window, client, journal, target, jobs, callbacks, switch, fire = setup(tmp_path)
    client.behavior = 'challenge'; continuations = []
    monkeypatch.setattr(window, 'reauthenticate', lambda _op, _id, _challenge, continuation, _ctx: continuations.append(continuation))
    window.secure_command('alert_ack', target, None); fire(); fire()
    assert len(client.sent) == 1 and len(continuations) == 1
    switch(); continuations[0]('proof')
    assert len(client.sent) == 1 and not jobs and journal.list()[0]['state'] == 'PREPARED' and not callbacks


def test_change_after_valid_response_keeps_confirmed_result_in_old_journal(tmp_path):
    window, client, journal, target, jobs, callbacks, switch, fire = setup(tmp_path)
    window.secure_command('alert_ack', target, None); fire()
    work, success, _failure = jobs.pop(0); response = work()
    assert journal.list()[0]['state'] == 'DONE'
    switch(); success(response)
    assert journal.list()[0]['state'] == 'DONE' and not callbacks
    assert len(client.sent) == 1 and journal.list()[0]['key'] == client.sent[0]


def test_change_during_send_never_updates_other_journal(tmp_path):
    window, client, journal, target, jobs, callbacks, switch, fire = setup(tmp_path)
    original = client.authorized
    def send_and_switch(*args, **kwargs):
        result = original(*args, **kwargs); switch(); return result
    client.authorized = send_and_switch
    window.secure_command('alert_ack', target, None); fire(); fire()
    assert journal.list()[0]['state'] == 'DONE' and len(client.sent) == 1
    assert not window.journal.list() and not callbacks


def test_new_session_same_account_is_not_same_context(tmp_path):
    window, client, journal, target, jobs, callbacks, switch, fire = setup(tmp_path)
    window.secure_command('alert_ack', target, None); fire()
    payload=base64.urlsafe_b64encode(json.dumps({'sid':str(uuid4())}).encode()).decode().rstrip('=')
    client.access='header.'+payload+'.signature'; client.session_id=json.loads(base64.urlsafe_b64decode(payload+'=' * (-len(payload) % 4)))['sid']
    fire()
    assert not client.sent and journal.list()[0]['state'] == 'PREPARED' and not callbacks


def test_lost_response_during_session_change_keeps_uncertain(tmp_path):
    window, client, journal, target, jobs, callbacks, switch, fire = setup(tmp_path)
    def send_and_lose(*_args, **_kwargs):
        client.sent.append('sent'); switch(); raise ConnectionError('respuesta perdida')
    client.authorized = send_and_lose
    window.secure_command('alert_ack', target, None); fire(); fire()
    assert journal.list()[0]['state'] == 'UNCERTAIN' and not window.journal.list() and not callbacks


def test_refreshed_access_same_sid_keeps_context(tmp_path):
    window, client, journal, target, jobs, callbacks, switch, fire = setup(tmp_path)
    window.secure_command('alert_ack', target, None); fire()
    header, payload, _signature = client.access.split('.')
    client.access = header + '.' + payload + '.new_signature'
    fire()
    assert len(client.sent) == 1 and journal.list()[0]['state'] == 'DONE' and callbacks == ['received']


def test_definitive_rejection_remains_failed_after_session_change(tmp_path):
    window, client, journal, target, jobs, callbacks, switch, fire = setup(tmp_path)
    def reject_and_switch(*_args, **_kwargs):
        client.sent.append('sent'); switch(); raise ApiError(409, 'conflict', 'rechazo definitivo')
    client.authorized = reject_and_switch
    window.secure_command('alert_ack', target, None); fire(); fire()
    entry = journal.list()[0]
    assert entry['state'] == 'DONE' and entry['status'] == 'FAILED'
    assert not window.journal.list() and not callbacks


def test_same_client_invalidated_clears_visible_session(tmp_path):
    window, client, journal, target, jobs, callbacks, switch, fire = setup(tmp_path)
    window.stack.setCurrentIndex(1); window.rows = [{'id': 'old'}]; window.table.setRowCount(1)
    def revoke(*_args, **_kwargs):
        client.user = None; client.access = None
        raise ApiError(401, 'identity_changed', 'Sesión terminada')
    client.authorized = revoke
    window.secure_command('alert_ack', target, None); fire(); fire()
    assert window.stack.currentIndex() == 0 and not window.rows and window.table.rowCount() == 0
    assert window.client is None and window.journal is None and journal.list()[0]['state'] == 'UNCERTAIN'


def test_refresh_in_progress_keeps_stable_context(tmp_path):
    from redhouse_desktop.session_context import OperationContext
    window, client, journal, target, jobs, callbacks, switch, fire = setup(tmp_path)
    context = OperationContext(window)
    client.access = None
    assert context.current()


def test_recovery_conflict_is_not_overwritten_by_context_change(tmp_path):
    from redhouse_desktop.durable_commands import prepare_command, submit_command
    window, client, journal, target, jobs, callbacks, switch, fire = setup(tmp_path)
    record = prepare_command(journal, 'alert_ack', target, None)
    def reject_and_switch(*_args, **_kwargs):
        client.sent.append('sent'); switch(); raise ApiError(409, 'conflict', 'conflicto de recuperación')
    client.authorized = reject_and_switch
    window.secure_attempt(record, 'alert_ack', target, lambda proof: submit_command(client, journal, record, proof=proof), lambda _:callbacks.append('received'))
    fire()
    entry = journal.list()[0]
    assert entry['state'] == 'PENDING' and entry['status'] == 'CONFLICT'
    assert not window.journal.list() and not callbacks
