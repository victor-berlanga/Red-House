"""Rutas web: monitoring. Las reglas residen en las API propietarias."""

from .common import call, detail, portal, render_template, submit, table, url_for
from ..presentation import related_alert


@portal.get("/notificaciones")
def alerts():
    return table(
        "Notificaciones",
        "alertas",
        "alertas",
        "/api/v1/alerts",
        [("message_code", "Evento"), ("status", "Estado"), ("created_at", "Fecha")],
        links=related_alert,
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
        prompt="Marcar esta notificación como leída.",
        active="alertas",
        back=url_for("portal.alerts"),
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
