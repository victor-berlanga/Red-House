"""Lecturas JSON/XML de doce propietarios sobre el despliegue autorizado."""

import argparse
import json
import sys
from pathlib import Path

import requests
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "apps/services"))
from redhouse.xml_response import validate_response


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--shipment", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    private = json.loads(args.input.read_text())
    assert private["base"] == "https://34.18.186.116"
    paths = {
        "identidad_acceso": ("/api/v1/users", "admin1"),
        "donantes": ("/api/v1/campaigns", "operator1"),
        "receptores": ("/api/v1/requests", "medical2"),
        "inventario": ("/api/v1/resources", "operator1"),
        "compatibilidad": ("/api/v1/evaluations", "medical2"),
        "priorizacion_geografia": ("/api/v1/routes", "coordinator1"),
        "transporte": ("/api/v1/shipments", "coordinator1"),
        "custodia": ("/api/v1/chains/{identifier}", "transport1"),
        "alertas": ("/api/v1/alerts", "operator1"),
        "auditoria": ("/api/v1/events", "auditor1"),
        "monitoreo": ("/api/v1/status", "admin1"),
        "documentos": ("/api/v1/export-jobs", "medical2"),
    }
    checks = []
    for service, (path, user) in paths.items():
        module = "servicio_monitoreo" if service == "monitoreo" else "ms_" + service
        contracts = ROOT / "apps/services" / module / "contracts"
        spec = json.loads((contracts / "openapi.json").read_text())
        operation = spec["paths"][path]["get"]["operationId"]
        schema = json.loads((contracts / (operation + ".response.json")).read_text())
        for representation in ("json", "xml"):
            response = requests.get(
                private["base"]
                + "/services/"
                + service.replace("_", "-")
                + path.replace("{identifier}", args.shipment),
                headers={
                    "Authorization": "Bearer " + private["tokens"][user],
                    "Accept": "application/" + representation,
                },
                timeout=30,
            )
            if response.status_code != 200:
                raise RuntimeError(
                    f"{service} {representation}: HTTP {response.status_code}"
                )
            if representation == "xml":
                validate_response(response.content, schema)
            else:
                Draft202012Validator(schema, format_checker=FormatChecker()).validate(
                    response.json()
                )
            checks.append(
                {
                    "service": service,
                    "representation": representation,
                    "status": "passed",
                }
            )
    args.output.write_text(
        json.dumps({"checks": checks, "passed": True}, indent=2) + "\n"
    )
    print(
        f"{len(checks)} respuestas JSON/XML validadas contra contratos; XML incluye XSD."
    )


if __name__ == "__main__":
    main()
