"""Contratos y aislamiento sin iniciar bases ni servicios de red."""

import importlib
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

import pytest
from redhouse.config import SERVICES
from redhouse.xml_response import validate_response
from redhouse.examples import response_xml
from scripts.package_service import package

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / "web"))


def test_xml_response_rejects_invalid_types_duplicates_and_missing_fields():
    schema = {
        "type": "object",
        "required": ["quantity"],
        "properties": {"quantity": {"type": "integer"}},
    }
    assert validate_response(response_xml({"quantity": 12}).encode(), schema) == {
        "quantity": 12
    }
    for xml in [
        b'<response type="object"><field name="quantity" type="integer">not-a-number</field></response>',
        b'<response type="object"><field name="quantity" type="integer">1</field><field name="quantity" type="integer">2</field></response>',
        b'<response type="object"/>',
    ]:
        with pytest.raises(ValueError):
            validate_response(xml, schema)


def test_legacy_rows_helper_does_not_truncate_after_first_hundred():
    from src.integration.routes.common import rows

    data = [{"id": str(uuid4())} for _ in range(125)]

    def page(*args, params):
        start = (params["page"] - 1) * 100
        return {"items": data[start : start + 100], "total": 125}

    with patch("src.integration.routes.common.call", side_effect=page):
        assert rows("donantes", "/api/v1/donors") == data


@pytest.mark.parametrize("service", list(SERVICES))
def test_service_artifact_loads_without_other_domain_packages(tmp_path, service):
    artifact = package(service, tmp_path / service)
    own = "servicio_monitoreo" if service == "monitoreo" else "ms_" + service
    domains = [
        p.name
        for p in artifact.iterdir()
        if p.name.startswith("ms_") or p.name == "servicio_monitoreo"
    ]
    assert domains == [own]
    program = """
import importlib,json,sys
module=sys.argv[1]
app=importlib.import_module(module).create_app({'DATABASE_URL':'unused','JWT_PUBLIC_KEY':'unused','JWT_PRIVATE_KEY':'unused'})
response=app.test_client().get('/openapi.json')
assert response.status_code==200
assert not any(k.startswith('ms_') and k.split('.')[0]!=module for k in sys.modules)
print(len(response.json['paths']))
"""
    result = subprocess.run(
        [sys.executable, "-B", "-c", program, own],
        cwd=artifact,
        env={**os.environ, "PYTHONPATH": str(artifact)},
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr


def test_catalogue_schemas_and_examples_compile_without_dependencies():
    from redhouse.codec import request_xsd
    from redhouse.examples import sample, request_xml
    from lxml import etree as E

    for service in SERVICES:
        own = "servicio_monitoreo" if service == "monitoreo" else "ms_" + service
        app = importlib.import_module(own).create_app(
            {
                "DATABASE_URL": "unused",
                "JWT_PUBLIC_KEY": "unused",
                "JWT_PRIVATE_KEY": "unused",
            }
        )
        for contract in app.extensions["contracts"]:
            model = contract["model"]
            if model:
                schema = E.XMLSchema(E.fromstring(request_xsd(model)))
                example = sample(model.model_json_schema())
                assert schema.validate(E.fromstring(request_xml(example).encode())), (
                    service,
                    contract["name"],
                    str(schema.error_log),
                )
