"""Piloto sintético: crea y usa exclusivamente un laboratorio local nuevo."""

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path
from time import perf_counter
from urllib.parse import urlsplit
from uuid import UUID, uuid5

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import psycopg
import redis
from psycopg.conninfo import conninfo_to_dict
from psycopg.types.json import Jsonb
from pymongo import MongoClient
from scripts.local import Environment

REFERENCE = datetime(2026, 11, 13, 12, tzinfo=timezone.utc)
NAMESPACE = UUID("1ca0d499-10ca-4e72-bd84-855863d07356")
MIN_FREE = 3 * 1024**3
MAX_OWN = 1536 * 1024**2
BATCH = 200
GROUPS = ("O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+")


def identifier(seed, kind, index):
    return uuid5(NAMESPACE, f"{seed}:{kind}:{index}")


def dimensions(seed):
    """Produce datos lógicos reproducibles, sin asignar elegibilidad clínica."""
    donors = [
        (identifier(seed, "donor", i), i % 2, f"PILOT-D-{i:05d}", GROUPS[i % 8])
        for i in range(200)
    ]
    resources = [
        (
            identifier(seed, "resource", i),
            i % 2,
            f"PILOT-R-{i:05d}",
            GROUPS[(i // 2) % 8],
            REFERENCE + timedelta(days=2 + i % 30),
            "AVAILABLE" if i % 4 < 2 else "QUARANTINE",
        )
        for i in range(1000)
    ]
    return donors, resources


def local_url(value, scheme):
    parsed = urlsplit(value)
    if parsed.scheme not in scheme or parsed.hostname != "127.0.0.1" or not parsed.port:
        raise ValueError("El laboratorio exige conexiones loopback explícitas")
    return parsed


def validate_environment(env):
    """Contrasta rutas y procesos propios antes de abrir conexiones de escritura."""
    state = env.state
    directory = env.directory.resolve(strict=True)
    if Path(state["directory"]).resolve(strict=True) != directory:
        raise ValueError("Directorio de laboratorio inconsistente")
    if len(env.processes) != 3 or any(
        process.poll() is not None for process in env.processes
    ):
        raise ValueError("Los motores no pertenecen al laboratorio activo")
    pids = state["infrastructure_pids"]
    if {p.pid for p in env.processes} != set(pids.values()):
        raise ValueError("Procesos del laboratorio inconsistentes")
    admin = local_url(state["database_admin"], {"postgres", "postgresql"})
    admin_options = conninfo_to_dict(state["database_admin"])
    if (
        admin_options.get("host") != "127.0.0.1"
        or admin_options.get("port") != str(admin.port)
        or any(admin_options.get(k) for k in ("hostaddr", "service", "options"))
    ):
        raise ValueError("DSN administrativo inválido")
    for service, dsn in state["database_owners"].items():
        parsed = local_url(dsn, {"postgres", "postgresql"})
        options = conninfo_to_dict(dsn)
        if (
            parsed.port != admin.port
            or options.get("host") != "127.0.0.1"
            or options.get("port") != str(admin.port)
            or options.get("dbname") != "red_house"
            or options.get("hostaddr")
            or options.get("service")
            or options.get("options") != f"-csearch_path=access_{service},pg_catalog"
        ):
            raise ValueError("DSN de propietario no corresponde al clúster privado")
    local_url(state["redis_admin"], {"redis"})
    local_url(state["mongo_admin"], {"mongodb"})
    with psycopg.connect(state["database_admin"], connect_timeout=2) as conn:
        pgdir = Path(conn.execute("SHOW data_directory").fetchone()[0]).resolve()
        if pgdir != directory / "pg":
            raise ValueError("PostgreSQL no pertenece al laboratorio")
    with redis.Redis.from_url(
        state["redis_admin"], socket_connect_timeout=2, socket_timeout=2
    ) as client:
        info = client.info("server")
        config_file = info.get("config_file", b"")
        if isinstance(config_file, bytes):
            config_file = config_file.decode()
        if (
            Path(config_file).resolve() != directory / "redis.conf"
            or info["process_id"] != pids["redis"]
        ):
            raise ValueError("Redis no pertenece al laboratorio")
    with MongoClient(state["mongo_admin"], serverSelectionTimeoutMS=2000) as client:
        options = client.admin.command("getCmdLineOpts")["parsed"]
        pid = client.admin.command("serverStatus")["pid"]
        if (
            Path(options["storage"]["dbPath"]).resolve() != directory / "mongo"
            or pid != pids["mongodb"]
        ):
            raise ValueError("MongoDB no pertenece al laboratorio")


def own_bytes(directory):
    total = 0
    for root, dirs, files in os.walk(directory, followlinks=False):
        for name in dirs + files:
            path = Path(root) / name
            info = path.lstat()
            if path.is_symlink():
                raise ValueError("Enlace inesperado dentro del laboratorio")
            total += info.st_size if path.is_file() else 0
    return total


def budget(directory):
    free = shutil.disk_usage(directory).free
    used = own_bytes(directory)
    if free < MIN_FREE or used > MAX_OWN:
        raise RuntimeError("Límite de espacio del laboratorio alcanzado")
    return {"free_bytes": free, "owned_bytes": used}


def chunks(values):
    for i in range(0, len(values), BATCH):
        yield values[i : i + BATCH]


def populate(env, report, seed):
    state = env.state
    donors, resources = dimensions(seed)
    tenants, region = state["tenants"], state["region_id"]
    report["dataset_sha256"] = hashlib.sha256(
        json.dumps([donors, resources], default=str, separators=(",", ":")).encode()
    ).hexdigest()
    report["committed"] = {"donors": 0, "resources": 0, "events": 0}
    report["phase"] = "donors"
    started = perf_counter()
    with psycopg.connect(state["database_owners"]["donantes"]) as conn:
        for batch in chunks(donors):
            budget(env.directory)
            with conn.transaction(), conn.cursor() as cur:
                cur.executemany(
                    "INSERT INTO donors(id,tenant_id,folio,display_name,blood_group,consent,status,created_at) VALUES(%s,%s,%s,%s,%s,true,'PRELIMINARY',%s)",
                    [
                        (
                            key,
                            tenants[tenant],
                            folio,
                            "Donante sintético",
                            group,
                            REFERENCE,
                        )
                        for key, tenant, folio, group in batch
                    ],
                )
            report["committed"]["donors"] += len(batch)
            budget(env.directory)
    with psycopg.connect(state["database_owners"]["inventario"]) as conn:
        report["phase"] = "resources"
        for batch in chunks(resources):
            budget(env.directory)
            with conn.transaction(), conn.cursor() as cur:
                cur.executemany(
                    "INSERT INTO resources(id,tenant_id,current_institution_id,region_id,folio,kind,component,blood_group,expires_at,status,created_at) VALUES(%s,%s,%s,%s,%s,'BLOOD','RBC',%s,%s,%s,%s)",
                    [
                        (
                            key,
                            tenants[tenant],
                            tenants[tenant],
                            region,
                            folio,
                            group,
                            expiry,
                            status,
                            REFERENCE,
                        )
                        for key, tenant, folio, group, expiry, status in batch
                    ],
                )
            report["committed"]["resources"] += len(batch)
            budget(env.directory)
        report["phase"] = "events"
        for group in range(50):
            budget(env.directory)
            rows = []
            for i in range(group * BATCH, (group + 1) * BATCH):
                resource, tenant, *_ = resources[i % len(resources)]
                event_id = identifier(seed, "event", i)
                when = REFERENCE + timedelta(seconds=i)
                event = {
                    "event_id": str(event_id),
                    "source": "inventario",
                    "action": "SYNTHETIC_TRACE",
                    "resource_id": str(resource),
                    "tenant_id": str(tenants[tenant]),
                    "region_id": str(region),
                    "occurred_at": when.isoformat(),
                    "metadata": {"synthetic": True},
                }
                rows.append((event_id, tenants[tenant], Jsonb(event), when))
            with conn.transaction(), conn.cursor() as cur:
                cur.executemany(
                    "INSERT INTO activity_events(id,tenant_id,event,created_at) VALUES(%s,%s,%s,%s)",
                    rows,
                )
            report["committed"]["events"] += len(rows)
            budget(env.directory)
        report["phase"] = "measurements"
        report["insertion_ms"] = round((perf_counter() - started) * 1000, 3)
        database_name = conninfo_to_dict(state["database_owners"]["inventario"])[
            "dbname"
        ]
        admin_dsn = psycopg.conninfo.make_conninfo(
            state["database_admin"], dbname=database_name
        )
        with psycopg.connect(admin_dsn, connect_timeout=2, autocommit=True) as admin:
            admin.execute("ANALYZE red_house.resource")
            admin.execute("ANALYZE red_house.service_activity_events")
        report["plans"] = {
            "availability": conn.execute(
                "EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) SELECT id FROM resources WHERE region_id=%s AND status='AVAILABLE' AND expires_at>%s ORDER BY expires_at,id LIMIT 20",
                (region, REFERENCE),
            ).fetchone()[0],
            "trace": conn.execute(
                "EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) SELECT id FROM activity_events WHERE event->>'resource_id'=%s ORDER BY created_at,id LIMIT 2000",
                (str(resources[0][0]),),
            ).fetchone()[0],
        }
        report["indexes"] = conn.execute(
            "SELECT tablename,indexname,indexdef FROM pg_indexes WHERE schemaname='red_house' AND tablename IN ('resource','service_activity_events') ORDER BY tablename,indexname"
        ).fetchall()
        report["counts"] = {
            "resources": conn.execute(
                "SELECT count(*) FROM resources WHERE folio LIKE 'PILOT-R-%%'"
            ).fetchone()[0],
            "events": conn.execute(
                "SELECT count(*) FROM activity_events WHERE event->>'action'='SYNTHETIC_TRACE'"
            ).fetchone()[0],
        }
        report["resource_statuses"] = conn.execute(
            "SELECT status,count(*) FROM resources WHERE folio LIKE 'PILOT-R-%%' GROUP BY status ORDER BY status"
        ).fetchall()
        report["linked_resources"] = conn.execute(
            "SELECT count(DISTINCT event->>'resource_id') FROM activity_events WHERE event->>'action'='SYNTHETIC_TRACE'"
        ).fetchone()[0]
        report["database_bytes"] = conn.execute(
            "SELECT pg_database_size(current_database())"
        ).fetchone()[0]
        report["relation_bytes"] = conn.execute(
            "SELECT pg_total_relation_size('red_house.resource'),pg_total_relation_size('red_house.service_activity_events')"
        ).fetchone()
    with psycopg.connect(state["database_owners"]["donantes"]) as conn:
        report["counts"]["donors"] = conn.execute(
            "SELECT count(*) FROM donors WHERE folio LIKE 'PILOT-D-%%'"
        ).fetchone()[0]
    if (
        report["counts"] != {"donors": 200, "resources": 1000, "events": 10000}
        or report["linked_resources"] != 1000
    ):
        raise RuntimeError("Conteos del piloto inesperados")
    report["disk"] = budget(env.directory)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20261113)
    parser.add_argument("--mongod", type=Path)
    args = parser.parse_args()
    if any(name in os.environ for name in ("PGHOSTADDR", "PGSERVICE", "PGOPTIONS")):
        raise RuntimeError(
            "Quitar las variables libpq que alteran el destino o la sesión"
        )
    parent = Path("/tmp").resolve(strict=True)
    if shutil.disk_usage(parent).free < MIN_FREE:
        raise RuntimeError("Espacio libre insuficiente antes de iniciar")
    directory = Path(tempfile.mkdtemp(prefix="rh-load-", dir=parent))
    os.chmod(directory, 0o700)
    report_path = directory / "pilot-report.json"
    report = {
        "status": "started",
        "seed": args.seed,
        "reference": REFERENCE.isoformat(),
        "expected": {"donors": 200, "resources": 1000, "events": 10000},
        "notice": "Datos sintéticos por SQL; no son registros API ni decisiones clínicas.",
    }
    env = Environment(directory, str(args.mongod) if args.mongod else None)
    diagnostics = []
    try:
        report["initial_disk"] = budget(directory)
        env.init()
        report["initialized_disk"] = budget(directory)
        validate_environment(env)
        with psycopg.connect(env.state["database_owners"]["inventario"]) as conn:
            report["initialized_database_bytes"] = conn.execute(
                "SELECT pg_database_size(current_database())"
            ).fetchone()[0]
        populate(env, report, args.seed)
        report["database_delta_bytes"] = (
            report["database_bytes"] - report["initialized_database_bytes"]
        )
        report["owned_delta_bytes"] = (
            report["disk"]["owned_bytes"] - report["initialized_disk"]["owned_bytes"]
        )
        report["status"] = "prepared"
    except BaseException as exc:  # noqa: BLE001 - retain failure evidence, including interruption
        report["status"] = "failed"
        report["error_type"] = type(exc).__name__
        diagnostics.append(traceback.format_exc())
    finally:
        try:
            env.stop()
        except BaseException as exc:  # noqa: BLE001 - preserve cleanup failure and report
            report["status"] = "failed"
            report["cleanup_error_type"] = type(exc).__name__
            diagnostics.append(traceback.format_exc())
        if diagnostics:
            try:
                descriptor = os.open(
                    directory / "pilot-diagnostic.private.log",
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                    0o600,
                )
                with os.fdopen(descriptor, "w") as stream:
                    stream.write("\n".join(diagnostics))
            except OSError:
                report["diagnostic_write_failed"] = True
        report_path.write_text(json.dumps(report, indent=2, default=str) + "\n")
        os.chmod(report_path, 0o600)
        print("Informe privado:", report_path)
    if report["status"] != "prepared":
        raise RuntimeError(
            "Preparación aislada fallida; consultar el informe privado"
        ) from None


if __name__ == "__main__":
    main()
