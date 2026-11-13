"""CONT-01: continuidad académica HLA, sin interpretar compatibilidad clínica."""

import json
from uuid import uuid4

import pytest
import requests
from jsonschema import Draft202012Validator
from redhouse.examples import request_xml
from redhouse.openapi import spec
from redhouse.xml_response import validate_response

from .helpers import iso, resource, route
from .test_final_quality import api

CONFIRM = {"human_confirmation": True, "reason": "Revisión humana sintética"}


def rejected(p, service, path, body, user, fmt):
    headers = {"Authorization": "Bearer " + p.tokens[user], "Accept": "application/" + fmt,
               "Content-Type": "application/" + fmt, "Idempotency-Key": uuid4().hex}
    encoded = request_xml(body).encode() if fmt == "xml" else json.dumps(body)
    response = requests.post(p.urls[service] + path, headers=headers, data=encoded, timeout=20)
    assert response.status_code == 409, response.text
    document = validate_response(response.content, {"type": "object"}) if fmt == "xml" else response.json()
    schema = spec(p.apps[service])["components"]["schemas"]
    Draft202012Validator({"$ref": "#/components/schemas/Error", "components": {"schemas": schema}}).validate(document)
    return document["error"]


@pytest.mark.parametrize("fmt", ["json", "xml"])
def test_hla_recipient_evaluation_review_and_correction_staleness(p, monkeypatch, fmt):
    unit = resource(p, kind="ORGAN", component="KIDNEY", group="A+")
    route(p)
    recipient = api(p, "receptores", "/api/v1/recipients", {
        "folio": "HLA-R-" + uuid4().hex[:10], "display_name": "Receptor ficticio",
        "kind": "ORGAN", "blood_group": "A+", "organ_type": "KIDNEY", "studies": "Sin interpretación clínica",
    }, user="medical2", fmt=fmt)
    request = api(p, "receptores", "/api/v1/requests", {
        "recipient_id": recipient["id"], "component": "KIDNEY", "quantity": 1, "urgency": 3,
    }, user="medical2", fmt=fmt)
    profile = api(p, "compatibilidad", "/api/v1/laboratory/profiles", {
        "name": "Perfil HLA sintético", "kind": "ORGAN", "component": "KIDNEY", "version": 1,
        "required_tests": ["HLA"], "required_loci": ["A"], "source": "Protocolo académico ficticio",
        "synthetic": True, "effective_at": iso(),
    }, user="medical2", fmt=fmt)
    sample = api(p, "compatibilidad", "/api/v1/laboratory/samples", {
        "recipient_id": recipient["id"], "request_id": request["id"], "profile_id": profile["id"],
        "identifier": "HLA-" + uuid4().hex[:12], "collected_at": iso(minutes=-5),
    }, user="medical2", fmt=fmt)
    api(p, "compatibilidad", f"/api/v1/laboratory/samples/{sample['id']}/receive",
        dict(CONFIRM, version=1, decision="RECEIVED"), user="medical2", fmt=fmt)
    check_path = f"/api/v1/laboratory/samples/{sample['id']}/completeness"
    incomplete = api(p, "compatibilidad", check_path, user="medical2", fmt=fmt, method="GET")
    assert not incomplete["complete"] and not incomplete["clinical_approval"] and not incomplete["clinical_enabled"]
    assert "HLA" in incomplete["missing"] and "HLA:A" in incomplete["missing"]

    def evaluate():
        row = api(p, "compatibilidad", "/api/v1/evaluations", {"request_id": request["id"]}, user="medical2", fmt=fmt)
        candidate = next(c for c in row["candidates"] if c["resource_id"] == unit["id"])
        assert row["algorithm_version"] == "ORGAN-1.0"
        assert row["snapshot"]["preselection_only"] and row["snapshot"]["operation_scope"] == "ACADEMIC"
        assert "no interpreta HLA" in candidate["explanation"] and "dictamen médico" in candidate["explanation"]
        return row

    def detail(row):
        return api(p, "compatibilidad", f"/api/v1/evaluations/{row['id']}", user="medical2", fmt=fmt, method="GET")

    review_body = dict(CONFIRM, resource_id=unit["id"], decision="FAVORABLE")
    initial = evaluate()
    initial_detail = detail(initial)
    assert not initial_detail["reviews"] and not initial_detail["validity"]["current"]
    assert "RECIPIENT_LABORATORY_INCOMPLETE" in initial_detail["validity"]["reasons"]
    error = rejected(p, "compatibilidad", f"/api/v1/evaluations/{initial['id']}/reviews", review_body, "medical2", fmt)
    assert error["code"] == "stale_evaluation"

    body = {"sample_id": sample["id"], "test_code": "HLA", "result_state": "REPORTED",
            "method": "Declaración sintética", "laboratory": "Laboratorio ficticio", "reference": "Sin uso clínico",
            "measured_at": iso(minutes=-2), "issued_at": iso(minutes=-1),
            "hla": {"nomenclature": "HLA-colon-2010", "nomenclature_version": "2010", "resolution": "Dos campos",
                    "loci": [{"locus": "A", "alleles": ["A*01:01"], "ambiguous": False}]}}
    first = api(p, "compatibilidad", "/api/v1/laboratory/results", body, user="medical2", fmt=fmt)
    pending = api(p, "compatibilidad", check_path, user="medical2", fmt=fmt, method="GET")
    assert not pending["complete"] and not pending["clinical_approval"]
    api(p, "compatibilidad", f"/api/v1/laboratory/results/{first['id']}/review",
        dict(CONFIRM, version=first["version"], decision="AUTHORIZED"), user="medical2", fmt=fmt)
    complete = api(p, "compatibilidad", check_path, user="medical2", fmt=fmt, method="GET")
    assert complete["complete"] and not complete["clinical_approval"] and not complete["clinical_enabled"]
    assert complete["profile_version"] == 1 and complete["result_ids"] == [first["id"]]
    assert "RECIPIENT_LABORATORY_CHANGED" in detail(initial)["validity"]["reasons"]

    reviewed = evaluate()
    assert detail(reviewed)["validity"]["current"] and not detail(reviewed)["reviews"]
    decision = api(p, "compatibilidad", f"/api/v1/evaluations/{reviewed['id']}/reviews", review_body, user="medical2", fmt=fmt)
    assert decision["decision"] == "FAVORABLE" and decision["reason"] == CONFIRM["reason"]
    assert decision["operation_scope"] == "ACADEMIC"
    corrected_body = dict(body, result_state="CORRECTED", supersedes=first["id"],
                          hla=dict(body["hla"], loci=[{"locus": "A", "alleles": ["A*02:01"], "ambiguous": False}]))
    corrected = api(p, "compatibilidad", "/api/v1/laboratory/results", corrected_body, user="medical2", fmt=fmt)
    assert corrected["version"] == 2 and corrected["supersedes"] == first["id"]
    changed = detail(reviewed)
    assert not changed["validity"]["current"] and "RECIPIENT_LABORATORY_CHANGED" in changed["validity"]["reasons"]
    assert len(changed["reviews"]) == 1 and changed["reviews"][0]["id"] == decision["id"]
    error = rejected(p, "compatibilidad", f"/api/v1/evaluations/{reviewed['id']}/reviews", review_body, "medical2", fmt)
    assert error["code"] == "stale_evaluation"
    api(p, "compatibilidad", f"/api/v1/laboratory/results/{corrected['id']}/review",
        dict(CONFIRM, version=2, decision="AUTHORIZED"), user="medical2", fmt=fmt)
    latest = api(p, "compatibilidad", check_path, user="medical2", fmt=fmt, method="GET")
    assert latest["complete"] and not latest["clinical_approval"] and not latest["clinical_enabled"]
    assert latest["result_ids"] == [corrected["id"]] and latest["fingerprint"] != complete["fingerprint"]
    fresh = evaluate()
    fresh_detail = detail(fresh)
    assert fresh_detail["validity"]["current"] and not fresh_detail["reviews"]
    assert fresh["snapshot"]["recipient_laboratory"]["fingerprint"] != reviewed["snapshot"]["recipient_laboratory"]["fingerprint"]
    monkeypatch.setitem(p.apps["compatibilidad"].config, "OPERATION_SCOPE", "CLINICAL")
    denied = rejected(p, "compatibilidad", "/api/v1/evaluations", {"request_id": request["id"]}, "medical2", fmt)
    assert denied["code"] == "clinical_profile_required"
