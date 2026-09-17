from flask import g, request, render_template

def business_error(error):
    if error.status in (403, 404) and getattr(g, "principal", None):
        from ..data_access.connection import transaction
        from ..data_access.repositories.audit import record
        with transaction() as conn:
            record(conn, g.principal, "ACCESS", "ENDPOINT", request.endpoint or "UNKNOWN",
                   "Operación denegada", outcome="DENIED")
    return render_template("error.html", title="Operación no completada", message=error.message, code=error.status), error.status

