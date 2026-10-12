"""Regresiones del arranque local, sin bases ni instalaciones del equipo."""

import importlib.util
import json
import sys
import subprocess
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from scripts import dependencies, local

REPO = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location(
    "local_manager", REPO / "scripts/manage.py"
)
manager = importlib.util.module_from_spec(spec)
spec.loader.exec_module(manager)


def binary(tmp_path, name, output):
    path = tmp_path / name
    path.write_text("#!/bin/sh\nprintf '%s\\n' '" + output + "'\n")
    path.chmod(0o700)
    return str(path)


def test_missing_saved_mongodb_falls_back_to_persistent_install(tmp_path, monkeypatch):
    monkeypatch.setattr(dependencies, "REPO", tmp_path)
    monkeypatch.setattr(dependencies.shutil, "which", lambda _: None)
    folder = tmp_path / f".local/tools/mongodb-{dependencies.MONGO_VERSION}/bin"
    folder.mkdir(parents=True)
    installed = binary(folder, "mongod", "db version v8.0.17")
    assert (
        dependencies.resolve_binary("mongod", tmp_path, saved="/missing/mongod")
        == installed
    )


def test_wrong_postgres_major_rejected_before_opening_data(tmp_path):
    (tmp_path / "pg").mkdir()
    (tmp_path / "pg/PG_VERSION").write_text("14\n")
    wrong = binary(tmp_path, "postgres", "postgres (PostgreSQL) 16.5")
    with pytest.raises(RuntimeError, match="PostgreSQL 14"):
        dependencies.resolve_binary("postgres", tmp_path, explicit=wrong)


def test_explicit_missing_binary_is_not_silently_replaced(tmp_path, monkeypatch):
    installed = binary(tmp_path, "mongod", "db version v8.0.17")
    monkeypatch.setattr(dependencies.shutil, "which", lambda _: installed)
    with pytest.raises(RuntimeError):
        dependencies.resolve_binary("mongod", tmp_path, explicit="/missing/mongod")


def environment(tmp_path):
    env = local.Environment(tmp_path)
    env.state = {
        "directory": str(tmp_path),
        "service_pids": {"donantes": 100, "inventario": 200},
        "worker_pids": {"donantes": 101, "inventario": 201},
        "urls": {
            "donantes": "http://127.0.0.1:5102",
            "inventario": "http://127.0.0.1:5104",
        },
    }
    return env


def test_start_preserves_apis_and_recovers_only_missing_worker(tmp_path, monkeypatch):
    env = environment(tmp_path)
    monkeypatch.setattr(local, "pid_matches", lambda pid, _: pid in (100, 200, 201))
    env.start_api = Mock()
    env.start_worker = Mock()
    env.wait = Mock()
    env.start(services=["donantes", "inventario"])
    env.start_api.assert_not_called()
    env.start_worker.assert_called_once_with("donantes")
    assert env.state["service_pids"] == {"donantes": 100, "inventario": 200}


def test_empty_selection_starts_nothing(tmp_path):
    env = environment(tmp_path)
    env.start_api = Mock()
    env.start_worker = Mock()
    env.start(services=[])
    env.start_api.assert_not_called()
    env.start_worker.assert_not_called()


def test_port_conflict_prevents_all_selected_launches(tmp_path, monkeypatch):
    env = environment(tmp_path)
    monkeypatch.setattr(local, "pid_matches", lambda *_: False)
    monkeypatch.setattr(
        local, "check_port", Mock(side_effect=[None, RuntimeError("ocupado")])
    )
    env.launch = Mock()
    with pytest.raises(RuntimeError, match="ocupado"):
        env.start(services=["donantes", "inventario"])
    env.launch.assert_not_called()


def test_missing_dependency_preflight_launches_nothing(tmp_path, monkeypatch):
    env = environment(tmp_path)
    env.state["infrastructure_commands"] = {
        "postgres": [sys.executable],
        "redis": [sys.executable],
        "mongodb": ["/missing/mongod"],
    }
    env.state["database_admin"] = "postgresql://localhost:5432/test"
    env.state["redis_admin"] = "redis://localhost:6379/0"
    monkeypatch.setattr(local, "infrastructure_pid", lambda *_: None)
    monkeypatch.setattr(local, "check_port", Mock())
    monkeypatch.setattr(
        local,
        "resolve_binary",
        Mock(side_effect=AssertionError("No revisar versiones al iniciar")),
    )
    env.launch = Mock()
    with pytest.raises(RuntimeError, match="instalar.sh"):
        env.ensure_infrastructure()
    env.launch.assert_not_called()


def test_save_is_private_and_preserves_previous_state_on_replace_failure(
    tmp_path, monkeypatch
):
    env = environment(tmp_path)
    env.save()
    path = tmp_path / "state.json"
    original = path.read_bytes()
    assert path.stat().st_mode & 0o777 == 0o600
    env.state["service_pids"] = {}
    monkeypatch.setattr(local.os, "replace", Mock(side_effect=OSError("interrumpido")))
    with pytest.raises(OSError):
        env.save()
    assert path.read_bytes() == original


def test_web_preparation_preserves_existing_config_and_keys(tmp_path, monkeypatch):
    web = tmp_path / "web"
    web.mkdir()
    key1, key2 = "a" * 64, "b" * 64
    (web / ".env").write_text(f"SECRET_KEY={key1}\nJWT_SECRET_KEY={key2}\n")
    monkeypatch.setattr(manager, "WEB", web)
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    config = tmp_path / "web-client.json"
    config.write_text('{"existing": true}')
    manager.prepare_web(tmp_path, {"urls": {}})
    secrets = tmp_path / "web-secrets.env"
    assert key1 in secrets.read_text() and key2 in secrets.read_text()
    before = secrets.read_bytes()
    manager.prepare_web(tmp_path, {"urls": {"other": "ignored"}})
    assert secrets.read_bytes() == before
    assert json.loads(config.read_text()) == {"existing": True}
    assert secrets.stat().st_mode & 0o777 == 0o600


def test_corrupt_download_is_not_installed(tmp_path, monkeypatch):
    monkeypatch.setattr(manager, "REPO", tmp_path)
    monkeypatch.setattr(manager.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(manager.platform, "machine", lambda: "x86_64")
    monkeypatch.setattr(
        manager, "run", lambda command: Path(command[-1]).write_bytes(b"corrupt")
    )
    with pytest.raises(RuntimeError, match="SHA-256"):
        manager.install_binary("mongod", tmp_path)
    assert not (
        tmp_path / f".local/tools/mongodb-{dependencies.MONGO_VERSION}"
    ).exists()


def test_wrong_directory_rejected_before_preparation(tmp_path, monkeypatch):
    (tmp_path / "state.json").write_text(json.dumps({"directory": "/somewhere/else"}))
    monkeypatch.setattr(manager, "ensure_python", Mock())
    with pytest.raises(RuntimeError, match="directorio"):
        manager.operate(SimpleNamespace(directory=tmp_path, action="todo"))
    manager.ensure_python.assert_not_called()


def test_incomplete_directory_never_reinitialized(tmp_path, monkeypatch):
    (tmp_path / "pg").mkdir()
    monkeypatch.setattr(manager, "ensure_binaries", Mock())
    monkeypatch.setattr(local.Environment, "init", Mock())
    with pytest.raises(RuntimeError, match="no se reinicializa"):
        manager.prepare_environment(
            SimpleNamespace(directory=tmp_path, no_install=True)
        )
    local.Environment.init.assert_not_called()


@pytest.mark.parametrize("script", ["iniciar.sh", "componentes.sh", "instalar.sh"])
def test_shell_help_from_another_directory(script, tmp_path):
    result = subprocess.run(
        ["bash", str(REPO / script), "--help"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0 and "instalar.sh" in result.stdout


def test_menu_dispatches_selected_service_without_shell_evaluation(tmp_path):
    result = subprocess.run(
        ["bash", str(REPO / "componentes.sh")],
        input="4\ninvalid; touch INJECTED\n",
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert not (tmp_path / "INJECTED").exists()


@pytest.mark.parametrize(
    "action",
    ["todo", "ms", "web", "bases", "inventario", "estado", "detener", "reiniciar"],
)
def test_runtime_never_checks_or_installs_dependencies(action, tmp_path, monkeypatch):
    service_root = tmp_path / "services"
    python = service_root / ".venv/bin/python"
    python.parent.mkdir(parents=True)
    python.touch()
    directory = tmp_path / "demo"
    directory.mkdir()
    state = {
        "directory": str(directory),
        "urls": {name: "http://127.0.0.1:5100" for name in manager.SERVICES},
        "web_url": "http://127.0.0.1:5050",
    }
    (directory / "state.json").write_text(json.dumps(state))
    monkeypatch.setattr(manager, "REPO", tmp_path)
    monkeypatch.setattr(manager, "SERVICES_ROOT", service_root)
    monkeypatch.setattr(sys, "prefix", str(service_root / ".venv"))
    monkeypatch.setattr(
        sys, "argv", ["manage.py", action, "--directory", str(directory)]
    )
    for name in ("ensure_python", "ensure_binaries", "prepare_web", "install_binary"):
        monkeypatch.setattr(
            manager,
            name,
            Mock(
                side_effect=AssertionError("El arranque no debe preparar dependencias")
            ),
        )
    monkeypatch.setattr(manager, "run", Mock())
    monkeypatch.setattr(manager, "wait_ready", Mock())
    manager.main()
    manager.run.assert_called()


def test_unprepared_start_does_not_initialize_or_install(tmp_path, monkeypatch):
    directory = tmp_path / "new"
    monkeypatch.setattr(
        manager, "ensure_python", Mock(side_effect=AssertionError("No instalar"))
    )
    monkeypatch.setattr(
        local.Environment, "init", Mock(side_effect=AssertionError("No inicializar"))
    )
    with pytest.raises(RuntimeError, match="instalar.sh"):
        manager.operate(SimpleNamespace(directory=directory, action="todo"))
    assert not directory.exists()


def test_running_infrastructure_does_not_check_binary_versions(tmp_path, monkeypatch):
    env = environment(tmp_path)
    env.state["infrastructure_commands"] = {
        name: ["/not/consulted"] for name in ("postgres", "redis", "mongodb")
    }
    env.state["infrastructure_pids"] = {}
    monkeypatch.setattr(local, "infrastructure_pid", lambda *_: 100)
    monkeypatch.setattr(
        local,
        "resolve_binary",
        Mock(side_effect=AssertionError("No revisar versiones")),
    )
    env.wait = Mock()
    env.launch = Mock()
    env.ensure_infrastructure()
    env.launch.assert_not_called()
