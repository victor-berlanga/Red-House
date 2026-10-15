"""Definición de almacenamiento común y vistas de compatibilidad de las API."""

# Tabla API -> tabla relacional compartida, columnas API -> columnas físicas.
TABLES = {
    "institutions": (
        "institution",
        {"id": "institution_id", "name": "institution_name", "version": "version_no"},
    ),
    "users": ("user_account", {"id": "account_id", "version": "version_no"}),
    "sessions": ("web_session", {"id": "session_id", "user_id": "account_id"}),
    "catalogue": ("catalogue_entry", {}),
    "donors": (
        "donor",
        {
            "id": "donor_id",
            "tenant_id": "institution_id",
            "folio": "record_code",
            "status": "current_status",
            "version": "version_no",
            "created_at": "registered_at",
            "user_id": "account_id",
        },
    ),
    "donor_reviews": ("donor_review", {"id": "review_id", "created_at": "occurred_at"}),
    "donations": (
        "donation",
        {
            "id": "donation_id",
            "status": "current_status",
            "version": "version_no",
            "created_at": "registered_at",
        },
    ),
    "donation_steps": (
        "donation_event",
        {
            "id": "event_id",
            "state": "status",
            "reason": "observation",
            "created_at": "occurred_at",
        },
    ),
    "campaigns": (
        "campaign",
        {
            "id": "campaign_id",
            "tenant_id": "institution_id",
            "status": "current_status",
            "version": "version_no",
        },
    ),
    "appointments": (
        "appointment",
        {"id": "appointment_id", "status": "current_status"},
    ),
    "recipients": (
        "recipient",
        {
            "id": "recipient_id",
            "tenant_id": "institution_id",
            "folio": "record_code",
            "status": "current_status",
            "version": "version_no",
        },
    ),
    "requests": (
        "blood_request",
        {
            "id": "request_id",
            "status": "current_status",
            "version": "version_no",
            "created_at": "requested_at",
            "urgency": "priority_level",
        },
    ),
    "holds": ("request_hold", {}),
    "resources": ("resource", {"id": "resource_id", "kind": "resource_kind"}),
    "resource_reviews": ("resource_review", {}),
    "operations": ("allocation_operation", {}),
    "reservations": (
        "blood_allocation",
        {
            "id": "allocation_id",
            "status": "current_status",
            "created_at": "reserved_at",
        },
    ),
    "movements": ("blood_movement", {"id": "movement_id", "created_at": "occurred_at"}),
    "evaluations": (
        "candidate_evaluation",
        {"id": "evaluation_id", "created_at": "occurred_at"},
    ),
    "reviews": ("blood_review", {"id": "review_id", "created_at": "occurred_at"}),
    "routes": (
        "regional_route",
        {
            "id": "route_id",
            "source": "source_reference",
            "version": "version_no",
            "updated_at": "recorded_at",
        },
    ),
    "rankings": ("ranking_run", {}),
    "proposals": ("balance_proposal", {}),
    "shipments": (
        "shipment",
        {
            "id": "shipment_id",
            "reservation_id": "allocation_id",
            "transport_user_id": "transport_id",
            "status": "current_status",
            "version": "version_no",
        },
    ),
    "transitions": ("shipment_transition", {}),
    "telemetry": ("transport_telemetry", {"id": "telemetry_id"}),
    "files": (
        "stored_file",
        {"id": "file_id", "size": "size_bytes", "status": "current_status"},
    ),
    "chains": ("custody_chain", {}),
    "custody_events": (
        "custody_event",
        {"id": "event_id", "hash": "event_hash", "created_at": "occurred_at"},
    ),
    "alerts": (
        "notification",
        {
            "id": "notification_id",
            "tenant_id": "institution_id",
            "target_user_id": "target_account_id",
            "resource_id": "entity_reference",
            "status": "current_status",
        },
    ),
    "audit_events": (
        "audit_event",
        {
            "id": "event_id",
            "tenant_id": "institution_id",
            "source": "source_service",
            "created_at": "occurred_at",
        },
    ),
    "checks": (
        "service_health_check",
        {"id": "check_id", "version": "deployed_version", "created_at": "checked_at"},
    ),
}
COMMON_TABLES = (
    "schema_version",
    "activity_events",
    "outbox",
    "inbox",
    "idempotency",
    "decisions",
    "worker_health",
)
# References shared by services become real SQL constraints, not HTTP assumptions.
REFERENCES = {
    "users": {"tenant_id": ("institutions", "id")},
    "donors": {"tenant_id": ("institutions", "id"), "user_id": ("users", "id")},
    "donor_reviews": {"actor_id": ("users", "id")},
    "donations": {"tenant_id": ("institutions", "id")},
    "donation_steps": {"actor_id": ("users", "id")},
    "campaigns": {"tenant_id": ("institutions", "id")},
    "appointments": {"tenant_id": ("institutions", "id")},
    "recipients": {"tenant_id": ("institutions", "id")},
    "requests": {"tenant_id": ("institutions", "id")},
    "holds": {"resource_id": ("resources", "id")},
    "resources": {
        "tenant_id": ("institutions", "id"),
        "current_institution_id": ("institutions", "id"),
        "donation_id": ("donations", "id"),
    },
    "resource_reviews": {"actor_id": ("users", "id")},
    "operations": {"user_id": ("users", "id"), "tenant_id": ("institutions", "id")},
    "reservations": {
        "hold_id": ("holds", "id"),
        "request_id": ("requests", "id"),
        "recipient_id": ("recipients", "id"),
        "origin_id": ("institutions", "id"),
        "destination_id": ("institutions", "id"),
        "evaluation_id": ("evaluations", "id"),
        "route_id": ("routes", "id"),
    },
    "movements": {"actor_id": ("users", "id")},
    "evaluations": {
        "tenant_id": ("institutions", "id"),
        "request_id": ("requests", "id"),
    },
    "reviews": {
        "tenant_id": ("institutions", "id"),
        "actor_id": ("users", "id"),
        "resource_id": ("resources", "id"),
    },
    "routes": {
        "origin_id": ("institutions", "id"),
        "destination_id": ("institutions", "id"),
    },
    "rankings": {
        "tenant_id": ("institutions", "id"),
        "evaluation_id": ("evaluations", "id"),
    },
    "proposals": {"tenant_id": ("institutions", "id")},
    "shipments": {
        "reservation_id": ("reservations", "id"),
        "origin_id": ("institutions", "id"),
        "destination_id": ("institutions", "id"),
        "transport_user_id": ("users", "id"),
    },
    "transitions": {"actor_id": ("users", "id")},
    "telemetry": {"actor_id": ("users", "id")},
    "files": {"owner_id": ("users", "id")},
    "chains": {
        "id": ("shipments", "id"),
        "origin_id": ("institutions", "id"),
        "destination_id": ("institutions", "id"),
    },
    "alerts": {
        "tenant_id": ("institutions", "id"),
        "target_user_id": ("users", "id"),
        "acknowledged_by": ("users", "id"),
    },
    "audit_events": {"tenant_id": ("institutions", "id"), "actor_id": ("users", "id")},
}


def service_schema(service):
    from .config import SERVICES

    if service not in SERVICES:
        raise ValueError("Servicio desconocido")
    return "access_" + service
