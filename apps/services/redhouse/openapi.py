import re

from flask import Response, jsonify
from swagger_ui import api_doc

from .codec import request_xsd

META = {
    "type": "object",
    "required": ["correlation_id", "service", "version"],
    "properties": {
        "correlation_id": {"type": "string", "format": "uuid"},
        "service": {"type": "string"},
        "version": {"type": "string"},
    },
}
ERROR = {
    "type": "object",
    "required": ["error", "meta"],
    "properties": {
        "meta": META,
        "error": {
            "type": "object",
            "required": ["code", "message", "details"],
            "properties": {
                "code": {"type": "string"},
                "message": {"type": "string"},
                "details": {"type": "array", "items": {"type": "object"}},
            },
        },
    },
}


def spec(app):
    from .examples import EXAMPLE_ID, request_xml, response_xml, sample

    prefix = app.config.get("PUBLIC_API_PREFIX", "")
    paths, schemas = {}, {"Error": ERROR}
    for contract in app.extensions["contracts"]:
        path = re.sub(r"<(?:(?:[^:>]+):)?([^>]+)>", r"{\1}", contract["path"])
        parameters = [
            {
                "name": name,
                "in": "path",
                "required": True,
                "schema": {"type": "string", "format": "uuid"},
            }
            for name in re.findall(r"\{([^}]+)\}", path)
        ]
        parameters += [
            {
                "name": "X-Correlation-ID",
                "in": "header",
                "schema": {"type": "string", "format": "uuid"},
            },
            {
                "name": "Accept",
                "in": "header",
                "schema": {
                    "type": "string",
                    "enum": ["application/json", "application/xml"],
                },
            },
        ]
        if contract["paginated"]:
            parameters += [
                {
                    "name": "page",
                    "in": "query",
                    "schema": {"type": "integer", "minimum": 1, "default": 1},
                },
                {
                    "name": "page_size",
                    "in": "query",
                    "schema": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 100,
                        "default": 20,
                    },
                },
            ]
        parameters += [
            {
                "name": name,
                "in": "query",
                "schema": {"type": "string", "maxLength": 100},
            }
            for name in contract.get("query", ())
        ]
        if contract["internal"]:
            parameters += [
                {
                    "name": "X-Service",
                    "in": "header",
                    "required": True,
                    "schema": {"type": "string", "enum": list(contract["internal"])},
                },
                {
                    "name": "X-Service-Time",
                    "in": "header",
                    "required": True,
                    "schema": {"type": "string"},
                },
                {
                    "name": "X-Service-Nonce",
                    "in": "header",
                    "required": True,
                    "schema": {"type": "string", "format": "uuid"},
                },
            ]
        if (
            contract["method"] in ("POST", "PATCH", "PUT")
            and not contract["internal"]
            and not contract["public"]
            and contract["name"] != "operation_resume"
        ):
            parameters.append(
                {
                    "name": "Idempotency-Key",
                    "in": "header",
                    "required": True,
                    "schema": {"type": "string", "minLength": 8, "maxLength": 100},
                }
            )
        from .output_schemas import result_schema

        result = contract["result"] or result_schema(
            app.config["SERVICE"], contract["name"]
        )
        schema = {
            "type": "object",
            "required": ["data", "meta"],
            "properties": {"data": result, "meta": META},
        }
        example = {
            "data": sample(result),
            "meta": {
                "correlation_id": EXAMPLE_ID,
                "service": app.config["SERVICE"],
                "version": app.config["VERSION"],
            },
        }
        operation = {
            "operationId": contract["name"],
            "summary": contract["summary"],
            "parameters": parameters,
            "description": "Roles: "
            + (", ".join(contract["roles"]) or "según sesión")
            + ". "
            + (
                "Contrato interno firmado; consumidores: "
                + ", ".join(contract["internal"])
                if contract["internal"]
                else "Contrato público de API."
            ),
            "security": []
            if contract["public"]
            else (
                [
                    dict(
                        {"ServiceSignature": []},
                        **({"BearerJWT": []} if contract["delegate"] else {}),
                    )
                ]
                if contract["internal"]
                else [{"BearerJWT": []}]
            ),
            "responses": {
                str(contract["status"]): {
                    "description": "Resultado confirmado o estado pendiente documentado.",
                    "content": {
                        "application/json": {"schema": schema, "example": example},
                        "application/xml": {
                            "schema": {"type": "string"},
                            "example": response_xml(example),
                            "x-json-equivalent-schema": schema,
                            "x-xsd": prefix + "/schemas/response.xsd",
                            "x-response-schema": f"{prefix}/schemas/{contract['name']}.response.json",
                        },
                    },
                }
            },
        }
        for status in (400, 401, 403, 404, 406, 409, 413, 415, 422, 429, 500, 503):
            error_example = {
                "error": {
                    "code": {
                        400: "validation",
                        401: "unauthorized",
                        403: "forbidden",
                        404: "not_found",
                        406: "not_acceptable",
                        409: "conflict",
                        413: "http_error",
                        415: "unsupported_media",
                        422: "validation",
                        429: "rate_limit",
                        500: "internal_error",
                        503: "dependency_unavailable",
                    }[status],
                    "message": {
                        401: "Credencial inválida, expirada o revocada.",
                        403: "Sin permiso institucional o de recurso.",
                        409: "Conflicto de estado, versión o idempotencia.",
                        503: "Dependencia inaccesible; consultar estado antes de repetir.",
                    }.get(status, "Petición no disponible o inválida."),
                    "details": [],
                },
                "meta": example["meta"],
            }
            operation["responses"][str(status)] = {
                "description": {
                    401: "Credencial inválida, expirada o revocada.",
                    403: "Sin permiso institucional o de recurso.",
                    409: "Conflicto de estado, versión o idempotencia.",
                    503: "Dependencia inaccesible; consultar estado antes de repetir.",
                }.get(status, "Error uniforme."),
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/Error"},
                        "example": error_example,
                    },
                    "application/xml": {
                        "schema": {"type": "string"},
                        "example": response_xml(error_example),
                    },
                },
            }
        if contract["model"]:
            model = contract["model"]
            input_example = sample(model.model_json_schema())
            schema = model.model_json_schema(
                ref_template="#/components/schemas/{model}"
            )
            schemas.update(schema.pop("$defs", {}))
            schemas[model.__name__] = schema
            operation["requestBody"] = {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {"$ref": f"#/components/schemas/{model.__name__}"},
                        "example": input_example,
                    },
                    "application/xml": {
                        "schema": {"type": "string"},
                        "example": request_xml(input_example),
                        "x-xsd": f"{prefix}/schemas/{contract['name']}.xsd",
                        "x-json-equivalent-schema": {
                            "$ref": f"#/components/schemas/{model.__name__}"
                        },
                    },
                },
            }
        paths.setdefault(path, {})[contract["method"].lower()] = operation
    document = {
        "openapi": "3.1.0",
        "info": {
            "title": "Red House — " + app.config["SERVICE"],
            "version": app.config["VERSION"],
            "description": "API independiente JSON/XML. Reglas clínicas ilustrativas; requiere revisión humana. XML de respuesta validable en /schemas/response.xsd.",
        },
        "paths": paths,
        "components": {
            "schemas": schemas,
            "securitySchemes": {
                "BearerJWT": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT RS256",
                },
                "ServiceSignature": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "X-Service-Signature",
                    "description": "Ed25519; requiere X-Service, X-Service-Time y X-Service-Nonce. No es un token de usuario.",
                },
            },
        },
    }
    if prefix:
        document["servers"] = [{"url": prefix}]
    return document


def install(app):
    @app.get("/schemas/<name>.response.json")
    def response_contract(name):
        contract = next(
            (c for c in app.extensions["contracts"] if c["name"] == name), None
        )
        if contract is None:
            from .errors import APIError

            raise APIError("not_found", "Contrato inexistente.", 404)
        from .output_schemas import result_schema

        return jsonify(
            {
                "type": "object",
                "required": ["data", "meta"],
                "properties": {
                    "data": contract["result"]
                    or result_schema(app.config["SERVICE"], name),
                    "meta": META,
                },
            }
        )

    @app.get("/openapi.json")
    def openapi():
        return jsonify(spec(app))

    @app.get("/schemas/<name>.xsd")
    def schema(name):
        if name == "response":
            from pathlib import Path

            content = (Path(__file__).parent / "response.xsd").read_bytes()
        else:
            model = next(
                (
                    c["model"]
                    for c in app.extensions["contracts"]
                    if c["name"] == name and c["model"]
                ),
                None,
            )
            if model is None:
                from .errors import APIError

                raise APIError("not_found", "Esquema inexistente.", 404)
            content = request_xsd(model)
        return Response(content, mimetype="application/xml")

    api_doc(
        app,
        config=spec(app),
        url_prefix=app.config.get("PUBLIC_API_PREFIX", "") + "/docs",
        host_inject=False,
        title="Red House — " + app.config["SERVICE"],
    )
