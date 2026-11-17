"""Recorridos HTTP de carga sobre cuentas y datos exclusivamente sintéticos."""

import json
import os
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from uuid import uuid4

from scripts.load_client import LoadFailure, ReauthenticationRequired


class TransactionTrace:
    """Diario privado de recorridos sintéticos; nunca recibe credenciales."""

    def __init__(self, api, path, account, stage, reauthenticate=None):
        self.api, self.account, self.stage = api, account, stage
        self.stream = path.open("x", encoding="utf-8")
        path.chmod(0o600)
        self.reauthenticate = reauthenticate
        self.mfa_wait_ms = 0.0
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
        self.mfa_wait_ms = 0.0
        self.emit("cycle_start")

    def end(self, error):
        self.emit("cycle_end", success=error is None)

    def request(self, service, path, label, **kwargs):
        critical = kwargs.pop("critical", None)
        if "proof" in kwargs:
            raise LoadFailure("proof_must_not_enter_trace")
        if critical:
            if not self.reauthenticate or kwargs.get("method", "GET") != "POST":
                raise LoadFailure("reauthentication_handler_missing")
            kwargs["allow_reauthentication"] = True
        if kwargs.get("method", "GET") == "GET":
            return self.api.request(service, path, label, **kwargs)
        if service not in (
            "donantes",
            "inventario",
            "compatibilidad",
            "transporte",
        ) or not kwargs.get("key"):
            raise LoadFailure("untracked_write")

        def secret(value):
            if isinstance(value, dict):
                return any(
                    k.lower()
                    in {
                        "password",
                        "otp",
                        "challenge",
                        "proof",
                        "access_token",
                        "refresh_token",
                        "authorization",
                    }
                    or secret(v)
                    for k, v in value.items()
                )
            return isinstance(value, list) and any(secret(v) for v in value)

        if secret(kwargs.get("body")):
            raise LoadFailure("secret_must_not_enter_trace")
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
        try:
            result = self.api.request(service, path, label, **kwargs)
        except ReauthenticationRequired as challenge:
            if not critical:
                raise LoadFailure("unexpected_reauthentication") from None
            self.emit("reauthentication_requested", key=key, operation=critical[0])
            proof, waiting = self.reauthenticate(challenge.challenge, *critical)
            self.mfa_wait_ms += waiting
            self.emit("mfa_wait", key=key, duration_ms=waiting)
            try:
                result = self.api.request(service, path, label, proof=proof, **kwargs)
            finally:
                proof = None
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


def _confirmed(fetch, predicate, timeout=20):
    """Observe the original asynchronous command; never create a replacement."""
    deadline = time.monotonic() + timeout
    while True:
        value = fetch()
        if predicate(value):
            return value
        if value.get("status") in (
            "FAILED",
            "ROLLBACK_PENDING",
            "REJECTED",
            "CANCELLED",
        ):
            raise LoadFailure("business_command_failed")
        if time.monotonic() >= deadline:
            raise LoadFailure("business_command_pending")
        time.sleep(0.25)


def medical_cycle(api, case):
    """Academic confirmation of the exact prepared candidate, never ranking autopick."""
    request_id, resource_id = case["request_id"], case["resource_id"]
    api.request(
        "receptores",
        "/api/v1/requests/" + request_id,
        "Médico / Solicitud propia",
        canonical="/api/v1/requests/{identifier}",
        check=lambda row: row["id"] == request_id and row["status"] == "OPEN",
    )
    evaluation = api.request(
        "compatibilidad",
        "/api/v1/evaluations",
        "Médico / Evaluar",
        method="POST",
        expected=201,
        key=str(uuid4()),
        body={"request_id": request_id},
        check=lambda row: (
            row["request_id"] == request_id
            and sum(c["resource_id"] == resource_id for c in row["candidates"]) == 1
        ),
    )
    reviewed = api.request(
        "compatibilidad",
        "/api/v1/evaluations/" + evaluation["id"] + "/reviews",
        "Médico / Dictamen académico",
        canonical="/api/v1/evaluations/{identifier}/reviews",
        method="POST",
        expected=201,
        key=str(uuid4()),
        critical=("evaluation_review", evaluation["id"]),
        body={
            "resource_id": resource_id,
            "decision": "FAVORABLE",
            "human_confirmation": True,
            "reason": case["approved_reason"],
        },
        check=lambda row: (
            row["evaluation_id"] == evaluation["id"]
            and row["resource_id"] == resource_id
            and row["decision"] == "FAVORABLE"
        ),
    )
    operation = api.request(
        "inventario",
        "/api/v1/reservations",
        "Médico / Reservar",
        method="POST",
        expected=202,
        key=str(uuid4()),
        critical=("reservation_create", resource_id),
        body={
            "evaluation_id": evaluation["id"],
            "resource_id": resource_id,
            "human_confirmation": True,
            "reason": case["approved_reason"],
        },
    )
    final = _confirmed(
        lambda: api.request(
            "inventario",
            "/api/v1/operations/" + operation["operation_id"],
            "Médico / Confirmar operación",
            canonical="/api/v1/operations/{identifier}",
        ),
        lambda row: (
            row["operation_id"] == operation["operation_id"]
            and row["status"] == "COMPLETED"
            and row["reservation"] is not None
            and row["reservation"]["status"] == "RESERVED"
        ),
    )
    if (
        final["reservation"]["resource_id"] != resource_id
        or final["reservation"]["request_id"] != request_id
    ):
        raise LoadFailure("reservation_correlation")
    api.emit(
        "case_result",
        case_id=case["case_id"],
        resource_id=resource_id,
        evaluation_id=evaluation["id"],
        review_id=reviewed["id"],
        operation_id=operation["operation_id"],
        reservation_id=final["reservation"]["id"],
        status="RESERVED",
    )


def coordinator_cycle(api, case):
    reservation_id = case["reservation_id"]
    reserved = api.request(
        "inventario",
        "/api/v1/reservations/" + reservation_id,
        "Coordinación / Reserva propia",
        canonical="/api/v1/reservations/{identifier}",
        check=lambda row: (
            row["id"] == reservation_id
            and row["resource_id"] == case["resource_id"]
            and row["status"] == "RESERVED"
            and row["shipment_id"] is None
        ),
    )
    resource = api.request(
        "inventario",
        "/api/v1/resources/" + reserved["resource_id"],
        "Coordinación / Caducidad del recurso reservado",
        canonical="/api/v1/resources/{identifier}",
        check=lambda row: (
            row["id"] == reserved["resource_id"] == case["resource_id"]
            and row["status"] == "RESERVED"
        ),
    )
    route = api.request(
        "priorizacion_geografia",
        "/api/v1/routes/" + reserved["route_id"],
        "Coordinación / Ruta vigente",
        canonical="/api/v1/routes/{identifier}",
        check=lambda row: (
            row["id"] == reserved["route_id"]
            and row["version"] == reserved["route_version"]
        ),
    )
    api.request(
        "identidad_acceso",
        "/api/v1/users?"
        + urlencode({"q": case["transport_username"], "page_size": 20}),
        "Coordinación / Responsable habilitado",
        check=lambda value: any(
            row["id"] == case["transport_user_id"]
            and row["role"] == "TRANSPORT"
            and row["active"]
            and row["tenant_id"] == reserved["origin_id"]
            for row in value["items"]
        ),
    )
    departure = datetime.now(timezone.utc) + timedelta(minutes=1)
    eta = departure + timedelta(minutes=route["travel_minutes"] + 1)
    if eta >= datetime.fromisoformat(resource["expires_at"].replace("Z", "+00:00")):
        raise LoadFailure("prepared_reservation_expiring")
    planned = api.request(
        "transporte",
        "/api/v1/shipments",
        "Coordinación / Planificar",
        method="POST",
        expected=202,
        key=str(uuid4()),
        body={
            "reservation_id": reservation_id,
            "transport_user_id": case["transport_user_id"],
            "departure_at": departure.isoformat(),
            "eta": eta.isoformat(),
            "human_confirmation": True,
            "reason": case["approved_reason"],
        },
    )
    final = _confirmed(
        lambda: api.request(
            "transporte",
            "/api/v1/shipments/" + planned["id"],
            "Coordinación / Confirmar plan",
            canonical="/api/v1/shipments/{identifier}",
        ),
        lambda row: (
            row["id"] == planned["id"]
            and row["status"] == "PLANNED"
            and not row["inventory_pending"]
        ),
    )
    if (
        final["reservation_id"] != reservation_id
        or final["transport_user_id"] != case["transport_user_id"]
    ):
        raise LoadFailure("shipment_correlation")
    api.emit(
        "case_result",
        case_id=case["case_id"],
        reservation_id=reservation_id,
        resource_id=case["resource_id"],
        shipment_id=final["id"],
        status="PLANNED",
    )


def transport_cycle(api, case):
    shipment_id, resource_id = case["shipment_id"], case["resource_id"]
    path = "/api/v1/shipments/" + shipment_id
    current = api.request(
        "transporte",
        path,
        "Traslado / Tarea asignada",
        canonical="/api/v1/shipments/{identifier}",
        check=lambda row: (
            row["id"] == shipment_id
            and row["reservation_id"] == case["reservation_id"]
            and row["transport_user_id"] == api.account["id"]
            and row["status"] == "PREPARED"
            and not row["inventory_pending"]
        ),
    )
    context = api.request(
        "transporte",
        path + "/operational-context",
        "Traslado / Contrapartes",
        canonical="/api/v1/shipments/{identifier}/operational-context",
        check=lambda row: (
            row["shipment_id"] == shipment_id
            and row["shipment_version"] == current["version"]
        ),
    )
    for stage, field in (("COLLECTED", "origin"), ("DELIVERED", "destination")):
        counterparty = case[field + "_operator_id"]
        if not any(row["id"] == counterparty for row in context[field]["operators"]):
            raise LoadFailure("prepared_counterparty_unavailable")
        scanned = api.request(
            "transporte",
            path + "/scan",
            "Traslado / Verificar unidad",
            canonical="/api/v1/shipments/{identifier}/scan",
            method="POST",
            key=str(uuid4()),
            body={"scanned_resource_id": resource_id},
            check=lambda row: (
                row["shipment_id"] == shipment_id
                and row["resource_id"] == resource_id
                and row["verified"]
            ),
        )
        if scanned["version"] != current["version"]:
            raise LoadFailure("shipment_version_changed")
        current = api.request(
            "transporte",
            path + "/transitions",
            "Traslado / " + stage,
            canonical="/api/v1/shipments/{identifier}/transitions",
            method="POST",
            key=str(uuid4()),
            body={
                "state": stage,
                "version": current["version"],
                "human_confirmation": True,
                "reason": case["approved_reason"],
                "custody": {
                    "scanned_resource_id": resource_id,
                    "seal": case["seal"],
                    "captured_at": datetime.now(timezone.utc).isoformat(),
                    "reported_handover_user_id": counterparty,
                    "electronic_acceptance": True,
                },
            },
            check=lambda row, expected_stage=stage: (
                row["id"] == shipment_id and row["status"] == expected_stage
            ),
        )
        if stage == "COLLECTED":
            current = api.request(
                "transporte",
                path + "/transitions",
                "Traslado / IN_TRANSIT",
                canonical="/api/v1/shipments/{identifier}/transitions",
                method="POST",
                key=str(uuid4()),
                body={
                    "state": "IN_TRANSIT",
                    "version": current["version"],
                    "human_confirmation": True,
                    "reason": case["approved_reason"],
                },
                check=lambda row: (
                    row["id"] == shipment_id and row["status"] == "IN_TRANSIT"
                ),
            )
    api.request(
        "transporte",
        path,
        "Traslado / Confirmar entrega",
        canonical="/api/v1/shipments/{identifier}",
        check=lambda row: (
            row["id"] == shipment_id
            and row["status"] == "DELIVERED"
            and row["version"] == current["version"]
        ),
    )
    api.emit(
        "case_result",
        case_id=case["case_id"],
        resource_id=resource_id,
        reservation_id=case["reservation_id"],
        shipment_id=shipment_id,
        status="DELIVERED",
        gps_in_this_increment=False,
        accepted_by_destination=False,
    )
