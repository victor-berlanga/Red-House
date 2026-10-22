"""Publica límites HTML desde los modelos vigentes, sin consultar servicios ni secretos."""

import argparse
import importlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps/services"))


def export():
    from redhouse.codec import _resolve
    from redhouse.config import SERVICES

    result = []
    for service in SERVICES:
        module = "servicio_monitoreo" if service == "monitoreo" else "ms_" + service
        app = importlib.import_module(module).create_app(
            {
                "DATABASE_URL": "postgresql://UNCONFIGURED",
                "JWT_PUBLIC_KEY": "UNCONFIGURED",
                "JWT_PRIVATE_KEY": "UNCONFIGURED",
                "SERVICE_PRIVATE_KEY": "UNCONFIGURED",
            }
        )
        for contract in app.extensions["contracts"]:
            if not contract["path"].startswith("/api/") or not contract["model"]:
                continue
            schema = contract["model"].model_json_schema()
            properties = {}
            for name, prop in schema["properties"].items():
                resolved = _resolve(prop, schema)
                properties[name] = {
                    key: value
                    for key, value in resolved.items()
                    if key
                    in (
                        "type",
                        "minLength",
                        "maxLength",
                        "minimum",
                        "maximum",
                        "pattern",
                        "minItems",
                        "maxItems",
                        "enum",
                        "const",
                    )
                }
            result.append(
                {
                    "service": service,
                    "path": contract["path"],
                    "method": contract["method"],
                    "fields": properties,
                }
            )
    return json.dumps(result, ensure_ascii=False, indent=2) + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    target = ROOT / "apps/web/src/integration/form_constraints.json"
    content = export()
    if args.check:
        if not target.exists() or target.read_text() != content:
            raise SystemExit("Regenera form_constraints.json con este script.")
    else:
        target.write_text(content)
    print(
        "Límites de formularios comprobados."
        if args.check
        else "Límites de formularios generados."
    )
