"""Regresiones del arranque local, sin bases ni instalaciones del equipo."""

import importlib.util
import json
import os
import subprocess
import sys
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
    with pytest.raises(RuntimeError, match="install.sh"):
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


@pytest.mark.parametrize(
    "script", ["start.sh", "components.sh", "install.sh", "stop.sh"]
)
def test_shell_help_from_another_directory(script, tmp_path):
    result = subprocess.run(
        check=False,
        args=["bash", str(REPO / script), "--help"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0 and "Uso:" in result.stdout
    assert script in result.stdout


def test_menu_dispatches_selected_service_without_shell_evaluation(tmp_path):
    result = subprocess.run(
        check=False,
        args=["bash", str(REPO / "components.sh")],
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
    directory = tmp_path / "sample"
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
    with pytest.raises(RuntimeError, match="install.sh"):
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


@pytest.mark.parametrize("app_name", ["services", "web"])
def test_missing_venv_support_has_wsl_instructions_before_creation(
    tmp_path, monkeypatch, app_name
):
    app = tmp_path / app_name
    monkeypatch.setattr(manager.platform, "system", lambda: "Linux")
    monkeypatch.setattr(manager.sys, "version_info", SimpleNamespace(major=3, minor=14))
    monkeypatch.setattr(
        manager.subprocess, "run", Mock(return_value=SimpleNamespace(returncode=1))
    )
    monkeypatch.setattr(manager, "run", Mock())
    with pytest.raises(RuntimeError, match="sudo apt install python3.14-venv") as error:
        manager.ensure_python(app, True)
    assert "WSL" in str(error.value)
    assert "administrador" in str(error.value)
    assert not (app / ".venv").exists()
    manager.run.assert_not_called()


@pytest.mark.parametrize(
    "failure", [PermissionError("denied"), subprocess.CalledProcessError(1, "venv")]
)
def test_venv_creation_failure_identifies_directory_and_permissions(
    tmp_path, monkeypatch, failure
):
    monkeypatch.setattr(
        manager.subprocess, "run", Mock(return_value=SimpleNamespace(returncode=0))
    )
    monkeypatch.setattr(manager, "run", Mock(side_effect=failure))
    with pytest.raises(RuntimeError, match="permisos de escritura") as error:
        manager.ensure_python(tmp_path, True)
    assert str(tmp_path / ".venv") in str(error.value)


def test_partial_venv_repairs_pip_without_recreating_it(tmp_path, monkeypatch):
    python = tmp_path / ".venv/bin/python"
    python.parent.mkdir(parents=True)
    python.touch()
    sentinel = tmp_path / ".venv/keep"
    sentinel.write_text("preservar")
    monkeypatch.setattr(
        manager.subprocess,
        "run",
        Mock(
            side_effect=[
                SimpleNamespace(returncode=0),  # versión
                SimpleNamespace(returncode=1),  # pip ausente
                SimpleNamespace(returncode=0),  # pip reparado
                SimpleNamespace(returncode=0, stdout=""),  # requisitos
                SimpleNamespace(returncode=0),  # pip check
                SimpleNamespace(returncode=0),  # extras
            ]
        ),
    )
    monkeypatch.setattr(manager, "run", Mock())
    assert manager.ensure_python(tmp_path, True) == python
    manager.run.assert_called_once_with([python, "-m", "ensurepip", "--upgrade"])
    assert sentinel.read_text() == "preservar"


def test_missing_pip_no_install_does_not_repair(tmp_path, monkeypatch):
    monkeypatch.setattr(
        manager.subprocess, "run", Mock(return_value=SimpleNamespace(returncode=1))
    )
    monkeypatch.setattr(manager, "run", Mock())
    with pytest.raises(RuntimeError, match="Falta pip"):
        manager.ensure_pip(tmp_path / ".venv/bin/python", False)
    manager.run.assert_not_called()


def test_pip_repair_failure_reports_required_system_package(tmp_path, monkeypatch):
    monkeypatch.setattr(manager.platform, "system", lambda: "Linux")
    monkeypatch.setattr(
        manager.subprocess, "run", Mock(return_value=SimpleNamespace(returncode=1))
    )
    monkeypatch.setattr(
        manager, "run", Mock(side_effect=subprocess.CalledProcessError(1, "ensurepip"))
    )
    with pytest.raises(RuntimeError, match="sudo apt install python") as error:
        manager.ensure_pip(tmp_path / ".venv/bin/python", True)
    assert "No se pudo preparar pip" in str(error.value)


@pytest.mark.parametrize("install", [False, True])
def test_missing_requirements_or_failed_install_has_actionable_error(
    tmp_path, monkeypatch, install
):
    python = tmp_path / ".venv/bin/python"
    python.parent.mkdir(parents=True)
    python.touch()
    monkeypatch.setattr(manager, "ensure_pip", Mock())
    monkeypatch.setattr(
        manager.subprocess,
        "run",
        Mock(
            side_effect=[
                SimpleNamespace(returncode=0),
                SimpleNamespace(returncode=1, stdout="Flask==3.1.2"),
            ]
        ),
    )
    monkeypatch.setattr(
        manager, "run", Mock(side_effect=subprocess.CalledProcessError(1, "pip"))
    )
    with pytest.raises(RuntimeError) as error:
        manager.ensure_python(tmp_path, install)
    if install:
        assert "requirements.txt" in str(error.value)
        assert "permisos de escritura" in str(error.value)
        assert "pip check" in str(error.value)
    else:
        assert "Flask==3.1.2" in str(error.value)
        manager.run.assert_not_called()


def test_real_venv_without_pip_can_be_repaired_offline(tmp_path):
    subprocess.run(
        [sys.executable, "-m", "venv", "--without-pip", str(tmp_path / "venv")],
        check=True,
    )
    python = tmp_path / "venv/bin/python"
    assert (
        subprocess.run(
            check=False,
            args=[str(python), "-m", "pip", "--version"],
            capture_output=True,
        ).returncode
        != 0
    )
    manager.ensure_pip(python, True)
    assert (
        subprocess.run(
            check=False,
            args=[str(python), "-m", "pip", "--version"],
            capture_output=True,
        ).returncode
        == 0
    )


def test_homebrew_rejects_linux_before_searching_or_installing(tmp_path):
    binary(tmp_path, "uname", "Linux")
    marker = tmp_path / "brew-called"
    brew = tmp_path / "brew"
    brew.write_text('#!/bin/sh\ntouch "' + str(marker) + '"\n')
    brew.chmod(0o700)
    result = subprocess.run(
        ["bash", str(REPO / "scripts/homebrew.sh"), "redis"],
        check=False,
        env={**os.environ, "PATH": str(tmp_path) + os.pathsep + os.environ["PATH"]},
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "exclusivo de macOS" in result.stderr
    assert not marker.exists()


def test_default_install_does_not_hide_an_existing_environment(tmp_path, monkeypatch):
    old = tmp_path / ".local/previous"
    old.mkdir(parents=True)
    (old / "state.json").write_text("{}")
    monkeypatch.setattr(manager, "REPO", tmp_path)
    monkeypatch.setattr(sys, "argv", ["manage.py", "preparar"])
    monkeypatch.setattr(manager, "ensure_python", Mock())
    with pytest.raises(RuntimeError, match="No se creará otra base"):
        manager.main()
    manager.ensure_python.assert_not_called()
    assert not (tmp_path / ".local/runtime").exists()
