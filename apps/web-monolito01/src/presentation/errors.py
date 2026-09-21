from flask import g, request, render_template

def business_error(error):
    if error.status in (403, 404) and getattr(g, "principal", None):
        from ..data_access.connection import transaction
        from ..data_access.repositories.audit import record
        with transaction() as conn:
            record(conn, g.principal, "ACCESS", "ENDPOINT", request.endpoint or "UNKNOWN",
                   "Operación denegada", outcome="DENIED")
    title = {403: 'No tienes los permisos requeridos', 404: 'Registro no disponible', 409: 'El registro no admite esta operación'}.get(error.status, 'Operación no completada')
    message = error.message
    if error.status == 403:
        message += ' Puedes volver al panel o solicitar al administrador que revise tu perfil y ámbito de acceso.'
    return render_template("error.html", title=title, message=message, code=error.status), error.status
