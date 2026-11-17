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
from tests.load_support import verify_created_sessions_closed, verify_new_sessions

ROOT = Path(__file__).resolve().parents[1]
PROFILES = ("medical2", "operator1", "coordinator1", "auditor1", "donor1", "transport1")
MFA_PROFILES = ("medical2", "coordinator1")


def request_counts(rows, count_field):
    """Keep HTTP totals separate from Locust transaction/drain markers."""
    http, by_method = {}, {}
    for row in rows:
        method, name = row["method"], row["name"]
        count = int(row[count_field])
        group = by_method.setdefault(method, {})
        group[name] = group.get(name, 0) + count
        if method in {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}:
            http[name] = http.get(name, 0) + count
    return http, by_method


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
        ROOT / "scripts/load_workflows.py",
        ROOT / "scripts/prepare_load.py",
        ROOT / "tests/load_support.py",
        ROOT / "tests/load_cleanup.py",
        ROOT / "tests/locust_transactions.py",
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


def evaluate_measurement(measured, failures, cache, *, no_cache, execution_valid):
    p95_values = [
        row["p95_ms"]
        for row in measured
        if row.get("method") == "GET"
        and row.get("requests", 0)
        and row.get("p95_ms") is not None
    ]
    requests_count = sum(row.get("requests", 0) for row in measured)
    cache_verified = bool(
        (
            cache.get("BYPASS", 0) > 0
            and not cache.get("HIT", 0)
            and not cache.get("MISS", 0)
        )
        if no_cache
        else (cache.get("HIT", 0) > 0 and not cache.get("BYPASS", 0))
    )
    accepted = bool(
        execution_valid
        and p95_values
        and requests_count
        and cache_verified
        and max(p95_values) < 2000
        and failures / requests_count < 0.01
    )
    return {
        "max_p95_ms": max(p95_values) if p95_values else None,
        "p95_limit_ms": 2000,
        "cache_mode_verified": cache_verified,
        "measurement_accepted": accepted,
    }


def cleanup_failures(rows):
    if not isinstance(rows, list):
        raise TypeError("Estadísticas finales inválidas")
    return sum(
        int(row["num_failures"])
        for row in rows
        if row.get("method") == "CLEANUP" and row.get("name") == "Cierre / sesiones"
    )


def phase_execution_valid(result, users, seconds):
    timing = result.get("timing", {})
    reads = (
        "inventario / Disponibilidad regional",
        "inventario / Inventario propio",
        "priorizacion_geografia / Rutas",
        "auditoria / Bitácora",
        "donantes / Agenda propia",
        "transporte / Tareas propias",
    )

    return not (
        result.get("runner_exit") != 0
        or result["stopped_by_guard"]
        or not result["session_revocation_verified"]
        or not result.get("session_count_verified")
        or result.get("cleanup_failures") != 0
        or result.get("counts", {}).get("Identidad / revocación al salir") != users
        or any(result.get("measurement_counts", {}).get(name, 0) <= 0 for name in reads)
        or timing.get("stage") != "finished"
        or timing.get("warmup", {}).get("requests", 0) <= 0
        or timing.get("warmup_min_users") != users
        or timing.get("measurement_min_users") != users
        or timing.get("user_errors") != 0
        or timing.get("measured", 0) - timing.get("started", 0) < 30
        or timing.get("finished", 0) - timing.get("measured", 0) < seconds
    )


def record_phase(summary, name, phase):
    summary["phases"].append(
        {
            "name": name,
            "execution_valid": phase["execution_valid"],
            "measurement_accepted": phase["measurement_accepted"],
        }
    )
    if not phase["execution_valid"]:
        raise RuntimeError("La fase no completó las verificaciones del arnés")


def run_phase(
    env,
    factors,
    directory,
    budget,
    *,
    users=6,
    no_cache=False,
    seconds=120,
    name="run",
    mfa_after=-1,
    transactional=False,
    finite_manifest=None,
):
    finite = finite_manifest is not None
    if finite and (users != 3 or seconds != 120 or no_cache or transactional):
        raise ValueError(
            "La cobertura finita exige tres identidades, 120 s y caché normal"
        )
    if not finite and (users not in (6, 12, 24, 36) or seconds not in (60, 120)):
        raise ValueError("Configuración de fase inválida")
    if transactional and (users != 12 or no_cache):
        raise ValueError("La carga transaccional exige 12 identidades y caché normal")
    multiplicity = 1 if (transactional or finite) else users // len(PROFILES)
    auth_timeout = 120 if finite else 45 if transactional else 35 * multiplicity + 15
    output = directory / name
    output.mkdir(mode=0o700)
    fixture = None
    if finite:
        finite_manifest = Path(finite_manifest).resolve()
        if finite_manifest.parent != env.directory.resolve():
            raise ValueError("Manifiesto finito ajeno al laboratorio")
        fixture = json.loads(finite_manifest.read_text())
        if fixture.get("directory") != str(env.directory) or not fixture.get(
            "preparation_complete"
        ):
            raise ValueError("Preparación finita no confirmada")
    user_ids = (
        [a["id"] for a in fixture["accounts"]]
        if finite
        else [a["id"] for a in env.state["load_accounts"]]
        if transactional
        else [env.state["accounts"][name]["id"] for name in PROFILES]
    )
    if len(set(user_ids)) != (3 if finite else 12 if transactional else 6) or len(
        user_ids
    ) != (3 if finite else 12 if transactional else 6):
        raise ValueError("Seis identidades independientes requeridas")
    if finite:
        from tests.load_finite_support import finite_commits

        business_before = finite_commits(env, fixture["accounts"])
    if transactional:
        from tests.load_support import transaction_commits

        business_before = transaction_commits(env, env.state["load_accounts"])
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
        REDHOUSE_LOAD_USERS=str(users),
        REDHOUSE_LOAD_MEASURE_SECONDS=str(seconds),
        REDHOUSE_LOAD_MFA_AFTER=str(mfa_after),
    )
    environment.pop("REDHOUSE_LOAD_FINITE_ROLES", None)
    environment.pop("REDHOUSE_LOAD_FINITE_MANIFEST", None)
    if finite:
        environment["REDHOUSE_LOAD_FINITE_ROLES"] = "1"
        environment["REDHOUSE_LOAD_FINITE_MANIFEST"] = str(finite_manifest)
    if no_cache:
        environment["REDHOUSE_LOAD_NO_CACHE"] = "1"
    else:
        environment.pop("REDHOUSE_LOAD_NO_CACHE", None)
    environment.pop("REDHOUSE_LOAD_TRANSACTIONAL", None)
    if transactional:
        environment["REDHOUSE_LOAD_TRANSACTIONAL"] = "1"
    command = [
        sys.executable,
        "-m",
        "locust",
        "-f",
        str(
            ROOT
            / (
                "tests/locust_transactions.py"
                if transactional or finite
                else "tests/locust_sustained.py"
            )
        ),
        "--headless",
        "--users",
        str(users),
        "--spawn-rate",
        str(users),
        "--run-time",
        str(auth_timeout + 30 + seconds + (60 if transactional or finite else 30))
        + "s",
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
        "0",
        "--only-summary",
        "FiniteRoleUser"
        if finite
        else "TransactionUser"
        if transactional
        else "SustainedUser",
    ]
    result = {
        "warmup_seconds": 30,
        "measurement_seconds": seconds,
        "users": users,
        "cache_mode": "bypass" if no_cache else "active",
        "authentication_timeout_seconds": auth_timeout,
        "disk_samples": [],
        "stopped_by_guard": False,
        "session_revocation_verified": False,
        "workload": "finite-three-roles"
        if finite
        else "transactions"
        if transactional
        else "reads",
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
            deadline = (
                started
                + auth_timeout
                + 30
                + seconds
                + (95 if transactional or finite else 65)
            )
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
                if time.monotonic() - started > auth_timeout and not marker.exists():
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
                rows = session_rows(env, user_ids)
                verify_created_sessions_closed(
                    previous_ids, rows, user_ids, prefix, client
                )
                try:
                    verify_new_sessions(
                        previous_ids,
                        rows,
                        user_ids,
                        prefix,
                        client,
                        multiplicity=multiplicity,
                    )
                    result["session_count_verified"] = True
                except ValueError:
                    result["session_count_verified"] = False
            result["session_revocation_verified"] = True
        except Exception:  # noqa: BLE001 - no credentials in report
            result["session_revocation_verified"] = False
        final = output / "final.json"
        if final.exists():
            try:
                rows = json.loads(final.read_text())
                result["cleanup_failures"] = cleanup_failures(rows)
                result["failures"] = sum(int(row["num_failures"]) for row in rows)
                result["counts"], result["counts_by_method"] = request_counts(
                    rows, "num_requests"
                )
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
                    (
                        result["measurement_counts"],
                        result["measurement_counts_by_method"],
                    ) = request_counts(measured, "requests")
            except (ValueError, OSError, TypeError, KeyError):
                result["timing_invalid"] = True
        if finite:
            try:
                from tests.load_finite_support import verify_finite_persistence

                result["business"] = verify_finite_persistence(
                    env, output, fixture, business_before
                )
            except Exception as error:  # noqa: BLE001 - preserve failed run and always close owned processes
                result["business"] = {
                    "persistence_verified": False,
                    "error_type": type(error).__name__,
                }
        if transactional:
            try:
                from tests.load_support import verify_transaction_persistence

                result["business"] = verify_transaction_persistence(
                    env, output, env.state["load_accounts"], business_before
                )
            except Exception as error:  # noqa: BLE001 - retain failed oracle without private SQL details
                result["business"] = {
                    "persistence_verified": False,
                    "error_type": type(error).__name__,
                }
        (output / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
        (output / "summary.json").chmod(0o600)
    timing = result.get("timing", {})
    if finite:
        result.update(evaluate_finite_transactions(result))
        (output / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
        return result
    if transactional:
        result.update(evaluate_transactions(result, users, seconds))
        (output / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
        return result
    execution_valid = phase_execution_valid(result, users, seconds)
    if result["stopped_by_guard"] or not result["session_revocation_verified"]:
        raise RuntimeError("La fase interrumpió guardas o no revocó sesiones")
    measured = timing.get("measurement", [])
    measured_requests = sum(row.get("requests", 0) for row in measured)
    result["execution_valid"] = execution_valid
    result.update(
        evaluate_measurement(
            measured,
            result.get("measurement_failures", measured_requests),
            timing.get("cache", {}),
            no_cache=no_cache,
            execution_valid=execution_valid,
        )
    )
    (output / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
    (output / "summary.json").chmod(0o600)
    return result


def evaluate_transactions(result, users, seconds):
    timing, business = result.get("timing", {}), result.get("business", {})
    measured = timing.get("measurement", [])
    duration = timing.get("finished", 0) - timing.get("measured", 0)
    http = [
        r for r in measured if r["method"] in ("GET", "POST", "PATCH", "PUT", "DELETE")
    ]
    cycles = [r for r in measured if r["method"] == "TRANSACTION"]
    reads = [r for r in http if r["method"] == "GET" and r["requests"] > 0]
    read_p95 = max((r["p95_ms"] for r in reads), default=None)
    transaction_p95 = max((r["p95_ms"] for r in cycles), default=None)
    profile_targets = {
        r["name"].removeprefix("Recorrido / "): {
            "p95_ms": r["p95_ms"],
            "p99_ms": r["p99_ms"],
            "p95_limit_exclusive_ms": 5000,
            "target_met": r["requests"] > 0 and 0 <= r["p95_ms"] < 5000,
            "completed_per_second": (r["requests"] - r["failures"]) / duration
            if duration > 0
            else 0,
        }
        for r in cycles
    }
    latency_met = (
        read_p95 is not None
        and 0 <= read_p95 < 2000
        and set(profile_targets) == {"DONOR", "OPERATOR"}
        and all(r["target_met"] for r in profile_targets.values())
    )
    http_count = sum(r["requests"] for r in http)
    http_failures = sum(r["failures"] for r in http)
    completed = sum(r["requests"] - r["failures"] for r in cycles)
    measured_by_role = {
        r["name"].removeprefix("Recorrido / "): r["requests"] - r["failures"]
        for r in cycles
    }
    valid = (
        users == 12
        and result.get("runner_exit") == 0
        and not result.get("stopped_by_guard")
        and result.get("session_revocation_verified")
        and result.get("session_count_verified")
        and result.get("cleanup_failures") == 0
        and result.get("failures") == 0
        and result.get("counts", {}).get("Identidad / revocación al salir") == users
        and timing.get("stage") == "finished"
        and timing.get("user_errors") == 0
        and timing.get("warmup_min_users") == users
        and timing.get("measurement_min_users") == users
        and timing.get("measured", 0) - timing.get("started", 0) >= 30
        and duration >= seconds
        and timing.get("warmup", {}).get("requests", 0) > 0
        and timing.get("warmup", {}).get("failures") == 0
        and business.get("persistence_verified")
        and business.get("not_committed") == 0
        and business.get("response_lost_committed") == 0
        and business.get("incomplete_cycles") == 0
        and business.get("replays") == users
        and business.get("unconfirmed_replays") == 0
        and business.get("measured_completed") == measured_by_role
        and {r["name"] for r in cycles if r["requests"] > r["failures"]}
        == {"Recorrido / DONOR", "Recorrido / OPERATOR"}
    )
    return {
        "execution_valid": bool(valid),
        "measurement_accepted": bool(valid and http_failures == 0 and latency_met),
        "latency_targets_met": latency_met,
        "read_p95_max_ms": read_p95,
        "transaction_p95_max_ms": transaction_p95,
        "read_p95_limit_exclusive_ms": 2000,
        "transaction_p95_limit_exclusive_ms": 5000,
        "profile_targets": profile_targets,
        "http_requests": http_count,
        "http_failures": http_failures,
        "http_per_second": http_count / duration if duration > 0 else 0,
        "business_completed": completed,
        "business_per_second": completed / duration if duration > 0 else 0,
        "business_latency": cycles,
        "quota_429": timing.get("http", {}).get("quota_429", 0),
    }


def run_transactions(env, budget):
    """Dos recorridos en el dataset conservado; sin repoblar ni reenrolar MFA."""
    from scripts.prepare_load import source_snapshot
    from tests.load_support import prepare_transaction_fixture

    directory = env.directory / (
        "transactions-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    )
    directory.mkdir(mode=0o700)
    global_before = source_snapshot()
    before = source_hashes(env)
    configuration = topology(env)
    budget(env.directory)
    fixture = prepare_transaction_fixture(env)
    env.state.update(
        load_accounts=fixture["accounts"],
        load_campaign=fixture["prefix"],
        load_profile=fixture["profile_id"],
    )
    env.save()
    old_proxy = {name: os.environ.get(name) for name in ("NO_PROXY", "no_proxy")}
    try:
        os.environ.update(NO_PROXY="127.0.0.1", no_proxy="127.0.0.1")
        env.start()
    finally:
        for key, value in old_proxy.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
    runtime = runtime_topology(env)
    summary = {
        "status": "failed",
        "hashes_before": before,
        "source_hashes_before": global_before,
        "source_scope": "apps/services (.py/.sql/.json/.xsd) y data/database/schema.sql; excluye ocultos, __pycache__ y enlaces",
        "fixture": fixture["prefix"],
        "topology": configuration,
    }
    try:
        phase = run_phase(
            env,
            {},
            directory,
            budget,
            users=12,
            seconds=120,
            name="12-transactions",
            transactional=True,
        )
        summary["phase"] = phase
        if not phase["execution_valid"]:
            raise RuntimeError("La fase transaccional no completó su oráculo")
        if (
            topology(env) != configuration
            or runtime_topology(env) != runtime
            or source_hashes(env) != before
        ):
            raise RuntimeError("Fuentes o topología cambiaron durante la carga")
        summary["status"] = (
            "passed" if phase["measurement_accepted"] else "completed_targets_not_met"
        )
    finally:
        try:
            summary["hashes_after"] = source_hashes(env)
            summary["source_hashes_after"] = source_snapshot()
            summary["source_hashes_match"] = (
                global_before == summary["source_hashes_after"]
            )
            if not summary["source_hashes_match"]:
                summary["status"] = "failed"
                raise RuntimeError("Fuentes globales cambiaron durante la carga")
        except OSError:
            summary["status"] = "failed"
            summary["source_hashes_unavailable"] = True
            raise
        finally:
            (directory / "summary.json").write_text(
                json.dumps(summary, indent=2) + "\n"
            )
            (directory / "summary.json").chmod(0o600)


def run(env, budget, *, series=False):
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
        if series:
            phases = [
                (12, False, 120, "12-active-a"),
                (12, True, 120, "12-bypass-a"),
                (12, False, 120, "12-active-b"),
                (12, True, 120, "12-bypass-b"),
                (24, False, 120, "24-active"),
            ]
            summary["phases"] = []
            for users, no_cache, seconds, name in phases:
                last_counter = int(time.time()) // 30
                wait_counter_after(last_counter)
                phase = run_phase(
                    env,
                    factors,
                    directory,
                    budget,
                    users=users,
                    no_cache=no_cache,
                    seconds=seconds,
                    name=name,
                    mfa_after=last_counter,
                )
                record_phase(summary, name, phase)
            if phase["measurement_accepted"]:
                last_counter = int(time.time()) // 30
                wait_counter_after(last_counter)
                stress = run_phase(
                    env,
                    factors,
                    directory,
                    budget,
                    users=36,
                    seconds=60,
                    name="36-stress",
                    mfa_after=last_counter,
                )
                record_phase(summary, "36-stress", stress)
            else:
                summary["stress_skipped"] = "24 no aceptado"
            last_counter = int(time.time()) // 30
            wait_counter_after(last_counter)
            recovery = run_phase(
                env,
                factors,
                directory,
                budget,
                users=6,
                seconds=60,
                name="6-recovery",
                mfa_after=last_counter,
            )
            record_phase(summary, "6-recovery", recovery)
        else:
            last_counter = int(time.time()) // 30
            wait_counter_after(last_counter)
            phase = run_phase(env, factors, directory, budget, mfa_after=last_counter)
            if (
                not phase["execution_valid"]
                or phase.get("failures") != 0
                or phase.get("measurement_failures") != 0
                or phase.get("timing", {}).get("warmup", {}).get("failures") != 0
            ):
                raise RuntimeError("La fase sostenida no completó las verificaciones")
        after_hashes = source_hashes(env)
        summary["hashes_after"] = after_hashes
        if (
            before_hashes != after_hashes
            or topology(env) != config
            or runtime_topology(env) != actual_runtime
        ):
            raise RuntimeError("Configuración o fuentes cambiaron durante la medición")
        summary["status"] = (
            "completed"
            if series and all(p["execution_valid"] for p in summary["phases"])
            else ("incomplete" if series else "passed")
        )
    finally:
        if "hashes_before" in summary and "hashes_after" not in summary:
            try:
                summary["hashes_after"] = source_hashes(env)
            except OSError:
                summary["hashes_after_unavailable"] = True
        (directory / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        (directory / "summary.json").chmod(0o600)


def evaluate_finite_transactions(result):
    """Six measured samples are complementary coverage, never a capacity estimate."""
    timing = result.get("timing", {})
    business = result.get("business", {})
    rows = timing.get("measurement", [])
    http = [r for r in rows if r["method"] in ("GET", "POST", "PATCH", "PUT", "DELETE")]
    cycles = [r for r in rows if r["method"] == "TRANSACTION"]
    expected = {role: 2 for role in ("MEDICAL", "COORDINATOR", "TRANSPORT")}
    observed = {
        r["name"].removeprefix("Recorrido finito / "): r["requests"] - r["failures"]
        for r in cycles
    }
    read_max = max(
        (r["p95_ms"] for r in http if r["method"] == "GET" and r["requests"]),
        default=None,
    )
    duration = timing.get("finished", 0) - timing.get("measured", 0)
    valid = bool(
        result.get("runner_exit") == 0
        and not result.get("stopped_by_guard")
        and result.get("session_revocation_verified")
        and result.get("session_count_verified")
        and result.get("cleanup_failures") == 0
        and result.get("failures") == 0
        and result.get("counts", {}).get("Identidad / revocación al salir") == 3
        and timing.get("stage") == "finished"
        and timing.get("user_errors") == 0
        and timing.get("warmup_min_users") == 3
        and timing.get("measurement_min_users") == 3
        and timing.get("measured", 0) - timing.get("started", 0) >= 30
        and duration >= 120
        and timing.get("warmup", {}).get("requests", 0) > 0
        and timing.get("warmup", {}).get("failures") == 0
        and business.get("persistence_verified")
        and business.get("not_committed") == 0
        and business.get("response_lost_committed") == 0
        and business.get("incomplete_cycles") == 0
        and business.get("unconfirmed_replays") == 0
        and business.get("replays") == 3
        and business.get("measured_completed") == expected
        and observed == expected
    )
    failures = sum(r["failures"] for r in http)
    read_target = read_max is not None and 0 <= read_max < 2000
    return {
        "execution_valid": valid,
        "measurement_accepted": bool(valid and failures == 0 and read_target),
        "capacity_estimate": False,
        "measured_sample_size": 6,
        "active_cycle_peak": business.get("active_cycle_peak"),
        "active_cycle_seconds": business.get("active_cycle_seconds"),
        "read_p95_max_ms": read_max,
        "read_p95_limit_exclusive_ms": 2000,
        "http_requests": sum(r["requests"] for r in http),
        "http_failures": failures,
        "business_completed": sum(observed.values()),
        "business_per_second": sum(observed.values()) / duration if duration > 0 else 0,
        "business_latency": cycles,
        "totp_waits_separate": business.get("timings", []),
        "transaction_p95_limit_exclusive_ms": None,
        "quota_429": timing.get("http", {}).get("quota_429", 0),
        "gps_in_this_increment": False,
    }
