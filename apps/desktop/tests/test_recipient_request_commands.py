"""Correcciones versionadas y recuperación segura con cliente doble."""

from uuid import uuid4

import pytest
from cryptography.fernet import Fernet
from redhouse_desktop.client import ApiError, ContractError
from redhouse_desktop.durable_commands import prepare_command, submit_command
from redhouse_desktop.journal import Journal


class Keys:
    def __init__(self):
        self.key = Fernet.generate_key()

    def get(self, identifier, exists):
        return self.key


def test_request_edit_retries_same_patch_and_rejects_stale_result(tmp_path):
    keys = Keys()
    store = Journal(tmp_path, "https://lab", "user", "tenant", keys)
    identifier = str(uuid4())
    body = {
        "component": "RBC",
        "quantity": 2,
        "urgency": 2,
        "version": 3,
        "reason": "Corrección documentada",
        "human_confirmation": "true",
    }
    record = prepare_command(store, "request_edit", identifier, body)
    calls = []

    class API:
        def authorized(self, service, path, operation, **kwargs):
            calls.append((kwargs["method"], kwargs["key"]))
            if len(calls) == 1:
                raise ConnectionError("respuesta perdida")
            return dict(body, id=identifier, version=4)

    api = API()
    with pytest.raises(ConnectionError):
        submit_command(api, store, record, fresh=True)
    restored = Journal(tmp_path, "https://lab", "user", "tenant", keys)
    submit_command(api, restored, restored.list()[0])
    assert calls == [("PATCH", record["key"]), ("PATCH", record["key"])]
    assert restored.list()[0]["state"] == "DONE"
    other = prepare_command(restored, "request_edit", identifier, body)

    class Stale:
        def authorized(self, *args, **kwargs):
            return dict(body, id=identifier, version=3)

    with pytest.raises(ContractError):
        submit_command(Stale(), restored, other, fresh=True)
    assert restored.list()[1]["state"] == "PREPARED"


def test_cancel_conflict_after_uncertain_is_not_reported_success(tmp_path):
    store = Journal(tmp_path, "https://lab", "user", "tenant", Keys())
    body = {
        "version": 2,
        "reason": "Cancelación documentada",
        "human_confirmation": "true",
    }
    record = prepare_command(store, "request_cancel", str(uuid4()), body)

    class API:
        def authorized(self, *args, **kwargs):
            raise ApiError(409, "conflict", "Cambió el estado.")

    with pytest.raises(ApiError):
        submit_command(API(), store, record)
    assert store.list()[0]["status"] == "CONFLICT"
