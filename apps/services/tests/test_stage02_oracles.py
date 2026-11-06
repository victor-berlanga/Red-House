"""Independent boundary oracles and authoritative anomaly facts in disposable stores."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import psycopg
import pytest
from psycopg import sql

from .helpers import evaluation, iso, plan, recipient_request, reservation, resource
from .test_final_algorithms_hla import experiment
from .test_final_quality import api
from .test_stage02_corrections import CONFIRM


@pytest.mark.parametrize(
    "missing",
    [
        "urgency",
        "urgency_source",
        "waiting_minutes",
        "expiry_minutes",
        "travel_minutes",
        "distance_km",
    ],
)
def test_each_missing_rank_factor_excludes_without_default_priority(missing):
    from ms_priorizacion_geografia.academic import execute

    candidate = {
        "identifier": "a",
        "component": "RBC",
        "available": True,
        "expired": False,
        "thermal_incident": False,
        "urgency": 1,
        "urgency_source": "SYNTHETIC",
        "waiting_minutes": 1,
        "expiry_minutes": 60,
        "travel_minutes": 5,
        "distance_km": 2,
    }
    candidate.pop(missing)
    result = execute(experiment("LOGISTICS-SIM-2.0", candidates=[candidate]))
    assert result["findings"] == [
        {"identifier": "a", "outcome": "EXCLUDED", "reasons": ["MISSING:" + missing]}
    ]


@pytest.mark.parametrize(
    "quantities,expected",
    [
        ([3, 1, 4, 5], [0, 1, 1, 4]),
        ([0, 1, 0, 0], [0, 1, 0, 0]),
        ([0, 10, 10, 10], [0, 1, 1, 4]),
    ],
)
def test_forecast_lots_against_constant_rate_capacity_oracle(quantities, expected):
    from ms_priorizacion_geografia.academic import execute

    as_of = datetime(2026, 10, 31, 12, tzinfo=timezone.utc)
    lots = [
        {
            "identifier": str(i),
            "quantity": q,
            "expires_at": (as_of + timedelta(days=d)).isoformat(),
        }
        for i, (q, d) in enumerate(zip(quantities, [-1, 0.5, 1, 3]))
    ]
    # Constant history has an exact forecast of two/day; cumulative capacities are 0,1,2,6.
    output = execute(
        experiment(
            "DEMAND-SES-1.0", history=[2] * 9, stock=sum(quantities), lots=lots[::-1]
        )
    )
    values = [
        float(
            next(
                r.split(":", 1)[1]
                for r in row["reasons"]
                if r.startswith("expected_consumption_before_expiry:")
            )
        )
        for row in output["findings"]
    ]
    assert values == expected


def test_authoritative_anomalies_outbox_failure_resolution_and_history(p, monkeypatch):
    """Administrative corruption is confined to this disposable fixture database."""
    from .test_correction_backend import laboratory

    first = resource(p)
    second = resource(p)
    _, req = recipient_request(p)
    ev = evaluation(p, req, [first])
    allocation = reservation(p, ev, first)["reservation"]
    _, req2 = recipient_request(p)
    ev2 = evaluation(p, req2, [second])
    allocation2 = reservation(p, ev2, second)["reservation"]
    shipment = plan(p, allocation)
    # Laboratory fixture can be attached to an unallocated separate resource.
    unit = api(
        p,
        "inventario",
        "/api/v1/resources",
        {
            "folio": "ANOMLAB-" + uuid4().hex[:10],
            "kind": "BLOOD",
            "component": "RBC",
            "blood_group": "O-",
            "expires_at": iso(days=1),
        },
        user="operator1",
    )
    _, body, _result = laboratory(p, unit, "json")
    donor = api(
        p,
        "donantes",
        "/api/v1/donors",
        {
            "folio": "ANOMDON-" + uuid4().hex[:10],
            "display_name": "Donante ficticio",
            "blood_group": "O-",
            "consent": True,
        },
    )
    donation = str(uuid4())
    lineage = str(uuid4())
    equipment = str(uuid4())
    cold = str(uuid4())
    reading = str(uuid4())
    hold = str(uuid4())
    tenant = p.env.state["tenants"][0]
    actor = p.env.state["accounts"]["medical1"]["id"]
    with p.owner("donantes") as conn:
        conn.execute(
            "INSERT INTO donations(id,donor_id,tenant_id,kind,component,blood_group,collected_at) VALUES(%s,%s,%s,'BLOOD','RBC','O-',now())",
            (donation, donor["id"], tenant),
        )
    foreign = api(
        p,
        "inventario",
        "/api/v1/resources",
        {
            "folio": first["folio"],
            "kind": "BLOOD",
            "component": "RBC",
            "blood_group": "O-",
            "expires_at": iso(days=1),
        },
        user="operator2",
    )
    indexes = []
    try:
        with p.owner("inventario") as conn:
            # Duplicate folios may arrive from another institution; no global uniqueness assumption.
            conn.execute(
                "UPDATE resources SET current_institution_id=%s WHERE id=%s",
                (tenant, foreign["id"]),
            )
            conn.execute(
                "INSERT INTO resource_lineage(id,parent_id,child_id,donation_id,tenant_id,author_id,reason) VALUES(%s,%s,%s,%s,%s,%s,%s)",
                (
                    lineage,
                    first["id"],
                    second["id"],
                    donation,
                    tenant,
                    actor,
                    "Corrupt fixture: donation differs from both resources",
                ),
            )
            conn.execute(
                "INSERT INTO cold_equipment(id,tenant_id,label,location) VALUES(%s,%s,'Synthetic equipment','Synthetic location')",
                (equipment, tenant),
            )
            conn.execute(
                "INSERT INTO cold_profiles(id,tenant_id,kind,component,minimum_c,maximum_c,max_gap_seconds,source,synthetic,version,author_id,effective_at) VALUES(%s,%s,'BLOOD','RBC',1,5,60,'Synthetic thresholds',true,1,%s,now())",
                (cold, tenant, actor),
            )
            conn.execute(
                "INSERT INTO cold_readings(id,resource_id,equipment_id,profile_id,tenant_id,temperature_c,captured_at,source,excursion,gap,author_id) VALUES(%s,%s,%s,%s,%s,20,now(),'Persisted fixture',false,false,%s)",
                (reading, unit["id"], equipment, cold, tenant, actor),
            )
            indexes = conn.execute(
                "SELECT indexname,indexdef FROM pg_indexes WHERE schemaname='red_house' AND tablename='blood_allocation' AND indexname IN ('allocation_resource_exclusive','api_resource_reserved')"
            ).fetchall()
            for name, _ in indexes:
                conn.execute(
                    sql.SQL("DROP INDEX red_house.{}").format(sql.Identifier(name))
                )
            conn.execute(
                "UPDATE reservations SET resource_id=%s WHERE id=%s",
                (first["id"], allocation2["id"]),
            )
        with p.owner("compatibilidad") as conn:
            conn.execute(
                "UPDATE lab_samples SET tenant_id=%s WHERE id=%s",
                (p.env.state["tenants"][1], body["sample_id"]),
            )
        with p.owner("transporte") as conn:
            conn.execute(
                "UPDATE shipments SET sequence=3 WHERE id=%s", (shipment["id"],)
            )
        with p.owner("receptores") as conn:
            conn.execute(
                "INSERT INTO holds(id,request_id,recipient_id,operation_id,resource_id,kind,request_version,region_id) SELECT %s,request_id,recipient_id,%s,%s,kind,request_version,region_id FROM holds WHERE id=%s",
                (hold, str(uuid4()), second["id"], allocation["hold_id"]),
            )
        app = p.apps["priorizacion_geografia"]
        original = app.config["SERVICE_URLS"]
        monkeypatch.setitem(
            app.config, "SERVICE_URLS", dict(original, auditoria="http://127.0.0.1:1")
        )
        run = api(
            p, "priorizacion_geografia", "/api/v1/decision-runs", {"branch": "ALG-05"}
        )
        expected = {
            "DUPLICATE_IDENTIFIER",
            "MULTIPLE_RESERVATIONS",
            "INVALID_DONATION_PROVENANCE",
            "INVALID_LINEAGE",
            "THERMAL_INCOHERENCE",
            "FOREIGN_SAMPLE",
            "BROKEN_SEQUENCE",
            "STALE_PROJECTION",
        }
        assert expected <= {x["code"] for x in run["result"]["findings"]}
        quantity_run = api(
            p,
            "priorizacion_geografia",
            "/api/v1/decision-runs",
            {"branch": "ALG-05"},
            user="medical2",
        )
        assert "INCOMPATIBLE_QUANTITY" in {
            x["code"] for x in quantity_run["result"]["findings"]
        }
        from redhouse.events import dispatch

        with app.app_context():
            assert dispatch(1000)["failed"] > 0
        with p.owner("auditoria") as conn:
            assert (
                conn.execute(
                    "SELECT count(*) FROM anomaly_reviews WHERE source_run_id=%s",
                    (run["id"],),
                ).fetchone()[0]
                == 0
            )
        monkeypatch.setitem(app.config, "SERVICE_URLS", original)
        with p.owner("priorizacion_geografia") as conn:
            conn.execute(
                "UPDATE outbox SET next_attempt=now() WHERE delivered_at IS NULL"
            )
        p.drain(30)
        with p.owner("auditoria") as conn:
            rows = conn.execute(
                "SELECT id,evidence FROM anomaly_reviews WHERE source_run_id=%s",
                (run["id"],),
            ).fetchall()
        assert expected <= {r[1]["finding"]["code"] for r in rows}
        target = str(
            next(r[0] for r in rows if r[1]["finding"]["code"] == "THERMAL_INCOHERENCE")
        )
        path = "/api/v1/anomaly-reviews/" + target
        before = api(p, "auditoria", path, method="GET")
        assert (
            p.request(
                "auditoria",
                "POST",
                path + "/resolve",
                user="medical1",
                data=dict(CONFIRM, version=1, state="CONFIRMED"),
            ).status_code
            == 403
        )
        assert p.request("auditoria", "GET", path, user="medical2").status_code == 403
        auditor = "auditor1"
        api(
            p,
            "auditoria",
            path + "/resolve",
            dict(CONFIRM, version=1, state="CONFIRMED"),
            user=auditor,
            fmt="xml",
        )
        after = api(p, "auditoria", path, method="GET", user=auditor)
        assert before["evidence"] == after["evidence"] and len(after["history"]) == 1
        assert after["state"] == "CONFIRMED"
        api(p, "priorizacion_geografia", "/api/v1/decision-runs", {"branch": "ALG-05"})
        p.drain(30)
        with p.owner("auditoria") as conn:
            assert (
                conn.execute(
                    "SELECT count(*) FROM anomaly_reviews WHERE deduplication_key=%s",
                    (before["deduplication_key"],),
                ).fetchone()[0]
                == 1
            )
        with (
            psycopg.connect(p.apps["auditoria"].config["DATABASE_URL"]) as conn,
            pytest.raises(psycopg.errors.InsufficientPrivilege),
        ):
            conn.execute(
                "UPDATE anomaly_reviews SET evidence=%s WHERE id=%s", ("{}", target)
            )
    finally:
        with p.owner("inventario") as conn:
            conn.execute(
                "UPDATE reservations SET resource_id=%s WHERE id=%s",
                (second["id"], allocation2["id"]),
            )
            for _, definition in indexes:
                conn.execute(definition)
        with p.owner("compatibilidad") as conn:
            conn.execute(
                "UPDATE lab_samples SET tenant_id=%s WHERE id=%s",
                (tenant, body["sample_id"]),
            )
        with p.owner("transporte") as conn:
            conn.execute(
                "UPDATE shipments SET sequence=%s WHERE id=%s",
                (shipment["sequence"], shipment["id"]),
            )
        with p.owner("receptores") as conn:
            conn.execute("DELETE FROM holds WHERE id=%s", (hold,))


def test_recipient_correction_serializes_with_reservation_commit(p, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    from time import monotonic, sleep

    from ms_inventario import quality

    unit = resource(p)
    rec, req = recipient_request(p)
    prof = api(
        p,
        "compatibilidad",
        "/api/v1/laboratory/profiles",
        {
            "name": "Concurrent synthetic profile",
            "kind": "BLOOD",
            "component": "RBC",
            "version": 1,
            "required_tests": ["ABO"],
            "source": "Synthetic concurrency case",
            "synthetic": True,
            "effective_at": iso(minutes=-60),
        },
        user="medical2",
    )
    sample = api(
        p,
        "compatibilidad",
        "/api/v1/laboratory/samples",
        {
            "recipient_id": rec["id"],
            "request_id": req["id"],
            "profile_id": prof["id"],
            "identifier": "LOCK-" + uuid4().hex,
            "collected_at": iso(minutes=-10),
        },
        user="medical2",
    )
    api(
        p,
        "compatibilidad",
        "/api/v1/laboratory/samples/" + sample["id"] + "/receive",
        dict(CONFIRM, version=1, decision="RECEIVED"),
        user="medical2",
    )
    body = {
        "sample_id": sample["id"],
        "test_code": "ABO",
        "value": "Dato ficticio",
        "method": "Ficticio",
        "laboratory": "Ficticio",
        "reference": "Fixture",
        "measured_at": iso(minutes=-5),
    }
    result = api(
        p, "compatibilidad", "/api/v1/laboratory/results", body, user="medical2"
    )
    api(
        p,
        "compatibilidad",
        "/api/v1/laboratory/results/" + result["id"] + "/review",
        dict(CONFIRM, version=1, decision="AUTHORIZED"),
        user="medical2",
    )
    ev = evaluation(p, req, [unit])
    entered = Event()
    release = Event()
    original = quality.guard

    def paused(conn, row, **kwargs):
        value = original(conn, row, **kwargs)
        if str(row["id"]) == unit["id"]:
            entered.set()
            assert release.wait(10)
        return value

    monkeypatch.setattr(quality, "guard", paused)
    with ThreadPoolExecutor(max_workers=2) as pool:
        booking = pool.submit(reservation, p, ev, unit)
        try:
            assert entered.wait(10)
            correction = pool.submit(
                api,
                p,
                "compatibilidad",
                "/api/v1/laboratory/results",
                dict(
                    body,
                    supersedes=result["id"],
                    result_state="CORRECTED",
                    value="Dato corregido",
                ),
                user="medical2",
            )
            waited = False
            deadline = monotonic() + 2
            while monotonic() < deadline:
                with p.owner("compatibilidad") as conn:
                    waited = bool(
                        conn.execute(
                            "SELECT 1 FROM pg_stat_activity WHERE datname=current_database() AND wait_event='advisory' AND query LIKE 'SELECT pg_advisory_xact_lock%' AND pid<>pg_backend_pid()"
                        ).fetchone()
                    )
                if waited:
                    break
                sleep(0.05)
            assert waited and not correction.done()
        finally:
            release.set()
        assert booking.result()["reservation"]["resource_id"] == unit["id"]
        assert correction.result()["supersedes"] == result["id"]
    detail = api(
        p,
        "compatibilidad",
        "/api/v1/evaluations/" + ev["id"],
        method="GET",
        user="medical2",
    )
    assert "RECIPIENT_LABORATORY_CHANGED" in detail["validity"]["reasons"]
    with p.owner("inventario") as conn:
        assert (
            conn.execute(
                "SELECT count(*) FROM reservations WHERE resource_id=%s", (unit["id"],)
            ).fetchone()[0]
            == 1
        )


def test_complete_academic_profile_and_review_never_enable_clinical_operations(
    p, monkeypatch
):
    from .test_correction_backend import laboratory

    unit = api(
        p,
        "inventario",
        "/api/v1/resources",
        {
            "folio": "SCOPE-" + uuid4().hex[:10],
            "kind": "BLOOD",
            "component": "RBC",
            "blood_group": "O-",
            "expires_at": iso(days=1),
        },
        user="operator1",
    )
    prof, _, _ = laboratory(p, unit, "json")
    check = api(
        p,
        "compatibilidad",
        "/api/v1/laboratory/resources/" + unit["id"] + "/check",
        {"profile_id": prof["id"], "tenant_id": p.env.state["tenants"][0]},
    )
    assert (
        check["complete"]
        and not check["clinical_enabled"]
        and not check["clinical_approval"]
    )
    cfg = p.apps["inventario"].config
    monkeypatch.setitem(cfg, "OPERATION_SCOPE", "CLINICAL")
    denied = p.request(
        "inventario",
        "POST",
        "/api/v1/resources/" + unit["id"] + "/release",
        user="medical1",
        data=dict(CONFIRM, version=2),
    )
    assert (
        denied.status_code == 409
        and denied.json()["error"]["code"] == "clinical_policy_disabled"
    )
    monkeypatch.setitem(cfg, "OPERATION_SCOPE", "ACADEMIC")
    unit = api(
        p,
        "inventario",
        "/api/v1/resources/" + unit["id"] + "/release",
        dict(CONFIRM, version=2),
    )
    _, req = recipient_request(p)
    ev = evaluation(p, req, [unit])
    monkeypatch.setitem(cfg, "OPERATION_SCOPE", "CLINICAL")
    denied = p.request(
        "inventario",
        "POST",
        "/api/v1/reservations",
        data=dict(CONFIRM, evaluation_id=ev["id"], resource_id=unit["id"]),
    )
    assert (
        denied.status_code == 409
        and denied.json()["error"]["code"] == "academic_execution"
    )
    with p.owner("inventario") as conn:
        assert (
            conn.execute(
                "SELECT count(*) FROM reservations WHERE resource_id=%s", (unit["id"],)
            ).fetchone()[0]
            == 0
        )
    monkeypatch.setitem(p.apps["compatibilidad"].config, "OPERATION_SCOPE", "CLINICAL")
    denied = p.request(
        "compatibilidad", "POST", "/api/v1/evaluations", data={"request_id": req["id"]}
    )
    assert denied.status_code == 409
