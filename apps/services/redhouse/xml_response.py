"""Validación XML v1: XSD estructural y DTO público, sin cambiar el formato existente."""

import math
import re
from pathlib import Path
from functools import lru_cache
from lxml import etree as E
from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError


@lru_cache(maxsize=1)
def envelope():
    return E.XMLSchema(E.parse(str(Path(__file__).with_name("response.xsd"))))


def validate_response(content, schema):
    """Devuelve el equivalente JSON validado o ValueError; no hace consultas de red."""
    if len(content) > 8 * 1024 * 1024:
        raise ValueError("Respuesta demasiado grande")
    try:
        root = E.fromstring(
            content,
            E.XMLParser(resolve_entities=False, load_dtd=False, no_network=True),
        )
        if root.getroottree().docinfo.doctype:
            raise ValueError("DTD prohibido")
        envelope().assertValid(root)

        def decode(node):
            kind = node.get("type")
            text = node.text or ""
            if kind in ("object", "array"):
                if text.strip() or any((child.tail or "").strip() for child in node):
                    raise ValueError("Contenido mixto inesperado")
                if kind == "object":
                    result = {}
                    for child in node:
                        name = child.get("name")
                        if child.tag != "field" or name in result:
                            raise ValueError("Campo duplicado o inválido")
                        result[name] = decode(child)
                    return result
                if any(child.tag != "item" for child in node):
                    raise ValueError("Lista inválida")
                return [decode(child) for child in node]
            if len(node):
                raise ValueError("Un escalar no admite elementos hijos")
            if kind == "string":
                return text
            if kind == "null":
                if text.strip():
                    raise ValueError("Nulo con contenido")
                return None
            if kind == "boolean":
                if text not in ("true", "false"):
                    raise ValueError("Booleano inválido")
                return text == "true"
            if kind == "integer":
                if not re.fullmatch(r"-?[0-9]+", text):
                    raise ValueError("Entero inválido")
                return int(text)
            if kind == "number":
                result = float(text)
                if not math.isfinite(result):
                    raise ValueError("Número no finito")
                return result
            raise ValueError("Tipo no admitido")

        value = decode(root)
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(value)
        return value
    except (
        E.XMLSyntaxError,
        E.DocumentInvalid,
        ArithmeticError,
        ValidationError,
    ) as exc:
        raise ValueError("XML contrario al contrato") from exc
