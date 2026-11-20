"""Flujo persistente de laboratorio/frío/destino y controles por institución."""

from uuid import uuid4
import pytest

from redhouse.examples import request_xml
from redhouse.xml_response import validate_response
from .helpers import iso


def api(p, service, path, data=None, user="medical1", fmt="json", method="POST"):
    if fmt == "json":
        result = p.ok(service, method, path, user=user, data=data)
        import jsonschema
        from redhouse.output_schemas import result_schema

        name, _ = (
            p.apps[service]
            .url_map.bind("localhost")
            .match(path.split("?")[0], method=method)
        )
        contract = next(
            c for c in p.apps[service].extensions["contracts"] if c["name"] == name
        )
        jsonschema.validate(result, contract["result"] or result_schema(service, name))
        return result
    import requests

    headers = {
        "Content-Type": "application/xml",
        "Accept": "application/xml",
        "Idempotency-Key": uuid4().hex,
    }
    if user:
        headers["Authorization"] = "Bearer " + p.tokens[user]
    if path == "/api/v1/auth/login" and data:
        headers["X-RedHouse-Client"] = p.client_of(data.get("username", ""))
    response = requests.request(
        method,
        p.urls[service] + path,
        data=request_xml(data).encode() if data else None,
        headers=headers,
        timeout=20,
    )
    assert response.status_code < 300, response.text
    # La respuesta XML se convierte validando XSD y DTO publicado por operación.
    name, _ = (
        p.apps[service]
        .url_map.bind("localhost")
        .match(path.split("?")[0], method=method)
    )
    contract = next(
        c for c in p.apps[service].extensions["contracts"] if c["name"] == name
    )
    from redhouse.output_schemas import result_schema

    output = contract["result"] or result_schema(service, name)
    return validate_response(
        response.content, {"type": "object", "properties": {"data": output}}
    )["data"]


@pytest.mark.parametrize("fmt", ["json", "xml"])
def test_laboratory_missing_results_correction_quarantine_and_final_destination(p, fmt):
    unit = api(
        p,
        "inventario",
        "/api/v1/resources",
        {
            "folio": "FINAL-" + uuid4().hex[:10],
            "kind": "BLOOD",
            "component": "RBC",
            "blood_group": "O-",
            "expires_at": iso(days=2),
        },
        "operator1",
        fmt,
    )
    profile = api(
        p,
        "compatibilidad",
        "/api/v1/laboratory/profiles",
        {
            "name": "Perfil sintético",
            "kind": "BLOOD",
            "component": "RBC",
            "version": 1,
            "required_tests": ["ABO", "TEST_SYNTHETIC"],
            "source": "Caso sintético de integración, sin aplicación clínica",
            "synthetic": True,
            "effective_at": iso(),
        },
        fmt=fmt,
    )
    equipment = api(
        p,
        "inventario",
        "/api/v1/cold/equipment",
        {"label": "Equipo ficticio", "location": "Sede de prueba"},
        "operator1",
        fmt,
    )
    cold = api(
        p,
        "inventario",
        "/api/v1/cold/profiles",
        {
            "kind": "BLOOD",
            "component": "RBC",
            "minimum_c": 1.0,
            "maximum_c": 9.0,
            "max_gap_seconds": 600,
            "effective_at": iso(),
            "source": "Valores exclusivamente sintéticos de prueba",
            "synthetic": True,
        },
        fmt=fmt,
    )
    confirmation = {
        "human_confirmation": True,
        "reason": "Revisión humana de prueba sintética",
    }
    api(
        p,
        "inventario",
        f"/api/v1/resources/{unit['id']}/controls",
        {
            **confirmation,
            "version": unit["version"],
            "lab_profile_id": profile["id"],
            "cold_equipment_id": equipment["id"],
            "cold_profile_id": cold["id"],
        },
        fmt=fmt,
    )
    sample = api(
        p,
        "compatibilidad",
        "/api/v1/laboratory/samples",
        {
            "resource_id": unit["id"],
            "profile_id": profile["id"],
            "identifier": "SAMPLE-" + uuid4().hex[:10],
            "collected_at": iso(minutes=-10),
        },
        "operator1",
        fmt,
    )
    result_body = {
        "sample_id": sample["id"],
        "test_code": "ABO",
        "value": "O",
        "method": "Método sintético",
        "laboratory": "Laboratorio ficticio",
        "reference": "Referencia de prueba",
        "measured_at": iso(minutes=-1),
    }
    assert (
        p.request(
            "compatibilidad",
            "POST",
            "/api/v1/laboratory/results",
            user="operator1",
            data=result_body,
        ).status_code
        == 409
    )
    api(
        p,
        "compatibilidad",
        f"/api/v1/laboratory/samples/{sample['id']}/receive",
        {**confirmation, "version": 1, "decision": "RECEIVED"},
        "operator1",
        fmt,
    )
    api(
        p,
        "inventario",
        f"/api/v1/resources/{unit['id']}/cold-readings",
        {"temperature_c": 5.0, "captured_at": iso(), "source": "Manual sintético"},
        "operator1",
        fmt,
    )
    assert (
        p.request(
            "inventario",
            "POST",
            f"/api/v1/resources/{unit['id']}/release",
            user="medical1",
            data={**confirmation, "version": 2},
        ).status_code
        == 409
    )
    results = []
    for code in ("ABO", "TEST_SYNTHETIC"):
        result = api(
            p,
            "compatibilidad",
            "/api/v1/laboratory/results",
            dict(result_body, test_code=code),
            "operator1",
            fmt,
        )
        assert (
            p.request(
                "compatibilidad",
                "POST",
                f"/api/v1/laboratory/results/{result['id']}/review",
                user="operator1",
                data={**confirmation, "version": 1, "decision": "AUTHORIZED"},
            ).status_code
            == 403
        )
        api(
            p,
            "compatibilidad",
            f"/api/v1/laboratory/results/{result['id']}/review",
            {**confirmation, "version": 1, "decision": "AUTHORIZED"},
            fmt=fmt,
        )
        results.append(result)
    correction = api(
        p,
        "compatibilidad",
        "/api/v1/laboratory/results",
        dict(result_body, value="O corregido sintético", supersedes=results[0]["id"]),
        "operator1",
        fmt,
    )
    assert correction["version"] == 2
    assert (
        p.request(
            "inventario",
            "POST",
            f"/api/v1/resources/{unit['id']}/release",
            user="medical1",
            data={**confirmation, "version": 2},
        ).status_code
        == 409
    )
    api(
        p,
        "compatibilidad",
        f"/api/v1/laboratory/results/{correction['id']}/review",
        {**confirmation, "version": correction["version"], "decision": "AUTHORIZED"},
        fmt=fmt,
    )
    unit = api(
        p,
        "inventario",
        f"/api/v1/resources/{unit['id']}/release",
        {**confirmation, "version": 2},
        fmt=fmt,
    )
    reading = api(
        p,
        "inventario",
        f"/api/v1/resources/{unit['id']}/cold-readings",
        {"temperature_c": 20.0, "captured_at": iso(), "source": "Sensor sintético"},
        "operator1",
        fmt,
    )
    assert reading["excursion"] is True
    unit = p.ok("inventario", "GET", f"/api/v1/resources/{unit['id']}", user="medical1")
    assert unit["status"] == "QUARANTINE"
    assert (
        p.request(
            "inventario",
            "POST",
            f"/api/v1/resources/{unit['id']}/release",
            user="medical1",
            data={**confirmation, "version": unit["version"]},
        ).status_code
        == 409
    )
    assert (
        p.request(
            "inventario",
            "GET",
            f"/api/v1/resources/{unit['id']}/controls",
            user="medical2",
        ).status_code
        == 403
    )
    destination = api(
        p,
        "inventario",
        f"/api/v1/resources/{unit['id']}/destination",
        {
            **confirmation,
            "version": unit["version"],
            "destination": "DISCARDED",
            "reference": "Acta ficticia",
            "occurred_at": iso(),
        },
        fmt=fmt,
    )
    assert destination["destination"] == "DISCARDED"
    unit = p.ok("inventario", "GET", f"/api/v1/resources/{unit['id']}", user="medical1")
    assert unit["status"] == "WITHDRAWN"

    p.drain()
    events = api(
        p,
        "auditoria",
        "/api/v1/events?action=RESOURCE_COLD_QUARANTINE&resource=" + unit["id"],
        user="auditor1",
        fmt=fmt,
        method="GET",
    )
    assert events["total"] == 1 and events["items"][0]["category"] == "DECISION"
