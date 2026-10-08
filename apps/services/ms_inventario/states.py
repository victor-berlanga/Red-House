"""Vocabulario público del inventario; alias v1 para consumidores anteriores."""

RESOURCE_STATES = (
    "QUARANTINE",
    "AVAILABLE",
    "RESERVED",
    "IN_TRANSIT",
    "RECEIVED",
    "WITHDRAWN",
)
RESERVATION_STATES = ("PENDING", "RESERVED", "IN_TRANSIT", "RECEIVED", "CANCELLED")
RESOURCE_FILTER = {**{s: s for s in RESOURCE_STATES}, "COLLECTED": "IN_TRANSIT"}
RESERVATION_FILTER = {**{s: s for s in RESERVATION_STATES}, "COLLECTED": "IN_TRANSIT"}
