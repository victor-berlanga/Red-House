"""Lectura sostenida aislada; llamada únicamente con Environment propio y activo."""

import hashlib
import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

import psycopg
import redis
import requests
from ms_identidad_acceso.strong_auth import totp
from psycopg.conninfo import conninfo_to_dict
from redhouse.config import SERVICES, settings
from scripts.load_client import isolated_urls
from scripts.load_guard import guard_diagnostic
from tests.load_support import verify_new_sessions

ROOT = Path(__file__).resolve().parents[1]
PROFILES = ("medical2", "operator1", "coordinator1", "auditor1", "donor1", "transport1")
MFA_PROFILES = ("medical2", "coordinator1")


def source_hashes(env):
    paths = [
        ROOT / "run.py",
        ROOT / "worker.py",
        ROOT / "redhouse/config.py",
        ROOT / "tests/locustfile.py",
        ROOT / "tests/locust_sustained.py",
        ROOT / "scripts/sustained_read.py",
        ROOT / "scripts/load_client.py",
        ROOT / "scripts/load_guard.py",
    ]
    paths.extend(env.directory / f"{service}.json" for service in SERVICES)
    return {
        str(path.relative_to(ROOT))
        if path.is_relative_to(ROOT)
        else "config/" + path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in paths
    }


def topology(env):
    urls = isolated_urls(env.state["urls"])
    if set(urls) != set(SERVICES) or any(
        not url.startswith("http://127.0.0.1:") for url in urls.values()
    ):
        raise ValueError("Destinos del laboratorio inválidos")
    output = {}
    postgres_port = urlsplit(env.state["database_admin"]).port
    redis_port = urlsplit(env.state["redis_admin"]).port
    mongo_port = urlsplit(env.state["mongo_admin"]).port
    for service in SERVICES:
        configuration = json.loads((env.directory / f"{service}.json").read_text())
        actual = settings(service, configuration)
        if (
            actual["TESTING"]
            or actual["RATE_LIMIT"] != 180
            or actual["INTERNAL_RATE_LIMIT"] != 1800
        ):
            raise ValueError("Configuración de prueba o cuotas distintas")
        if not actual.get("WORKER_REQUIRED"):
            raise ValueError("Workers requeridos")
        if actual.get("STORAGE_PROVIDER") not in ("", "local") or actual.get(
            "GCS_BUCKET"
        ):
            raise ValueError("Almacenamiento de nube no permitido")
        for name, port in (("DATABASE_URL", postgres_port), ("REDIS_URL", redis_port)):
            parsed = urlsplit(actual[name])
            if parsed.hostname != "127.0.0.1" or parsed.port != port:
                raise ValueError("Dependencia ajena al laboratorio")
        database = conninfo_to_dict(actual["DATABASE_URL"])
        if (
            database.get("host") != "127.0.0.1"
            or database.get("port") != str(postgres_port)
            or database.get("dbname") != "red_house"
            or database.get("hostaddr")
            or database.get("service")
        ):
            raise ValueError("DSN de servicio ajeno al laboratorio")
        if configuration.get("MONGODB_URL"):
            parsed = urlsplit(configuration["MONGODB_URL"])
            if parsed.hostname != "127.0.0.1" or parsed.port != mongo_port:
                raise ValueError("MongoDB ajeno al laboratorio")
        if actual["SERVICE_URLS"] != urls:
            raise ValueError("Rutas internas ajenas al laboratorio")
        if service == "identidad_acceso" and not {
            "ADMIN",
            "MEDICAL",
            "COORDINATOR",
        }.issubset(actual["MFA_REQUIRED_ROLES"]):
            raise ValueError("MFA obligatorio ausente")
        output[service] = {
            "server_from_run_py": "gevent-pool96"
            if service == "transporte"
            else "waitress-threads8",
            "rate_limit": actual["RATE_LIMIT"],
            "internal_rate_limit": actual["INTERNAL_RATE_LIMIT"],
            "database_pool_size": actual.get("DATABASE_POOL_SIZE", 0),
            "testing": actual["TESTING"],
        }
    return output


def runtime_topology(env):
    launched = {process.pid: process for process in env.processes}
    result = {}
    for service in SERVICES:
        api_pid = env.state["service_pids"][service]
        worker_pid = env.state["worker_pids"][service]
        api = launched.get(api_pid)
        worker = launched.get(worker_pid)
        config = str(env.directory / f"{service}.json")
        if not api or not worker or api.poll() is not None or worker.poll() is not None:
            raise ValueError("Proceso propio ausente")
        if api.args != [
            sys.executable,
            str(ROOT / "run.py"),
            service,
            "--config",
            config,
        ]:
            raise ValueError("Argumentos API inesperados")
        if worker.args != [
            sys.executable,
            str(ROOT / "worker.py"),
            service,
            "--config",
            config,
        ]:
            raise ValueError("Argumentos worker inesperados")
        port = urlsplit(env.state["urls"][service]).port
        listener = subprocess.run(
            [
                "lsof",
                "-nP",
                "-a",
                "-p",
                str(api_pid),
                f"-iTCP:{port}",
                "-sTCP:LISTEN",
                "-Fpn",
            ],
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        ).stdout.splitlines()
        if f"p{api_pid}" not in listener or f"n127.0.0.1:{port}" not in listener:
            raise ValueError("Listener API ajeno o ausente")
        result[service] = {
            "api_pid": api_pid,
            "worker_pid": worker_pid,
            "api_argv": api.args,
            "worker_argv": worker.args,
            "listener": f"127.0.0.1:{port}",
        }
    return result


def enroll_factors(env):
    base = env.state["urls"]["identidad_acceso"].rstrip("/")
    factors = {}
    with requests.Session() as session:
        session.trust_env = False
        for username in MFA_PROFILES:
            body = {"username": username, "password": env.state["password"]}
            response = session.post(
                base + "/api/v1/auth/mfa/enrollment",
                json=body,
                timeout=(5, 10),
                allow_redirects=False,
            )
            if response.status_code != 200:
                raise RuntimeError("No se pudo enrolar MFA sintético")
            value = response.json()["data"]
            secret, challenge = value["secret"], value["challenge"]
            response = session.post(
                base + "/api/v1/auth/mfa/confirm",
                json={
                    "challenge": challenge,
                    "code": totp(secret, int(time.time()) // 30),
                },
                timeout=(5, 10),
                allow_redirects=False,
            )
            if response.status_code != 200:
                raise RuntimeError("No se pudo confirmar MFA sintético")
            factors[username] = secret
    return factors


def wait_counter_after(previous):
    deadline = time.monotonic() + 35
    while int(time.time()) // 30 <= previous:
        if time.monotonic() >= deadline:
            raise RuntimeError("El reloj no avanzó al siguiente periodo MFA")
        time.sleep(0.25)


def session_rows(env, user_ids):
    with psycopg.connect(env.state["database_owners"]["identidad_acceso"]) as conn:
        return conn.execute(
            "SELECT id,user_id,revoked_at FROM sessions WHERE user_id=ANY(%s::uuid[])",
            (user_ids,),
        ).fetchall()


def process_sample(env, locust):
    roots = {p.pid for p in env.processes if p.poll() is None} | {locust.pid}
    try:
        result = subprocess.run(
            ["ps", "-axo", "pid=,ppid=,rss=,pcpu="],
            capture_output=True,
            text=True,
            timeout=3,
            check=True,
        )
        rows = [line.split() for line in result.stdout.splitlines() if line.strip()]
        indexed = {
            int(row[0]): (int(row[1]), int(row[2]), float(row[3])) for row in rows
        }
        selected = set(roots)
        while True:
            expanded = selected | {
                pid for pid, (parent, _, _) in indexed.items() if parent in selected
            }
            if expanded == selected:
                break
            selected = expanded
        sampled = [indexed[pid] for pid in selected if pid in indexed]
        return {
            "rss_sum_kib": sum(row[1] for row in sampled),
            "ps_cpu_percent_sum": sum(row[2] for row in sampled),
            "sampled_processes": len(sampled),
            "root_processes_missing": len(roots - set(indexed)),
        }
    except (OSError, ValueError, IndexError, subprocess.SubprocessError):
        return {"unavailable": True}


def check_budget(budget, directory, started):
    try:
        sample = budget(directory)
    except (OSError, ValueError, RuntimeError) as error:
        return None, {
            **guard_diagnostic(error),
            "utc": datetime.now(timezone.utc).isoformat(),
            "elapsed_seconds": round(time.monotonic() - started, 3),
        }
    return {
        **sample,
        "utc": datetime.now(timezone.utc).isoformat(),
        "elapsed_seconds": round(time.monotonic() - started, 3),
    }, None


def sample_or_interrupt(budget, directory, started, process):
    sample, failure = check_budget(budget, directory, started)
    if failure is not None:
        try:
            process.send_signal(signal.SIGINT)
        except ProcessLookupError:
            pass
    return sample, failure


def run_phase(env, factors, directory, budget):
    output = directory / "run"
    output.mkdir(mode=0o700)
    user_ids = [env.state["accounts"][name]["id"] for name in PROFILES]
    if len(set(user_ids)) != 6:
        raise ValueError("Seis identidades independientes requeridas")
    previous_ids = {str(row[0]) for row in session_rows(env, user_ids)}
    read_fd, write_fd = os.pipe()
    os.write(write_fd, json.dumps(factors).encode())
    os.close(write_fd)
    marker = output / "phase.json"
    environment = dict(
        os.environ,
        REDHOUSE_LOAD_ISOLATED="1",
        REDHOUSE_LOAD_STATE=str(env.directory / "state.json"),
        REDHOUSE_LOAD_MFA_FD=str(read_fd),
        REDHOUSE_LOAD_MARKER=str(marker),
    )
    environment.pop("REDHOUSE_LOAD_NO_CACHE", None)
    command = [
        sys.executable,
        "-m",
        "locust",
        "-f",
        str(ROOT / "tests/locust_sustained.py"),
        "--headless",
        "--users",
        "6",
        "--spawn-rate",
        "6",
        "--run-time",
        "210s",
        "--stop-timeout",
        "30",
        "--host",
        "http://127.0.0.1",
        "--csv",
        str(output / "run"),
        "--csv-full-history",
        "--json-file",
        str(output / "final"),
        "--exit-code-on-error",
        "1",
        "--only-summary",
        "SustainedUser",
    ]
    result = {
        "warmup_seconds": 30,
        "measurement_seconds": 120,
        "users": 6,
        "disk_samples": [],
        "stopped_by_guard": False,
        "session_revocation_verified": False,
    }
    log = output / "runner.private.log"
    process = None
    try:
        with log.open("wb") as stream:
            os.chmod(log, 0o600)
            process = subprocess.Popen(
                command,
                cwd=ROOT,
                env=environment,
                stdout=stream,
                stderr=subprocess.STDOUT,
                pass_fds=(read_fd,),
            )
            os.close(read_fd)
            read_fd = None
            started = time.monotonic()
            deadline = started + 245
            while process.poll() is None:
                sample, guard_error = sample_or_interrupt(
                    budget, env.directory, started, process
                )
                if guard_error is None:
                    sample["processes"] = process_sample(env, process)
                    result["disk_samples"].append(sample)
                else:
                    result["stopped_by_guard"] = True
                    result["guard_interruption"] = guard_error
                    break
                if time.monotonic() > deadline:
                    result["timed_out"] = True
                    result["interruption"] = {
                        "category": "timeout",
                        "utc": datetime.now(timezone.utc).isoformat(),
                        "elapsed_seconds": round(time.monotonic() - started, 3),
                    }
                    process.send_signal(signal.SIGINT)
                    break
                if time.monotonic() - started > 45 and not marker.exists():
                    result["startup_timeout"] = True
                    result["interruption"] = {
                        "category": "startup_timeout",
                        "utc": datetime.now(timezone.utc).isoformat(),
                        "elapsed_seconds": round(time.monotonic() - started, 3),
                    }
                    process.send_signal(signal.SIGINT)
                    break
                time.sleep(2)
            try:
                process.wait(timeout=40)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
                result["forced_kill"] = True
        result["runner_exit"] = process.returncode
    finally:
        if read_fd is not None:
            os.close(read_fd)
        if process is not None and process.poll() is None:
            process.kill()
            process.wait(timeout=5)
        try:
            prefix = settings("identidad_acceso", env.configs["identidad_acceso"])[
                "REDIS_PREFIX"
            ]
            with redis.Redis.from_url(
                env.state["redis_admin"], socket_timeout=3
            ) as client:
                verify_new_sessions(
                    previous_ids, session_rows(env, user_ids), user_ids, prefix, client
                )
            result["session_revocation_verified"] = True
        except Exception:  # noqa: BLE001 - no credentials in report
            result["session_revocation_verified"] = False
        final = output / "final.json"
        if final.exists():
            try:
                rows = json.loads(final.read_text())
                result["failures"] = sum(int(row["num_failures"]) for row in rows)
                result["counts"] = {
                    row["name"]: int(row["num_requests"]) for row in rows
                }
            except (ValueError, TypeError, KeyError):
                result["final_statistics_invalid"] = True
        if marker.exists():
            try:
                result["timing"] = json.loads(marker.read_text())
                measured = result["timing"].get("measurement")
                if isinstance(measured, list):
                    stats_path = output / "measurement.json"
                    stats_path.write_text(json.dumps(measured, indent=2) + "\n")
                    stats_path.chmod(0o600)
                    result["measurement_failures"] = sum(
                        int(row["failures"]) for row in measured
                    )
                    result["measurement_counts"] = {
                        row["name"]: int(row["requests"]) for row in measured
                    }
            except (ValueError, OSError, TypeError, KeyError):
                result["timing_invalid"] = True
        (output / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
        (output / "summary.json").chmod(0o600)
    timing = result.get("timing", {})
    reads = (
        "inventario / Disponibilidad regional",
        "inventario / Inventario propio",
        "priorizacion_geografia / Rutas",
        "auditoria / Bitácora",
        "donantes / Agenda propia",
        "transporte / Tareas propias",
    )
    if (
        result.get("runner_exit") != 0
        or result["stopped_by_guard"]
        or not result["session_revocation_verified"]
        or result.get("failures") != 0
        or result.get("measurement_failures") != 0
        or result.get("counts", {}).get("Identidad / revocación al salir") != 6
        or any(result.get("measurement_counts", {}).get(name, 0) <= 0 for name in reads)
        or timing.get("stage") != "finished"
        or timing.get("warmup", {}).get("failures") != 0
        or timing.get("warmup", {}).get("requests", 0) <= 0
        or timing.get("warmup_min_users") != 6
        or timing.get("measurement_min_users") != 6
        or timing.get("user_errors") != 0
        or timing.get("measured", 0) - timing.get("started", 0) < 30
        or timing.get("finished", 0) - timing.get("measured", 0) < 120
    ):
        raise RuntimeError("La fase sostenida no completó las verificaciones")
    return result


def run(env, budget):
    directory = env.directory / "sustained-read"
    directory.mkdir(mode=0o700)
    summary = {"status": "failed"}
    try:
        config = topology(env)
        before_hashes = source_hashes(env)
        summary["hashes_before"] = before_hashes
        (directory / "topology.json").write_text(json.dumps(config, indent=2) + "\n")
        (directory / "topology.json").chmod(0o600)
        budget(env.directory)
        previous_no_proxy = {
            name: os.environ.get(name) for name in ("NO_PROXY", "no_proxy")
        }
        try:
            for name in previous_no_proxy:
                os.environ[name] = "127.0.0.1"
            env.start()
        finally:
            for name, value in previous_no_proxy.items():
                if value is None:
                    os.environ.pop(name, None)
                else:
                    os.environ[name] = value
        budget(env.directory)
        actual_runtime = runtime_topology(env)
        (directory / "runtime.json").write_text(
            json.dumps(actual_runtime, indent=2) + "\n"
        )
        (directory / "runtime.json").chmod(0o600)
        factors = enroll_factors(env)
        wait_counter_after(int(time.time()) // 30)
        run_phase(env, factors, directory, budget)
        after_hashes = source_hashes(env)
        summary["hashes_after"] = after_hashes
        if (
            before_hashes != after_hashes
            or topology(env) != config
            or runtime_topology(env) != actual_runtime
        ):
            raise RuntimeError("Configuración o fuentes cambiaron durante la medición")
        summary["status"] = "passed"
    finally:
        if "hashes_before" in summary and "hashes_after" not in summary:
            try:
                summary["hashes_after"] = source_hashes(env)
            except OSError:
                summary["hashes_after_unavailable"] = True
        (directory / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        (directory / "summary.json").chmod(0o600)
