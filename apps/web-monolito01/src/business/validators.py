import re
from datetime import datetime, timezone
from uuid import UUID

from .access import BusinessError


def text(data, name, label, limit=120, required=True):
    value = str(data.get(name, "")).strip()
    if (required and not value) or len(value) > limit or any(ord(c) < 32 for c in value):
        raise BusinessError(f"Revisa {label}: es obligatorio y admite hasta {limit} caracteres." if required
                            else f"Revisa {label}: admite hasta {limit} caracteres sin controles.")
    return value


def code(data, name, label):
    value = text(data, name, label, 30).upper()
    if not re.fullmatch(r"[A-Z0-9][A-Z0-9_-]{1,29}", value):
        raise BusinessError(f"{label}: usa de 2 a 30 letras, números, guiones o guiones bajos.")
    return value


def choice(data, name, options, label):
    value = text(data, name, label, 40)
    if value not in options:
        raise BusinessError(f"Selecciona un valor válido para {label}.")
    return value


def identifier(data, name):
    try:
        return UUID(str(data.get(name, "")))
    except (ValueError, TypeError, AttributeError):
        raise BusinessError("Selecciona una referencia válida.") from None


def integer(data, name, minimum=1, maximum=1_000_000):
    try:
        value = int(data.get(name, ""))
        if not minimum <= value <= maximum:
            raise ValueError
        return value
    except (ValueError, TypeError):
        raise BusinessError(f"{name}: escribe un entero entre {minimum} y {maximum}.") from None


def email(data, name="login_email", required=True):
    value = text(data, name, "el correo electrónico", 180, required).lower()
    if value and not re.fullmatch(r"[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+", value):
        raise BusinessError("Escribe un correo electrónico válido.")
    return value


def password(value):
    if not 12 <= len(value) <= 128 or value.isspace():
        raise BusinessError("La contraseña debe tener entre 12 y 128 caracteres.")
    return value


def timestamp(data, name):
    try:
        result = datetime.fromisoformat(data.get(name, ""))
        # Formularios y etiquetas indican UTC. No se infiere una zona clínica.
        return result.replace(tzinfo=timezone.utc) if result.tzinfo is None else result.astimezone(timezone.utc)
    except (ValueError, TypeError):
        raise BusinessError("Escribe fechas válidas en UTC.") from None
