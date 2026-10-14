"""Completa catálogos administrativos ficticios de el entorno NL, por API e idempotentemente."""

import argparse
import hashlib
import json
from pathlib import Path

import requests

MUNICIPALITIES = [
    "Monterrey",
    "San Nicolás de los Garza",
    "Guadalupe",
    "Apodaca",
    "General Escobedo",
    "Santa Catarina",
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    directory = args.directory.resolve()
    state = json.loads((directory / "state.json").read_text())
    if (
        str(directory) != state["directory"]
        or not (directory / "dataset-nl.json").exists()
    ):
        raise RuntimeError(
            "Este script requiere el entorno NL previamente provisionada."
        )
    result = {}
    with requests.Session() as http:
        http.trust_env = False
        base = state["urls"]["identidad_acceso"]
        for i, municipality in enumerate(MUNICIPALITIES, 1):
            login = http.post(
                base + "/api/v1/auth/login",
                json={"username": "admin" + str(i), "password": state["password"]},
                timeout=15,
            )
            if login.status_code != 200:
                raise RuntimeError("No se pudo autenticar el administrador.")
            headers = {
                "Authorization": "Bearer " + login.json()["data"]["access_token"]
            }
            counts = {}

            def create(kind, data):
                path = "/api/v1/catalogues/" + kind
                response = http.get(
                    base + path,
                    params={"q": data["name"], "page_size": 100},
                    headers=headers,
                    timeout=10,
                )
                if response.status_code != 200:
                    raise RuntimeError("No se pudo consultar " + kind)
                existing = next(
                    (
                        r
                        for r in response.json()["data"]["items"]
                        if r["name"] == data["name"]
                    ),
                    None,
                )
                if existing:
                    return existing
                idem = hashlib.sha256(
                    (str(i) + kind + data["name"]).encode()
                ).hexdigest()
                response = http.post(
                    base + path,
                    json=data,
                    headers={**headers, "Idempotency-Key": idem},
                    timeout=10,
                )
                if response.status_code not in (200, 201):
                    raise RuntimeError(
                        "No se pudo registrar "
                        + kind
                        + "; HTTP "
                        + str(response.status_code)
                    )
                counts[kind] = counts.get(kind, 0) + 1
                return response.json()["data"]

            site = create(
                "sites",
                {
                    "name": "Sede " + municipality,
                    "municipality": municipality,
                    "address": "Avenida de la Solidaridad "
                    + str(100 + i)
                    + ", domicilio ficticio, Nuevo León",
                },
            )
            create(
                "contacts",
                {
                    "name": "Coordinación",
                    "value": "coordinacion" + str(i) + "@red-house.example",
                },
            )
            for day in range(5):
                create(
                    "schedules",
                    {
                        "name": "Atención administrativa "
                        + ["lunes", "martes", "miércoles", "jueves", "viernes"][day],
                        "parent_id": site["id"],
                        "weekday": day,
                        "opens_at": "08:00",
                        "closes_at": "17:00",
                    },
                )
            create(
                "capacities",
                {
                    "name": "Capacidad declarada",
                    "parent_id": site["id"],
                    "component": "RBC",
                    "quantity": 240,
                },
            )
            create(
                "locations",
                {
                    "name": "Registro de ubicación",
                    "parent_id": site["id"],
                    "description": "Referencia logística ficticia; sin reglas clínicas de conservación",
                },
            )
            result[municipality] = counts
    args.report.write_text(
        json.dumps(
            {"result": "passed", "created": result}, indent=2, ensure_ascii=False
        )
        + "\n"
    )
    print(
        "Catálogos verificados para seis instituciones; sin modificar inventarios ni reglas clínicas."
    )


if __name__ == "__main__":
    main()
