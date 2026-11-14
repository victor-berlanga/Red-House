"""Recuperación de alta de muestra con diario y cliente sintéticos."""

from uuid import uuid4

import pytest
from cryptography.fernet import Fernet
from redhouse_desktop.client import ContractError
from redhouse_desktop.durable_commands import prepare_command, submit_command
from redhouse_desktop.journal import Journal


class Keys:
    def __init__(self):
        self.key = Fernet.generate_key()

    def get(self, identifier, exists):
        return self.key


def test_sample_recovery_reuses_key_and_checks_subject(tmp_path):
    keys = Keys()
    journal = Journal(tmp_path, "https://lab", "user", "tenant", keys)
    body = {
        "resource_id": str(uuid4()),
        "profile_id": str(uuid4()),
        "identifier": "MUESTRA-01",
        "collected_at": "2026-01-01T12:00:00Z",
    }
    record = prepare_command(journal, "lab_sample_create", None, body)
    sent = []

    class API:
        def authorized(self, service, path, operation, **kwargs):
            sent.append(kwargs["key"])
            assert kwargs["body"] == body
            if len(sent) == 1:
                raise ConnectionError("respuesta perdida")
            return dict(body, id=str(uuid4()))

    api = API()
    with pytest.raises(ConnectionError):
        submit_command(api, journal, record, fresh=True)
    restored = Journal(tmp_path, "https://lab", "user", "tenant", keys)
    submit_command(api, restored, restored.list()[0])
    assert sent == [record["key"], record["key"]]
    assert restored.list()[0]["state"] == "DONE"

    other = prepare_command(restored, "lab_sample_create", None, body)

    class Wrong:
        def authorized(self, *args, **kwargs):
            return dict(body, id=str(uuid4()), resource_id=str(uuid4()))

    with pytest.raises(ContractError):
        submit_command(Wrong(), restored, other, fresh=True)
    assert restored.list()[1]["state"] == "PREPARED"

    class WrongTime:
        def authorized(self, *args, **kwargs):
            return dict(body, id=str(uuid4()), collected_at="2026-01-01T12:01:00Z")

    with pytest.raises(ContractError):
        submit_command(WrongTime(), restored, other, fresh=True)
    assert restored.list()[1]["state"] == "PREPARED"
