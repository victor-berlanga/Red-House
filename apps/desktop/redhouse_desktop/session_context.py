"""Ancla una operación a la sesión y diario que la iniciaron."""
import base64
import json
from uuid import UUID


def session_id(token):
    # Solo vincula el contexto local. El servicio sigue validando la firma y la sesión.
    try:
        parts = token.split('.')
        if len(parts) != 3: raise ValueError()
        payload = json.loads(base64.urlsafe_b64decode(parts[1] + '=' * (-len(parts[1]) % 4)))
        value = payload['sid']
        if not isinstance(value, str) or str(UUID(value)) != value: raise ValueError()
        return value
    except (AttributeError, KeyError, TypeError, ValueError, UnicodeDecodeError):
        return None


class SessionChanged(Exception):
    """La cuenta cambió durante una operación."""


class OperationContext:
    def __init__(self, window):
        self.window = window
        self.client = window.client
        self.journal = window.journal
        if not self.client or not self.client.user or not self.journal:
            raise SessionChanged('La sesión terminó.')
        self.actor = tuple(self.client.user.get(key) for key in ('id', 'tenant_id', 'role'))
        self.sid = self.client.session_id
        if not all(self.actor) or not self.sid: raise SessionChanged('La sesión no tiene ámbito completo.')

    def current(self):
        user = self.client.user
        return (self.window.client is self.client and self.window.journal is self.journal and bool(user)
                and tuple(user.get(key) for key in ('id', 'tenant_id', 'role')) == self.actor
                and self.client.session_id == self.sid)

    def check(self):
        if not self.current(): raise SessionChanged('La sesión cambió.')

    def submit(self, record, callback):
        self.check()
        try:
            return callback()
        except Exception:
            # Si cambió la cuenta y no hay resultado válido, conservar clave y ámbito.
            if not self.current(): self.journal.mark_uncertain(record['key'])
            raise
