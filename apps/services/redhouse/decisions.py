"""Motivos y cambios privados del propietario, atómicos con la operación."""

from uuid import uuid4

from flask import g

from .db import insert


def record(conn, resource_id, tenant_id, action, reason, changes=None):
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
