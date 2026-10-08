"""Rutas web: dashboard. Las reglas residen en las API propietarias."""

from .common import BusinessError, call, display, g, portal, regional, render_template


@portal.get("/panel")
@regional.get("/regional")
def dashboard():
    role = g.principal.role_code
    stats, charts, failures = [], [], []

    def fetch(service):
        try:
            return call(service, "/api/v1/summary")
        except BusinessError as exc:
            failures.append((service, exc.message))
            return None

    if role in ("OPERATOR", "MEDICAL", "COORDINATOR"):
        stock = fetch("inventario")
        if stock:
            stats += [
                ("Recursos en tu ámbito", stock["total"]),
                ("Próximos a caducar · 48 h", stock["expiring"]),
                ("Disponibles con fecha vencida", stock["expired"]),
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
        req = fetch("receptores")
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
    if not stats:
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
    )
