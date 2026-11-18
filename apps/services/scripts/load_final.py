"""Carga final y volumen en un laboratorio desechable nuevo (/private/tmp/rh-final-*).

Cierra INC-436: cada usuario Locust inicia sesión con su propia cuenta sintética.
Las cuentas adicionales se crean por SQL en el laboratorio desechable, con el mismo
mecanismo de ``tests/load_support.prepare_transaction_fixture`` (copia del hash de
contraseña de ``operator1``). No cambia código de producto, cuotas ni configuración.

Fases:
1. ``reads``: serie de lectura 12/24/36 + recuperación 6 (mismas operaciones y
   espera que la serie sostenida, una identidad por usuario).
2. ``mixed``: perfiles diferenciados 12/24/36/48 + recuperación 12.
3. ``volume``: >=1,000,000 eventos de auditoría SQL y >=100,000 documentos MongoDB;
   inserción, consulta con/sin índice (EXPLAIN ANALYZE), API, caché Redis y
   recursos.  Al final se detiene el Redis propio para observar el
   comportamiento sin Redis.

Uso:
  PYTHONPATH=.:apps/services apps/services/.venv/bin/python \\
    apps/services/scripts/load_final.py --mongod /opt/homebrew/bin/mongod \\
    --evidence documentation/evidencias/entrega-final/carga-final-20261118/raw
"""

import argparse
import contextlib
import io
import json
import os
import shutil
import signal
import statistics
import subprocess
import sys
import tempfile
import threading
import time
import traceback
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import psutil
import psycopg
import requests
from psycopg.conninfo import make_conninfo
from pymongo import MongoClient

from ms_identidad_acceso.strong_auth import totp
from scripts.local import Environment, private_file
from scripts.prepare_load import populate, validate_environment

ACCOUNTS = {
    "MEDICAL": 20,
    "OPERATOR": 20,
    "COORDINATOR": 8,
    "AUDITOR": 10,
    "DONOR": 20,
    "TRANSPORT": 10,
}
MFA_ROLES = ("MEDICAL", "COORDINATOR")
MIXED_CLASSES = (
    "ConsultaWeb",
    "MovilDonante",
    "MovilTransportista",
    "EscritorioOperador",
    "PanelAuditoria",
    "ProcesoAutomatico",
)
MIN_FREE = 5 * 1024**3
MAX_OWN = 8 * 1024**3


def now_iso():
    return datetime.now(UTC).isoformat(timespec="seconds")


def disk_guard(directory):
    free = shutil.disk_usage(directory).free
    used = sum(
        p.stat().st_size
        for p in Path(directory).rglob("*")
        if p.is_file() and not p.is_symlink()
    )
    if free < MIN_FREE or used > MAX_OWN:
        raise RuntimeError(f"Guarda de disco: libre={free} propio={used}")
    return {"free_bytes": free, "owned_bytes": used}


# --- Recursos -----------------------------------------------------------------


class Sampler:
    """Muestrea CPU % y RSS por grupo de procesos del laboratorio cada 2 s."""

    def __init__(self, env, extra=None, interval=2.0):
        self.env = env
        self.extra = extra or {}
        self.interval = interval
        self.samples = []
        self.stop_event = threading.Event()
        self.cache = {}
        self.thread = threading.Thread(target=self.loop, daemon=True)

    def groups(self):
        st = self.env.state
        infra = st["infrastructure_pids"]
        result = {
            "servicios_api": list(st.get("service_pids", {}).values()),
            "workers": list(st.get("worker_pids", {}).values()),
            "postgres": [infra["postgres"]],
            "mongodb": [infra["mongodb"]],
            "redis": [infra["redis"]],
        }
        result.update({k: [v] for k, v in self.extra.items()})
        return result

    def proc(self, pid):
        process = self.cache.get(pid)
        if process is None:
            process = psutil.Process(pid)
            process.cpu_percent(None)
            self.cache[pid] = process
        return process

    def sample(self):
        row = {"t": time.time()}
        for name, pids in self.groups().items():
            cpu = rss = 0.0
            for pid in pids:
                try:
                    root = psutil.Process(pid)
                    members = [root] + root.children(recursive=True)
                except psutil.Error:
                    continue
                for member in members:
                    try:
                        fresh = member.pid not in self.cache
                        process = self.proc(member.pid)
                        # Un proceso recién visto solo se ceba: su primera lectura
                        # tendría un intervalo ~0 y un porcentaje espurio.
                        cpu += 0.0 if fresh else process.cpu_percent(None)
                        rss += process.memory_info().rss
                    except psutil.Error:
                        self.cache.pop(member.pid, None)
            row[name] = {
                "cpu_percent": round(cpu, 1),
                "rss_mb": round(rss / 1024**2, 1),
            }
        memory = psutil.virtual_memory()
        row["sistema"] = {
            "available_mb": round(memory.available / 1024**2),
            "cpu_percent": psutil.cpu_percent(None),
        }
        return row

    def loop(self):
        self.sample()
        while not self.stop_event.wait(self.interval):
            # El muestreo no debe tumbar la corrida.
            with contextlib.suppress(Exception):
                self.samples.append(self.sample())

    def __enter__(self):
        psutil.cpu_percent(None)
        self.thread.start()
        return self

    def __exit__(self, *_exc):
        self.stop_event.set()
        self.thread.join(timeout=10)

    def summary(self):
        if not self.samples:
            return {}
        result = {"samples": len(self.samples)}
        for key in self.samples[0]:
            if key == "t":
                continue
            values = [s[key] for s in self.samples if key in s]
            result[key] = {
                metric: {
                    "mean": round(statistics.fmean(v[metric] for v in values), 1),
                    "max": max(v[metric] for v in values),
                    **(
                        {"min": min(v[metric] for v in values)}
                        if metric == "available_mb"
                        else {}
                    ),
                }
                for metric in values[0]
            }
        return result


# --- Fixture: una cuenta sintética por usuario concurrente ----------------------


def make_fixture(env, scale=1):
    validate_environment(env)
    tenant = env.state["tenants"][0]
    prefix = "final-" + uuid4().hex[:8]
    now = datetime.now(UTC)
    fixture = {
        "directory": str(env.directory),
        "prefix": prefix,
        "tenant_id": tenant,
        "campaign_id": str(uuid4()),
        "campaign_title": prefix,
        "site_id": str(uuid4()),
        "slot_ids": [str(uuid4()), str(uuid4())],
        "starts_at": (now + timedelta(days=1)).isoformat(),
        "ends_at": (now + timedelta(days=2)).isoformat(),
        "accounts": {},
        "notice": "Cuentas y campaña sintéticas creadas por SQL en el laboratorio desechable",
    }
    for role, count in ACCOUNTS.items():
        fixture["accounts"][role] = [
            {
                "id": str(uuid4()),
                "username": f"{prefix}-{role.lower()}-{index:02d}",
                "role": role,
                "donor_id": str(uuid4()) if role == "DONOR" else None,
            }
            for index in range(count * scale)
        ]
    with psycopg.connect(env.state["database_owners"]["identidad_acceso"]) as conn:
        password_hash = conn.execute(
            "SELECT password_hash FROM users WHERE id=%s AND role='OPERATOR' AND active",
            (env.state["accounts"]["operator1"]["id"],),
        ).fetchone()[0]
        for accounts in fixture["accounts"].values():
            for account in accounts:
                conn.execute(
                    "INSERT INTO users(id,tenant_id,username,password_hash,role) VALUES(%s,%s,%s,%s,%s)",
                    (
                        account["id"],
                        tenant,
                        account["username"],
                        password_hash,
                        account["role"],
                    ),
                )
                if account["donor_id"]:
                    conn.execute(
                        "INSERT INTO access_donantes.donors(id,tenant_id,user_id,folio,display_name,blood_group,consent,status) "
                        "VALUES(%s,%s,%s,%s,'Persona sintética','O-',true,'PRELIMINARY')",
                        (
                            account["donor_id"],
                            tenant,
                            account["id"],
                            account["username"],
                        ),
                    )
        conn.execute(
            "INSERT INTO access_identidad_acceso.catalogue(id,tenant_id,kind,name,details) "
            "VALUES(%s,%s,'sites',%s,%s::jsonb)",
            (
                fixture["site_id"],
                tenant,
                prefix,
                json.dumps(
                    {"municipality": "Monterrey", "address": "Dirección sintética"}
                ),
            ),
        )
        conn.execute(
            "INSERT INTO access_donantes.campaigns(id,tenant_id,title,starts_at,ends_at,capacity) VALUES(%s,%s,%s,%s,%s,10000)",
            (
                fixture["campaign_id"],
                tenant,
                prefix,
                fixture["starts_at"],
                fixture["ends_at"],
            ),
        )
        for index, identifier in enumerate(fixture["slot_ids"]):
            start = datetime.fromisoformat(fixture["starts_at"]) + timedelta(
                minutes=index * 30
            )
            conn.execute(
                "INSERT INTO access_donantes.campaign_slots(id,campaign_id,tenant_id,site_id,starts_at,ends_at,capacity) "
                "VALUES(%s,%s,%s,%s,%s,%s,10000)",
                (
                    identifier,
                    fixture["campaign_id"],
                    tenant,
                    fixture["site_id"],
                    start,
                    start + timedelta(minutes=15),
                ),
            )
    private_file(env.directory / "final-fixture.json", json.dumps(fixture, indent=2))
    return fixture


def enroll(env, fixture):
    """Enrola MFA para MEDICAL/COORDINATOR por la API pública del laboratorio."""
    base = env.state["urls"]["identidad_acceso"].rstrip("/")
    factors = {}
    with requests.Session() as session:
        session.trust_env = False
        for role in MFA_ROLES:
            for account in fixture["accounts"][role]:
                body = {
                    "username": account["username"],
                    "password": env.state["password"],
                }
                response = session.post(
                    base + "/api/v1/auth/mfa/enrollment", json=body, timeout=(5, 15)
                )
                if response.status_code != 200:
                    raise RuntimeError(f"Enrolamiento MFA {response.status_code}")
                value = response.json()["data"]
                response = session.post(
                    base + "/api/v1/auth/mfa/confirm",
                    json={
                        "challenge": value["challenge"],
                        "code": totp(value["secret"], int(time.time()) // 30),
                    },
                    timeout=(5, 15),
                )
                if response.status_code != 200:
                    raise RuntimeError(f"Confirmación MFA {response.status_code}")
                factors[account["username"]] = value["secret"]
                time.sleep(0.8)  # bajo la cuota anónima por IP (180/min) de Identidad
    return factors


# --- Fases Locust -------------------------------------------------------------


def run_phase(
    env,
    factors,
    workdir,
    evidence,
    *,
    name,
    mode,
    users,
    seconds,
    warmup=30,
    no_cache=False,
):
    output = workdir / name
    output.mkdir(mode=0o700)
    marker = output / "phase.json"
    read_fd, write_fd = os.pipe()
    os.write(write_fd, json.dumps(factors).encode())
    os.close(write_fd)
    environment = dict(
        os.environ,
        REDHOUSE_LOAD_ISOLATED="1",
        REDHOUSE_LOAD_STATE=str(env.directory / "state.json"),
        REDHOUSE_LOAD_MFA_FD=str(read_fd),
        REDHOUSE_LOAD_MARKER=str(marker),
        REDHOUSE_LOAD_USERS=str(users),
        REDHOUSE_LOAD_MODE=mode,
        REDHOUSE_LOAD_MEASURE_SECONDS=str(seconds),
        REDHOUSE_LOAD_WARMUP_SECONDS=str(warmup),
        NO_PROXY="127.0.0.1",
        no_proxy="127.0.0.1",
    )
    environment.pop("REDHOUSE_LOAD_NO_CACHE", None)
    if no_cache:
        environment["REDHOUSE_LOAD_NO_CACHE"] = "1"
    classes = ["ReadUser"] if mode == "reads" else list(MIXED_CLASSES)
    command = [
        sys.executable,
        "-m",
        "locust",
        "-f",
        str(ROOT / "tests/locust_final.py"),
        "--headless",
        "--users",
        str(users),
        "--spawn-rate",
        str(users),
        "--run-time",
        f"{150 + warmup + seconds + 60}s",
        "--stop-timeout",
        "20",
        "--host",
        "http://127.0.0.1",
        "--csv",
        str(output / "run"),
        "--json-file",
        str(output / "final"),
        "--exit-code-on-error",
        "0",
        "--only-summary",
        *classes,
    ]
    started = now_iso()
    log = output / "runner.private.log"
    with log.open("wb") as stream:
        os.chmod(log, 0o600)
        process = subprocess.Popen(
            command,
            cwd=ROOT,
            env=environment,
            stdout=stream,
            stderr=subprocess.STDOUT,
            pass_fds=(read_fd,),
            start_new_session=True,
        )
        os.close(read_fd)
        sampler = Sampler(env, extra={"locust": process.pid})
        measuring = None
        with sampler:
            deadline = time.monotonic() + 150 + warmup + seconds + 120
            while process.poll() is None:
                if time.monotonic() > deadline:
                    os.killpg(process.pid, signal.SIGTERM)
                    break
                if measuring is None and marker.exists():
                    try:
                        if json.loads(marker.read_text()).get("stage") == "measuring":
                            measuring = len(sampler.samples)
                    except ValueError:
                        pass
                time.sleep(1)
            process.wait(timeout=60)
    result = json.loads(marker.read_text()) if marker.exists() else {"stage": "missing"}
    measured_samples = sampler.samples[measuring or 0 :]
    sampler.samples = measured_samples
    result.update(
        name=name,
        started_utc=started,
        finished_utc=now_iso(),
        cache_mode="bypass" if no_cache else "active",
        exit_code=process.returncode,
        resources=sampler.summary(),
    )
    target = evidence / name
    target.mkdir(parents=True, exist_ok=True)
    (target / "phase.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    )
    for suffix in ("_stats.csv", "_failures.csv", "_exceptions.csv"):
        source = output / ("run" + suffix)
        if source.exists():
            shutil.copyfile(source, target / ("run" + suffix))
    if (output / "final.json").exists():
        shutil.copyfile(output / "final.json", target / "final.json")
    return result


# --- Volumen ------------------------------------------------------------------


def audit_actions():
    from redhouse.audit_catalog import ACTIONS

    return [
        code
        for code, values in ACTIONS.items()
        if values[1] in ("BUSINESS", "DECISION", "SECURITY")
    ]


def audit_chunk(start, count, region, tenants, actors, actions, base_time):
    """Filas COPY de eventos de auditoría con la forma del evento real."""
    buffer = io.StringIO()
    for i in range(start, start + count):
        event_id = str(uuid4())
        tenant = tenants[i % len(tenants)]
        actor = actors[i % len(actors)]
        action = actions[i % len(actions)]
        when = base_time + timedelta(seconds=i * 3)
        event = {
            "event_id": event_id,
            "source": "inventario",
            "action": action,
            "tenant_id": tenant,
            "region_id": region,
            "actor_id": actor,
            "resource_id": str(uuid4()),
            "correlation_id": str(uuid4()),
            "occurred_at": when.isoformat(),
            "metadata": {"synthetic": True, "audit": {"reason": "Volumen sintético"}},
        }
        text = json.dumps(event, separators=(",", ":")).replace("\\", "\\\\")
        fields = (event_id, actor, tenant, when.isoformat(), action, "inventario")
        buffer.write("\t".join((*fields, region, text)) + "\n")
    return buffer.getvalue()


def timed(fn, repeat):
    values = []
    for _ in range(repeat):
        begin = time.perf_counter()
        fn()
        values.append((time.perf_counter() - begin) * 1000)
    values.sort()
    return {
        "repeat": repeat,
        "median_ms": round(statistics.median(values), 2),
        "p95_ms": round(values[max(0, int(len(values) * 0.95) - 1)], 2),
        "max_ms": round(values[-1], 2),
    }


def plan_summary(plan):
    root = plan[0]
    nodes = []

    def walk(node):
        nodes.append(
            {
                k: node.get(k)
                for k in (
                    "Node Type",
                    "Index Name",
                    "Relation Name",
                    "Actual Rows",
                    "Actual Total Time",
                )
                if node.get(k) is not None
            }
        )
        for child in node.get("Plans", []):
            walk(child)

    walk(root["Plan"])
    return {
        "execution_ms": root.get("Execution Time"),
        "planning_ms": root.get("Planning Time"),
        "nodes": nodes,
        "indexes_used": sorted({n["Index Name"] for n in nodes if "Index Name" in n}),
        "seq_scans": [
            n.get("Relation Name") for n in nodes if n.get("Node Type") == "Seq Scan"
        ],
    }


def audit_queries(region, window_from, window_to, action):
    from ms_auditoria.queries import BASE, DEFAULT_CATEGORIES

    categories = list(DEFAULT_CATEGORIES)
    order = " ORDER BY executed_at DESC NULLS LAST,created_at DESC,id LIMIT 20 OFFSET 0"
    return {
        "listado_por_defecto": (
            BASE + "SELECT count(*) AS n FROM audit WHERE category = ANY(%s)",
            BASE + "SELECT * FROM audit WHERE category = ANY(%s)" + order,
            [region, categories],
        ),
        "ventana_1h": (
            BASE
            + "SELECT count(*) AS n FROM audit WHERE category = ANY(%s) AND executed_at >= %s AND executed_at <= %s",
            BASE
            + "SELECT * FROM audit WHERE category = ANY(%s) AND executed_at >= %s AND executed_at <= %s"
            + order,
            [region, categories, window_from, window_to],
        ),
        "filtro_accion": (
            BASE
            + "SELECT count(*) AS n FROM audit WHERE category = ANY(%s) AND action=%s",
            BASE + "SELECT * FROM audit WHERE category = ANY(%s) AND action=%s" + order,
            [region, categories, action],
        ),
    }


def explain_set(conn, queries):
    result = {}
    for name, (count_sql, page_sql, values) in queries.items():
        entry = {}
        for kind, sql in (("count", count_sql), ("page", page_sql)):
            plan = conn.execute(
                "EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) " + sql, values
            ).fetchone()[0]
            entry[kind] = {"summary": plan_summary(plan), "plan": plan}
        result[name] = entry
    return result


def api_login(env, username, otp_secret=None):
    base = env.state["urls"]["identidad_acceso"].rstrip("/")
    body = {"username": username, "password": env.state["password"]}
    if otp_secret:
        body["otp"] = totp(otp_secret, int(time.time()) // 30 + 1)
    with requests.Session() as session:
        session.trust_env = False
        response = session.post(base + "/api/v1/auth/login", json=body, timeout=(5, 15))
    response.raise_for_status()
    return response.json()["data"]["access_token"]


def api_timing(env, token, service, path, repeat=10, headers=None):
    url = env.state["urls"][service].rstrip("/") + path
    statuses, cache = {}, {}
    session = requests.Session()
    session.trust_env = False
    request_headers = {
        "Authorization": "Bearer " + token,
        "Accept": "application/json",
        **(headers or {}),
    }

    def call():
        response = session.get(url, headers=request_headers, timeout=(5, 30))
        statuses[response.status_code] = statuses.get(response.status_code, 0) + 1
        label = response.headers.get("X-Cache")
        if label:
            cache[label] = cache.get(label, 0) + 1

    result = timed(call, repeat)
    session.close()
    result.update(statuses={str(k): v for k, v in statuses.items()}, cache=cache)
    return result


def index_usage(conn):
    return {
        row[0]: row[1]
        for row in conn.execute(
            "SELECT indexrelname, idx_scan FROM pg_stat_user_indexes WHERE schemaname='red_house' AND relname='audit_event' ORDER BY 1"
        ).fetchall()
    }


def table_sizes(conn):
    row = conn.execute(
        "SELECT count(*), pg_relation_size('red_house.audit_event'), pg_indexes_size('red_house.audit_event'), pg_total_relation_size('red_house.audit_event') FROM red_house.audit_event"
    ).fetchone()
    return {
        "rows": row[0],
        "table_bytes": row[1],
        "index_bytes": row[2],
        "total_bytes": row[3],
    }


def volume(env, evidence, rows_target, docs_target, factors_unused=None):
    st = env.state
    admin_dsn = make_conninfo(st["database_admin"], dbname="red_house")
    region, tenants = st["region_id"], st["tenants"]
    actors = [a["id"] for a in st["accounts"].values()]
    actions = audit_actions()
    base_time = datetime(2026, 1, 1, tzinfo=UTC)
    report = {
        "started_utc": now_iso(),
        "audit_sql": {"checkpoints": []},
        "mongo": {"checkpoints": []},
    }
    auditor_token = api_login(env, "auditor1")
    # 1) Inserción transaccional por lotes (executemany), comparación de método.
    with psycopg.connect(admin_dsn, autocommit=True) as conn:
        report["audit_sql"]["initial"] = table_sizes(conn)
        sample_rows = []
        for i in range(20000):
            event_id = str(uuid4())
            when = base_time - timedelta(days=30) + timedelta(seconds=i)
            event = {
                "event_id": event_id,
                "source": "inventario",
                "action": actions[i % len(actions)],
                "tenant_id": tenants[i % 2],
                "region_id": region,
                "actor_id": actors[i % len(actors)],
                "resource_id": str(uuid4()),
                "occurred_at": when.isoformat(),
                "metadata": {"synthetic": True},
            }
            sample_rows.append(
                (
                    event_id,
                    actors[i % len(actors)],
                    tenants[i % 2],
                    when,
                    event["action"],
                    "inventario",
                    region,
                    json.dumps(event),
                )
            )
        with Sampler(env) as sampler:
            begin = time.perf_counter()
            with conn.cursor() as cur:
                for offset in range(0, len(sample_rows), 1000):
                    with conn.transaction():
                        cur.executemany(
                            "INSERT INTO red_house.audit_event(event_id,actor_id,institution_id,occurred_at,action,source_service,region_id,event) VALUES(%s,%s,%s,%s,%s,%s,%s,%s::jsonb)",
                            sample_rows[offset : offset + 1000],
                        )
            elapsed = time.perf_counter() - begin
        report["audit_sql"]["executemany_20k"] = {
            "rows": len(sample_rows),
            "seconds": round(elapsed, 2),
            "rows_per_second": round(len(sample_rows) / elapsed),
            "batch": 1000,
            "resources": sampler.summary(),
        }
        del sample_rows
    # 2) COPY por bloques hasta 100k y 1M, con mediciones en cada punto.
    inserted = 20000
    checkpoints = [100000, 500000, rows_target]
    copy_seconds = gen_seconds = 0.0
    chunk = 50000
    with psycopg.connect(admin_dsn, autocommit=True) as conn:
        for checkpoint in checkpoints:
            with Sampler(env) as sampler:
                stage_copy = 0.0
                stage_rows = 0
                while inserted < checkpoint:
                    disk_guard(env.directory)
                    count = min(chunk, checkpoint - inserted)
                    g0 = time.perf_counter()
                    data = audit_chunk(
                        inserted, count, region, tenants, actors, actions, base_time
                    )
                    gen_seconds += time.perf_counter() - g0
                    c0 = time.perf_counter()
                    with (
                        conn.transaction(),
                        conn.cursor() as cur,
                        cur.copy(
                            "COPY red_house.audit_event(event_id,actor_id,institution_id,occurred_at,action,source_service,region_id,event) FROM STDIN"
                        ) as copy,
                    ):
                        copy.write(data)
                    spent = time.perf_counter() - c0
                    copy_seconds += spent
                    stage_copy += spent
                    stage_rows += count
                    inserted += count
                    del data
            conn.execute("ANALYZE red_house.audit_event")
            sizes = table_sizes(conn)
            point = {
                "target_rows": checkpoint,
                "table": sizes,
                "copy_stage": {
                    "rows": stage_rows,
                    "seconds": round(stage_copy, 2),
                    "rows_per_second": round(stage_rows / stage_copy)
                    if stage_copy
                    else None,
                    "resources": sampler.summary(),
                },
            }
            # Consulta del producto con índices vigentes.
            window_from = base_time + timedelta(seconds=(checkpoint // 2) * 3)
            window_to = window_from + timedelta(hours=1)
            queries = audit_queries(region, window_from, window_to, actions[3])
            owner = psycopg.connect(st["database_owners"]["auditoria"])
            try:
                owner.execute(
                    "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY"
                )
                point["with_index"] = explain_set(owner, queries)
                owner.rollback()
                point["with_index_timing"] = {
                    name: {
                        kind: timed(
                            lambda sql=sql, v=values, c=owner: c.execute(
                                sql, v
                            ).fetchall(),
                            5,
                        )
                        for kind, sql in (("count", c), ("page", p))
                    }
                    for name, (c, p, values) in queries.items()
                }
                owner.rollback()
            finally:
                owner.close()
            # API real: misma consulta por HTTP (sin caché Redis en Auditoría).
            usage_before = index_usage(conn)
            auditor_token = api_login(env, "auditor1")
            point["api"] = {
                "listado_por_defecto": api_timing(
                    env, auditor_token, "auditoria", "/api/v1/events?page_size=20", 8
                ),
                "ventana_1h": api_timing(
                    env,
                    auditor_token,
                    "auditoria",
                    "/api/v1/events?page_size=20&from="
                    + window_from.isoformat().replace("+00:00", "Z")
                    + "&to="
                    + window_to.isoformat().replace("+00:00", "Z"),
                    8,
                ),
                "filtro_accion": api_timing(
                    env,
                    auditor_token,
                    "auditoria",
                    "/api/v1/events?page_size=20&action=" + actions[3],
                    8,
                ),
            }
            time.sleep(1)
            usage_after = index_usage(conn)
            point["index_scans_during_api"] = {
                k: usage_after.get(k, 0) - usage_before.get(k, 0)
                for k in usage_after
                if usage_after.get(k, 0) != usage_before.get(k, 0)
            }
            # Sin índices: DROP INDEX dentro de una transacción que se revierte.
            conn.execute("SET lock_timeout = '10s'")
            with conn.transaction(force_rollback=True):
                names = [
                    r[0]
                    for r in conn.execute(
                        "SELECT indexname FROM pg_indexes WHERE schemaname='red_house' AND tablename='audit_event' AND indexname <> 'audit_event_pkey'"
                    ).fetchall()
                ]
                for index in names:
                    conn.execute(f'DROP INDEX red_house."{index}"')
                conn.execute("SET LOCAL search_path = access_auditoria, pg_catalog")
                point["without_index"] = explain_set(conn, queries)
                point["dropped_indexes"] = names
            conn.execute("SET search_path = DEFAULT")
            report["audit_sql"]["checkpoints"].append(point)
            (evidence / "volume.partial.json").write_text(
                json.dumps(report, indent=2, default=str)
            )
    report["audit_sql"]["copy_total"] = {
        "rows": inserted - 20000,
        "copy_seconds": round(copy_seconds, 2),
        "generation_seconds": round(gen_seconds, 2),
        "rows_per_second": round((inserted - 20000) / copy_seconds),
    }
    # 3) MongoDB: proyección documental de Auditoría.
    with MongoClient(st["mongo_admin"], serverSelectionTimeoutMS=3000) as client:
        collection = client["rh_auditoria"].events
        report["mongo"]["initial_count"] = collection.count_documents({})
        report["mongo"]["indexes"] = list(collection.index_information())
        done = 0
        for checkpoint in (10000, 50000, docs_target):
            with Sampler(env) as sampler:
                spent = 0.0
                stage = 0
                while done < checkpoint:
                    count = min(5000, checkpoint - done)
                    docs = []
                    for i in range(done, done + count):
                        event_id = str(uuid4())
                        docs.append(
                            {
                                "_id": event_id,
                                "event_id": event_id,
                                "source": "inventario",
                                "action": actions[i % len(actions)],
                                "tenant_id": tenants[i % 2],
                                "region_id": region,
                                "actor_id": actors[i % len(actors)],
                                "resource_id": str(uuid4()),
                                "occurred_at": (
                                    base_time + timedelta(seconds=i)
                                ).isoformat(),
                                "metadata": {"synthetic": True},
                            }
                        )
                    begin = time.perf_counter()
                    collection.insert_many(docs, ordered=False)
                    spent += time.perf_counter() - begin
                    stage += count
                    done += count
            point = {
                "documents": collection.count_documents({}),
                "insert_stage": {
                    "documents": stage,
                    "seconds": round(spent, 2),
                    "documents_per_second": round(stage / spent),
                    "resources": sampler.summary(),
                },
                "storage": {
                    k: client["rh_auditoria"].command("collStats", "events").get(k)
                    for k in ("size", "storageSize", "totalIndexSize", "count")
                },
            }

            def explain_mongo():
                find = (
                    collection.find({"region_id": region}, {"_id": 0})
                    .sort("_id", 1)
                    .skip(0)
                    .limit(20)
                    .explain()
                )
                count = client["rh_auditoria"].command(
                    "explain",
                    {"count": "events", "query": {"region_id": region}},
                    verbosity="executionStats",
                )

                def brief(value):
                    stats = value.get("executionStats", {})
                    winning = value.get("queryPlanner", {}).get("winningPlan", {})
                    return {
                        "executionTimeMillis": stats.get("executionTimeMillis"),
                        "totalDocsExamined": stats.get("totalDocsExamined"),
                        "totalKeysExamined": stats.get("totalKeysExamined"),
                        "winningPlan": json.loads(json.dumps(winning, default=str)),
                    }

                return {"find_page": brief(find), "count": brief(count)}

            point["with_index"] = explain_mongo()
            auditor_token = api_login(env, "auditor1")
            point["api"] = api_timing(
                env,
                auditor_token,
                "auditoria",
                "/api/v1/documentary-events?page_size=20",
                8,
            )
            index_name = "region_id_1_source_1"
            if index_name in collection.index_information():
                collection.drop_index(index_name)
                try:
                    point["without_index"] = explain_mongo()
                    point["api_without_index"] = api_timing(
                        env,
                        auditor_token,
                        "auditoria",
                        "/api/v1/documentary-events?page_size=20",
                        8,
                    )
                finally:
                    collection.create_index([("region_id", 1), ("source", 1)])
            report["mongo"]["checkpoints"].append(point)
    # 4) Caché Redis de lectura (Inventario) con y sin bypass.
    operator_token = api_login(env, "operator1")
    report["cache"] = {
        "endpoint": "inventario GET /api/v1/resources?page_size=20 (operator1)",
        "activa": api_timing(
            env, operator_token, "inventario", "/api/v1/resources?page_size=20", 60
        ),
        "bypass": api_timing(
            env,
            operator_token,
            "inventario",
            "/api/v1/resources?page_size=20",
            60,
            headers={"Cache-Control": "no-cache"},
        ),
    }
    with psycopg.connect(admin_dsn, autocommit=True) as conn:
        report["inventory_rows"] = conn.execute(
            "SELECT count(*) FROM red_house.resource"
        ).fetchone()[0]
    # 5) Sin Redis: se detiene solo el Redis propio del laboratorio.
    redis_pid = st["infrastructure_pids"]["redis"]
    os.kill(redis_pid, signal.SIGTERM)
    time.sleep(2)
    without = {}
    for label, service, path, token in (
        (
            "inventario_resources",
            "inventario",
            "/api/v1/resources?page_size=20",
            operator_token,
        ),
        ("auditoria_events", "auditoria", "/api/v1/events?page_size=20", auditor_token),
    ):
        url = st["urls"][service].rstrip("/") + path
        begin = time.perf_counter()
        try:
            response = requests.get(
                url,
                headers={
                    "Authorization": "Bearer " + token,
                    "Accept": "application/json",
                },
                timeout=(5, 15),
                proxies={"http": None, "https": None},
            )
            code = response.status_code
            error = (
                response.json().get("error", {}).get("code")
                if response.content
                else None
            )
        except requests.RequestException as exc:
            code, error = None, type(exc).__name__
        without[label] = {
            "status": code,
            "error_code": error,
            "elapsed_ms": round((time.perf_counter() - begin) * 1000, 1),
        }
    ready = requests.get(
        st["urls"]["inventario"].rstrip("/") + "/health/ready",
        timeout=(5, 15),
        proxies={"http": None, "https": None},
    )
    without["inventario_health_ready"] = {
        "status": ready.status_code,
        "redis": ready.json().get("data", {}).get("dependencies", {}).get("redis"),
    }
    report["without_redis"] = without
    report["finished_utc"] = now_iso()
    return report


# --- Principal ----------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--mongod", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20261113)
    parser.add_argument("--seconds", type=int, default=120)
    parser.add_argument("--recovery-seconds", type=int, default=60)
    parser.add_argument("--read-users", default="12,24,36")
    parser.add_argument("--mixed-users", default="12,24,36,48")
    parser.add_argument("--rows", type=int, default=1000000)
    parser.add_argument("--docs", type=int, default=100000)
    parser.add_argument("--skip-load", action="store_true")
    parser.add_argument("--skip-volume", action="store_true")
    parser.add_argument(
        "--account-scale",
        type=int,
        default=1,
        help="Multiplica las cuentas por rol (estrés)",
    )
    parser.add_argument("--mixed-recovery-users", type=int, default=12)
    parser.add_argument("--pause", type=int, default=20, help="Segundos entre fases")
    args = parser.parse_args()
    for name in (
        "PGHOSTADDR",
        "PGSERVICE",
        "PGOPTIONS",
        "REDHOUSE_ENV",
        "GOOGLE_APPLICATION_CREDENTIALS",
        "GCS_BUCKET",
    ):
        if name in os.environ:
            raise RuntimeError(
                "Quitar variables de conexión o nube ajenas al laboratorio"
            )
    evidence = args.evidence.resolve()
    evidence.mkdir(parents=True, exist_ok=True)
    parent = Path("/tmp").resolve(strict=True)
    if shutil.disk_usage(parent).free < MIN_FREE + 3 * 1024**3:
        raise RuntimeError("Espacio libre insuficiente")
    directory = Path(tempfile.mkdtemp(prefix="rh-final-", dir=parent))
    os.chmod(directory, 0o700)
    print("Laboratorio:", directory, flush=True)
    summary = {
        "started_utc": now_iso(),
        "laboratory": "/private/tmp/rh-final-* (borrado al terminar)",
        "phases": [],
    }
    env = Environment(directory, str(args.mongod))
    try:
        env.init()
        validate_environment(env)
        report = {}
        populate(env, report, args.seed, 10)
        summary["dataset"] = {
            "counts": report["counts"],
            "insertion_ms": report["insertion_ms"],
        }
        fixture = make_fixture(env, args.account_scale)
        summary["accounts_by_role"] = {
            r: len(a) for r, a in fixture["accounts"].items()
        }
        os.environ.update(NO_PROXY="127.0.0.1", no_proxy="127.0.0.1")
        env.start()
        factors = enroll(env, fixture)
        summary["mfa_enrolled"] = len(factors)
        time.sleep(2)
        workdir = directory / "phases"
        workdir.mkdir(mode=0o700)
        if not args.skip_load:
            plan = []
            if args.read_users:
                plan = [
                    ("reads", u, args.seconds, f"lecturas-{u}")
                    for u in map(int, args.read_users.split(","))
                ]
                plan.append(
                    ("reads", 6, args.recovery_seconds, "lecturas-recuperacion-6")
                )
            plan += [
                ("mixed", u, args.seconds, f"mixta-{u}")
                for u in map(int, args.mixed_users.split(","))
            ]
            r = args.mixed_recovery_users
            plan.append(("mixed", r, args.recovery_seconds, f"mixta-recuperacion-{r}"))
            for mode, users, seconds, name in plan:
                print(now_iso(), "fase", name, flush=True)
                result = run_phase(
                    env,
                    factors,
                    workdir,
                    evidence,
                    name=name,
                    mode=mode,
                    users=users,
                    seconds=seconds,
                )
                total = next(
                    (
                        r
                        for r in result.get("measurement", [])
                        if r["name"] == "Aggregated"
                    ),
                    {},
                )
                print(
                    now_iso(),
                    name,
                    "stage",
                    result.get("stage"),
                    "logged",
                    result.get("logged_in"),
                    "req",
                    total.get("requests"),
                    "fail",
                    total.get("failures"),
                    "p95",
                    total.get("p95_ms"),
                    flush=True,
                )
                summary["phases"].append({"name": name, "stage": result.get("stage")})
                (evidence / "summary.json").write_text(
                    json.dumps(summary, indent=2) + "\n"
                )
                time.sleep(args.pause)
        if not args.skip_volume:
            print(now_iso(), "volumen", flush=True)
            result = volume(env, evidence, args.rows, args.docs)
            (evidence / "volume.json").write_text(
                json.dumps(result, indent=2, default=str, ensure_ascii=False) + "\n"
            )
            partial = evidence / "volume.partial.json"
            if partial.exists():
                partial.unlink()
        summary["status"] = "completed"
    except BaseException as exc:  # noqa: BLE001
        summary["status"] = "failed"
        summary["error_type"] = type(exc).__name__
        diagnostic = directory / "final-diagnostic.private.log"
        diagnostic.write_text(traceback.format_exc())
        traceback.print_exc()
    finally:
        try:
            env.stop()
        except BaseException:  # noqa: BLE001
            summary["cleanup_error"] = True
        summary["finished_utc"] = now_iso()
        (evidence / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        print("Directorio a borrar:", directory, flush=True)


if __name__ == "__main__":
    main()
