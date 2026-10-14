"""Comprobación de lectura de el entorno y cuentas conservadas; nunca publica secretos."""

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import requests


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    directory = args.directory.resolve()
    state = json.loads((directory / "state.json").read_text())
    if Path(state["directory"]).resolve() != directory:
        raise RuntimeError("Entorno propio inválido.")
    tokens = {}
    report = {
        "date": datetime.now(timezone.utc).isoformat(),
        "health": {},
        "counts": {},
        "limits": {},
        "custody_chains": 0,
    }

    def api(service, path, user="coordinator1"):
        if user not in tokens:
            result = requests.post(
                state["urls"]["identidad_acceso"] + "/api/v1/auth/login",
                json={"username": user, "password": state["password"]},
                timeout=20,
            )
            if result.status_code != 200:
                raise RuntimeError("No se pudo autenticar un perfil de comprobación.")
            tokens[user] = result.json()["data"]["access_token"]
        response = requests.get(
            state["urls"][service] + path,
            headers={"Authorization": "Bearer " + tokens[user]},
            timeout=20,
        )
        if response.status_code != 200:
            raise RuntimeError(
                "Falló consulta de comprobación "
                + service
                + " ("
                + str(response.status_code)
                + ")."
            )
        return response

    for service, url in state["urls"].items():
        status = requests.get(url + "/health/ready", timeout=10).status_code
        report["health"][service] = status
        assert status == 200, service
        limit = json.loads((directory / (service + ".json")).read_text())["RATE_LIMIT"]
        report["limits"][service] = limit
        assert limit == 180, service
    report["health"]["web"] = requests.get(
        state["web_url"] + "/health/live", timeout=10
    ).status_code
    assert report["health"]["web"] == 200
    report["counts"]["institutions"] = api(
        "identidad_acceso", "/api/v1/institutions?page_size=1"
    ).json()["data"]["total"]
    for name, service, path in [
        ("donors", "donantes", "donors"),
        ("donations", "donantes", "donations"),
        ("campaigns", "donantes", "campaigns"),
        ("appointments", "donantes", "appointments"),
        ("recipients", "receptores", "recipients"),
        ("requests", "receptores", "requests"),
    ]:
        report["counts"][name] = sum(
            api(
                service,
                "/api/v1/" + path + "?page_size=1",
                "medical" + str(i)
                if name in ("recipients", "requests")
                else "operator" + str(i),
            ).json()["data"]["total"]
            for i in range(1, 7)
        )
    for name, kind in [("blood_units", "BLOOD"), ("organ_offers", "ORGAN")]:
        report["counts"][name] = api(
            "inventario", "/api/v1/resources?kind=" + kind + "&page_size=1"
        ).json()["data"]["total"]
    ships = api("transporte", "/api/v1/shipments?page_size=100").json()["data"]
    report["counts"]["shipments"] = ships["total"]
    report["shipment_states"] = dict(Counter(row["status"] for row in ships["items"]))
    for row in ships["items"]:
        chain = api("custodia", "/api/v1/chains/" + row["id"]).json()["data"]
        previous = ""
        for sequence, event in enumerate(chain["events"], 1):
            serialized = json.dumps(
                event["event"], sort_keys=True, separators=(",", ":")
            )
            digest = hashlib.sha256((previous + serialized).encode()).hexdigest()
            assert (
                event["sequence"] == sequence
                and event["previous_hash"] == previous
                and event["hash"] == digest
            )
            previous = digest
        assert chain["chain"]["last_hash"] == previous and chain["chain"][
            "last_sequence"
        ] == len(chain["events"])
        report["custody_chains"] += 1
    api("inventario", "/api/v1/availability?page_size=20")
    cached = api("inventario", "/api/v1/availability?page_size=20")
    report["availability_cache"] = cached.headers.get("X-Cache")
    assert report["availability_cache"] == "HIT"
    report["counts"]["audit_events"] = api(
        "auditoria", "/api/v1/events?page_size=1", "auditor1"
    ).json()["data"]["total"]
    report["counts"]["alerts_in_first_institution"] = api(
        "alertas", "/api/v1/alerts?page_size=1", "operator1"
    ).json()["data"]["total"]
    expected = {
        "institutions": 6,
        "donors": 108,
        "donations": 36,
        "campaigns": 12,
        "appointments": 36,
        "recipients": 72,
        "requests": 72,
        "blood_units": 216,
        "organ_offers": 36,
        "shipments": 18,
    }
    assert all(report["counts"][name] == count for name, count in expected.items()), (
        "La carga cambió; revisar conteos."
    )
    report["result"] = "passed"
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
