"""Finite custody clock tolerance; original captured timestamp remains unchanged."""
from datetime import timedelta

from redhouse.errors import APIError


def validate_custody_capture_time(captured, now):
    """Validate the existing 24h window with at most 5s of device clock lead."""
    if not now - timedelta(hours=24) <= captured <= now + timedelta(seconds=5):
        raise APIError(
            "custody_timestamp_invalid",
            "La fecha del intercambio está fuera del margen permitido. Revisa la hora del dispositivo antes de volver a confirmar.",
            409,
        )
