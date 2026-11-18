from uuid import uuid4

from flask import g

from redhouse.api import atomic, endpoint, listing
from redhouse.db import get, insert, transaction, update
from redhouse.errors import APIError
from redhouse.event_model import Event
from redhouse.events import consume, emit
from redhouse.models import validate_id

SOURCES = (
    "donantes",
    "receptores",
    "inventario",
    "transporte",
    "monitoreo",
    "auditoria",
)


def register(app):
    @endpoint(
        app,
        "/internal/v1/events",
        "POST",
        model=Event,
        internal=SOURCES,
        delegate=False,
        summary="Generar alertas por evento con deduplicación y destinatarios explícitos",
    )
    def alert_ingest(data):
        if data["source"] != g.caller or not data["region_id"]:
            raise APIError("forbidden", "Fuente o región de evento incorrectas.", 403)
        action, metadata = data["action"], data["metadata"]
        recipients = [(data["tenant_id"], "OPERATOR", None)]
        if data["source"] == "auditoria" and action.startswith("AUDIT_FINDING_"):
            recipients = [
                (
                    metadata["recipient_tenant_id"],
                    metadata["recipient_role"],
                    metadata["recipient_user_id"],
                )
            ]
        elif action.startswith("REQUEST_"):
            recipients = [(data["tenant_id"], "MEDICAL", None)]
        elif action.startswith("SHIPMENT_") or action == "RESOURCE_RESERVED":
            recipients = [
                (metadata.get("origin_id", data["tenant_id"]), "OPERATOR", None),
                (metadata.get("destination_id", data["tenant_id"]), "OPERATOR", None),
            ]
        elif action in (
            "APPOINTMENT_BOOKED",
            "APPOINTMENT_REMINDER",
            "DONOR_REVIEWED",
        ) and metadata.get("recipient_user_id"):
            recipients.append(
                (data["tenant_id"], "DONOR", metadata["recipient_user_id"])
            )
        elif data["source"] == "monitoreo":
            recipients = [(data["tenant_id"], "ADMIN", None)]
        with transaction() as conn:
            if not consume(conn, data):
                return {"duplicate": True}
            for tenant, role, user in set(recipients):
                insert(
                    conn,
                    "alerts",
                    dict(
                        id=str(uuid4()),
                        event_id=data["event_id"],
                        tenant_id=tenant,
                        region_id=data["region_id"],
                        target_role=role,
                        target_user_id=user,
                        message_code=action,
                        resource_id=data["resource_id"],
                    ),
                )
        return {"stored": True, "recipients": len(set(recipients))}

    @endpoint(
        app,
        "/api/v1/alerts",
        paginated=True,
        summary="Bandeja autorizada: institución, rol y usuario",
        query=("q", "from_at", "until_at", "date_field", "sort"),
    )
    def alerts_list():
        with transaction() as conn:
            return listing(
                conn,
                "alerts",
                "tenant_id=%s AND target_role=%s AND (target_user_id IS NULL OR target_user_id=%s)",
                (g.actor["tenant_id"], g.actor["role"], g.actor["id"]),
                columns="alerts.*, (SELECT severity FROM alert_severity s WHERE s.id=alerts.id) AS severity",
            )

    @endpoint(
        app,
        "/api/v1/alerts/<identifier>",
        summary="Detalle de un aviso de la bandeja autorizada",
    )
    def alert_detail(identifier):
        # Mismo ámbito que la bandeja: institución, rol y usuario destinatario. Un aviso
        # ajeno responde 404 igual que uno inexistente, para no revelar que existe.
        validate_id(identifier)
        with transaction() as conn:
            row = conn.execute(
                "SELECT alerts.*, (SELECT severity FROM alert_severity s WHERE s.id=alerts.id) AS severity"
                " FROM alerts WHERE id=%s AND tenant_id=%s AND target_role=%s"
                " AND (target_user_id IS NULL OR target_user_id=%s)",
                (identifier, g.actor["tenant_id"], g.actor["role"], g.actor["id"]),
            ).fetchone()
        if not row:
            raise APIError("not_found", "Recurso inexistente.", 404)
        return row

    @endpoint(
        app,
        "/api/v1/alerts/<identifier>/acknowledge",
        "POST",
        summary="Acusar recibo sin modificar el hecho de origen",
    )
    def alert_ack(identifier):
        def work(conn):
            row = get(conn, "alerts", identifier, True)
            if (
                str(row["tenant_id"]) != g.actor["tenant_id"]
                or row["target_role"] != g.actor["role"]
                or (
                    row["target_user_id"]
                    and str(row["target_user_id"]) != g.actor["id"]
                )
            ):
                raise APIError("forbidden", "Alerta de otro destinatario.", 403)
            if row["status"] == "CLOSED":
                raise APIError("conflict", "La alerta está cerrada.", 409)
            result = update(
                conn,
                "alerts",
                identifier,
                {"status": "ACKNOWLEDGED", "acknowledged_by": g.actor["id"]},
            )
            emit(conn, "ALERT_ACKNOWLEDGED", identifier, row["tenant_id"])
            return result

        return atomic("alert_ack:" + identifier, {}, work)
