"""Corrective cases: real owner APIs, isolated databases and independent oracles."""

from uuid import uuid4

import pytest

from .helpers import iso
from .test_final_quality import api
from .test_final_tracking import tracking  # noqa: F401 - pytest fixture dependency


def profile(p, **changes):
    data = {
        "name": "Perfil sintético correctivo",
        "kind": "ORGAN",
        "component": "KIDNEY",
        "version": 1,
        "required_tests": ["HLA"],
        "source": "Ensayo sintético; sin aprobación clínica",
        "synthetic": True,
        "effective_at": iso(minutes=-60),
    }
    data.update(changes)
    return api(p, "compatibilidad", "/api/v1/laboratory/profiles", data)


def recipient(p, organ="LIVER"):
    return api(
        p,
        "receptores",
        "/api/v1/recipients",
        {
            "folio": "COR-" + uuid4().hex[:8],
            "display_name": "Receptor ficticio",
            "studies": "Estudios sintéticos pendientes",
            "kind": "ORGAN",
            "organ_type": organ,
            "blood_group": "O+",
        },
    )


def test_hla_one_field_is_not_reported_allele():
    from ms_compatibilidad.hla import Typing
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        Typing(
            nomenclature="HLA-colon-2010",
            nomenclature_version="2010",
            resolution="two fields",
            loci=[{"locus": "A", "alleles": ["A*01"]}],
        )


def test_recipient_organ_profile_mismatch_rejected(p):
    rec = recipient(p)
    prof = profile(p)
    res = p.request(
        "compatibilidad",
        "POST",
        "/api/v1/laboratory/samples",
        user="medical1",
        data={
            "recipient_id": rec["id"],
            "profile_id": prof["id"],
            "identifier": "mismatch-" + uuid4().hex,
            "collected_at": iso(),
        },
    )
    assert res.status_code == 409, res.text


def test_future_profile_cannot_collect_sample(p):
    rec = recipient(p, "KIDNEY")
    prof = profile(p, effective_at=iso(days=1))
    res = p.request(
        "compatibilidad",
        "POST",
        "/api/v1/laboratory/samples",
        user="medical1",
        data={
            "recipient_id": rec["id"],
            "profile_id": prof["id"],
            "identifier": "future-" + uuid4().hex,
            "collected_at": iso(),
        },
    )
    assert res.status_code == 409, res.text


CONFIRM = {"human_confirmation": True, "reason": "Revisión técnica de datos ficticios"}


@pytest.mark.parametrize("fmt", ["json", "xml"])
def test_registry_transitions_history_and_disabled_clinical_scope(p, fmt, monkeypatch):
    prof = profile(p)
    base = "/api/v1/laboratory/profiles/" + prof["id"]
    change = dict(
        CONFIRM,
        sequence=1,
        state="APPROVED",
        competency_reference="Cuenta de prueba no acredita competencia",
    )
    assert (
        p.request(
            "compatibilidad", "POST", base + "/actions", user="medical1", data=change
        ).status_code
        == 403
    )
    review = api(
        p,
        "compatibilidad",
        base + "/actions",
        dict(CONFIRM, sequence=1, state="IN_REVIEW"),
        fmt=fmt,
    )
    assert review["state"] == "IN_REVIEW"
    assert (
        p.request(
            "compatibilidad",
            "POST",
            base + "/actions",
            user="operator1",
            data=dict(CONFIRM, sequence=2, state="RETIRED"),
        ).status_code
        == 403
    )
    api(
        p,
        "compatibilidad",
        base + "/actions",
        dict(CONFIRM, sequence=2, state="RETIRED"),
        fmt=fmt,
    )
    history = api(p, "compatibilidad", base + "/governance", method="GET", fmt=fmt)
    assert len(history["actions"]) == 2 and not history["clinical_enabled"]
    original = api(p, "compatibilidad", base, method="GET", fmt=fmt)
    assert original["rule_status"] == "DRAFT"
    monkeypatch.setitem(p.apps["inventario"].config, "OPERATION_SCOPE", "CLINICAL")
    unit = api(
        p,
        "inventario",
        "/api/v1/resources",
        {
            "folio": "CLIN-" + uuid4().hex[:10],
            "kind": "BLOOD",
            "component": "RBC",
            "blood_group": "O-",
            "expires_at": iso(days=1),
        },
        user="operator1",
    )
    res = p.request(
        "inventario",
        "POST",
        "/api/v1/resources/" + unit["id"] + "/release",
        user="medical1",
        data=dict(CONFIRM, version=1),
    )
    assert res.status_code == 409
    assert (
        api(p, "inventario", "/api/v1/resources/" + unit["id"], method="GET")["status"]
        == "QUARANTINE"
    )


@pytest.mark.parametrize("fmt", ["json", "xml"])
def test_partial_hla_and_unknown_version_persist_without_approval(p, fmt):
    rec = recipient(p, "KIDNEY")
    prof = profile(p)
    sample = api(
        p,
        "compatibilidad",
        "/api/v1/laboratory/samples",
        {
            "recipient_id": rec["id"],
            "profile_id": prof["id"],
            "identifier": "PART-" + uuid4().hex,
            "collected_at": iso(minutes=-5),
        },
        fmt=fmt,
    )
    api(
        p,
        "compatibilidad",
        "/api/v1/laboratory/samples/" + sample["id"] + "/receive",
        dict(CONFIRM, version=1, decision="RECEIVED"),
        fmt=fmt,
    )
    body = {
        "sample_id": sample["id"],
        "test_code": "HLA",
        "result_state": "INDETERMINATE",
        "method": "Tipificación ficticia",
        "laboratory": "Laboratorio ficticio",
        "reference": "Documento pendiente",
        "measured_at": iso(minutes=-2),
        "issued_at": iso(minutes=-1),
        "hla": {
            "nomenclature": "HLA-colon-2010",
            "nomenclature_version": "unknown",
            "resolution": "Grupo parcial",
            "loci": [
                {
                    "locus": "A",
                    "alleles": [],
                    "groups": ["A*01"],
                    "partial": True,
                    "ambiguous": True,
                }
            ],
        },
    }
    assert (
        p.request(
            "compatibilidad",
            "POST",
            "/api/v1/laboratory/results",
            user="medical1",
            data=body,
        ).status_code
        == 422
    )
    body["hla"]["nomenclature_version"] = "2010:syntax-2"
    row = api(p, "compatibilidad", "/api/v1/laboratory/results", body, fmt=fmt)
    assert row["hla"]["loci"][0]["groups"] == ["A*01"]
    assert row["status"] == "CAPTURED"
    api(
        p,
        "compatibilidad",
        "/api/v1/laboratory/results/" + row["id"] + "/review",
        dict(CONFIRM, version=1, decision="AUTHORIZED"),
        fmt=fmt,
    )
    check = api(
        p,
        "compatibilidad",
        "/api/v1/laboratory/samples/" + sample["id"] + "/completeness",
        method="GET",
        fmt=fmt,
    )
    assert not check["complete"] and not check["clinical_approval"]
    assert "HLA:UNRESOLVED_DECLARATION" in check["missing"]
    assert (
        api(
            p,
            "compatibilidad",
            "/api/v1/laboratory/results/" + row["id"],
            method="GET",
            fmt=fmt,
        )["hla"]
        == row["hla"]
    )


@pytest.mark.parametrize("fmt", ["json", "xml"])
def test_recipient_lab_change_invalidates_review_detail_and_reserve(p, fmt):
    from .helpers import evaluation, recipient_request, resource

    unit = resource(p)
    rec, req = recipient_request(p)
    ev = evaluation(p, req, [unit])
    # Recipient's own institution records a pending immunological result after review.
    prof = api(
        p,
        "compatibilidad",
        "/api/v1/laboratory/profiles",
        {
            "name": "Receptor",
            "kind": "BLOOD",
            "component": "RBC",
            "version": 1,
            "required_tests": ["CROSSMATCH"],
            "source": "Caso sintético",
            "synthetic": True,
            "effective_at": iso(minutes=-60),
        },
        user="medical2",
        fmt=fmt,
    )
    sample = api(
        p,
        "compatibilidad",
        "/api/v1/laboratory/samples",
        {
            "recipient_id": rec["id"],
            "request_id": req["id"],
            "profile_id": prof["id"],
            "identifier": "REC-" + uuid4().hex,
            "collected_at": iso(minutes=-5),
        },
        user="medical2",
        fmt=fmt,
    )
    api(
        p,
        "compatibilidad",
        "/api/v1/laboratory/samples/" + sample["id"] + "/receive",
        dict(CONFIRM, version=1, decision="RECEIVED"),
        user="medical2",
        fmt=fmt,
    )
    api(
        p,
        "compatibilidad",
        "/api/v1/laboratory/results",
        {
            "sample_id": sample["id"],
            "test_code": "CROSSMATCH",
            "result_state": "PENDING",
            "method": "Ensayo ficticio",
            "laboratory": "Laboratorio ficticio",
            "reference": "Solicitud documentada",
            "measured_at": iso(),
        },
        user="medical2",
        fmt=fmt,
    )
    detail = api(
        p,
        "compatibilidad",
        "/api/v1/evaluations/" + ev["id"],
        method="GET",
        user="medical2",
        fmt=fmt,
    )
    assert "RECIPIENT_LABORATORY_CHANGED" in detail["validity"]["reasons"]
    denied = p.request(
        "inventario",
        "POST",
        "/api/v1/reservations",
        data=dict(CONFIRM, evaluation_id=ev["id"], resource_id=unit["id"]),
    )
    assert denied.status_code == 409, denied.text
    with p.owner("inventario") as conn:
        assert (
            conn.execute(
                "SELECT count(*) FROM reservations WHERE evaluation_id=%s", (ev["id"],)
            ).fetchone()[0]
            == 0
        )


def graph_body():
    return {
        "name": "Nuevo León sintético",
        "source": "Fixture regional identificado; no cartografía vial",
        "observed_at": iso(minutes=-60),
        "valid_until": iso(days=1),
        "quality": "Pesos ficticios sin tráfico",
        "nodes": [
            {"id": "Monterrey", "latitude": 25.67, "longitude": -100.31},
            {"id": "Linares", "latitude": 24.86, "longitude": -99.57},
        ],
        "edges": [
            {
                "origin": "Monterrey",
                "destination": "Linares",
                "minutes": 90.0,
                "distance_km": 130.0,
            }
        ],
    }


@pytest.mark.parametrize("fmt", ["json", "xml"])
def test_regional_graph_authoritative_runs_and_anomaly_outbox(p, fmt):
    graph = api(
        p, "priorizacion_geografia", "/api/v1/regional-graphs", graph_body(), fmt=fmt
    )
    geo = api(
        p,
        "priorizacion_geografia",
        "/api/v1/decision-runs",
        {
            "branch": "ALG-02-GEO",
            "graph_id": graph["id"],
            "origin": "Monterrey",
            "destination": "Linares",
        },
        fmt=fmt,
    )
    assert geo["result"]["path"] == ["Monterrey", "Linares"]
    assert geo["result"]["tracking"]["state"] == "NOT_REQUESTED"
    assert api(
        p,
        "priorizacion_geografia",
        "/api/v1/decision-runs/" + geo["id"] + "/reproduce",
        method="GET",
        fmt=fmt,
    )["identical"]
    assert (
        p.request(
            "priorizacion_geografia",
            "GET",
            "/api/v1/decision-runs/" + geo["id"],
            user="medical2",
        ).status_code
        == 403
    )
    demand = api(
        p,
        "priorizacion_geografia",
        "/api/v1/decision-runs",
        {"branch": "ALG-04", "component": "RBC", "days": 6},
        fmt=fmt,
    )
    assert len(demand["snapshot"]["inventory"]["observations"]) == 6
    assert api(
        p,
        "priorizacion_geografia",
        "/api/v1/decision-runs/" + demand["id"] + "/reproduce",
        method="GET",
        fmt=fmt,
    )["identical"]
    # Unlinked academic inventory is a real stored provenance anomaly, not a client flag.
    api(
        p,
        "inventario",
        "/api/v1/resources",
        {
            "folio": "ANOM-" + uuid4().hex[:10],
            "kind": "BLOOD",
            "component": "RBC",
            "blood_group": "O-",
            "expires_at": iso(days=1),
        },
        user="operator1",
    )
    run = api(
        p,
        "priorizacion_geografia",
        "/api/v1/decision-runs",
        {"branch": "ALG-05"},
        fmt=fmt,
    )
    assert any(
        f["code"] == "INVALID_DONATION_PROVENANCE" for f in run["result"]["findings"]
    )
    p.drain(20)
    reviews = api(p, "auditoria", "/api/v1/anomaly-reviews", method="GET", fmt=fmt)
    assert reviews["total"] > 0
    with p.owner("auditoria") as conn:
        before = conn.execute("SELECT count(*) FROM anomaly_reviews").fetchone()[0]
    api(
        p,
        "priorizacion_geografia",
        "/api/v1/decision-runs",
        {"branch": "ALG-05"},
        fmt=fmt,
    )
    p.drain(20)
    with p.owner("auditoria") as conn:
        assert (
            conn.execute("SELECT count(*) FROM anomaly_reviews").fetchone()[0] == before
        )


@pytest.mark.parametrize(
    "factor,b_value,first",
    [
        ("urgency", 3, "b"),
        ("waiting_minutes", 20, "b"),
        ("expiry_minutes", 50, "b"),
        ("travel_minutes", 5, "b"),
        ("distance_km", 2, "b"),
        ("identifier", "0", "0"),
    ],
)
def test_each_rank_factor_changes_result_with_prior_factors_tied(
    factor, b_value, first
):
    from ms_priorizacion_geografia.academic import execute

    from .test_final_algorithms_hla import experiment

    base = {
        "identifier": "a",
        "component": "RBC",
        "available": True,
        "expired": False,
        "thermal_incident": False,
        "urgency": 1,
        "urgency_source": "Escala sintética",
        "waiting_minutes": 10,
        "expiry_minutes": 100,
        "travel_minutes": 20,
        "distance_km": 5,
    }
    b = dict(base, identifier="b")
    b[factor] = b_value
    data = experiment("LOGISTICS-SIM-2.0", candidates=[base, b])
    result = execute(data)
    assert result["findings"][0]["identifier"] == first
    assert execute(dict(data, candidates=[b, base])) == result


def test_temporal_forecast_against_independent_full_oracle():
    from datetime import datetime, timedelta, timezone

    from ms_priorizacion_geografia.decisions import forecast
    from redhouse.errors import APIError

    values = [2, 5, 1, 4, 3, 7, 6, 8, 2]
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    snapshot = {
        "as_of": (start + timedelta(days=9)).isoformat(),
        "component": "RBC",
        "lots": [],
        "observations": [
            {
                "start_at": (start + timedelta(days=i)).isoformat(),
                "end_at": (start + timedelta(days=i + 1)).isoformat(),
                "value": v,
            }
            for i, v in enumerate(values)
        ],
    }
    train = values[:6]

    def predictions(alpha, series):
        level = series[0]
        errors = []
        for value in series[1:]:
            errors.append(abs(value - level))
            level = alpha * value + (1 - alpha) * level
        return sum(errors), level

    alpha = min([0.2, 0.5, 0.8], key=lambda a: (predictions(a, train)[0], a))
    level = predictions(alpha, train)[1]
    errors = []
    for value in values[6:]:
        errors.append(abs(value - level))
        level = alpha * value + (1 - alpha) * level
    result = forecast(snapshot)
    metrics = {x["name"]: x["value"] for x in result["metrics"]}
    assert metrics["alpha"] == alpha
    assert metrics["mae"] == pytest.approx(sum(errors) / 3)
    assert metrics["naive_mae"] == pytest.approx(
        sum(abs(values[i] - values[i - 1]) for i in range(6, 9)) / 3
    )
    bad = dict(
        snapshot,
        observations=snapshot["observations"][1:] + [snapshot["observations"][0]],
    )
    with pytest.raises(APIError):
        forecast(bad)


@pytest.mark.parametrize("fmt", ["json", "xml"])
def test_completeness_conflict_expiry_and_successor(p, fmt):
    from .test_correction_backend import laboratory

    unit = api(
        p,
        "inventario",
        "/api/v1/resources",
        {
            "folio": "COMP-" + uuid4().hex[:10],
            "kind": "BLOOD",
            "component": "RBC",
            "blood_group": "O-",
            "expires_at": iso(days=1),
        },
        user="operator1",
    )
    prof, body, _original = laboratory(p, unit, fmt)
    check = "/api/v1/laboratory/resources/" + unit["id"] + "/check"
    args = {"profile_id": prof["id"], "tenant_id": p.env.state["tenants"][0]}
    assert api(p, "compatibilidad", check, args, fmt=fmt)["complete"]
    other = api(
        p,
        "compatibilidad",
        "/api/v1/laboratory/samples",
        {
            "resource_id": unit["id"],
            "profile_id": prof["id"],
            "identifier": "OTHER-" + uuid4().hex,
            "collected_at": iso(minutes=-5),
        },
        fmt=fmt,
    )
    api(
        p,
        "compatibilidad",
        "/api/v1/laboratory/samples/" + other["id"] + "/receive",
        dict(CONFIRM, version=1, decision="RECEIVED"),
        fmt=fmt,
    )
    result = api(
        p,
        "compatibilidad",
        "/api/v1/laboratory/results",
        dict(body, sample_id=other["id"], value="A"),
        fmt=fmt,
    )
    api(
        p,
        "compatibilidad",
        "/api/v1/laboratory/results/" + result["id"] + "/review",
        dict(CONFIRM, version=1, decision="AUTHORIZED"),
        fmt=fmt,
    )
    completeness = api(p, "compatibilidad", check, args, fmt=fmt)
    assert (
        not completeness["complete"]
        and "CONTRADICTORY:ABO" in completeness["conflicts"]
    )
    successor = api(
        p,
        "compatibilidad",
        "/api/v1/laboratory/profiles",
        {
            "name": "Sucesor",
            "kind": "BLOOD",
            "component": "RBC",
            "version": 2,
            "required_tests": ["ABO"],
            "source": "Perfil sintético sucesor",
            "synthetic": True,
            "effective_at": iso(),
            "supersedes": prof["id"],
        },
        fmt=fmt,
    )
    assert successor["supersedes"] == prof["id"]
    assert (
        "PROFILE_SUPERSEDED"
        in api(p, "compatibilidad", check, args, fmt=fmt)["missing"]
    )
    from ms_compatibilidad.rules import validity
    from redhouse.db import get, transaction
    from redhouse.models import utc_date

    expiry = profile(p, valid_until=iso(minutes=30))
    with p.apps["compatibilidad"].test_request_context(), transaction() as conn:
        row = get(conn, "lab_profiles", expiry["id"])
        assert "PROFILE_FUTURE" in validity(
            conn,
            row,
            utc_date(expiry["effective_at"])
            - __import__("datetime").timedelta(microseconds=1),
        )
        assert not validity(conn, row, utc_date(expiry["effective_at"]))
        assert "PROFILE_EXPIRED" in validity(conn, row, utc_date(expiry["valid_until"]))
    aged_profile = profile(
        p,
        kind="BLOOD",
        component="RBC",
        required_tests=["ABO"],
        policy={"version": "COMPLETENESS-2.0", "max_age_seconds": 60},
    )
    aged_sample = api(
        p,
        "compatibilidad",
        "/api/v1/laboratory/samples",
        {
            "resource_id": unit["id"],
            "profile_id": aged_profile["id"],
            "identifier": "AGED-" + uuid4().hex,
            "collected_at": iso(minutes=-5),
        },
        fmt=fmt,
    )
    api(
        p,
        "compatibilidad",
        "/api/v1/laboratory/samples/" + aged_sample["id"] + "/receive",
        dict(CONFIRM, version=1, decision="RECEIVED"),
        fmt=fmt,
    )
    aged = api(
        p,
        "compatibilidad",
        "/api/v1/laboratory/results",
        dict(body, sample_id=aged_sample["id"], measured_at=iso(minutes=-2)),
        fmt=fmt,
    )
    api(
        p,
        "compatibilidad",
        "/api/v1/laboratory/results/" + aged["id"] + "/review",
        dict(CONFIRM, version=1, decision="AUTHORIZED"),
        fmt=fmt,
    )
    check_age = api(
        p,
        "compatibilidad",
        "/api/v1/laboratory/samples/" + aged_sample["id"] + "/completeness",
        method="GET",
        fmt=fmt,
    )
    assert "STALE:ABO" in check_age["missing"] and not check_age["complete"]
    from datetime import timedelta

    from ms_compatibilidad.laboratory import completeness as calculate_completeness

    with p.apps["compatibilidad"].test_request_context(), transaction() as conn:
        boundary = utc_date(aged["measured_at"]) + timedelta(seconds=60)
        exact = calculate_completeness(
            conn,
            unit["id"],
            aged_profile["id"],
            p.env.state["tenants"][0],
            now=boundary,
        )
        after = calculate_completeness(
            conn,
            unit["id"],
            aged_profile["id"],
            p.env.state["tenants"][0],
            now=boundary + timedelta(microseconds=1),
        )
        assert exact["complete"] and "STALE:ABO" in after["missing"]


@pytest.mark.parametrize("component", ["RBC", "PLASMA", "PLATELETS"])
@pytest.mark.parametrize("fmt", ["json", "xml"])
def test_profile_execution_manual_products_and_all_candidate_branches(
    p, component, fmt
):
    from .helpers import recipient_request, route
    from .test_correction_backend import laboratory

    # Source owner profile + destination immutable requirement profile, no copied RBC matrix.
    unit = api(
        p,
        "inventario",
        "/api/v1/resources",
        {
            "folio": "PROD-" + uuid4().hex[:10],
            "kind": "BLOOD",
            "component": component,
            "blood_group": "O-",
            "expires_at": iso(days=2),
        },
        user="operator1",
    )
    if component == "RBC":
        prof, _, _ = laboratory(p, unit, "json")
    else:
        prof = profile(p, kind="BLOOD", component=component, required_tests=["ABO"])
        api(
            p,
            "inventario",
            "/api/v1/resources/" + unit["id"] + "/controls",
            dict(CONFIRM, version=1, lab_profile_id=prof["id"]),
        )
        sample = api(
            p,
            "compatibilidad",
            "/api/v1/laboratory/samples",
            {
                "resource_id": unit["id"],
                "profile_id": prof["id"],
                "identifier": "MANUAL-" + uuid4().hex,
                "collected_at": iso(minutes=-5),
            },
        )
        api(
            p,
            "compatibilidad",
            "/api/v1/laboratory/samples/" + sample["id"] + "/receive",
            dict(CONFIRM, version=1, decision="RECEIVED"),
        )
        result = api(
            p,
            "compatibilidad",
            "/api/v1/laboratory/results",
            {
                "sample_id": sample["id"],
                "test_code": "ABO",
                "value": "Dato informado",
                "method": "Ficticio",
                "laboratory": "Ficticio",
                "reference": "Sintético",
                "measured_at": iso(),
            },
        )
        api(
            p,
            "compatibilidad",
            "/api/v1/laboratory/results/" + result["id"] + "/review",
            dict(CONFIRM, version=1, decision="AUTHORIZED"),
        )
    unit = api(
        p,
        "inventario",
        "/api/v1/resources/" + unit["id"] + "/release",
        dict(CONFIRM, version=2),
    )
    route(p)
    _, req = recipient_request(p, component=component)
    required = api(
        p,
        "compatibilidad",
        "/api/v1/laboratory/profiles",
        {
            "name": "Requisitos de revisión",
            "kind": "BLOOD",
            "component": component,
            "version": 1,
            "required_tests": ["ABO"],
            "source": "Política sintética",
            "synthetic": True,
            "effective_at": iso(minutes=-60),
            "policy": {
                "version": "COMPLETENESS-2.0",
                "ranking_order": "URGENCY_WAIT_EXPIRY_TIME_DISTANCE_ID",
                "urgency_scale": "CAPTURED_1_3_SYNTHETIC",
            },
        },
        user="medical2",
    )
    ev = api(
        p,
        "compatibilidad",
        "/api/v1/evaluations",
        {"request_id": req["id"], "profile_id": required["id"]},
        user="medical2",
    )
    assert ev["snapshot"]["manual_review"] == (component != "RBC")
    assert any(c["resource_id"] == unit["id"] for c in ev["candidates"])
    api(
        p,
        "compatibilidad",
        "/api/v1/evaluations/" + ev["id"] + "/reviews",
        dict(CONFIRM, resource_id=unit["id"], decision="FAVORABLE"),
        user="medical2",
    )
    for branch in ("ALG-01", "ALG-02", "ALG-03"):
        run = api(
            p,
            "priorizacion_geografia",
            "/api/v1/decision-runs",
            {
                "branch": branch,
                "evaluation_ids": [ev["id"]],
                "component": component,
                "policy_id": required["id"],
            },
            user="medical2",
            fmt=fmt,
        )
        assert api(
            p,
            "priorizacion_geografia",
            "/api/v1/decision-runs/" + run["id"] + "/reproduce",
            method="GET",
            user="medical2",
            fmt=fmt,
        )["identical"]
    with p.owner("inventario") as conn:
        assert (
            conn.execute(
                "SELECT count(*) FROM reservations WHERE resource_id=%s", (unit["id"],)
            ).fetchone()[0]
            == 0
        )
    replay = "/api/v1/evaluations/" + ev["id"] + "/reproduce"
    original = api(p, "compatibilidad", replay, method="GET", user="medical2")
    assert original["identical"]
    successor = api(
        p,
        "compatibilidad",
        "/api/v1/laboratory/profiles",
        {
            "name": "Changed requirements",
            "kind": "BLOOD",
            "component": component,
            "version": 2,
            "required_tests": ["ABO", "IMMUNO"],
            "source": "Synthetic successor",
            "synthetic": True,
            "effective_at": iso(),
            "supersedes": required["id"],
        },
        user="medical2",
    )
    assert api(p, "compatibilidad", replay, method="GET", user="medical2") == original
    assert not api(
        p,
        "compatibilidad",
        "/api/v1/evaluations/" + ev["id"],
        method="GET",
        user="medical2",
    )["validity"]["current"]
    changed = api(
        p,
        "compatibilidad",
        "/api/v1/evaluations",
        {"request_id": req["id"], "profile_id": successor["id"]},
        user="medical2",
    )
    trace = next(
        x for x in changed["snapshot"]["considered"] if x["resource_id"] == unit["id"]
    )
    assert (
        trace["outcome"] == "EXCLUDED" and "PROFILE_MISSING:IMMUNO" in trace["reasons"]
    )


def test_geo_consumes_positions_persisted_by_real_wss_without_measured_eta(
    p, request, monkeypatch
):
    from .test_final_tracking import connect, point, receive, send

    t = request.getfixturevalue("tracking")
    graph = api(p, "priorizacion_geografia", "/api/v1/regional-graphs", graph_body())
    body = {
        "branch": "ALG-02-GEO",
        "graph_id": graph["id"],
        "origin": "Monterrey",
        "destination": "Linares",
        "shipment_id": t["shipment"]["id"],
    }
    pub = connect(t, t["credential"]["credential"], "device")
    receive(pub, "authenticated")
    try:
        before = api(p, "priorizacion_geografia", "/api/v1/decision-runs", body)
        assert before["result"]["tracking"]["state"] == "NO_DATA"
        position = point(t, 1, captured_at=iso(minutes=-2))
        send(pub, {"type": "position.publish", "position": position})
        receive(pub, "position.ack")
        run = api(p, "priorizacion_geografia", "/api/v1/decision-runs", body)
        assert run["result"]["tracking"]["state"] == "STALE"
        assert run["result"]["tracking"]["position"]["event_id"] == position["event_id"]
        assert (
            run["result"]["tracking"]["events"][0]["event_id"] == position["event_id"]
        )
        assert (
            run["result"]["eta_basis"]
            == "SIMULATED_DEPARTURE_AT_AS_OF_FROM_GRAPH_ORIGIN"
        )
        fresh = point(t, 2)
        send(pub, {"type": "position.publish", "position": fresh})
        receive(pub, "position.ack")
        run = api(p, "priorizacion_geografia", "/api/v1/decision-runs", body)
        assert run["result"]["tracking"]["state"] == "LIVE"
        missing = point(
            t, 3, fix_valid=False, latitude=None, longitude=None, accuracy_m=None
        )
        send(pub, {"type": "position.publish", "position": missing})
        receive(pub, "position.ack")
        run = api(p, "priorizacion_geografia", "/api/v1/decision-runs", body)
        assert run["result"]["tracking"]["state"] == "NO_FIX"
        assert run["result"]["path"] == ["Monterrey", "Linares"]
    finally:
        pub.close()


@pytest.mark.parametrize("fmt", ["json", "xml"])
def test_result_private_document_binding_generation_analysis_and_scope(
    p, fmt, monkeypatch
):
    import hashlib
    from io import BytesIO

    from PIL import Image

    from .final_receivers import clamd_receiver
    from .test_correction_backend import laboratory
    from .test_final_delivery_documents import TestBucket

    storage = TestBucket()
    app = p.apps["documentos"]
    monkeypatch.setitem(app.config, "GCS_BUCKET", "private-test")
    monkeypatch.setitem(app.extensions, "gcs_client", storage)
    unit = api(
        p,
        "inventario",
        "/api/v1/resources",
        {
            "folio": "DOC-" + uuid4().hex[:10],
            "kind": "BLOOD",
            "component": "RBC",
            "blood_group": "O-",
            "expires_at": iso(days=1),
        },
        user="operator1",
    )
    _prof, body, result = laboratory(p, unit, fmt)
    content = BytesIO()
    Image.new("RGB", (4, 4), color="blue").save(content, format="PNG")
    payload = content.getvalue()
    doc = api(
        p,
        "documentos",
        "/api/v1/documents",
        {
            "subject_kind": "RESULT",
            "subject_id": result["id"],
            "category": "LAB_RESULT",
            "mime_type": "image/png",
            "size": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "policy_reference": "Política sintética de privacidad",
        },
        fmt=fmt,
    )
    correction = dict(
        body,
        document_id=doc["id"],
        issued_at=iso(),
        supersedes=result["id"],
        result_state="CORRECTED",
    )
    assert (
        p.request(
            "compatibilidad",
            "POST",
            "/api/v1/laboratory/results",
            user="medical1",
            data=correction,
        ).status_code
        == 409
    )
    assert (
        p.request(
            "documentos",
            "GET",
            "/api/v1/files/" + doc["id"] + "/download",
            user="medical1",
        ).status_code
        == 409
    )
    with p.owner("documentos") as conn:
        path = conn.execute(
            "SELECT object_path FROM files WHERE id=%s", (doc["id"],)
        ).fetchone()[0]
    storage.objects[path] = (payload, "image/png")
    with clamd_receiver() as (port, _scanned):
        monkeypatch.setitem(app.config, "CLAMD_HOST", "127.0.0.1")
        monkeypatch.setitem(app.config, "CLAMD_PORT", port)
        api(p, "documentos", "/api/v1/files/" + doc["id"] + "/verify", fmt=fmt)
    verified = api(
        p, "compatibilidad", "/api/v1/laboratory/results", correction, fmt=fmt
    )
    assert (
        verified["document_snapshot"]["sha256"] == hashlib.sha256(payload).hexdigest()
    )
    assert verified["document_snapshot"]["analysis"] == "CLEAN"
    api(
        p,
        "documentos",
        "/api/v1/files/" + doc["id"] + "/download",
        method="GET",
        fmt=fmt,
    )
    assert (
        p.request(
            "documentos",
            "GET",
            "/api/v1/files/" + doc["id"] + "/download",
            user="medical2",
        ).status_code
        == 403
    )
    other_sample = api(
        p,
        "compatibilidad",
        "/api/v1/laboratory/samples",
        {
            "resource_id": unit["id"],
            "profile_id": _prof["id"],
            "identifier": "OTHER-DOC-" + uuid4().hex,
            "collected_at": iso(minutes=-5),
        },
        fmt=fmt,
    )
    api(
        p,
        "compatibilidad",
        "/api/v1/laboratory/samples/" + other_sample["id"] + "/receive",
        dict(CONFIRM, version=1, decision="RECEIVED"),
        fmt=fmt,
    )
    wrong_sample = dict(
        body, sample_id=other_sample["id"], document_id=doc["id"], issued_at=iso()
    )
    assert (
        p.request(
            "compatibilidad",
            "POST",
            "/api/v1/laboratory/results",
            user="medical1",
            data=wrong_sample,
        ).status_code
        == 409
    )
    bad_doc = api(
        p,
        "documentos",
        "/api/v1/documents",
        {
            "subject_kind": "RESULT",
            "subject_id": result["id"],
            "category": "LAB_RESULT",
            "mime_type": "image/png",
            "size": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "policy_reference": "Ficticio",
            "supersedes": doc["id"],
        },
        fmt=fmt,
    )
    with p.owner("documentos") as conn:
        path = conn.execute(
            "SELECT object_path FROM files WHERE id=%s", (bad_doc["id"],)
        ).fetchone()[0]
    storage.objects[path] = (b"not the declared bytes", "image/png")
    assert (
        p.request(
            "documentos",
            "POST",
            "/api/v1/files/" + bad_doc["id"] + "/verify",
            user="medical1",
        ).status_code
        == 422
    )
    assert (
        p.request(
            "documentos",
            "GET",
            "/api/v1/documents/" + bad_doc["id"] + "/verified",
            user="medical1",
        ).status_code
        == 409
    )
    assert (
        p.request(
            "compatibilidad",
            "POST",
            "/api/v1/laboratory/results",
            user="medical1",
            data=dict(correction, supersedes=verified["id"], document_id=bad_doc["id"]),
        ).status_code
        == 409
    )
    with p.owner("compatibilidad") as conn:
        assert (
            conn.execute(
                "SELECT count(*) FROM lab_results WHERE sample_id=%s",
                (body["sample_id"],),
            ).fetchone()[0]
            == 2
        )
    # The SDK double proves binding and authorization, not a successful cloud download.


def test_rule_approval_mechanism_scoped_fixture_and_revocation(p, monkeypatch):
    """Fictitious authority in isolated configuration tests mechanics, never real approval."""
    import hashlib
    from io import BytesIO

    from PIL import Image

    from .final_receivers import clamd_receiver
    from .test_final_delivery_documents import TestBucket

    authority_name = "approver_" + uuid4().hex[:10]
    actor = api(
        p,
        "identidad_acceso",
        "/api/v1/users",
        {
            "username": authority_name,
            "password": p.env.state["password"],
            "tenant_id": p.env.state["tenants"][0],
            "role": "MEDICAL",
        },
        user="admin1",
    )
    login = api(
        p,
        "identidad_acceso",
        "/api/v1/auth/login",
        {"username": authority_name, "password": p.env.state["password"]},
        user=None,
    )
    p.tokens[authority_name] = login["access_token"]
    prof = profile(
        p,
        synthetic=False,
        valid_until=iso(days=1),
        policy={"version": "COMPLETENESS-2.0", "require_document": True},
    )
    base = "/api/v1/laboratory/profiles/" + prof["id"]
    api(
        p,
        "compatibilidad",
        base + "/actions",
        dict(CONFIRM, sequence=1, state="IN_REVIEW"),
    )
    storage = TestBucket()
    app = p.apps["documentos"]
    monkeypatch.setitem(app.config, "GCS_BUCKET", "private-test")
    monkeypatch.setitem(app.extensions, "gcs_client", storage)
    buf = BytesIO()
    Image.new("RGB", (4, 4)).save(buf, format="PNG")
    payload = buf.getvalue()
    doc = api(
        p,
        "documentos",
        "/api/v1/documents",
        {
            "subject_kind": "RULE",
            "subject_id": prof["id"],
            "category": "RULE_APPROVAL",
            "mime_type": "image/png",
            "size": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "policy_reference": "Evidencia ficticia de mecanismo; no aprobación profesional",
        },
    )
    with p.owner("documentos") as conn:
        object_path = conn.execute(
            "SELECT object_path FROM files WHERE id=%s", (doc["id"],)
        ).fetchone()[0]
    storage.objects[object_path] = (payload, "image/png")
    with clamd_receiver() as (port, _):
        monkeypatch.setitem(app.config, "CLAMD_HOST", "127.0.0.1")
        monkeypatch.setitem(app.config, "CLAMD_PORT", port)
        api(p, "documentos", "/api/v1/files/" + doc["id"] + "/verify")
    authority = {
        "tenant_id": p.env.state["tenants"][0],
        "reference": "FIXTURE-NOT-PROFESSIONAL",
        "components": ["KIDNEY"],
        "valid_until": iso(days=1),
    }
    cfg = p.apps["compatibilidad"].config
    monkeypatch.setitem(
        cfg,
        "CLINICAL_APPROVERS",
        {actor["id"]: authority, p.env.state["accounts"]["medical1"]["id"]: authority},
    )
    decision = dict(
        CONFIRM,
        sequence=2,
        state="APPROVED",
        competency_reference=authority["reference"],
        document_id=doc["id"],
    )
    assert (
        p.request(
            "compatibilidad", "POST", base + "/actions", user="medical1", data=decision
        ).status_code
        == 409
    )
    api(p, "compatibilidad", base + "/actions", decision, user=authority_name)
    assert api(p, "compatibilidad", base + "/governance", method="GET")[
        "clinical_enabled"
    ]
    monkeypatch.setitem(cfg, "CLINICAL_APPROVERS", {})
    assert not api(p, "compatibilidad", base + "/governance", method="GET")[
        "clinical_enabled"
    ]
    api(
        p,
        "compatibilidad",
        base + "/actions",
        dict(CONFIRM, sequence=3, state="RETIRED"),
    )
    gov = api(p, "compatibilidad", base + "/governance", method="GET")
    assert len(gov["actions"]) == 3 and gov["state"] == "RETIRED"


def test_crossmatch_associations_and_unperformed_not_negative(p):
    rec = recipient(p, "KIDNEY")
    req = api(
        p,
        "receptores",
        "/api/v1/requests",
        {"recipient_id": rec["id"], "component": "KIDNEY", "quantity": 1, "urgency": 2},
    )
    prof = profile(p, required_tests=["CROSSMATCH"])
    organ = api(
        p,
        "inventario",
        "/api/v1/resources",
        {
            "folio": "CROSS-" + uuid4().hex[:10],
            "kind": "ORGAN",
            "component": "KIDNEY",
            "blood_group": "O+",
            "expires_at": iso(days=1),
        },
        user="operator1",
    )
    samples = []
    for subject in ({"resource_id": organ["id"]}, {"recipient_id": rec["id"]}):
        sample = api(
            p,
            "compatibilidad",
            "/api/v1/laboratory/samples",
            dict(
                subject,
                profile_id=prof["id"],
                request_id=req["id"],
                identifier="CROSS-" + uuid4().hex,
                collected_at=iso(minutes=-5),
            ),
        )
        api(
            p,
            "compatibilidad",
            "/api/v1/laboratory/samples/" + sample["id"] + "/receive",
            dict(CONFIRM, version=1, decision="RECEIVED"),
        )
        samples.append(sample)
    body = {
        "sample_id": samples[0]["id"],
        "test_code": "CROSSMATCH",
        "result_state": "PENDING",
        "method": "Método registrado",
        "laboratory": "Laboratorio ficticio",
        "reference": "Solicitud sintética",
        "measured_at": iso(),
        "crossmatch": {
            "donor_sample_id": samples[0]["id"],
            "recipient_sample_id": samples[1]["id"],
            "request_id": req["id"],
            "technique": "Técnica declarada",
            "reported_interpretation": "PENDING",
        },
    }
    invalid = dict(
        body, crossmatch=dict(body["crossmatch"], recipient_sample_id=samples[0]["id"])
    )
    assert (
        p.request(
            "compatibilidad",
            "POST",
            "/api/v1/laboratory/results",
            user="medical1",
            data=invalid,
        ).status_code
        == 409
    )
    row = api(p, "compatibilidad", "/api/v1/laboratory/results", body)
    assert row["value"] is None and row["result_state"] == "PENDING"
    assert row["crossmatch"]["reported_interpretation"] == "PENDING"


_HTTP_SAMPLES = []


@pytest.fixture(autouse=True)
def record_http_distribution(request, monkeypatch):
    import json
    import os
    import re
    import time
    from pathlib import Path

    directory = os.environ.get("REDHOUSE_STAGE02_EVIDENCE")
    if not directory or "p" not in request.fixturenames:
        yield
        return
    platform = request.getfixturevalue("p")
    original = platform.request

    def measured(service, method, path, **kwargs):
        started = time.perf_counter()
        response = original(service, method, path, **kwargs)
        _HTTP_SAMPLES.append(
            {
                "service": service,
                "method": method,
                "path": re.sub(
                    r"[a-f0-9]{8}-[a-f0-9-]{27,}", ":id", path.split("?")[0]
                ),
                "status": response.status_code,
                "elapsed_ms": (time.perf_counter() - started) * 1000,
            }
        )
        return response

    monkeypatch.setattr(platform, "request", measured)
    yield
    groups = {}
    for sample in _HTTP_SAMPLES:
        key = sample["service"] + " " + sample["method"] + " " + sample["path"]
        groups.setdefault(key, []).append(sample["elapsed_ms"])
    import math
    import statistics

    summary = {
        key: {
            "n": len(values),
            "mean_ms": statistics.mean(values),
            "median_ms": statistics.median(values),
            "p95_ms": sorted(values)[math.ceil(0.95 * len(values)) - 1],
            "p99_ms": sorted(values)[math.ceil(0.99 * len(values)) - 1],
        }
        for key, values in groups.items()
    }
    Path(directory, "http-latencies.json").write_text(
        json.dumps(
            {
                "samples": _HTTP_SAMPLES,
                "summary": summary,
                "limitation": "Peticiones de integración secuenciales JSON; errores esperados incluidos; no estrés sostenido ni percentiles productivos.",
            },
            indent=2,
        )
    )
