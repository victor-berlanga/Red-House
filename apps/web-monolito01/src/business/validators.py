import re
from datetime import datetime, timezone
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .access import BusinessError


def text(data, name, label, limit=120, required=True, *, multiline=False):
    value = str(data.get(name, "")).strip()
    if (required and not value) or len(value) > limit or any(ord(c) < 32 and not (multiline and c in '\n\r\t') for c in value):
        raise BusinessError(f"Revisa {label}: es obligatorio y admite hasta {limit} caracteres." if required
                            else f"Revisa {label}: admite hasta {limit} caracteres sin controles.", field=name)
    return value


def paragraph(data, name, label, limit=1000, required=True):
    return text(data,name,label,limit,required,multiline=True)


def code(data, name, label):
    value = text(data, name, label, 30).upper()
    if not re.fullmatch(r"[A-Z0-9][A-Z0-9_-]{1,29}", value):
        raise BusinessError(f"{label}: usa de 2 a 30 letras, números, guiones o guiones bajos.", field=name)
    return value


def choice(data, name, options, label):
    value = text(data, name, label, 40)
    if value not in options:
        raise BusinessError(f"Selecciona un valor válido para {label}.", field=name)
    return value


def identifier(data, name):
    try:
        return UUID(str(data.get(name, "")))
    except (ValueError, TypeError, AttributeError):
        raise BusinessError("Selecciona una referencia válida.", field=name) from None


def integer(data, name, minimum=1, maximum=1_000_000):
    try:
        value = int(data.get(name, ""))
        if not minimum <= value <= maximum:
            raise ValueError
        return value
    except (ValueError, TypeError):
        raise BusinessError(f"{name}: escribe un entero entre {minimum} y {maximum}.", field=name) from None


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
        if result.tzinfo is not None: return result.astimezone(timezone.utc)
        name_zone=data.get('_timezone','UTC')
        if name_zone not in ('UTC','America/Monterrey'): raise ValueError
        zone=ZoneInfo(name_zone)
        aware=result.replace(tzinfo=zone)
        # Rechazar horas inexistentes o ambiguas en transiciones históricas.
        if aware.astimezone(timezone.utc).astimezone(zone).replace(tzinfo=None)!=result or aware.utcoffset()!=result.replace(tzinfo=zone,fold=1).utcoffset():
            raise ValueError
        return aware.astimezone(timezone.utc)
    except (ValueError, TypeError, ZoneInfoNotFoundError):
        raise BusinessError("Escribe una fecha válida y no ambigua en la zona horaria indicada.", field=name) from None
