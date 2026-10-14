"""Rutas web: dashboard. Las reglas residen en las API propietarias."""

from .common import BusinessError, call, display, g, portal, regional, render_template
from ..appointments import enrich_appointments


@portal.get("/panel")
@regional.get("/regional")
def dashboard():
    role = g.principal.role_code
    stats, charts, failures = [], [], []

    def fetch(service, path="/api/v1/summary", params=None):
        try:
            return call(service, path, params=params)
        except BusinessError as exc:
            failures.append((service, exc.message))
            return None

    if role in ("OPERATOR", "MEDICAL", "COORDINATOR"):
        stock = fetch("inventario")
        if stock:
            stats += [
                ("Recursos en tu ámbito", stock["total"]),
                ("Próximos a caducar · 48 h", stock["expiring"]),
                ("Requieren revisión por caducidad", stock["expired"]),
            ]
            charts += [
                ("Disponibilidad sanguínea por ABO / Rh", stock["groups"]),
                (
                    "Estado del inventario",
                    [
                        {"label": display(r["status"]), "value": r["value"]}
                        for r in stock["statuses"]
                    ],
                ),
            ]
            if role == "COORDINATOR":
                charts.append(
                    (
                        "Recursos por institución",
                        [
                            {"label": display(r["institution_id"]), "value": r["value"]}
                            for r in stock["institutions"]
                        ],
                    )
                )
        req = fetch("receptores") if role in ("MEDICAL", "OPERATOR") else None
        if req:
            stats.append(("Solicitudes institucionales", req["total"]))
            charts.append(
                (
                    "Urgencia capturada · solicitudes abiertas",
                    [
                        {"label": "Nivel " + str(r["label"]), "value": r["value"]}
                        for r in req["urgencies"]
                    ],
                )
            )
    if role in ("MEDICAL", "OPERATOR"):
        donors = fetch("donantes")
        if donors:
            stats.append(("Donantes institucionales", donors["total"]))
    if role in ("MEDICAL", "OPERATOR", "COORDINATOR", "TRANSPORT"):
        shipments = fetch("transporte")
        if shipments:
            stats.append(("Traslados autorizados", shipments["total"]))
            charts.append(
                (
                    "Etapas de traslado",
                    [
                        {"label": display(r["status"]), "value": r["value"]}
                        for r in shipments["statuses"]
                    ],
                )
            )
    alerts = call("alertas", "/api/v1/alerts", params={"page_size": 5})
    appointments, audit_events = [], []
    if role == "DONOR":
        registrations = fetch("donantes", "/api/v1/appointments", {"page_size": 5})
        if registrations:
            appointments = registrations["items"]
            enrich_appointments(appointments)
        # El resumen es personal; no cuenta instituciones ajenas a la tarea.
    elif role == "AUDITOR":
        audit = fetch("auditoria", "/api/v1/events", {"page_size": 5})
        if audit:
            stats = [("Eventos en la bitácora regional", audit["total"])]
            audit_events = audit["items"]
    elif not stats and role == "ADMIN":
        stats = [
            ("Instituciones de la región", len(g.institutions)),
            ("Notificaciones autorizadas", alerts["total"]),
        ]
    return render_template(
        "integration/dashboard.html",
        title="Panel principal",
        active="dashboard",
        stats=stats,
        charts=charts,
        failures=failures,
        alerts=alerts["items"],
        appointments=appointments,
        audit_events=audit_events,
    )
