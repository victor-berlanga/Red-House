"""Ejemplos públicos ficticios de contratos; nunca contienen credenciales reales."""

from lxml import etree as E

from .codec import xml_value

EXAMPLE_ID = "00000000-0000-4000-8000-000000000001"


def sample(schema, root=None, name="", depth=0):
    root = root or schema
    if depth > 8:
        return None
    if "$ref" in schema:
        schema = root.get("$defs", {}).get(schema["$ref"].split("/")[-1], {})
    if "const" in schema:
        return schema["const"]
    if "enum" in schema:
        return schema["enum"][0]
    if "anyOf" in schema:
        if any(s.get("type") == "null" for s in schema["anyOf"]):
            return None
        return sample(schema["anyOf"][0], root, name, depth + 1)
    typ = schema.get("type", "object")
    if isinstance(typ, list):
        typ = next(t for t in typ if t != "null")
    if typ == "object":
        return {
            k: sample(v, root, k, depth + 1)
            for k, v in schema.get("properties", {}).items()
        }
    if typ == "array":
        return [
            sample(schema["items"], root, name, depth + 1)
            for _ in range(schema.get("minItems", 0))
        ]
    if typ == "boolean":
        return True
    if typ == "integer":
        return max(1, schema.get("minimum", 1))
    if typ == "number":
        return float(max(1, schema.get("minimum", 1)))
    if (
        schema.get("format") == "uuid"
        or name.endswith("_id")
        or name in ("id", "identifier", "evaluation_ids")
    ):
        return EXAMPLE_ID
    if "pattern" in schema and "[0-9a-f]{8}" in schema["pattern"]:
        return EXAMPLE_ID
    if name == "sha256":
        return "0" * 64
    if name == "password":
        return "CAMBIAR_CREDENCIAL_PRIVADA"
    if name == "refresh_token":
        return EXAMPLE_ID + ".CAMBIAR_POR_RENOVACION_RECIBIDA_EN_LOGIN_00000000"
    if (
        name in ("expires_at", "starts_at", "departure_at", "eta", "ends_at")
        or schema.get("format") == "date-time"
    ):
        return "2030-01-01T15:00:00+00:00"
    if name in ("captured_at", "collected_at", "occurred_at"):
        return "2026-10-01T15:00:00+00:00"
    if name == "component":
        return "RBC"
    if name in ("opens_at", "closes_at"):
        return "08:00" if name == "opens_at" else "17:00"
    if name == "folio":
        return "PRUEBA-000001"
    return "Dato ficticio para reemplazar"


def request_xml(value):
    root = E.Element(
        "request", nsmap={"xsi": "http://www.w3.org/2001/XMLSchema-instance"}
    )

    def add(parent, key, value):
        child = E.SubElement(parent, key)
        if value is None:
            child.set("{http://www.w3.org/2001/XMLSchema-instance}nil", "true")
        elif isinstance(value, dict):
            for k, v in value.items():
                add(child, k, v)
        elif isinstance(value, list):
            for v in value:
                add(child, "item", v)
        else:
            child.text = str(value).lower() if type(value) is bool else str(value)

    for k, v in value.items():
        add(root, k, v)
    return E.tostring(root, encoding="UTF-8", xml_declaration=True).decode()


def response_xml(value):
    root = E.Element("response")
    xml_value(root, value)
    return E.tostring(root, encoding="UTF-8", xml_declaration=True).decode()
