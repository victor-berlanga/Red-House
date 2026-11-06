"""Public data are real references; all subjects and transactions are fictitious."""

import json
from datetime import datetime
from uuid import uuid4

import pytest
from flask import Flask

from .helpers import iso
from .test_final_quality import api
from .test_stage02_corrections import CONFIRM, profile, recipient


def typing(allele="A*01:01:01:01", version="3.66.0"):
    return {
        "nomenclature": "HLA-colon-2010",
        "nomenclature_version": "2010:syntax-2",
        "catalogue_version": version,
        "resolution": "Declarada en prueba",
        "loci": [{"locus": "A", "alleles": [allele], "groups": []}],
    }


@pytest.mark.parametrize(
    "allele,expected,count",
    [
        ("A*01:01:01:01", "EXACT", 1),
        ("A*01:01", "LOW_RESOLUTION", 303),
        ("A*99:99999", "NOT_FOUND", 0),
    ],
)
def test_pinned_public_hla_membership_and_resolution(allele, expected, count):
    from ms_compatibilidad.reference_catalogue import check

    app = Flask(__name__)
    with app.app_context():
        result = check(typing(allele))
    assert result["entries"][0]["status"] == expected
    assert result["entries"][0]["matching_entries"] == count
    assert result["catalogue"]["version"] == "3.66.0"
    assert not result["clinical_approval"]


def test_catalogue_unavailable_tampered_unknown_and_partial(tmp_path):
    from ms_compatibilidad.reference_catalogue import check
    from redhouse.errors import APIError

    app = Flask(__name__)
    app.config["HLA_REFERENCE_DIR"] = str(tmp_path)
    with app.app_context():
        assert check(typing(version=None))["status"] == "NOT_CHECKED"
        with pytest.raises(APIError) as e:
            check(typing(version="unknown"))
        assert e.value.status == 422
        for contents in (None, b"modified catalogue"):
            if contents:
                target = tmp_path / "3.66.0/Allelelist.txt"
                target.parent.mkdir()
                target.write_bytes(contents)
            with pytest.raises(APIError) as e:
                check(typing())
            assert e.value.status == 503
    app.config.pop("HLA_REFERENCE_DIR")
    value = typing()
    value["loci"][0].update(alleles=[], groups=["A*01"], partial=True)
    with app.app_context():
        result = check(value)
    assert result["entries"][0]["status"] == "GROUP_NOT_ALLELE"
    assert not result["all_alleles_recognized"]


@pytest.mark.parametrize(
    "moment,old,new",
    [
        ("2027-04-10T05:59:59+00:00", [], ["REFERENCE_FUTURE"]),
        ("2027-04-10T06:00:00+00:00", ["REFERENCE_EXPIRED"], []),
    ],
)
def test_normative_transition_exact_mexican_date(moment, old, new):
    from ms_compatibilidad.public_sources import reference_reasons, resolve

    refs = resolve(["MX-NOM253-2012-9.5.1", "MX-NOM253-2025-TRANSICION"], "BLOOD")
    assert [
        r.split(":")[0]
        for r in reference_reasons(refs[:1], datetime.fromisoformat(moment))
    ] == old
    assert [
        r.split(":")[0]
        for r in reference_reasons(refs[1:], datetime.fromisoformat(moment))
    ] == new


@pytest.mark.parametrize("fmt", ["json", "xml"])
def test_cited_profile_scope_future_and_no_clinical_activation(p, fmt):
    sources = api(
        p,
        "compatibilidad",
        "/api/v1/laboratory/reference-sources",
        method="GET",
        fmt=fmt,
    )
    assert len(sources["rules"]) == 5 and not sources["clinical_approval"]
    assert sources["catalogues"][0]["available"]
    for reference in ("unknown", "MX-NOM253-2012-9.5.1"):
        response = p.request(
            "compatibilidad",
            "POST",
            "/api/v1/laboratory/profiles",
            user="medical1",
            data={
                "name": "Invalid cited profile",
                "kind": "ORGAN",
                "component": "KIDNEY",
                "version": 1,
                "required_tests": ["HLA"],
                "source": "Prueba",
                "synthetic": True,
                "effective_at": iso(minutes=-60),
                "evidence_rules": [reference],
            },
        )
        assert response.status_code == 422, response.text
    prof = profile(p, evidence_rules=["MX-TRASPLANTES-2014-33"])
    assert prof["reference_snapshot"][0]["section"].startswith("1;")
    saved = api(
        p,
        "compatibilidad",
        "/api/v1/laboratory/profiles/" + prof["id"],
        method="GET",
        fmt=fmt,
    )
    assert saved["reference_snapshot"] == prof["reference_snapshot"]
    gov = api(
        p,
        "compatibilidad",
        "/api/v1/laboratory/profiles/" + prof["id"] + "/governance",
        method="GET",
        fmt=fmt,
    )
    assert not gov["clinical_enabled"] and gov["state"] == "DRAFT"
    future = profile(
        p,
        kind="BLOOD",
        component="RBC",
        required_tests=["ABO"],
        evidence_rules=["MX-NOM253-2025-TRANSICION"],
    )
    future_gov = api(
        p,
        "compatibilidad",
        "/api/v1/laboratory/profiles/" + future["id"] + "/governance",
        method="GET",
        fmt=fmt,
    )
    assert "REFERENCE_FUTURE:MX-NOM253-2025-TRANSICION" in future_gov["invalid_reasons"]
    assert (
        p.request(
            "compatibilidad",
            "GET",
            "/api/v1/laboratory/profiles/" + prof["id"],
            user="medical2",
        ).status_code
        == 403
    )


@pytest.mark.parametrize("fmt", ["json", "xml"])
@pytest.mark.parametrize("test_code", ["HLA", "CUSTOM_HLA"])
def test_hla_catalogue_persisted_correction_completeness_without_verdict(
    p, fmt, test_code
):
    prof = profile(
        p,
        evidence_rules=["HLA-NAMING-2010-SYNTAX2"],
        required_tests=[test_code],
        required_loci=["A"],
        policy={"require_hla_catalogue": True},
    )
    rec = recipient(p, "KIDNEY")
    sample = api(
        p,
        "compatibilidad",
        "/api/v1/laboratory/samples",
        {
            "recipient_id": rec["id"],
            "profile_id": prof["id"],
            "identifier": "REF-" + uuid4().hex,
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
        "test_code": test_code,
        "result_state": "REPORTED",
        "method": "Declaración ficticia",
        "laboratory": "Laboratorio de prueba",
        "reference": "Catálogo público, sujeto ficticio",
        "measured_at": iso(minutes=-2),
        "issued_at": iso(minutes=-1),
        "hla": typing(version="unknown"),
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
    body["hla"] = typing("A*99:99999")
    first = api(p, "compatibilidad", "/api/v1/laboratory/results", body, fmt=fmt)
    assert first["catalogue_check"]["entries"][0]["status"] == "NOT_FOUND"
    api(
        p,
        "compatibilidad",
        "/api/v1/laboratory/results/" + first["id"] + "/review",
        dict(CONFIRM, version=1, decision="AUTHORIZED"),
        fmt=fmt,
    )
    missing = api(
        p,
        "compatibilidad",
        "/api/v1/laboratory/samples/" + sample["id"] + "/completeness",
        method="GET",
        fmt=fmt,
    )
    assert "HLA:CATALOGUE_UNVERIFIED" in missing["missing"]
    body.update(hla=typing(), supersedes=first["id"], result_state="CORRECTED")
    corrected = api(p, "compatibilidad", "/api/v1/laboratory/results", body, fmt=fmt)
    api(
        p,
        "compatibilidad",
        "/api/v1/laboratory/results/" + corrected["id"] + "/review",
        dict(CONFIRM, version=2, decision="AUTHORIZED"),
        fmt=fmt,
    )
    complete = api(
        p,
        "compatibilidad",
        "/api/v1/laboratory/samples/" + sample["id"] + "/completeness",
        method="GET",
        fmt=fmt,
    )
    assert (
        complete["complete"]
        and not complete["clinical_approval"]
        and not complete["clinical_enabled"]
    )
    assert (
        api(
            p,
            "compatibilidad",
            "/api/v1/laboratory/results/" + first["id"],
            method="GET",
            fmt=fmt,
        )["catalogue_check"]
        == first["catalogue_check"]
    )
    with p.owner("compatibilidad") as conn:
        assert (
            conn.execute(
                "SELECT count(*) FROM lab_results WHERE sample_id=%s", (sample["id"],)
            ).fetchone()[0]
            == 2
        )


@pytest.mark.parametrize("fmt", ["json", "xml"])
def test_real_road_source_import_route_replay_and_no_gps(p, fmt):
    import hashlib

    from ms_priorizacion_geografia.road_sources import ROOT, manifest

    spec = manifest()
    api(
        p,
        "priorizacion_geografia",
        "/api/v1/regional-graph-sources",
        method="GET",
        fmt=fmt,
    )
    graph = api(
        p,
        "priorizacion_geografia",
        "/api/v1/regional-graphs/from-reference",
        {"reference_id": spec["id"]},
        fmt=fmt,
    )
    assert not graph["synthetic"] and graph["provenance"]["license"] == "ODbL-1.0"
    # Independent provider response oracle, not the graph conversion helper.
    raw = (ROOT / "monterrey-guadalupe.json").read_bytes()
    route = json.loads(raw)["routes"][0]
    run = api(
        p,
        "priorizacion_geografia",
        "/api/v1/decision-runs",
        {
            "branch": "ALG-02-GEO",
            "graph_id": graph["id"],
            "origin": "MONTERREY",
            "destination": "GUADALUPE",
        },
        fmt=fmt,
    )
    assert run["algorithm_version"] == "REGIONAL-OSM-DIJKSTRA-3.0"
    out = run["result"]
    assert out["path"] == ["MONTERREY", "GUADALUPE"]
    assert next(
        m["value"] for m in out["metrics"] if m["name"] == "planned_minutes"
    ) == pytest.approx(route["duration"] / 60)
    ref = out["road_reference"]
    assert ref["segments"][0]["sha256"] == hashlib.sha256(raw).hexdigest()
    assert ref["segments"][0]["geometry"] == route["geometry"]
    assert (
        ref["map_age_seconds"] is None
        and not ref["traffic_measured"]
        and not ref["observed_gps_used"]
    )
    assert out["tracking"]["state"] == "NOT_REQUESTED"
    replay = api(
        p,
        "priorizacion_geografia",
        "/api/v1/decision-runs/" + run["id"] + "/reproduce",
        method="GET",
        fmt=fmt,
    )
    assert replay["identical"]
    assert (
        p.request(
            "priorizacion_geografia",
            "GET",
            "/api/v1/decision-runs/" + run["id"],
            user="medical2",
        ).status_code
        == 403
    )
    assert (
        p.request(
            "priorizacion_geografia",
            "POST",
            "/api/v1/regional-graphs/from-reference",
            data={"reference_id": spec["id"]},
            user="operator1",
        ).status_code
        == 403
    )
    # Client cannot label an arbitrary graph as a real provider source.
    forged = {
        k: v
        for k, v in graph.items()
        if k not in ("id", "tenant_id", "author_id", "created_at", "provenance")
    }
    assert (
        p.request(
            "priorizacion_geografia",
            "POST",
            "/api/v1/regional-graphs",
            data=forged,
            user="medical1",
        ).status_code
        == 422
    )


def test_road_integrity_and_unknown_source_fail_closed(tmp_path, monkeypatch):
    from ms_priorizacion_geografia import road_sources
    from redhouse.errors import APIError

    spec = road_sources.manifest()
    with pytest.raises(APIError) as exc:
        road_sources.build("unknown")
    assert exc.value.status == 422
    (tmp_path / "manifest.json").write_text(json.dumps(spec))
    monkeypatch.setattr(road_sources, "ROOT", tmp_path)
    with pytest.raises(APIError) as exc:
        road_sources.build(spec["id"])
    assert exc.value.status == 503
    status = road_sources.source_status()
    assert (
        status["in_validity_window"]
        and not status["integrity_verified"]
        and not status["available"]
    )
