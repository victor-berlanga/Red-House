"""Minimal donation provenance facts; donor identities stay with their owner."""

from flask import g
from redhouse.api import endpoint
from redhouse.db import transaction
from redhouse.errors import APIError


def install(app):
    @endpoint(
        app, "/api/v1/decision-data", roles=("MEDICAL",), result={"type": "object"}
    )
    def donation_decision_data():
        with transaction() as conn:
            rows = conn.execute(
                "SELECT d.id,d.kind,d.component,d.status,d.version,d.collected_at,(p.tenant_id=d.tenant_id) AS subject_tenant_matches,EXISTS(SELECT 1 FROM donation_steps s WHERE s.donation_id=d.id) AS has_history FROM donations d JOIN donors p ON p.id=d.donor_id WHERE d.tenant_id=%s ORDER BY d.id LIMIT 10001",
                (g.actor["tenant_id"],),
            ).fetchall()
            if len(rows) > 10000:
                raise APIError("volume_limit", "Más de 10000 donaciones.", 422)
            return {"source": "donantes", "donations": rows}
