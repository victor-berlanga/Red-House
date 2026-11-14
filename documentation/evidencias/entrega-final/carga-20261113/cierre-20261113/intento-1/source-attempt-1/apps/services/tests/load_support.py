"""Ejecución Locust aislada compartida por los ensayos funcionales."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


def run_locust(
    platform,
    tmp_path,
    *,
    workload="locustfile",
    users=6,
    extra_state=None,
    label="smoke",
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
    result = subprocess.run(
        command, cwd=root, env=env, capture_output=True, text=True, timeout=75
    )
    (private / "runner.private.log").write_text(result.stdout + result.stderr)
    summary = {"runner_exit": result.returncode, "users": users, "seconds": 12}
    # CSV is periodic and can precede on_stop. Locust writes this final JSON
    # after runner.quit(), including the requests made while closing users.
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
    assert summary["failures"] == 0
    assert summary["counts"]["Identidad / login"] == users
    assert summary["counts"]["Identidad / renovación"] == users
    assert summary["counts"]["Identidad / revocación al salir"] == users
    return summary
