"""Presentación compartida de restricciones y errores; el servidor conserva autoridad."""

import json
import re
from pathlib import Path

CONTRACTS = json.loads(Path(__file__).with_name("form_constraints.json").read_text())
ATTRIBUTES = {
    "minLength": "minlength",
    "maxLength": "maxlength",
    "minimum": "min",
    "maximum": "max",
    "pattern": "pattern",
}
HELP = {
    "folio": "Usa de 6 a 30 letras ASCII, números, guion o guion bajo. No admite espacios ni acentos.",
    "consent_reference": "Captura también la fecha del consentimiento o deja ambos campos vacíos.",
    "consent_at": "Captura también la referencia. La fecha no puede ser posterior al momento actual.",
    "ends_at": "Debe ser posterior al inicio y no estar vencida.",
    "travel_minutes": "Duración estimada en minutos enteros.",
    "distance_km": "Distancia estimada en kilómetros.",
    "latitude": "Latitud en grados decimales.",
    "longitude": "Longitud en grados decimales.",
    "captured_at": "Diferencia máxima de cinco minutos respecto al momento actual, solo durante el traslado autorizado.",
    "opens_at": "La apertura debe ser anterior al cierre del mismo día.",
    "closes_at": "El cierre debe ser posterior a la apertura del mismo día.",
    "organ_type": "Selecciona un órgano únicamente cuando el tipo de recurso sea Órgano.",
}


def prepare_fields(fields, service, path, method):
    constraints = next(
        (
            c["fields"]
            for c in CONTRACTS
            if c["service"] == service
            and c["method"] == method
            and re.fullmatch(re.sub(r"<[^>]+>", "[^/]+", c["path"]), path)
        ),
        {},
    )
    result = []
    for original in fields:
        item = dict(original)
        name, typ = item["name"], item["type"]
        rule = constraints.get(name, {})
        attrs = {attr: rule[key] for key, attr in ATTRIBUTES.items() if key in rule}
        # Text (fechas/UUID) comparte límites de longitud con su representación API;
        # los controles de fecha/número no admiten atributos de longitud/patrón.
        if typ in (
            "datetime-local",
            "time",
            "number",
            "decimal",
            "hidden",
            "checkbox",
            "select",
            "multiselect",
            "integer-select",
        ):
            attrs = {k: v for k, v in attrs.items() if k in ("min", "max")}
        if typ in ("number", "decimal"):
            attrs["step"] = "1" if typ == "number" else "any"
        # HTML usa expresiones Unicode v; escapar el guion dentro de la clase.
        if name == "folio" and "pattern" in attrs:
            attrs["pattern"] = "[A-Za-z0-9_\\-]+"
        hints = []
        if not item["required"]:
            hints.append("Opcional.")
        if "minlength" in attrs and "maxlength" in attrs:
            low, high = attrs["minlength"], attrs["maxlength"]
            hints.append(
                f"Entre {low} y {high} caracteres."
                if low > 1
                else f"Máximo {high} caracteres."
            )
        if "min" in attrs and "max" in attrs:
            hints.append(f"Entre {attrs['min']} y {attrs['max']}.")
        if "maxItems" in rule:
            hints.append(f"Selecciona como máximo {rule['maxItems']} opciones.")
        if name in HELP:
            hints.append(HELP[name])
        item.update(attrs=attrs, help=" ".join(hints), errors=[])
        result.append(item)
    return result


def attach_errors(fields, error):
    visible = {item["name"]: item for item in fields if item["type"] != "hidden"}
    details = list(error.details)
    if error.field:
        details.append({"field": error.field, "message": error.message})
    for detail in details[:100]:
        if not isinstance(detail, dict):
            continue
        item = visible.get(str(detail.get("field", "")).split(".")[0])
        if item is None:
            continue
        message = detail.get("message")
        if not isinstance(message, str) or not message or len(message) > 600:
            message = "Revisa el formato y los límites indicados."
        if detail.get("code") == "string_too_short" and not item["required"]:
            minimum = item["attrs"].get("minlength")
            message = (
                f"Escribe al menos {minimum} caracteres o deja este campo vacío."
                if minimum
                else "Completa este dato o deja el campo vacío."
            )
        if item["name"] == "folio" and detail.get("code") == "string_pattern_mismatch":
            message = HELP["folio"]
        if message not in item["errors"]:
            item["errors"].append(message)
    errors = [item for item in fields if item.get("errors")]
    return errors
