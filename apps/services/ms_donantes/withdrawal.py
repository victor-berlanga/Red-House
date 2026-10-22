"""Baja institucional: elimina altas sin historia y conserva expedientes relacionados."""

from typing import Annotated

from pydantic import Field

from redhouse.api import atomic, endpoint
from redhouse.db import get, update
from redhouse.decisions import record
from redhouse.errors import APIError
from redhouse.events import emit
from redhouse.models import Confirm
from redhouse.security import own


class DonorWithdrawal(Confirm):
    version: Annotated[int, Field(ge=1)]


def require_active(row):
    if row["status"] == "INACTIVE":
        raise APIError("donor_inactive", "El donante está dado de baja.", 409)


def install(app):
    @endpoint(
        app,
        "/api/v1/donors/<identifier>/withdraw",
        "POST",
        model=DonorWithdrawal,
        roles=("MEDICAL",),
        summary="Dar de baja: borrar sin historial o conservar como inactivo",
    )
    def donor_withdraw(identifier, data):
        def work(conn):
            # Altas de citas, dictámenes y donaciones bloquean esta misma fila.
            donor = get(conn, "donors", identifier, True)
            own(donor["tenant_id"])
            require_active(donor)
            if donor["version"] != data["version"]:
                raise APIError(
                    "stale_version", "Expediente actualizado; vuelve a revisarlo.", 409
                )
            has_history = conn.execute(
                "SELECT 1 FROM donor_reviews WHERE donor_id=%s "
                "UNION ALL SELECT 1 FROM donations WHERE donor_id=%s "
                "UNION ALL SELECT 1 FROM appointments WHERE donor_id=%s "
                "UNION ALL SELECT 1 FROM decisions WHERE resource_id=%s LIMIT 1",
                (identifier, identifier, identifier, identifier),
            ).fetchone()
            # Las lecturas y el evento de alta no convierten una captura vacía
            # en historia clínica. Las correcciones con motivo sí se conservan.
            mode = "INACTIVE" if has_history else "DELETED"
            cancelled = 0
            if has_history:
                pending = conn.execute(
                    "UPDATE appointments SET status='CANCELLED' "
                    "WHERE donor_id=%s AND status='BOOKED' RETURNING id",
                    (identifier,),
                ).fetchall()
                cancelled = len(pending)
                for appointment in pending:
                    record(
                        conn,
                        appointment["id"],
                        donor["tenant_id"],
                        "APPOINTMENT_CANCELLED",
                        data["reason"],
                        {"cause": "DONOR_WITHDRAWN"},
                    )
                    emit(
                        conn,
                        "APPOINTMENT_CANCELLED",
                        appointment["id"],
                        donor["tenant_id"],
                    )
                update(
                    conn,
                    "donors",
                    identifier,
                    {"status": "INACTIVE", "version": donor["version"] + 1},
                )
            else:
                # Sin CASCADE: cualquier referencia no prevista impide el borrado.
                conn.execute("DELETE FROM donors WHERE id=%s", (identifier,))
            record(
                conn,
                identifier,
                donor["tenant_id"],
                "DONOR_WITHDRAWN",
                data["reason"],
                {
                    "mode": mode,
                    "previous_status": donor["status"],
                    "cancelled_appointments": cancelled,
                },
            )
            emit(
                conn,
                "DONOR_WITHDRAWN",
                identifier,
                donor["tenant_id"],
                targets=("auditoria", "alertas"),
                metadata={
                    "mode": mode,
                    "recipient_user_id": str(donor["user_id"])
                    if donor["user_id"]
                    else None,
                },
            )
            return {"id": identifier, "mode": mode, "cancelled_appointments": cancelled}

        return atomic("donor_withdraw:" + identifier, data, work)
