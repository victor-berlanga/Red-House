"""Políticas simultáneas con TOTP real; datos de órgano exclusivamente sintéticos."""

import time
from uuid import uuid4

import pytest

from .helpers import iso, route
from .test_correction_backend import CONFIRM
from .test_final_quality import api


@pytest.mark.parametrize("fmt", ["json", "xml"])
def test_combined_operational_organ_policies(p, monkeypatch, fmt):
    from ms_identidad_acceso.strong_auth import totp
    from redhouse.examples import request_xml
    from redhouse.xml_response import validate_response
    import requests
    import jsonschema

    accounts = {}
    # Altas y enrolamiento reales; no se fabrican JWT, factores ni pruebas Redis.
    for index in (0, 1):
        name = "policy_" + uuid4().hex[:12]
        password = p.env.state["password"]
        api(
            p,
            "identidad_acceso",
            "/api/v1/users",
            dict(
                username=name,
                password=password,
                tenant_id=p.env.state["tenants"][index],
                role="MEDICAL",
            ),
            "admin" + str(index + 1),
            fmt,
        )
        enrollment = api(
            p,
            "identidad_acceso",
            "/api/v1/auth/mfa/enrollment",
            dict(username=name, password=password),
            None,
            fmt,
        )
        counter = int(time.time()) // 30 - 1
        api(
            p,
            "identidad_acceso",
            "/api/v1/auth/mfa/confirm",
            dict(
                challenge=enrollment["challenge"],
                code=totp(enrollment["secret"], counter),
            ),
            None,
            fmt,
        )
        accounts[index] = dict(name=name, secret=enrollment["secret"], counter=counter)
    for app in p.apps.values():
        monkeypatch.setitem(app.config, "MFA_REQUIRED_ROLES", ["MEDICAL"])
        monkeypatch.setitem(
            app.config,
            "REAUTH_REQUIRED_OPERATIONS",
            ["resource_release", "lab_result_review", "reservation_create"],
        )
        monkeypatch.setitem(app.config, "REQUIRE_LAB_PROFILE", True)
        monkeypatch.setitem(app.config, "REQUIRE_ORGAN_AUTHORIZATION", True)

    def code(index):
        account = accounts[index]
        while int(time.time()) // 30 <= account["counter"]:
            time.sleep(0.2)
        account["counter"] = int(time.time()) // 30
        return totp(account["secret"], account["counter"])

    for index, account in accounts.items():
        assert (
            p.request(
                "identidad_acceso",
                "POST",
                "/api/v1/auth/login",
                user=None,
                data=dict(username=account["name"], password=password),
            ).status_code
            == 401
        )
        session = api(
            p,
            "identidad_acceso",
            "/api/v1/auth/login",
            dict(username=account["name"], password=password, otp=code(index)),
            None,
            fmt,
        )
        monkeypatch.setitem(p.tokens, account["name"], session["access_token"])

    def protected(service, path, body, index, operation, resource_id, expected=200):
        user = accounts[index]["name"]
        proof = api(
            p,
            "identidad_acceso",
            "/api/v1/auth/reauthenticate",
            dict(
                password=password,
                otp=code(index),
                operation=operation,
                resource_id=resource_id,
            ),
            user,
            fmt,
        )
        headers = {
            "Authorization": "Bearer " + p.tokens[user],
            "Accept": "application/" + fmt,
            "Content-Type": "application/" + fmt,
            "Idempotency-Key": uuid4().hex,
            "X-Reauthentication-Proof": proof["proof"],
        }
        response = requests.post(
            p.urls[service] + path,
            headers=headers,
            data=request_xml(body).encode()
            if fmt == "xml"
            else __import__("json").dumps(body),
            timeout=20,
        )
        assert response.status_code == expected, response.text
        if expected >= 400:
            return
        name, _ = p.apps[service].url_map.bind("localhost").match(path, method="POST")
        contract = next(
            c for c in p.apps[service].extensions["contracts"] if c["name"] == name
        )
        from redhouse.output_schemas import result_schema

        schema = contract["result"] or result_schema(service, name)
        if fmt == "xml":
            return validate_response(
                response.content, {"type": "object", "properties": {"data": schema}}
            )["data"]
        data = response.json()["data"]
        jsonschema.validate(data, schema)
        return data

    origin, destination = accounts[0]["name"], accounts[1]["name"]
    route(p)
    unit = api(
        p,
        "inventario",
        "/api/v1/resources",
        dict(
            folio="POLICY-" + uuid4().hex[:10],
            kind="ORGAN",
            component="KIDNEY",
            blood_group="A-",
            expires_at=iso(days=2),
        ),
        "operator1",
        fmt,
    )
    release = f"/api/v1/resources/{unit['id']}/release"
    assert (
        p.request(
            "inventario", "POST", release, user=origin, data=dict(CONFIRM, version=1)
        ).status_code
        == 403
    )
    protected(
        "inventario",
        release,
        dict(CONFIRM, version=1),
        0,
        "resource_release",
        unit["id"],
        409,
    )
    profile = api(
        p,
        "compatibilidad",
        "/api/v1/laboratory/profiles",
        dict(
            name="Perfil sintético de órgano",
            kind="ORGAN",
            component="KIDNEY",
            version=1,
            required_tests=["SYNTHETIC"],
            source="Prueba técnica, sin validez clínica",
            synthetic=True,
            effective_at=iso(),
        ),
        origin,
        fmt,
    )
    api(
        p,
        "inventario",
        f"/api/v1/resources/{unit['id']}/controls",
        dict(CONFIRM, version=1, lab_profile_id=profile["id"]),
        origin,
        fmt,
    )
    sample = api(
        p,
        "compatibilidad",
        "/api/v1/laboratory/samples",
        dict(
            resource_id=unit["id"],
            profile_id=profile["id"],
            identifier="SYN-" + uuid4().hex,
            collected_at=iso(minutes=-2),
        ),
        "operator1",
        fmt,
    )
    api(
        p,
        "compatibilidad",
        f"/api/v1/laboratory/samples/{sample['id']}/receive",
        dict(CONFIRM, version=1, decision="RECEIVED"),
        "operator1",
        fmt,
    )
    result = api(
        p,
        "compatibilidad",
        "/api/v1/laboratory/results",
        dict(
            sample_id=sample["id"],
            test_code="SYNTHETIC",
            value="Dato sintético",
            method="Prueba",
            laboratory="Prueba",
            reference="Sin validez clínica",
            measured_at=iso(minutes=-1),
        ),
        "operator1",
        fmt,
    )
    protected(
        "compatibilidad",
        f"/api/v1/laboratory/results/{result['id']}/review",
        dict(CONFIRM, version=1, decision="AUTHORIZED"),
        0,
        "lab_result_review",
        result["id"],
    )
    current = api(
        p,
        "inventario",
        f"/api/v1/resources/{unit['id']}",
        user=origin,
        fmt=fmt,
        method="GET",
    )
    protected(
        "inventario",
        release,
        dict(CONFIRM, version=current["version"]),
        0,
        "resource_release",
        unit["id"],
    )
    recipient = api(
        p,
        "receptores",
        "/api/v1/recipients",
        dict(
            folio="SYN-" + uuid4().hex[:10],
            display_name="Paciente sintético",
            kind="ORGAN",
            blood_group="A+",
            organ_type="KIDNEY",
            studies="Referencia sintética, no autorización clínica",
        ),
        destination,
        fmt,
    )
    req = api(
        p,
        "receptores",
        "/api/v1/requests",
        dict(recipient_id=recipient["id"], component="KIDNEY", quantity=1, urgency=2),
        destination,
        fmt,
    )
    evaluation = api(
        p,
        "compatibilidad",
        "/api/v1/evaluations",
        dict(request_id=req["id"]),
        destination,
        fmt,
    )
    api(
        p,
        "compatibilidad",
        f"/api/v1/evaluations/{evaluation['id']}/reviews",
        dict(CONFIRM, resource_id=unit["id"], decision="FAVORABLE"),
        destination,
        fmt,
    )
    body = dict(CONFIRM, evaluation_id=evaluation["id"], resource_id=unit["id"])
    protected(
        "inventario",
        "/api/v1/reservations",
        body,
        1,
        "reservation_create",
        unit["id"],
        409,
    )
    with p.owner("inventario") as conn:
        assert (
            conn.execute(
                "SELECT count(*) FROM reservations WHERE resource_id=%s", (unit["id"],)
            ).fetchone()[0]
            == 0
        )
    api(
        p,
        "receptores",
        f"/api/v1/requests/{req['id']}/external-authorizations",
        dict(
            CONFIRM,
            authority="Autoridad ficticia",
            reference="Constancia sintética; no autorización oficial",
            valid_from=iso(days=-1),
            valid_until=iso(days=1),
            effective_at=iso(),
            decision="RECORDED",
        ),
        destination,
        fmt,
    )
    accepted = protected(
        "inventario",
        "/api/v1/reservations",
        body,
        1,
        "reservation_create",
        unit["id"],
        202,
    )
    assert accepted
    with p.owner("inventario") as conn:
        assert (
            conn.execute(
                "SELECT count(*) FROM reservations WHERE resource_id=%s", (unit["id"],)
            ).fetchone()[0]
            == 1
        )
