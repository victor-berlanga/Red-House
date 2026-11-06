"""Contratos compartidos validables sin arrancar bases ni servidores."""

import importlib
import json
from pathlib import Path

import pytest
from openapi_spec_validator import validate

from redhouse.config import SERVICES
from redhouse.openapi import spec


@pytest.mark.parametrize("service", SERVICES)
def test_shared_openapi_matches_export_and_preserves_representations(service):
    module = "servicio_monitoreo" if service == "monitoreo" else "ms_" + service
    app = importlib.import_module(module).create_app(
        {
            "DATABASE_URL": "postgresql://UNCONFIGURED",
            "JWT_PUBLIC_KEY": "UNCONFIGURED",
            "JWT_PRIVATE_KEY": "UNCONFIGURED",
            "SERVICE_PRIVATE_KEY": "UNCONFIGURED",
        }
    )
    document = spec(app)
    validate(document)
    exported = Path(__file__).resolve().parents[1] / module / "contracts/openapi.json"
    assert json.loads(exported.read_text()) == document
    client = app.test_client()
    assert client.get("/openapi.json").get_json() == document
    swagger = client.get("/docs/swagger.json")
    assert swagger.status_code == 200
    assert swagger.get_json() == document
    for path in document["paths"].values():
        for operation in path.values():
            for status, response in operation["responses"].items():
                if int(status) >= 400:
                    assert response == {"$ref": f"#/components/responses/Error{status}"}
                    response = document["components"]["responses"][f"Error{status}"]
                content = response["content"]
                assert {"application/json", "application/xml"} <= content.keys()
                assert (
                    content["application/json"]["example"]["meta"]["service"] == service
                )
                assert content["application/xml"]["example"].startswith("<?xml")
                if int(status) < 400:
                    reference = content["application/json"]["schema"]
                    assert (
                        content["application/xml"]["x-json-equivalent-schema"]
                        == reference
                    )
                    name = reference["$ref"].rsplit("/", 1)[1]
                    assert document["components"]["schemas"][name]["required"] == [
                        "data",
                        "meta",
                    ]
