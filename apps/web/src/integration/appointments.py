"""Presentación de inscripciones a campañas; no inventa horarios de atención."""

from flask import g
from ..access import BusinessError
from .client import call


def enrich_appointments(items):
    campaigns = g.setdefault("appointment_campaigns", {})
    donors = g.setdefault("appointment_donors", {})
    slots = g.setdefault("appointment_slots", {})
    sites = g.setdefault("appointment_sites", {})
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

        try:
            schedule = call("donantes", f"/api/v1/appointments/{row['id']}/schedule")
            row["schedule"] = schedule
            slot_id = schedule["slot_id"]
            if slot_id not in slots:
                slots[slot_id] = call("donantes", "/api/v1/campaign-slots/" + slot_id)
            slot = slots[slot_id]
            if not g.get("appointment_sites_loaded"):
                page = 1
                while True:
                    batch = call(
                        "identidad_acceso",
                        "/api/v1/appointment-sites",
                        params={"page": page, "page_size": 100},
                    )
                    sites.update({item["id"]: item["name"] for item in batch["items"]})
                    if page * 100 >= batch["total"] or not batch["items"]:
                        break
                    page += 1
                g.appointment_sites_loaded = True
            row.update(
                appointment_start=slot["starts_at"],
                appointment_end=slot["ends_at"],
                site_name=sites.get(slot["site_id"], "Sede no disponible"),
                schedule_status=schedule["status"],
            )
        except BusinessError as exc:
            if exc.status not in (404, 503):
                raise
            row.update(
                appointment_start=None,
                appointment_end=None,
                site_name="Sin horario asignado"
                if exc.status == 404
                else "Horario temporalmente no disponible",
                schedule_status=None,
            )
