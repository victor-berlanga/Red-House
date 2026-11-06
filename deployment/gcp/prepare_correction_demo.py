"""Preparación acotada por API: datos ficticios y factores privados, sin SQL de escritura."""

import argparse, base64, hashlib, hmac, json, os, struct, time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4
import requests

os.umask(0o077)
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument(
    "--directory",
    type=Path,
    required=True,
    help="Directorio privado con demo-credentials.json preexistente",
)
root = parser.parse_args().directory.resolve()
root.mkdir(mode=0o700, parents=True, exist_ok=True)
credentials = json.loads((root / "demo-credentials.json").read_text())
checkpoint = root / "demo-checkpoint.json"
state = (
    json.loads(checkpoint.read_text())
    if checkpoint.exists()
    else {"factors": {}, "records": {}, "tokens": {}}
)
origin = "https://34.18.186.116"


def save():
    checkpoint.write_text(json.dumps(state, indent=2) + "\n")
    checkpoint.chmod(0o600)


def code(user):
    account = state["factors"][user]
    counter = int(time.time()) // 30
    if counter <= account.get("lastCounter", -1):
        time.sleep((account["lastCounter"] + 1) * 30 - time.time() + 0.2)
        counter = int(time.time()) // 30
    account["lastCounter"] = counter
    save()
    return totp(account["secret"], counter)


def totp(secret, counter):
    raw = hmac.new(
        base64.b32decode(secret), struct.pack(">Q", counter), hashlib.sha1
    ).digest()
    i = raw[-1] & 15
    return str((struct.unpack(">I", raw[i : i + 4])[0] & 0x7FFFFFFF) % 1000000).zfill(6)


def call(service, method, path, data=None, user=None, headers=None):
    h = {"Accept": "application/json", "Idempotency-Key": uuid4().hex}
    if user:
        h["Authorization"] = "Bearer " + state["tokens"][user]
    h.update(headers or {})
    r = requests.request(
        method,
        origin + "/services/" + service.replace("_", "-") + path,
        json=data,
        headers=h,
        timeout=45,
    )
    try:
        body = r.json()
    except ValueError:
        raise RuntimeError(f"{method} {service}{path}: HTTP {r.status_code}") from None
    if not r.ok:
        raise RuntimeError(
            f"{method} {service}{path}: HTTP {r.status_code}, {body.get('error', {}).get('code', 'unknown')}"
        )
    return body["data"]


def once(name, fn):
    if name not in state["records"]:
        state["records"][name] = fn()
        save()
    return state["records"][name]


def iso(minutes=0, days=0):
    return (
        datetime.now(timezone.utc) + timedelta(minutes=minutes, days=days)
    ).isoformat()


confirm = {
    "human_confirmation": True,
    "reason": "Comprobación ficticia autorizada del despliegue GCP 0.4.1",
}
for user in ("admin1", "medical1", "medical2", "coordinator1"):
    if user not in state["factors"]:
        value = call(
            "identidad_acceso",
            "POST",
            "/api/v1/auth/mfa/enrollment",
            {"username": user, "password": credentials["password"]},
        )
        counter = int(time.time()) // 30 - 1
        state["factors"][user] = {
            "secret": value["secret"],
            "lastCounter": counter,
            "challenge": value["challenge"],
            "confirmed": False,
        }
        save()
    factor = state["factors"][user]
    if not factor["confirmed"]:
        call(
            "identidad_acceso",
            "POST",
            "/api/v1/auth/mfa/confirm",
            {
                "challenge": factor["challenge"],
                "code": totp(factor["secret"], factor["lastCounter"]),
            },
        )
        factor["confirmed"] = True
        factor.pop("challenge", None)
        save()
for user in (
    "admin1",
    "medical1",
    "medical2",
    "coordinator1",
    "operator1",
    "operator2",
    "transport1",
    "auditor1",
):
    data = {"username": user, "password": credentials["password"]}
    if user in state["factors"]:
        data["otp"] = code(user)
    state["tokens"][user] = call(
        "identidad_acceso", "POST", "/api/v1/auth/login", data
    )["access_token"]
    save()
print("Autenticación API y MFA verificadas.", flush=True)
limited = once(
    "limited",
    lambda: call(
        "identidad_acceso",
        "POST",
        "/api/v1/users",
        {
            "username": "gcp_check_" + uuid4().hex[:10],
            "password": credentials["password"],
            "tenant_id": credentials["tenants"][0],
            "role": "OPERATOR",
        },
        "admin1",
    ),
)
unit = once(
    "unit",
    lambda: call(
        "inventario",
        "POST",
        "/api/v1/resources",
        {
            "folio": "RH-GCP-" + uuid4().hex[:10],
            "kind": "BLOOD",
            "component": "RBC",
            "blood_group": "O-",
            "expires_at": iso(days=2),
        },
        "operator1",
    ),
)
profile = once(
    "profile",
    lambda: call(
        "compatibilidad",
        "POST",
        "/api/v1/laboratory/profiles",
        {
            "name": "Perfil ficticio de verificación GCP",
            "kind": "BLOOD",
            "component": "RBC",
            "version": 1,
            "required_tests": ["ABO"],
            "source": "Prueba técnica sintética; no habilita uso clínico",
            "synthetic": True,
            "effective_at": iso(),
        },
        "medical1",
    ),
)
once(
    "controls",
    lambda: call(
        "inventario",
        "POST",
        f"/api/v1/resources/{unit['id']}/controls",
        dict(confirm, version=unit["version"], lab_profile_id=profile["id"]),
        "medical1",
    ),
)
sample = once(
    "sample",
    lambda: call(
        "compatibilidad",
        "POST",
        "/api/v1/laboratory/samples",
        {
            "resource_id": unit["id"],
            "profile_id": profile["id"],
            "identifier": "GCP-" + uuid4().hex,
            "collected_at": iso(minutes=-5),
        },
        "operator1",
    ),
)
once(
    "sample_received",
    lambda: call(
        "compatibilidad",
        "POST",
        f"/api/v1/laboratory/samples/{sample['id']}/receive",
        dict(confirm, version=1, decision="RECEIVED"),
        "operator1",
    ),
)
result = once(
    "result",
    lambda: call(
        "compatibilidad",
        "POST",
        "/api/v1/laboratory/results",
        {
            "sample_id": sample["id"],
            "test_code": "ABO",
            "value": "O",
            "method": "Método ficticio",
            "laboratory": "Laboratorio sintético",
            "reference": "Comprobación técnica autorizada",
            "measured_at": iso(minutes=-1),
        },
        "operator1",
    ),
)


def review():
    proof = call(
        "identidad_acceso",
        "POST",
        "/api/v1/auth/reauthenticate",
        {
            "password": credentials["password"],
            "otp": code("medical1"),
            "operation": "lab_result_review",
            "resource_id": result["id"],
        },
        "medical1",
    )["proof"]
    return call(
        "compatibilidad",
        "POST",
        f"/api/v1/laboratory/results/{result['id']}/review",
        dict(confirm, version=1, decision="AUTHORIZED"),
        "medical1",
        {"X-Reauthentication-Proof": proof},
    )


once("result_review", review)
recipient = once(
    "recipient",
    lambda: call(
        "receptores",
        "POST",
        "/api/v1/recipients",
        {
            "folio": "RH-GCP-P-" + uuid4().hex[:8],
            "display_name": "Paciente ficticio de comprobación GCP",
            "kind": "BLOOD",
            "blood_group": "A+",
            "studies": "Datos sintéticos autorizados, sin uso clínico",
        },
        "medical2",
    ),
)
accounts = {}
for alias, user in [
    ("origin", "medical1"),
    ("destination", "medical2"),
    ("coordinator", "coordinator1"),
    ("admin", "admin1"),
]:
    accounts[alias] = dict(
        credentials["accounts"][user], username=user, **state["factors"][user]
    )
accounts["limited"] = limited
output = dict(
    base=origin,
    gateway="GCP Nginx HTTPS/WSS",
    password=credentials["password"],
    seedPassword=credentials["password"],
    seedAccounts=credentials["accounts"],
    accounts=accounts,
    tokens=state["tokens"],
    unit=unit,
    result=result,
    recipient=recipient,
    privateReports=True,
    output=str(
        Path("documentation/evidencias/gcp/correccion-20261031/recorrido").resolve()
    ),
    urls={
        s: origin + "/services/" + s.replace("_", "-")
        for s in ("identidad_acceso", "transporte", "documentos", "receptores")
    },
)
(root / "demo-input.json").write_text(json.dumps(output, indent=2) + "\n")
(root / "demo-input.json").chmod(0o600)
print(
    "Unidad, laboratorio y receptor ficticios preparados; credenciales conservadas en archivo privado.",
    flush=True,
)
