"""Recorridos HTTP de carga sobre cuentas y datos exclusivamente sintéticos."""

from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from uuid import uuid4


def appointment_cycle(api, campaign_title):
    donor = api.request(
        "donantes",
        "/api/v1/donors?page_size=20",
        "Citas / Expediente propio",
        check=lambda value: value["total"] == 1 and len(value["items"]) == 1,
    )["items"][0]
    campaign = api.request(
        "donantes",
        "/api/v1/campaigns?" + urlencode({"q": campaign_title, "page_size": 20}),
        "Citas / Buscar campaña",
        check=lambda value: (
            value["total"] == 1 and value["items"][0]["title"] == campaign_title
        ),
    )["items"][0]
    slots = api.request(
        "donantes",
        "/api/v1/campaign-slots?"
        + urlencode({"campaign_id": campaign["id"], "active": "true", "page_size": 20}),
        "Citas / Horarios autorizados",
        check=lambda value: (
            len(value["items"]) >= 2
            and all(item["campaign_id"] == campaign["id"] for item in value["items"])
        ),
    )["items"]
    booked = api.request(
        "donantes",
        "/api/v1/appointments",
        "Citas / Reservar",
        method="POST",
        expected=201,
        key=str(uuid4()),
        body={
            "donor_id": donor["id"],
            "campaign_id": campaign["id"],
            "slot_id": slots[0]["id"],
        },
        check=lambda value: (
            value["donor_id"] == donor["id"]
            and value["campaign_id"] == campaign["id"]
            and value["status"] == "BOOKED"
        ),
    )
    base = "/api/v1/appointments/" + booked["id"]
    schedule = api.request(
        "donantes",
        base + "/schedule",
        "Citas / Consultar horario",
        canonical="/api/v1/appointments/{identifier}/schedule",
        check=lambda value: (
            value["id"] == booked["id"] and value["slot_id"] == slots[0]["id"]
        ),
    )
    moved = api.request(
        "donantes",
        base + "/commands",
        "Citas / Reprogramar",
        method="POST",
        key=str(uuid4()),
        canonical="/api/v1/appointments/{identifier}/commands",
        body={
            "human_confirmation": True,
            "reason": "Escenario sintético de carga",
            "version": schedule["version"],
            "action": "RESCHEDULE",
            "slot_id": slots[1]["id"],
        },
        check=lambda value: (
            value["id"] == booked["id"]
            and value["slot_id"] == slots[1]["id"]
            and value["version"] == schedule["version"] + 1
        ),
    )
    cancelled = api.request(
        "donantes",
        base + "/commands",
        "Citas / Cancelar",
        method="POST",
        key=str(uuid4()),
        canonical="/api/v1/appointments/{identifier}/commands",
        body={
            "human_confirmation": True,
            "reason": "Cierre del escenario sintético",
            "version": moved["version"],
            "action": "CANCEL",
        },
        check=lambda value: (
            value["id"] == booked["id"]
            and value["status"] == "CANCELLED"
            and value["version"] == moved["version"] + 1
        ),
    )
    api.request(
        "donantes",
        base + "/schedule",
        "Citas / Confirmar cancelación",
        canonical="/api/v1/appointments/{identifier}/schedule",
        check=lambda value: (
            value["id"] == booked["id"]
            and value["status"] == "CANCELLED"
            and value["version"] == cancelled["version"]
        ),
    )


def inventory_cycle(api, _campaign_title):
    folio = "LOAD-" + uuid4().hex[:20]
    resource = api.request(
        "inventario",
        "/api/v1/resources",
        "Inventario / Registrar cuarentena",
        method="POST",
        expected=201,
        key=str(uuid4()),
        body={
            "folio": folio,
            "kind": "BLOOD",
            "component": "RBC",
            "blood_group": "O-",
            "expires_at": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
        },
        check=lambda value: value["folio"] == folio and value["status"] == "QUARANTINE",
    )
    api.request(
        "inventario",
        "/api/v1/resources/" + resource["id"],
        "Inventario / Consultar unidad registrada",
        canonical="/api/v1/resources/{identifier}",
        check=lambda value: (
            value["id"] == resource["id"]
            and value["folio"] == folio
            and value["status"] == "QUARANTINE"
        ),
    )
