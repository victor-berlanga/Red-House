"""Recorridos HTTP de carga sobre cuentas y datos exclusivamente sintéticos."""

import json
import os
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from uuid import uuid4

from scripts.load_client import LoadFailure


class TransactionTrace:
    """Diario privado de estos dos recorridos; nunca recibe credenciales."""

    def __init__(self, api, path, account, stage):
        self.api, self.account, self.stage = api, account, stage
        self.stream = path.open("x", encoding="utf-8")
        path.chmod(0o600)
        self.cycle = 0
        self.replay_remaining = 1

    def emit(self, kind, **fields):
        self.stream.write(
            json.dumps(
                {
                    "kind": kind,
                    "cycle": self.cycle,
                    "user_id": self.account["id"],
                    "tenant_id": self.account["tenant_id"],
                    "role": self.account["role"],
                    "stage": self.stage(),
                    "at": time.monotonic(),
                    **fields,
                },
                sort_keys=True,
            )
            + "\n"
        )
        self.stream.flush()
        os.fsync(self.stream.fileno())

    def begin(self):
        self.cycle += 1
        self.emit("cycle_start")

    def end(self, error):
        self.emit("cycle_end", success=error is None)

    def request(self, service, path, label, **kwargs):
        if kwargs.get("method", "GET") == "GET":
            return self.api.request(service, path, label, **kwargs)
        if service not in (
            "donantes",
            "inventario",
            "compatibilidad",
        ) or not kwargs.get("key"):
            raise LoadFailure("untracked_write")
        key = kwargs["key"]
        self.emit(
            "intent",
            key=key,
            service=service,
            path=path,
            canonical=kwargs.get("canonical", path),
            body=kwargs.get("body"),
            label=label,
        )
        result = self.api.request(service, path, label, **kwargs)
        self.emit("response", key=key, result=result)
        if self.replay_remaining:
            self.replay_remaining -= 1
            self.emit("replay_intent", key=key)
            repeated = self.api.request(
                service, path, "Idempotencia / Repetir mismo intento", **kwargs
            )
            if repeated != result:
                raise LoadFailure("idempotency_result_mismatch")
            self.emit("replay_response", key=key, result=repeated)
        return result

    def close(self):
        self.stream.close()


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


def inventory_cycle(api, _campaign_title, *, profile_id=None):
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
    if profile_id is None:
        return
    sample = api.request(
        "compatibilidad",
        "/api/v1/laboratory/samples",
        "Laboratorio / Registrar muestra",
        method="POST",
        expected=201,
        key=str(uuid4()),
        body={
            "resource_id": resource["id"],
            "profile_id": profile_id,
            "identifier": "LOAD-S-" + uuid4().hex[:20],
            "collected_at": datetime.now(timezone.utc).isoformat(),
        },
        check=lambda value: (
            value["resource_id"] == resource["id"]
            and value["profile_id"] == profile_id
            and value["status"] == "REQUESTED"
        ),
    )
    path = "/api/v1/laboratory/samples/" + sample["id"]
    received = api.request(
        "compatibilidad",
        path + "/receive",
        "Laboratorio / Recibir muestra",
        method="POST",
        key=str(uuid4()),
        canonical="/api/v1/laboratory/samples/{identifier}/receive",
        body={
            "version": sample["version"],
            "decision": "RECEIVED",
            "human_confirmation": True,
            "reason": "Recepción sintética del ensayo de carga",
        },
        check=lambda value: (
            value["id"] == sample["id"]
            and value["status"] == "RECEIVED"
            and value["version"] == sample["version"] + 1
        ),
    )
    api.request(
        "compatibilidad",
        path,
        "Laboratorio / Confirmar recepción",
        canonical="/api/v1/laboratory/samples/{identifier}",
        check=lambda value: (
            value["id"] == sample["id"]
            and value["resource_id"] == resource["id"]
            and value["status"] == "RECEIVED"
            and value["version"] == received["version"]
        ),
    )
