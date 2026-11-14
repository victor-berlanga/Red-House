"""Ejecución Locust aislada compartida por los ensayos funcionales."""

import json
import os
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

import redis


def verify_created_sessions_closed(before_ids, rows, user_ids, prefix, client):
    created = [row for row in rows if str(row[0]) not in before_ids]
    if len({str(row[0]) for row in created}) != len(created) or any(
        str(row[1]) not in user_ids or row[2] is None for row in created
    ):
        raise ValueError("Familias nuevas ajenas, duplicadas o no revocadas.")
    keys = [prefix + "session:" + str(row[0]) for row in created]
    if keys and any(value is not None for value in client.mget(keys)):
        raise ValueError("Sesiones nuevas todavía presentes en Redis.")
    return created


def verify_new_sessions(before_ids, rows, user_ids, prefix, client, multiplicity=1):
    if (
        not isinstance(multiplicity, int)
        or isinstance(multiplicity, bool)
        or multiplicity < 1
        or len(set(user_ids)) != len(user_ids)
    ):
        raise ValueError("Multiplicidad o identidades inválidas.")
    created = verify_created_sessions_closed(before_ids, rows, user_ids, prefix, client)
    if (
        len(created) != len(user_ids) * multiplicity
        or len({str(row[0]) for row in created}) != len(created)
        or Counter(str(row[1]) for row in created)
        != Counter({user_id: multiplicity for user_id in user_ids})
        or any(row[2] is None for row in created)
    ):
        raise ValueError("Familias nuevas incompletas o no revocadas.")


def run_locust(
    platform,
    tmp_path,
    *,
    workload="locustfile",
    users=6,
    extra_state=None,
    label="smoke",
    user_ids,
):
    root = Path(__file__).resolve().parents[1]
    private = tmp_path / "load"
    private.mkdir(mode=0o700)
    state = private / "state.json"
    state.write_text(
        json.dumps(
            {
                "directory": str(private),
                "urls": platform.urls,
                "password": platform.env.state["password"],
                **(extra_state or {}),
            }
        )
    )
    state.chmod(0o600)
    # Early rotation is deliberate; this smoke does not claim JWT expiration.
    base_import = (
        "from locustfile import RegionalUser"
        if workload == "locustfile"
        else "from locust_transactions import TransactionUser as RegionalUser"
    )
    (private / "probe.py").write_text(
        "import sys\n"
        f"sys.path.insert(0, {str(root / 'tests')!r})\n"
        f"{base_import}\n"
        "class RenewalProbe(RegionalUser):\n"
        "    def on_start(self):\n"
        "        super().on_start()\n"
        "        self.api.renew_at = self.api.clock() + 2\n"
    )
    command = [
        sys.executable,
        "-m",
        "locust",
        "-f",
        str(private / "probe.py"),
        "--headless",
        "--users",
        str(users),
        "--spawn-rate",
        "2",
        "--run-time",
        "12s",
        "--stop-timeout",
        "30",
        "--host",
        "http://127.0.0.1",
        "--csv",
        str(private / "smoke"),
        "--csv-full-history",
        "--json-file",
        str(private / "smoke-final"),
        "--exit-code-on-error",
        "1",
        "--only-summary",
        "RenewalProbe",
    ]
    env = {
        **os.environ,
        "REDHOUSE_LOAD_ISOLATED": "1",
        "REDHOUSE_LOAD_STATE": str(state),
    }
    env.pop("REDHOUSE_LOAD_NO_CACHE", None)
    if len(user_ids) != users or len(set(user_ids)) != users:
        raise ValueError("La carga exige una cuenta distinta por usuario.")

    def session_rows():
        with platform.owner("identidad_acceso") as conn:
            return conn.execute(
                "SELECT id,user_id,revoked_at FROM sessions WHERE user_id=ANY(%s::uuid[])",
                (user_ids,),
            ).fetchall()

    before_ids = {str(row[0]) for row in session_rows()}
    result = subprocess.run(
        command,
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        timeout=75,
        check=False,
    )
    (private / "runner.private.log").write_text(result.stdout + result.stderr)
    summary = {"runner_exit": result.returncode, "users": users, "seconds": 12}
    # El revoke responde uniformemente; verificar familias nuevas en las dos
    # autoridades del fixture, excluyendo las sesiones que ya existían.
    verification_error = None
    try:
        prefix = platform.apps["identidad_acceso"].config["REDIS_PREFIX"]
        with redis.Redis.from_url(
            platform.env.state["redis_admin"], socket_timeout=3
        ) as client:
            verify_new_sessions(before_ids, session_rows(), user_ids, prefix, client)
        summary["session_revocation_verified"] = True
    except Exception:  # noqa: BLE001 - resultados públicos no incluyen detalles de conexión
        verification_error = (
            "No se comprobó la revocación de todas las sesiones nuevas."
        )
        summary["session_revocation_verified"] = False
    # CSV is periodic and can precede test_stop. Locust writes this final JSON
    # after runner.quit(), including the coordinated revocations.
    if (private / "smoke-final.json").exists():
        rows = json.loads((private / "smoke-final.json").read_text())
        counts = {row["name"]: int(row["num_requests"]) for row in rows}
        failures = sum(int(row["num_failures"]) for row in rows)
        summary.update(counts=counts, failures=failures)
    output = os.environ.get("REDHOUSE_LOAD_OUTPUT")
    if output:
        directory = Path(output) / label
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "smoke-summary.json").write_text(
            json.dumps(summary, indent=2) + "\n"
        )
        for name in (
            "smoke-final.json",
            "smoke_stats.csv",
            "smoke_stats_history.csv",
            "smoke_failures.csv",
            "smoke_exceptions.csv",
        ):
            source = private / name
            if source.exists():
                raw = source.read_bytes()
                assert platform.env.state["password"].encode() not in raw
                shutil.copyfile(source, directory / name)
    assert result.returncode == 0, (
        "Locust falló; diagnóstico conservado en directorio privado."
    )
    assert verification_error is None, verification_error
    assert summary["failures"] == 0
    assert summary["counts"]["Identidad / login"] == users
    assert summary["counts"]["Identidad / renovación"] == users
    assert summary["counts"]["Identidad / revocación al salir"] == users
    return summary
