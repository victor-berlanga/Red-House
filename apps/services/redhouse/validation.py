"""Errores públicos de validación sin valores capturados ni excepciones internas."""

from .errors import APIError


def invalid(message, *fields, code="invalid_value", status=422, **limits):
    return APIError(
        "validation",
        message,
        status,
        [dict(field=name, code=code, message=message, **limits) for name in fields],
    )


def details_for(exc):
    details = []
    for error in exc.errors(
        include_input=False, include_context=True, include_url=False
    ):
        code, context = error["type"], error.get("ctx", {})
        limits = {
            name: value
            for name, value in context.items()
            if name in ("min_length", "max_length", "ge", "le", "gt", "lt")
            and type(value) in (int, float)
        }
        message = {
            "missing": "Completa este campo.",
            "string_type": "Escribe un texto válido.",
            "int_type": "Escribe un número entero.",
            "int_parsing": "Escribe un número entero.",
            "float_type": "Escribe un número válido.",
            "float_parsing": "Escribe un número válido.",
            "finite_number": "Escribe un número finito.",
            "bool_type": "Selecciona una opción válida.",
            "literal_error": "Selecciona o confirma una opción válida.",
            "string_pattern_mismatch": "Usa el formato indicado junto al campo.",
            "extra_forbidden": "Este dato no forma parte de la operación.",
            "list_type": "Selecciona las opciones correspondientes.",
        }.get(code, "Revisa este dato y utiliza el formato indicado.")
        if code == "string_too_short":
            message = f"Escribe al menos {limits['min_length']} caracteres."
        elif code == "string_too_long":
            message = f"Escribe como máximo {limits['max_length']} caracteres."
        elif code in (
            "greater_than_equal",
            "less_than_equal",
            "greater_than",
            "less_than",
        ):
            key, phrase = {
                "greater_than_equal": ("ge", "mayor o igual a"),
                "less_than_equal": ("le", "menor o igual a"),
                "greater_than": ("gt", "mayor que"),
                "less_than": ("lt", "menor que"),
            }[code]
            message = f"Escribe un valor {phrase} {limits[key]}."
        elif code in ("too_short", "too_long"):
            message = "Revisa la cantidad de opciones seleccionadas."
        details.append(
            dict(
                field=".".join(map(str, error["loc"])),
                code=code,
                message=message,
                **limits,
            )
        )
    return details
