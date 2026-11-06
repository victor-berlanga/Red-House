"""Synthetic algorithms, independent oracle, persistent JSON/XML and ACL."""

import random
from itertools import pairwise, permutations
from uuid import uuid4

import psycopg
import pytest
from ms_compatibilidad.hla import Typing
from ms_priorizacion_geografia.academic import execute
from pydantic import ValidationError

from .helpers import iso
from .test_final_quality import api


def experiment(version="ROUTE-DIJKSTRA-1.0", **kwargs):
    return dict(
        algorithm_version=version,
        synthetic=True,
        source="Grafo sintético de prueba",
        as_of="2026-10-31T12:00:00Z",
        component="RBC",
        profile_version="SYNTHETIC-1",
        origin="A",
        destination="D",
        graph_observed_at="2026-10-31T10:00:00Z",
        **kwargs,
    )


def test_dijkstra_against_independent_simple_path_oracle():
    rng = random.Random(31)
    nodes = "ABCD"
    for _ in range(80):
        edges = [
            {
                "origin": a,
                "destination": b,
                "minutes": rng.randint(0, 9),
                "distance_km": rng.randint(1, 9),
            }
            for a in nodes
            for b in nodes
            if a != b and rng.random() < 0.5
        ]
        weights = {
            (e["origin"], e["destination"]): (e["minutes"], e["distance_km"])
            for e in edges
        }
        costs = []
        for size in range(3):
            for middle in permutations("BC", size):
                path = ["A", *middle, "D"]
                if all((a, b) in weights for a, b in pairwise(path)):
                    costs.append(
                        tuple(
                            sum(weights[a, b][i] for a, b in pairwise(path))
                            for i in (0, 1)
                        )
                    )
        result = execute(experiment(edges=edges))
        values = {m["name"]: m["value"] for m in result["metrics"]}
        if costs:
            assert (values["planned_minutes"], values["planned_distance_km"]) == min(
                costs
            )
        else:
            assert result["path"] == []


def test_forecast_no_future_leakage_and_reproduction():
    data = experiment("DEMAND-SES-1.0", history=[2, 3, 2, 4, 2, 3, 4, 1, 8], stock=20)
    result = execute(data)
    changed = execute(dict(data, history=[2, 3, 2, 4, 2, 3, 999, 999, 999]))
    metric = lambda r: {m["name"]: m["value"] for m in r["metrics"]}
    assert metric(result)["alpha"] == metric(changed)["alpha"]
    assert execute(data) == result
    assert result["clinical_approval"] is False


def test_missing_hla_ambiguity_and_states():
    base = {
        "nomenclature": "HLA-colon-2010",
        "nomenclature_version": "2010",
        "resolution": "Dos campos",
        "loci": [{"locus": "A", "alleles": ["A*01:01", "A*02:01"], "ambiguous": True}],
    }
    assert Typing(**base).loci[0].ambiguous
    with pytest.raises(ValidationError):
        Typing(**dict(base, loci=[{"locus": "A", "alleles": ["B*01:01"]}]))
    result = execute(
        experiment(
            "EXPLAIN-ACADEMIC-1.0",
            required_tests=["ABO", "HLA"],
            candidates=[
                {
                    "identifier": "u1",
                    "component": "RBC",
                    "available": True,
                    "expired": False,
                    "thermal_incident": False,
                    "tests": ["ABO"],
                }
            ],
        )
    )
    assert result["findings"][0]["reasons"] == ["MISSING:HLA"]
    assert result["professional_verdict"] == "NOT_ISSUED"


def test_urgency_simulation_missing_factors_and_anomalies():
    candidate = {
        "component": "RBC",
        "available": True,
        "expired": False,
        "thermal_incident": False,
        "urgency": 1,
        "urgency_source": "Escala ficticia",
        "waiting_minutes": 10,
        "expiry_minutes": 100,
        "travel_minutes": 20,
        "distance_km": 5,
    }
    result = execute(
        experiment(
            "LOGISTICS-SIM-2.0",
            candidates=[
                dict(candidate, identifier="a"),
                dict(candidate, identifier="b", urgency=2),
            ],
        )
    )
    assert result["findings"][0]["identifier"] == "b"
    record = {
        "identifier": "r",
        "resource_id": "u",
        "reserved": True,
        "quantity": 2,
        "available_quantity": 1,
        "sequence": 2,
        "sample_subject": "a",
        "subject": "b",
        "thermal_incoherent": True,
        "projection_version": 1,
        "source_version": 2,
    }
    out = execute(experiment("CONSISTENCY-1.0", records=[record, record]))
    assert {
        "MULTIPLE_RESERVATIONS",
        "FOREIGN_SAMPLE",
        "BROKEN_SEQUENCE",
        "STALE_PROJECTION",
        "DUPLICATE_IDENTIFIER",
    } <= set(out["findings"][1]["reasons"])


@pytest.mark.parametrize("fmt", ["json", "xml"])
def test_persistent_algorithm_contract_and_tenant(p, fmt):
    data = experiment(
        edges=[{"origin": "A", "destination": "D", "minutes": 5, "distance_km": 3}]
    )
    run = api(p, "priorizacion_geografia", "/api/v1/algorithm-runs", data, fmt=fmt)
    restored = api(
        p,
        "priorizacion_geografia",
        "/api/v1/algorithm-runs/" + run["id"],
        fmt=fmt,
        method="GET",
    )
    assert restored["result"] == execute(data)
    assert restored["snapshot"]["synthetic"]
    assert (
        p.request(
            "priorizacion_geografia",
            "GET",
            "/api/v1/algorithm-runs/" + run["id"],
            user="medical2",
        ).status_code
        == 403
    )
    assert (
        p.request(
            "priorizacion_geografia",
            "POST",
            "/api/v1/algorithm-runs",
            user="operator1",
            data=data,
        ).status_code
        == 403
    )
    with (
        p.owner("priorizacion_geografia") as conn,
        pytest.raises(psycopg.errors.CheckViolation),
    ):
        conn.execute(
            "UPDATE algorithm_runs SET source=%s WHERE id=%s", ("changed", run["id"])
        )


@pytest.mark.parametrize("fmt", ["json", "xml"])
def test_hla_structured_history_missing_and_corrected(p, fmt):
    profile = api(
        p,
        "compatibilidad",
        "/api/v1/laboratory/profiles",
        {
            "name": "Perfil HLA sintético",
            "kind": "ORGAN",
            "component": "KIDNEY",
            "version": 1,
            "required_tests": ["HLA"],
            "required_loci": ["A"],
            "source": "Protocolo ficticio",
            "synthetic": True,
            "effective_at": iso(),
        },
        fmt=fmt,
    )
    resource = api(
        p,
        "inventario",
        "/api/v1/resources",
        {
            "folio": "HLA-" + uuid4().hex[:12],
            "kind": "ORGAN",
            "component": "KIDNEY",
            "blood_group": "A+",
            "expires_at": iso(days=2),
        },
        user="operator1",
        fmt=fmt,
    )
    sample = api(
        p,
        "compatibilidad",
        "/api/v1/laboratory/samples",
        {
            "resource_id": resource["id"],
            "profile_id": profile["id"],
            "identifier": uuid4().hex,
            "collected_at": iso(minutes=-10),
        },
        user="operator1",
        fmt=fmt,
    )
    api(
        p,
        "compatibilidad",
        f"/api/v1/laboratory/samples/{sample['id']}/receive",
        {
            "version": 1,
            "decision": "RECEIVED",
            "human_confirmation": True,
            "reason": "Recepción de muestra sintética",
        },
        user="operator1",
        fmt=fmt,
    )
    base = {
        "sample_id": sample["id"],
        "test_code": "HLA",
        "method": "Método declarado ficticio",
        "laboratory": "Laboratorio sintético",
        "reference": "Documento de prueba",
        "measured_at": iso(minutes=-2),
    }
    pending = api(
        p,
        "compatibilidad",
        "/api/v1/laboratory/results",
        dict(base, result_state="PENDING"),
        user="operator1",
        fmt=fmt,
    )
    typing = {
        "nomenclature": "HLA-colon-2010",
        "nomenclature_version": "2010",
        "resolution": "Dos campos",
        "loci": [{"locus": "A", "alleles": ["A*01:01"], "ambiguous": False}],
    }
    corrected = api(
        p,
        "compatibilidad",
        "/api/v1/laboratory/results",
        dict(
            base,
            result_state="CORRECTED",
            supersedes=pending["id"],
            hla=typing,
            issued_at=iso(minutes=-1),
        ),
        user="operator1",
        fmt=fmt,
    )
    assert corrected["version"] == 2 and corrected["hla"] == Typing.model_validate(typing).model_dump()
    prior = api(
        p,
        "compatibilidad",
        "/api/v1/laboratory/results/" + pending["id"],
        fmt=fmt,
        method="GET",
    )
    assert prior["result_state"] == "PENDING" and prior["value"] is None
    check = api(
        p,
        "compatibilidad",
        f"/api/v1/laboratory/resources/{resource['id']}/check",
        {"profile_id": profile["id"], "tenant_id": profile["tenant_id"]},
        fmt=fmt,
    )
    assert not check["complete"] and not check["clinical_approval"]
    review = {
        "version": 2,
        "decision": "AUTHORIZED",
        "human_confirmation": True,
        "reason": "Revisión exclusivamente sintética",
    }
    assert (
        p.request(
            "compatibilidad",
            "POST",
            f"/api/v1/laboratory/results/{corrected['id']}/review",
            user="operator1",
            data=review,
        ).status_code
        == 403
    )
    api(
        p,
        "compatibilidad",
        f"/api/v1/laboratory/results/{corrected['id']}/review",
        review,
        fmt=fmt,
    )
    check = api(
        p,
        "compatibilidad",
        f"/api/v1/laboratory/resources/{resource['id']}/check",
        {"profile_id": profile["id"], "tenant_id": profile["tenant_id"]},
        fmt=fmt,
    )
    assert check["complete"] and not check["clinical_approval"]


def test_limits_empty_graph_and_gps_separation():
    empty = execute(experiment())
    assert not empty["path"] and empty["estimated_arrival_at"] is None
    gps = {
        "latitude": 25.68,
        "longitude": -100.3,
        "captured_at": "2026-10-31T11:00:00Z",
        "received_at": "2026-10-31T11:01:00Z",
        "source": "Simulador",
        "accuracy_m": 30,
        "simulated": True,
    }
    route = execute(
        experiment(
            edges=[{"origin": "A", "destination": "D", "minutes": 5, "distance_km": 3}],
            observation=gps,
            websocket_track=[gps],
        )
    )
    assert route["estimated_arrival_at"] == "2026-10-31T12:05:00+00:00"
    assert {m["name"]: m["value"] for m in route["metrics"]}[
        "observed_gps_age_seconds"
    ] == 3600
    with pytest.raises(ValidationError):
        execute(
            experiment(
                edges=[
                    {"origin": "A", "destination": "D", "minutes": -1, "distance_km": 3}
                ]
            )
        )
    with pytest.raises(ValidationError):
        execute(experiment(observation=dict(gps, captured_at="2026-11-01T12:00:00Z")))
    with pytest.raises(ValidationError):
        execute(
            experiment(
                edges=[
                    {"origin": "A", "destination": "D", "minutes": 1, "distance_km": 3}
                ]
                * 10001
            )
        )


def test_web_simulation_view_and_form(p, monkeypatch):
    from .test_web_integration import login, post
    from .test_web_integration import web as web_fixture

    app = web_fixture.__wrapped__(p, monkeypatch)
    client = login(app, p, "medical1")
    location = post(
        client,
        "/algoritmos/demanda",
        {
            "component": "RBC",
            "source": "Historia ficticia",
            "as_of": "2026-10-30T12:00",
            "history": "2,3,2,4,2,3",
            "window_days": "1",
            "stock": "10",
        },
    )
    response = client.get(location)
    assert response.status_code == 200
    assert b"forecast_next_window" in response.data
    assert b"NOT_ISSUED" in response.data
    assert client.get("/algoritmos").status_code == 200


def test_expiry_estimate_does_not_double_count_demand():
    result = execute(
        experiment(
            "DEMAND-SES-1.0",
            history=[2, 2, 2, 2, 2, 2],
            stock=10,
            lots=[
                {
                    "identifier": "old",
                    "quantity": 5,
                    "expires_at": "2026-10-30T12:00:00Z",
                },
                {
                    "identifier": "new",
                    "quantity": 5,
                    "expires_at": "2026-11-01T12:00:00Z",
                },
            ],
        )
    )
    assert "estimated_unused_at_expiry:5.0" in result["findings"][0]["reasons"]
    assert "estimated_unused_at_expiry:3.0" in result["findings"][1]["reasons"]


def test_migration_13_to_current_preserves_rows_and_is_repeatable(tmp_path, monkeypatch):
    import os
    import tempfile

    from redhouse import extension_schema, shared_migrations
    from scripts.local import Environment

    env = Environment(
        tempfile.mkdtemp(prefix="rh-alg-migration-", dir="/tmp"),
        os.environ.get("REDHOUSE_TEST_MONGOD"),
    )
    try:
        with monkeypatch.context() as m:
            m.setattr(shared_migrations, "LATEST_VERSION", 13)
            m.setattr(
                extension_schema,
                "TABLES",
                {
                    k: {t: mutable for t,mutable in v.items() if t not in ("rule_actions","anomaly_reviews","anomaly_actions")}
                    for k, v in extension_schema.TABLES.items()
                    if k != "priorizacion_geografia"
                },
            )
            env.init()
        with psycopg.connect(env.state["database_admin"], dbname="red_house") as conn:
            tenant = conn.execute(
                "SELECT institution_id FROM red_house.institution LIMIT 1"
            ).fetchone()[0]
            author = conn.execute(
                "SELECT account_id FROM red_house.user_account LIMIT 1"
            ).fetchone()[0]
            resource = uuid4()
            conn.execute(
                "INSERT INTO red_house.resource(resource_id,resource_kind,tenant_id,region_id,folio,current_institution_id,component,blood_group,expires_at) SELECT %s,'BLOOD',institution_id,region_id,'MIGRATION-SYNTHETIC',institution_id,'RBC','O-',now()+interval '2 days' FROM red_house.institution WHERE institution_id=%s",
                (resource, tenant),
            )
            profile, sample, result = [uuid4() for _ in range(3)]
            conn.execute(
                "INSERT INTO red_house.lab_profiles(id,tenant_id,author_id,name,kind,component,version,required_tests,source,synthetic,effective_at) VALUES(%s,%s,%s,'Histórico sintético','BLOOD','RBC',1,'[\"ABO\"]','Prueba',true,now())",
                (profile, tenant, author),
            )
            conn.execute(
                "INSERT INTO red_house.lab_samples(id,tenant_id,author_id,resource_id,profile_id,identifier,collected_at) VALUES(%s,%s,%s,%s,%s,'SAMPLE-HISTORY',now())",
                (sample, tenant, author, resource, profile),
            )
            conn.execute(
                "INSERT INTO red_house.lab_results(id,sample_id,tenant_id,author_id,test_code,value,method,laboratory,reference,measured_at,version) VALUES(%s,%s,%s,%s,'ABO','O','Sintético','Ficticio','Fuente histórica',now(),1)",
                (result, sample, tenant, author),
            )
            historical = conn.execute(
                "SELECT to_jsonb(t) FROM red_house.lab_results t WHERE id=%s", (result,)
            ).fetchone()[0]
            before = conn.execute(
                "SELECT md5(string_agg(row_to_json(t)::text,',' ORDER BY resource_id)) FROM red_house.resource t"
            ).fetchone()[0]
            assert (
                conn.execute(
                    "SELECT max(version) FROM red_house.schema_migration"
                ).fetchone()[0]
                == 13
            )
            shared_migrations.upgrade(conn)
            shared_migrations.upgrade(conn)
            assert (
                conn.execute(
                    "SELECT max(version) FROM red_house.schema_migration"
                ).fetchone()[0]
                == shared_migrations.LATEST_VERSION
            )
            after = conn.execute(
                "SELECT md5(string_agg(row_to_json(t)::text,',' ORDER BY resource_id)) FROM red_house.resource t"
            ).fetchone()[0]
            assert before == after and before is not None
            current = conn.execute(
                "SELECT to_jsonb(t) FROM red_house.lab_results t WHERE id=%s", (result,)
            ).fetchone()[0]
            assert all(current[k] == v for k, v in historical.items())
            assert current["result_state"] == "REPORTED" and current["hla"] is None
    finally:
        env.stop()
