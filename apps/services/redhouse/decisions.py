"""Motivos y cambios privados del propietario, atómicos con la operación."""

from uuid import uuid4

from flask import g

from .db import insert


def record(conn, resource_id, tenant_id, action, reason, changes=None):
    # Conserva el motivo autorizado y nombres de campos, sin replicar estudios,
    # identidad clínica, contraseñas ni contenido de documentos en la bitácora.
    contexts = g.setdefault("audit_changes", {})
    contexts[str(resource_id)] = {
        "reason": reason,
        "changed_fields": sorted((changes or {}).keys()),
        "changes": {
            k: v
            for k, v in (changes or {}).items()
            if k
            in (
                "status",
                "state",
                "active",
                "version",
                "mode",
                "previous_status",
                "cancelled_appointments",
                "capacity",
                "quantity",
            )
        },
    }
    return insert(
        conn,
        "decisions",
        dict(
            id=str(uuid4()),
            resource_id=resource_id,
            tenant_id=tenant_id,
            actor_id=g.actor["id"],
            action=action,
            reason=reason,
            changes=changes or {},
        ),
    )


def history(conn, resource_id):
    # El endpoint debe autorizar el recurso antes de invocar este helper.
    return conn.execute(
        "SELECT id,actor_id,action,reason,changes,created_at FROM decisions "
        "WHERE resource_id=%s ORDER BY created_at,id",
        (resource_id,),
    ).fetchall()
