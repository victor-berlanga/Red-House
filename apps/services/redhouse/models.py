from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class Model(BaseModel):
    model_config = ConfigDict(
        extra="forbid", strict=True, str_strip_whitespace=True, allow_inf_nan=False
    )

    @model_validator(mode="before")
    @classmethod
    def safe_characters(cls, value):
        def visit(item):
            if isinstance(item, str) and any(
                (ord(c) < 32 and c not in "\t\n\r") or 0xD800 <= ord(c) <= 0xDFFF
                for c in item
            ):
                raise ValueError("Caracteres no representables en el contrato.")
            if isinstance(item, dict):
                for key, child in item.items():
                    visit(key)
                    visit(child)
            elif isinstance(item, list):
                for child in item:
                    visit(child)

        visit(value)
        return value


Text = Annotated[str, Field(min_length=1, max_length=200)]
Reason = Annotated[str, Field(min_length=6, max_length=1000)]
ID = Annotated[
    str,
    Field(pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"),
]
Group = Literal["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"]
Kind = Literal["BLOOD", "ORGAN"]
Organ = Literal["KIDNEY", "LIVER", "HEART"]
Role = Literal[
    "ADMIN", "OPERATOR", "MEDICAL", "COORDINATOR", "TRANSPORT", "AUDITOR", "DONOR"
]


class Confirm(Model):
    human_confirmation: Literal[True]
    reason: Reason


def utc_date(value, field=None):
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if result.tzinfo is None:
            raise ValueError()
        return result
    except (ValueError, AttributeError):
        if field:
            from .validation import invalid

            raise invalid(
                "Escribe una fecha y hora válidas con zona horaria.", field
            ) from None
        from .errors import APIError

        raise APIError(
            "validation", "Fecha ISO 8601 con zona horaria requerida."
        ) from None


def validate_id(value):
    try:
        if str(UUID(value)) != value:
            raise ValueError()
    except (ValueError, TypeError, AttributeError):
        from .errors import APIError

        raise APIError("validation", "Identificador UUID inválido.") from None
    return value
