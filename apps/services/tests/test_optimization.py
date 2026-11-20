"""Comparaciones reproducibles sobre almacenes aislados; nunca usan datos productivos."""

import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from statistics import median
from time import perf_counter
from uuid import UUID

from psycopg.rows import dict_row
from pymongo import MongoClient

OLD_LATEST = (
    "SELECT DISTINCT ON (service) * FROM checks ORDER BY service,created_at DESC,id"
)
from servicio_monitoreo.routes import LATEST_CHECKS_SQL as NEW_LATEST

from .test_continuity import autonomous as autonomous  # noqa: PLC0414 - pytest fixture
from .test_web_integration import web as web  # noqa: PLC0414 - pytest fixture


def evidence(name, data):
    destination = os.environ.get("OPTIMIZATION_EVIDENCE")
    if destination:
        Path(destination).mkdir(parents=True, exist_ok=True)
        (Path(destination) / (name + ".json")).write_text(
            json.dumps(data, indent=2, default=str) + "\n"
        )


def measure(fn, repeats=12):
    fn()  # mismo calentamiento para ambas variantes; no es caché fría
    samples = []
    for _ in range(repeats):
        start = perf_counter()
        result = fn()
        samples.append((perf_counter() - start) * 1000)
    return result, {"milliseconds": samples, "median_ms": median(samples)}


def test_monitor_history_cost_and_equivalence(p):
    """Volumen histórico, empates, servicio antiguo/desconocido y almacenes reales."""
    with p.owner("monitoreo") as conn:
        conn.execute("""
            INSERT INTO red_house.service_health_check(check_id,service,state,elapsed_ms,checked_at)
            SELECT md5('opt-monitor-'||i)::uuid,'opt-'||(i%12),
                CASE WHEN i%7=0 THEN 'down' ELSE 'up' END, (i%1000)::float,
                timestamptz '2026-11-10 12:00:00+00' - (i/12)*interval '30 seconds'
            FROM generate_series(1,786084) i
        """)
        conn.execute("""INSERT INTO checks(id,service,state,elapsed_ms,created_at)
            VALUES ('00000000-0000-0000-0000-000000000001','opt-1','degraded',4,
                    '2026-11-10 12:00:00+00')""")
        conn.execute("ANALYZE red_house.service_health_check")
    with p.owner("monitoreo") as conn:
        conn.row_factory = dict_row
        # La variante anterior recorre todo el histórico a propósito; en runners
        # lentos de GitHub pasa de 5 s. El límite solo evita una consulta colgada.
        conn.execute("SET statement_timeout=30000")
        old, old_time = measure(lambda: conn.execute(OLD_LATEST).fetchall())
        new, new_time = measure(lambda: conn.execute(NEW_LATEST).fetchall())
        assert old == new
        plans = {
            name: conn.execute(
                "EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) " + query
            ).fetchone()
            for name, query in (("before", OLD_LATEST), ("after", NEW_LATEST))
        }
        evidence(
            "monitor-sql",
            {
                "rows": 786085,
                "warmup": 1,
                "repetitions": 12,
                "before": old_time,
                "after": new_time,
                "plans": plans,
                "version": conn.execute("SELECT version()").fetchone(),
            },
        )
        assert new_time["median_ms"] < old_time["median_ms"]
    response = p.ok("monitoreo", "GET", "/api/v1/status", user="auditor1")
    assert len(response["latest"]) == 12
    assert all(
        row["stale"] and row["state"] == "degraded" for row in response["latest"]
    )
    assert (
        p.request("monitoreo", "GET", "/api/v1/status", user="donor1").status_code
        == 403
    )


def test_documentary_monitor_cost(p):
    from servicio_monitoreo.routes import latest_documents

    with MongoClient(p.env.state["mongo_admin"]) as client:
        collection = client.rh_monitoreo.events
        collection.drop_index("monitor_latest")
        base = datetime(2026, 11, 10, 12, tzinfo=UTC)
        for start in range(0, 786084, 5000):
            collection.insert_many(
                [
                    {
                        "_id": str(UUID(int=i + 1)),
                        "event_id": str(UUID(int=i + 1)),
                        "source": "monitoreo",
                        "service": "opt-" + str(i % 12),
                        "state": "up",
                        "elapsed_ms": float(i % 1000),
                        "checked_at": (
                            base - timedelta(seconds=(i // 12) * 30)
                        ).isoformat(),
                    }
                    for i in range(start, min(start + 5000, 786084))
                ]
            )
        match = {"$match": {"source": "monitoreo", "checked_at": {"$exists": True}}}
        group = {"$group": {"_id": "$service", "sample": {"$first": "$$ROOT"}}}
        before = [match, {"$sort": {"checked_at": -1}}, group]
        old, old_time = measure(lambda: list(collection.aggregate(before)), 5)
        start = perf_counter()
        collection.create_index(
            [("service", 1), ("checked_at", -1), ("event_id", 1)],
            name="monitor_latest",
            partialFilterExpression={
                "source": "monitoreo",
                "checked_at": {"$exists": True},
            },
        )
        build_ms = (perf_counter() - start) * 1000
        rejected_group = [
            match,
            {"$sort": {"service": 1, "checked_at": -1, "event_id": 1}},
            group,
        ]
        new, new_time = measure(
            lambda: [
                {"_id": e["service"], "sample": e} for e in latest_documents(collection)
            ],
            5,
        )
        assert sorted(old, key=lambda x: x["_id"]) == sorted(
            new, key=lambda x: x["_id"]
        )
        plans = {
            name: client.rh_monitoreo.command(
                "explain",
                {"aggregate": "events", "pipeline": pipeline, "cursor": {}},
                verbosity="executionStats",
            )
            for name, pipeline in (
                ("before", before),
                ("rejected_group", rejected_group),
            )
        }
        evidence(
            "monitor-mongo",
            {
                "rows": 786084,
                "warmup": 1,
                "repetitions": 5,
                "before": old_time,
                "after": new_time,
                "plans": plans,
                "index_build_ms": build_ms,
                "seek_plan": collection.find(
                    {
                        "source": "monitoreo",
                        "checked_at": {"$exists": True},
                        "service": {"$gt": "opt-1"},
                    }
                )
                .sort([("service", 1), ("checked_at", -1), ("event_id", 1)])
                .limit(1)
                .explain(),
                "index_sizes": client.rh_monitoreo.command("collStats", "events")[
                    "indexSizes"
                ],
                "version": client.server_info()["version"],
            },
        )
        assert new_time["median_ms"] < old_time["median_ms"]


def test_slot_batch_cost_and_results(p):
    from uuid import uuid4

    from ms_donantes.agenda import slot_availability, slots_availability

    # SQL real con tablas temporales: aísla el coste del enriquecimiento.
    with p.owner("donantes") as conn:
        conn.row_factory = dict_row
        conn.execute("CREATE TEMP TABLE appointments(id uuid PRIMARY KEY,status text)")
        conn.execute(
            "CREATE TEMP TABLE appointment_slots(id uuid PRIMARY KEY,slot_id uuid,status text)"
        )
        conn.execute("SET search_path=pg_temp,access_donantes,pg_catalog")
        rows = [{"id": uuid4(), "capacity": 3} for _ in range(100)]
        for i, row in enumerate(rows):
            for j in range(i % 5):
                identifier = uuid4()
                conn.execute(
                    "INSERT INTO appointments VALUES(%s,%s)",
                    (identifier, "CANCELLED" if j == 3 else "BOOKED"),
                )
                conn.execute(
                    "INSERT INTO appointment_slots VALUES(%s,%s,%s)",
                    (identifier, row["id"], "ATTENDED" if j == 2 else "BOOKED"),
                )
        results = {}
        for size in (1, 20, 100):
            old, before = measure(
                lambda size=size: [slot_availability(conn, row) for row in rows[:size]]
            )
            new, after = measure(
                lambda size=size: slots_availability(conn, rows[:size])
            )
            assert old == new
            results[size] = {
                "before": before,
                "after": after,
                "queries_before": size,
                "queries_after": 1,
            }
        assert slots_availability(conn, []) == []
        evidence("slots", results)


def test_session_poll_cost_and_security(web, p, monkeypatch):
    import ast
    from unittest.mock import patch

    from src import integration

    from .test_web_integration import login

    client = login(web, p, "operator1")
    original = web.before_request_funcs[None][0]
    baseline = (
        Path(__file__).resolve().parents[3]
        / "documentation/evidencias/optimizacion/20261111/before-identify.py"
    )
    timings = {}
    variants = {"after": original}
    if baseline.exists():
        tree = ast.parse(baseline.read_text())
        definition = next(
            n
            for n in ast.walk(tree)
            if isinstance(n, ast.FunctionDef) and n.name == "identify"
        )
        definition.decorator_list = []
        namespace = dict(vars(integration), app=web)
        exec(  # noqa: S102 - execute the committed, reviewed baseline hook only
            compile(
                ast.fix_missing_locations(
                    ast.Module(body=[definition], type_ignores=[])
                ),
                str(baseline),
                "exec",
            ),
            namespace,
        )
        variants = {"before": namespace["identify"], **variants}
    try:
        for name, hook in variants.items():
            web.before_request_funcs[None][0] = hook
            calls = []
            call = integration.call

            def counted(*args, _calls=calls, _call=call, **kwargs):
                _calls.append(args[:2])
                return _call(*args, **kwargs)

            def poll():
                web.extensions.pop("institution_names", None)
                response = client.get("/sesion/estado")
                assert response.status_code == 200
                assert response.headers["Cache-Control"] == "no-store"
                assert set(response.json) == {"expires_at", "server_time"}
                return response

            with patch.dict(hook.__globals__, {"call": counted}):
                _, timing = measure(poll)
            timings[name] = {**timing, "catalogue_calls_including_warmup": len(calls)}
        assert timings["after"]["catalogue_calls_including_warmup"] == 0
        if "before" in timings:
            assert timings["before"]["catalogue_calls_including_warmup"] == 13
        evidence("session-poll", timings)
    finally:
        web.before_request_funcs[None][0] = original
    # Revoke the actual authenticated session; no mocking of authorization.
    from src.integration import sessions

    cookie = client.get_cookie(web.config["JWT_COOKIE_NAME"]).value
    with web.app_context():
        assert sessions.logout(cookie)
    assert client.get("/sesion/estado").status_code == 401


def test_dashboard_assets_without_charts(web, p):
    from jinja2 import ChoiceLoader, DictLoader
    from lxml import etree

    from .test_web_integration import login

    web.config["HIGHCHARTS_ENABLED"] = True
    # AUDITOR: su panel no lleva gráficas (OPERATOR sí), como el de DONOR antes.
    client = login(web, p, "auditor1")
    loader = web.jinja_env.loader
    baseline = (
        Path(__file__).resolve().parents[3]
        / "documentation/evidencias/optimizacion/20261111/before-dashboard.html"
    )
    variants = {"after": loader}
    if baseline.exists():
        variants = {
            "before": ChoiceLoader(
                [
                    DictLoader({"integration/dashboard.html": baseline.read_text()}),
                    loader,
                ]
            ),
            **variants,
        }
    results = {}
    try:
        for name, choice in variants.items():
            web.jinja_env.loader = choice
            web.jinja_env.cache.clear()
            response = client.get("/panel")
            assert response.status_code == 200
            doc = etree.HTML(response.data)
            scripts = [
                url
                for url in doc.xpath("//script/@src")
                if "highcharts" in url or "charts.js" in url
            ]
            results[name] = {
                "scripts": scripts,
                "original_bytes": sum(len(client.get(url).data) for url in scripts),
            }
            assert not doc.xpath("//*[@data-chart-values]")
        assert results["after"]["scripts"] == []
        evidence("dashboard-assets", results)
    finally:
        web.jinja_env.loader = loader
        web.jinja_env.cache.clear()


def test_monitor_real_storage_outages_and_recovery(p):
    import signal

    import psycopg
    import pytest
    from servicio_monitoreo.routes import deliver_mongo

    # Stop only the private fixture's processes, never any pre-existing environment.
    pg = next(proc for proc in p.env.processes if Path(proc.args[0]).name == "postgres")
    mongo = next(
        proc for proc in p.env.processes if Path(proc.args[0]).name == "mongod"
    )
    now = datetime.now(UTC)
    with p.owner("monitoreo") as conn:
        for i, state in enumerate(("up", "down", "up")):
            identifier = str(UUID(int=9000000 + i))
            stamp = now - timedelta(seconds=2 - i)
            conn.execute(
                "INSERT INTO checks(id,service,state,elapsed_ms,created_at) VALUES(%s,%s,%s,%s,%s)",
                (identifier, "opt-recovery", state, (i + 1) * 10, stamp),
            )
            with p.apps["monitoreo"].app_context():
                deliver_mongo(
                    {
                        "event_id": identifier,
                        "source": "monitoreo",
                        "service": "opt-recovery",
                        "state": state,
                        "elapsed_ms": (i + 1) * 10,
                        "checked_at": stamp.isoformat(),
                    }
                )
    result = p.ok("monitoreo", "GET", "/api/v1/status", user="auditor1")
    stats = next(
        row for row in result["statistics"] if row["service"] == "opt-recovery"
    )
    assert stats["checks"] == 3 and stats["errors"] == 1 and stats["average_ms"] == 20
    statuses = []
    try:
        pg.send_signal(signal.SIGINT)
        pg.wait(timeout=20)
        fallback = p.request("monitoreo", "GET", "/api/v1/status", user="auditor1")
        statuses.append(fallback.status_code)
        assert fallback.status_code == 200
        alternative = next(
            row
            for row in fallback.json()["data"]["statistics"]
            if row["service"] == "opt-recovery"
        )
        assert (
            alternative["checks"] == 3
            and alternative["errors"] == 1
            and alternative["average_ms"] == 20
        )
        assert float(alternative["availability_percent"]) == pytest.approx(
            float(stats["availability_percent"])
        )
        mongo.terminate()
        mongo.wait(timeout=20)
        unavailable = p.request("monitoreo", "GET", "/api/v1/status", user="auditor1")
        statuses.append(unavailable.status_code)
        assert unavailable.status_code == 503
        assert unavailable.json()["error"]["code"] == "monitor_storage_unavailable"
    finally:
        for name, proc in (("postgres", pg), ("mongodb", mongo)):
            if proc.poll() is not None:
                p.env.processes.remove(proc)
                # test_resilience localiza el proceso por este PID.
                p.env.state["infrastructure_pids"][name] = p.env.launch(
                    p.env.state["infrastructure_commands"][name], name
                ).pid
        p.env.wait(lambda: psycopg.connect(p.env.state["database_admin"]).close())
        with MongoClient(
            p.env.state["mongo_admin"], serverSelectionTimeoutMS=1000
        ) as client:
            p.env.wait(lambda: client.admin.command("ping"))
    recovered = p.request("monitoreo", "GET", "/api/v1/status", user="auditor1")
    statuses.append(recovered.status_code)
    assert recovered.status_code == 200
    evidence(
        "monitor-outages",
        {
            "fault": "actual fixture PostgreSQL/MongoDB processes stopped and restarted",
            "http_statuses": statuses,
            "statistics_equivalent": True,
        },
    )


def test_monolith_monitor_and_session_without_api_listeners(autonomous, p):
    from .test_web_integration import login

    client = login(autonomous, p, "auditor1")
    response, timing = measure(lambda: client.get("/monitoreo"), 5)
    assert response.status_code == 200
    assert client.get("/sesion/estado").status_code == 200
    evidence(
        "monolith-monitor",
        {"http_status": response.status_code, "apis": "stopped", "timing": timing},
    )
