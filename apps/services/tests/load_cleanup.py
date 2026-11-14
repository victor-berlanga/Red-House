"""Cierre coordinado de sesiones del arnés Locust; solo memoria."""

from scripts.load_client import LoadFailure


class SessionCleanup:
    """Conserva clientes en memoria hasta que Locust termine sus usuarios."""

    def __init__(self, environment):
        self.environment = environment
        self.entries = []
        self.finished = False

    def add(self, api, client):
        self.entries.append((api, client))

    def failure(self, code):
        self.environment.events.request.fire(
            request_type="CLEANUP",
            name="Cierre / sesiones",
            response_time=0,
            response_length=0,
            exception=LoadFailure(code),
            context={},
        )

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
                    return
        except BaseException as exc:
            self.failure("drain_" + type(exc).__name__)
            if not isinstance(exc, Exception):
                raise
            return
        for api, client in self.entries:
            try:
                if api.user is not None and not api.refresh:
                    raise LoadFailure("cleanup_missing_refresh")
                api.close()
            except BaseException as exc:
                # No registrar mensajes que pudieran contener credenciales.
                self.failure("cleanup_" + type(exc).__name__)
                if not isinstance(exc, Exception):
                    raise
            finally:
                try:
                    client.close()
                except BaseException as exc:
                    self.failure("client_close_" + type(exc).__name__)
                    if not isinstance(exc, Exception):
                        raise
        self.entries.clear()


def cleanup_for(environment):
    cleanup = getattr(environment, "_redhouse_load_cleanup", None)
    if cleanup is None:
        cleanup = SessionCleanup(environment)
        environment._redhouse_load_cleanup = cleanup
        environment.events.test_stop.add_listener(cleanup.finish)
    elif cleanup.finished:
        if cleanup.entries:
            raise RuntimeError("Cierre anterior incompleto; no iniciar otra carga.")
        cleanup.finished = False
    return cleanup
