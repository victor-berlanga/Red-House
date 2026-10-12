"""Rutas web: monitoring. Las reglas residen en las API propietarias."""

from .common import call, detail, portal, render_template, submit, table, url_for


@portal.get("/notificaciones")
def alerts():
    return table(
        "Notificaciones",
        "alertas",
        "alertas",
        "/api/v1/alerts",
        [("message_code", "Evento"), ("status", "Estado"), ("created_at", "Fecha")],
        actions=lambda row: (
            [
                (
                    "Marcar como leída",
                    url_for("portal.alert_ack", identifier=row["id"]),
                    "read",
                )
            ]
            if row["status"] == "OPEN"
            else []
        ),
    )


@portal.route("/notificaciones/<uuid:identifier>/atender", methods=["GET", "POST"])
def alert_ack(identifier):
    return submit(
        "alertas",
        "/api/v1/alerts/" + str(identifier) + "/acknowledge",
        [],
        title="Confirmar lectura del aviso",
        active="alertas",
        back=url_for("portal.alerts"),
    )


@portal.get("/auditoria")
def audit():
    return table(
        "Bitácora de auditoría",
        "audit",
        "auditoria",
        "/api/v1/events",
        [("action", "Acción"), ("source", "Origen"), ("created_at", "Centralización")],
        links=lambda row: url_for("portal.audit_detail", identifier=row["id"]),
    )


@portal.get("/auditoria/<uuid:identifier>")
def audit_detail(identifier):
    row = call("auditoria", "/api/v1/events/" + str(identifier))
    event = row["event"]
    return detail(
        "Evento de auditoría",
        "audit",
        dict(row, occurred_at=event["occurred_at"]),
        sections=[
            (
                "Trazabilidad",
                [
                    {
                        "correlation_id": event["correlation_id"],
                        "resource": event["resource_id"],
                    }
                ],
            )
        ],
    )


@portal.get("/monitoreo")
def monitor():
    data = call("monitoreo", "/api/v1/status")
    return render_template(
        "integration/monitor.html",
        title="Estado de la plataforma",
        active="monitoreo",
        latest=data["latest"],
        statistics={r["service"]: r for r in data["statistics"]},
    )
