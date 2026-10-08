"""Contratos JSON y XML: parser sin DTD/entidades y XSD por solicitud."""

import json
import math
import re
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from flask import Response, request
from lxml import etree as E
from pydantic import ValidationError

from .errors import APIError

XS = "http://www.w3.org/2001/XMLSchema"
XSI = "http://www.w3.org/2001/XMLSchema-instance"


def plain(value):
    if isinstance(value, dict):
        return {k: plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(v) for v in value]
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Decimal):
        return float(value)
    return value


def representation():
    best = request.accept_mimetypes.best_match(
        ["application/json", "application/xml", "text/xml"]
    )
    if request.headers.get("Accept") and best is None:
        raise APIError(
            "not_acceptable", "Solicita application/json o application/xml.", 406
        )
    return "xml" if best in ("application/xml", "text/xml") else "json"


def _pairs(items):
    result = {}
    for k, v in items:
        if k in result:
            raise ValueError("duplicate")
        result[k] = v
    return result


def _resolve(schema, root):
    seen = set()
    while "$ref" in schema or "anyOf" in schema:
        if "$ref" in schema:
            reference = schema["$ref"]
            if reference in seen:
                raise ValueError("Referencia circular no admitida en el contrato XML.")
            seen.add(reference)
            schema = root["$defs"][reference.split("/")[-1]]
        else:
            schema = next((s for s in schema["anyOf"] if s.get("type") != "null"), {})
    return schema


def request_xsd(model):
    root_schema = model.model_json_schema()
    root = E.Element(f"{{{XS}}}schema", nsmap={"xs": XS})

    def field(parent, name, schema, required=True):
        nullable = any(s.get("type") == "null" for s in schema.get("anyOf", []))
        element = E.SubElement(
            parent,
            f"{{{XS}}}element",
            name=name,
            minOccurs="1" if required else "0",
            nillable="true" if nullable else "false",
        )
        schema = _resolve(schema, root_schema)
        typ = schema.get("type", "string")
        if typ in ("object", "array"):
            complex_type = E.SubElement(element, f"{{{XS}}}complexType")
            container = E.SubElement(
                complex_type, f"{{{XS}}}" + ("all" if typ == "object" else "sequence")
            )
            if typ == "object":
                for key, prop in schema.get("properties", {}).items():
                    field(container, key, prop, key in schema.get("required", []))
            else:
                child = field(container, "item", schema.get("items", {}))
                child.set("minOccurs", str(schema.get("minItems", 0)))
                child.set("maxOccurs", str(schema.get("maxItems", "unbounded")))
        else:
            simple = E.SubElement(element, f"{{{XS}}}simpleType")
            base = {
                "integer": "xs:integer",
                "number": "xs:double",
                "boolean": "xs:boolean",
            }.get(typ, "xs:string")
            choices = schema.get("enum", [schema["const"]] if "const" in schema else [])
            if typ == "boolean" and choices:
                base = "xs:string"  # XSD 1.0 no permite enumeration sobre xs:boolean.
            restriction = E.SubElement(simple, f"{{{XS}}}restriction", base=base)
            for k, facet in (
                ("minLength", "minLength"),
                ("maxLength", "maxLength"),
                ("minimum", "minInclusive"),
                ("maximum", "maxInclusive"),
            ):
                if k in schema:
                    E.SubElement(restriction, f"{{{XS}}}{facet}", value=str(schema[k]))
            if "pattern" in schema:
                # Los patrones usados por nuestros modelos son compatibles con XSD;
                # XSD ya aplica el patrón completo, sin los anclajes de Python.
                pattern = schema["pattern"].removeprefix("^").removesuffix("$")
                E.SubElement(restriction, f"{{{XS}}}pattern", value=pattern)
            for choice in choices:
                value = str(choice).lower() if isinstance(choice, bool) else str(choice)
                E.SubElement(restriction, f"{{{XS}}}enumeration", value=value)
        return element

    top = field(root, "request", root_schema)
    top.attrib.pop("minOccurs", None)
    return E.tostring(root, encoding="UTF-8", xml_declaration=True)


def _decode(element, schema, root):
    if element.get(f"{{{XSI}}}nil") == "true":
        return None
    schema = _resolve(schema, root)
    typ = schema.get("type")
    if typ == "object":
        return {
            child.tag: _decode(child, schema["properties"][child.tag], root)
            for child in element
        }
    if typ == "array":
        return [_decode(child, schema["items"], root) for child in element]
    text = element.text or ""
    if typ == "integer":
        return int(text)
    if typ == "number":
        return float(text)
    if typ == "boolean":
        return text in ("true", "1")
    return text


def parse(model):
    data = request.get_data()
    try:
        if request.mimetype == "application/json":
            obj = json.loads(
                data,
                object_pairs_hook=_pairs,
                parse_constant=lambda _: (_ for _ in ()).throw(ValueError()),
            )
        elif request.mimetype in ("application/xml", "text/xml"):
            parser = E.XMLParser(
                resolve_entities=False, load_dtd=False, no_network=True, huge_tree=False
            )
            tree = E.fromstring(data, parser)
            if tree.getroottree().docinfo.doctype:
                raise ValueError()
            if tree.tag != "request" or len(list(tree.iter())) > 2000:
                raise ValueError()
            E.XMLSchema(E.fromstring(request_xsd(model))).assertValid(tree)
            obj = _decode(tree, model.model_json_schema(), model.model_json_schema())
        else:
            raise APIError("unsupported_media_type", "Usa JSON o XML.", 415)
        if not isinstance(obj, dict):
            raise ValueError()

        # Evita que Literal[True] acepte el entero 1 y números no finitos.
        def strict(value, schema, root):
            schema = _resolve(schema, root)
            typ = schema.get("type")
            if value is None:
                return
            if typ == "boolean" and type(value) is not bool:
                raise ValueError()
            if typ == "number" and (
                type(value) not in (int, float) or not math.isfinite(value)
            ):
                raise ValueError()
            if typ == "object" and isinstance(value, dict):
                for k, v in value.items():
                    if k in schema.get("properties", {}):
                        strict(v, schema["properties"][k], root)
            if typ == "array" and isinstance(value, list):
                for v in value:
                    strict(v, schema["items"], root)

        schema = model.model_json_schema()
        strict(obj, schema, schema)
        return model.model_validate(obj).model_dump()
    except ValidationError as exc:
        details = [
            {"field": ".".join(map(str, e["loc"])), "code": e["type"]}
            for e in exc.errors()
        ]
        raise APIError(
            "validation", "La solicitud no cumple el contrato.", 422, details
        ) from None
    except (
        ValueError,
        UnicodeError,
        RecursionError,
        E.XMLSyntaxError,
        E.DocumentInvalid,
    ):
        raise APIError(
            "invalid_body", "JSON/XML inválido o contrario al esquema.", 400
        ) from None


def xml_value(parent, value):
    if value is None:
        parent.set("type", "null")
    elif isinstance(value, dict):
        parent.set("type", "object")
        for key, item in value.items():
            child = E.SubElement(parent, "field", name=key)
            xml_value(child, item)
    elif isinstance(value, list):
        parent.set("type", "array")
        for item in value:
            xml_value(E.SubElement(parent, "item"), item)
    else:
        parent.set(
            "type",
            "boolean"
            if type(value) is bool
            else "integer"
            if type(value) is int
            else "number"
            if type(value) is float
            else "string",
        )
        parent.text = str(value).lower() if type(value) is bool else str(value)


def respond(payload, status=200):
    payload = plain(payload)
    try:
        fmt = representation()
    except APIError:
        fmt = "json"
    if fmt == "xml":
        root = E.Element("response")
        xml_value(root, payload)
        return Response(
            E.tostring(root, encoding="UTF-8", xml_declaration=True),
            status=status,
            mimetype="application/xml",
        )
    return Response(
        json.dumps(payload, ensure_ascii=False, allow_nan=False),
        status=status,
        mimetype="application/json",
    )
