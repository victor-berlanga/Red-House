"""Verifica HTTPS público, prefijos y aislamiento desde un cliente externo."""

import json
import socket
import ssl
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import certifi
import requests

ROOT = Path(__file__).resolve().parents[2]
ADDRESS = "34.18.186.116"
BASE = "https://" + ADDRESS


def check_service(name):
    prefix = "/services/" + name
    statuses = {}
    for suffix in ("/health/ready", "/docs/", "/openapi.json", "/schemas/response.xsd"):
        response = requests.get(BASE + prefix + suffix, timeout=12)
        statuses[suffix] = response.status_code
        assert response.status_code == 200, (name, suffix, response.status_code)
        if suffix == "/openapi.json":
            assert response.json()["servers"] == [{"url": prefix}]
    assert (
        requests.get(BASE + prefix + "/internal/v1/test", timeout=8).status_code == 404
    )
    return {"service": name, "statuses": statuses, "internal_blocked": True}


def check_private_port(port):
    try:
        with socket.create_connection((ADDRESS, port), timeout=2):
            return {"port": port, "accessible": True}
    except OSError:
        return {"port": port, "accessible": False}


def main():
    names = [
        name[:-2]
        for name in json.loads((ROOT / "compose.yaml").read_text())["services"]
        if name.endswith("-a")
    ]
    with ThreadPoolExecutor(max_workers=3) as pool:
        services = list(pool.map(check_service, names))
    redirect = requests.get(
        "http://" + ADDRESS + "/login", allow_redirects=False, timeout=8
    )
    assert redirect.status_code == 308
    assert redirect.headers["Location"] == BASE + "/login"
    assert (
        requests.get(
            BASE + "/services/inventario/api/v1/resources", timeout=8
        ).status_code
        == 401
    )
    # Usar las mismas CA que requests, también en instalaciones de Python de
    # macOS que todavía no tienen configurado un almacén de certificados propio.
    context = ssl.create_default_context(cafile=certifi.where())
    with (
        socket.create_connection((ADDRESS, 443), timeout=8) as sock,
        context.wrap_socket(sock, server_hostname=ADDRESS) as connection,
    ):
        certificate = connection.getpeercert()
        protocol = connection.version()
    with ThreadPoolExecutor(max_workers=8) as pool:
        ports = list(
            pool.map(
                check_private_port, [5432, 27017, 6379, 5050, 6050, 6101, 6104, 6111]
            )
        )
    assert not any(row["accessible"] for row in ports)
    result = {
        "date": datetime.now(timezone.utc).isoformat(),
        "result": "passed",
        "origin": BASE,
        "redirect": 308,
        "unauthenticated_api": 401,
        "tls": {
            "protocol": protocol,
            "issuer": certificate["issuer"],
            "not_before": certificate["notBefore"],
            "not_after": certificate["notAfter"],
            "subject_alt_name": certificate["subjectAltName"],
            "trust_verified": True,
        },
        "services": services,
        "private_ports": ports,
    }
    path = ROOT / "documentation/evidencias/gcp/public/network.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"result": "passed", "services": len(services), "tls": protocol}))


if __name__ == "__main__":
    main()
