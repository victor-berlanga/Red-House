"""Valida un XML exportado contra XSD y el DTO de una operación, sin conectarse a bases."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from redhouse.config import SERVICES
from redhouse.openapi import META, ERROR
from redhouse.output_schemas import outputs
from redhouse.xml_response import validate_response


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("service", choices=SERVICES)
    parser.add_argument("operation")
    parser.add_argument("file", type=Path)
    args = parser.parse_args()
    if args.operation == "error":
        schema = ERROR
    else:
        contracts = outputs(args.service)
        if args.operation not in contracts:
            parser.error("Operación desconocida")
        schema = {
            "type": "object",
            "required": ["data", "meta"],
            "properties": {"data": contracts[args.operation], "meta": META},
        }
    validate_response(args.file.read_bytes(), schema)
    print("XML válido: estructura, tipos, campos obligatorios y contrato de operación.")


if __name__ == "__main__":
    main()
