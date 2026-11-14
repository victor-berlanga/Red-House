"""Guardas y datos del piloto, sin iniciar motores."""

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import prepare_load as pilot


def test_dimensions_are_fixed_and_seeded():
    first = pilot.dimensions(20261113)
    assert first == pilot.dimensions(20261113)
    assert first != pilot.dimensions(20261114)
    donors, resources = first
    assert (len(donors), len(resources)) == (200, 1000)
    assert len({row[0] for row in donors}) == 200
    assert len({row[0] for row in resources}) == 1000
    assert {
        state: sum(row[5] == state for row in resources)
        for state in ("AVAILABLE", "QUARANTINE")
    } == {"AVAILABLE": 500, "QUARANTINE": 500}
    assert all(sum(row[1] == tenant for row in resources) == 500 for tenant in (0, 1))
    large_donors, large_resources = pilot.dimensions(20261113, 10)
    assert (len(large_donors), len(large_resources)) == (2000, 10000)
    assert large_donors[:200] == donors
    assert large_resources[:1000] == resources


def test_wal_snapshot_counts_only_complete_segment_names(tmp_path):
    wal = tmp_path / "pg/pg_wal"
    wal.mkdir(parents=True)
    (wal / "000000010000000000000001").write_bytes(b"x" * 10)
    (wal / "000000010000000000000002").write_bytes(b"x" * 20)
    (wal / "000000010000000000000003.partial").write_bytes(b"ignored")
    assert pilot.wal_snapshot(tmp_path) == {"segments": 2, "bytes": 30}


@pytest.mark.parametrize(
    "url",
    [
        "postgresql://user@localhost:5432/x",
        "postgresql://user@10.1.2.3:5432/x",
        "postgresql://user@127.0.0.1/x",
        "mongodb://127.0.0.1:27017/x",
    ],
)
def test_nonisolated_dsn_rejected(url):
    with pytest.raises(ValueError):
        pilot.local_url(url, {"postgresql"})


def test_budget_and_symlinks_are_fail_closed(tmp_path, monkeypatch):
    (tmp_path / "data").write_bytes(b"1234")
    monkeypatch.setattr(
        pilot.shutil, "disk_usage", lambda _: SimpleNamespace(free=pilot.MIN_FREE)
    )
    assert pilot.budget(tmp_path)["owned_bytes"] == 4
    monkeypatch.setattr(pilot, "MAX_OWN", 3)
    with pytest.raises(pilot.BudgetExceeded) as failure:
        pilot.budget(tmp_path)
    assert failure.value.code == "owned_limit_exceeded"
    assert failure.value.sample == {
        "free_bytes": pilot.MIN_FREE,
        "owned_bytes": 4,
        "minimum_free_bytes": pilot.MIN_FREE,
        "maximum_owned_bytes": 3,
    }
    monkeypatch.setattr(pilot, "MAX_OWN", 10)
    (tmp_path / "link").symlink_to(tmp_path / "data")
    with pytest.raises(ValueError):
        pilot.budget(tmp_path)


def test_budget_reports_free_space_boundary(tmp_path, monkeypatch):
    monkeypatch.setattr(
        pilot.shutil, "disk_usage", lambda _: SimpleNamespace(free=pilot.MIN_FREE - 1)
    )
    with pytest.raises(pilot.BudgetExceeded) as failure:
        pilot.budget(tmp_path)
    assert failure.value.code == "free_insufficient"
    assert failure.value.sample["free_bytes"] == pilot.MIN_FREE - 1
    assert failure.value.sample["owned_bytes"] == 0


def test_disk_census_retries_complete_scan_after_transient_removal(
    tmp_path, monkeypatch
):
    victim = tmp_path / "temporary"
    victim.write_bytes(b"1234")
    actual = Path.lstat
    attempts = []

    def unstable(path, *args, **kwargs):
        if path == victim:
            attempts.append(path)
            if len(attempts) == 1:
                raise FileNotFoundError("transient")
        return actual(path, *args, **kwargs)

    monkeypatch.setattr(Path, "lstat", unstable)
    assert pilot.own_bytes(tmp_path) == 4
    assert len(attempts) == 2


def test_disk_census_fails_closed_on_persistent_removal_or_missing_root(
    tmp_path, monkeypatch
):
    victim = tmp_path / "temporary"
    victim.write_bytes(b"1234")
    actual = Path.lstat
    attempts = []

    def unstable(path, *args, **kwargs):
        if path == victim:
            attempts.append(path)
            raise FileNotFoundError("persistent")
        return actual(path, *args, **kwargs)

    monkeypatch.setattr(Path, "lstat", unstable)
    with pytest.raises(pilot.CensusFailure, match="unstable"):
        pilot.own_bytes(tmp_path)
    assert len(attempts) == 3
    with pytest.raises(pilot.CensusFailure, match="root_missing"):
        pilot.own_bytes(tmp_path / "missing")
    root_link = tmp_path / "root-link"
    root_link.symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(pilot.CensusFailure, match="root_invalid"):
        pilot.own_bytes(root_link)


def test_environment_rejects_foreign_process_before_network(tmp_path, monkeypatch):
    class Process:
        pid = 1

        def poll(self):
            return None

    env = SimpleNamespace(
        directory=tmp_path,
        state={
            "directory": str(tmp_path),
            "infrastructure_pids": {"postgres": 1, "redis": 2, "mongodb": 3},
        },
        processes=[Process(), Process(), Process()],
    )
    monkeypatch.setattr(
        pilot.psycopg, "connect", lambda *_a, **_k: pytest.fail("unexpected connection")
    )
    with pytest.raises(ValueError):
        pilot.validate_environment(env)


def test_environment_rejects_dsn_host_override_before_network(tmp_path, monkeypatch):
    def process(pid):
        return SimpleNamespace(pid=pid, poll=lambda: None)

    env = SimpleNamespace(
        directory=tmp_path,
        processes=[process(1), process(2), process(3)],
        state={
            "directory": str(tmp_path),
            "infrastructure_pids": {"postgres": 1, "redis": 2, "mongodb": 3},
            "database_admin": "postgresql://u:p@127.0.0.1:5432/postgres",
            "database_owners": {
                "inventario": "postgresql://u:p@127.0.0.1:5432/red_house?host=10.0.0.1"
            },
        },
    )
    monkeypatch.setattr(
        pilot.psycopg, "connect", lambda *_a, **_k: pytest.fail("unexpected connection")
    )
    with pytest.raises(ValueError):
        pilot.validate_environment(env)


def test_initialization_and_stop_failures_preserve_private_diagnostics(
    tmp_path, monkeypatch
):
    class FailingEnvironment:
        def __init__(self, *_args):
            pass

        def init(self):
            raise ValueError("private initialization detail")

        def stop(self):
            raise OSError("private cleanup detail")

    for key in (
        "PGHOSTADDR",
        "PGSERVICE",
        "PGOPTIONS",
        "REDHOUSE_ENV",
        "GOOGLE_APPLICATION_CREDENTIALS",
        "GCS_BUCKET",
    ):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr(sys, "argv", ["prepare_load.py"])
    monkeypatch.setattr(pilot.tempfile, "mkdtemp", lambda **_kw: str(tmp_path))
    monkeypatch.setattr(
        pilot.shutil, "disk_usage", lambda _: SimpleNamespace(free=pilot.MIN_FREE)
    )
    monkeypatch.setattr(pilot, "Environment", FailingEnvironment)
    with pytest.raises(RuntimeError, match="consultar el informe privado"):
        pilot.main()
    report = json.loads((tmp_path / "pilot-report.json").read_text())
    assert report["status"] == "failed"
    assert report["error_type"] == "ValueError"
    assert report["cleanup_error_type"] == "OSError"
    diagnostic = tmp_path / "pilot-diagnostic.private.log"
    assert diagnostic.stat().st_mode & 0o777 == 0o600
    assert "private initialization detail" in diagnostic.read_text()
    assert "private cleanup detail" in diagnostic.read_text()


@pytest.mark.parametrize(
    "name",
    [
        "PGHOSTADDR",
        "PGSERVICE",
        "PGOPTIONS",
        "REDHOUSE_ENV",
        "GOOGLE_APPLICATION_CREDENTIALS",
        "GCS_BUCKET",
    ],
)
def test_libpq_environment_is_rejected_before_creating_a_directory(name, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["prepare_load.py"])
    monkeypatch.setenv(name, "unexpected")
    monkeypatch.setattr(
        pilot.tempfile, "mkdtemp", lambda **_kw: pytest.fail("unexpected directory")
    )
    with pytest.raises(RuntimeError, match="variables de conexión"):
        pilot.main()
