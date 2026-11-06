"""Capacity facts from the request owner, excluding recipient identity."""

from flask import g
from redhouse.api import endpoint
from redhouse.db import transaction
from redhouse.errors import APIError


def install(app):
    @endpoint(
        app, "/api/v1/decision-data", roles=("MEDICAL",), result={"type": "object"}
    )
    def request_decision_data():
        with transaction() as conn:
            rows = conn.execute(
                "SELECT r.id,r.quantity,r.version,(SELECT count(*) FROM holds h WHERE h.request_id=r.id AND h.status<>'RELEASED') AS allocated FROM requests r WHERE r.tenant_id=%s ORDER BY r.id LIMIT 10001",
                (g.actor["tenant_id"],),
            ).fetchall()
            if len(rows) > 10000:
                raise APIError("volume_limit", "Más de 10000 solicitudes.", 422)
            return {"source": "receptores", "requests": rows}
