"""Presentación de inscripciones a campañas; no inventa horarios de atención."""

from flask import g
from ..access import BusinessError
from .client import call


def enrich_appointments(items):
    campaigns = g.setdefault("appointment_campaigns", {})
    donors = g.setdefault("appointment_donors", {})
    for row in items:
        identifier = row["campaign_id"]
        if identifier not in campaigns:
            try:
                campaigns[identifier] = call(
                    "donantes", "/api/v1/campaigns/" + str(identifier)
                )
            except BusinessError as exc:
                if exc.status != 503:
                    raise
                campaigns[identifier] = None
        campaign = campaigns[identifier]
        row.update(
            campaign_title=campaign["title"]
            if campaign
            else "Campaña temporalmente no disponible",
            campaign_start=campaign["starts_at"] if campaign else None,
            campaign_end=campaign["ends_at"] if campaign else None,
        )
        if g.principal.role_code == "OPERATOR":
            identifier = row["donor_id"]
            if identifier not in donors:
                try:
                    donors[identifier] = call(
                        "donantes", "/api/v1/donors/" + str(identifier)
                    )["display_name"]
                except BusinessError as exc:
                    if exc.status != 503:
                        raise
                    donors[identifier] = "Donante temporalmente no disponible"
            row["donor_name"] = donors[identifier]
