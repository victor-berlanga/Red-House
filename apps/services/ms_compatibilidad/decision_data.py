"""Technical consistency facts without free-text immunological inference."""

from flask import g
from redhouse.api import endpoint
from redhouse.db import transaction
from redhouse.errors import APIError


def install(app):
    @endpoint(
        app, "/api/v1/decision-data", roles=("MEDICAL",), result={"type": "object"}
    )
    def laboratory_decision_data():
        with transaction() as conn:
            rows = conn.execute(
                "SELECT r.id,r.sample_id,r.tenant_id,s.tenant_id AS sample_tenant_id,s.resource_id,s.recipient_id,s.donation_id,s.request_id,r.crossmatch FROM lab_results r JOIN lab_samples s ON s.id=r.sample_id WHERE r.tenant_id=%s ORDER BY r.id LIMIT 10001",
                (g.actor["tenant_id"],),
            ).fetchall()
            if len(rows) > 10000:
                raise APIError("volume_limit", "Más de 10000 resultados.", 422)
            return {"source": "compatibilidad", "results": rows}
