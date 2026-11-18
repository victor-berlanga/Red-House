"""Cierre coordinado de sesiones del arnés Locust; solo memoria."""

import logging

import gevent

from scripts.load_client import LoadFailure


class SessionCleanup:
    """Conserva clientes en memoria hasta que Locust termine sus usuarios."""

    def __init__(self, environment):
        self.environment = environment
        self.entries = []
        self.finished = False
        self.closers = {}
        self.failure_codes = []

    def add(self, api, client):
        self.entries.append((api, client))

    def failure(self, code):
        self.failure_codes.append(code)
        logging.getLogger(__name__).warning("load_cleanup_failed code=%s", code)
        self.environment.events.request.fire(
            request_type="CLEANUP",
            name="Cierre / sesiones",
            response_time=0,
            response_length=0,
            exception=LoadFailure(code),
            context={},
        )

    def schedule_close(self, api, client):
        """Network cleanup must outlive the user greenlet being stopped."""
        token = id(api)
        if token not in self.closers and any(
            e[0] is api and e[1] is client for e in self.entries
        ):
            self.closers[token] = gevent.spawn(
                self.close_entry, api, client, preserve_error=True
            )
        return self.closers.get(token)

    def close_entry(self, api, client, *, preserve_error=False):
        """Compensate one actor even when startup failed; never close it twice."""
        entry = next((e for e in self.entries if e[0] is api and e[1] is client), None)
        if entry is None:
            return
        self.entries.remove(entry)
        try:
            if api.user is not None and not api.refresh:
                raise LoadFailure("cleanup_missing_refresh")
            api.close()
        except BaseException as exc:
            # No registrar mensajes que pudieran contener credenciales.
            self.failure("cleanup_" + type(exc).__name__)
            if not isinstance(exc, Exception) and not preserve_error:
                raise
        finally:
            try:
                client.close()
            except BaseException as exc:
                self.failure("client_close_" + type(exc).__name__)
                if not isinstance(exc, Exception) and not preserve_error:
                    raise

    def finish(self, **_kwargs):
        if self.finished:
            return
        self.finished = True
        users = self.environment.runner.user_greenlets
        try:
            if not users.join(timeout=10) or len(users):
                self.failure("users_not_drained")
                users.kill(block=True, timeout=5)
                if len(users):
                    self.failure("users_still_active")
        except BaseException as exc:
            self.failure("drain_" + type(exc).__name__)
            if not isinstance(exc, Exception):
                raise
        finally:
            for api, client in list(self.entries):
                self.schedule_close(api, client)
            gevent.joinall(list(self.closers.values()), timeout=30)
            for closer in self.closers.values():
                if not closer.ready():
                    self.failure("close_timeout")
                elif closer.exception is not None:
                    self.failure("close_" + type(closer.exception).__name__)


def cleanup_for(environment):
    cleanup = getattr(environment, "_redhouse_load_cleanup", None)
    if cleanup is None:
        cleanup = SessionCleanup(environment)
        environment._redhouse_load_cleanup = cleanup
        environment.events.test_stop.add_listener(cleanup.finish)
    elif cleanup.finished:
        if cleanup.entries or any(not g.ready() for g in cleanup.closers.values()):
            raise RuntimeError("Cierre anterior incompleto; no iniciar otra carga.")
        cleanup.finished = False
        cleanup.closers.clear()
        cleanup.failure_codes.clear()
    return cleanup
