"""Rehearsal of additive configuration and credentials without touching user installs."""

import json
import os
import tempfile
import subprocess
import shutil
import sys
from pathlib import Path
from urllib.parse import urlsplit
from psycopg.conninfo import conninfo_to_dict

import pytest
import psycopg
import redis

from scripts.local import Environment
from redhouse.config import SERVICES
from scripts.upgrade_documents import provision_documents
from scripts.upgrade_final_acl import upgrade_acl


def test_documents_configuration_upgrade_repeatable_preserves_sessions(
    tmp_path, monkeypatch
):
    env = Environment(
        tempfile.mkdtemp(prefix="rh-upgrade-", dir="/tmp"),
        # Sin variable, Environment.init resuelve mongod como en conftest.
        os.environ.get("REDHOUSE_TEST_MONGOD"),
    )
    try:
        env.init(seed=False)
        directory = env.directory
        state = env.state
        before = {
            p.name: json.loads(p.read_text())
            for p in directory.glob("*.json")
            if p.stem in SERVICES
        }
        # Recreate the pre-extraction credentials topology on a real isolated cluster.
        with psycopg.connect(
            state["database_admin"], dbname="red_house", autocommit=True
        ) as conn:
            conn.execute("DROP OWNED BY rh_documentos")
            conn.execute("DROP ROLE rh_documentos")
        with redis.Redis.from_url(state["redis_admin"]) as admin:
            admin.acl_deluser("documentos")
            marker = (
                before["identidad_acceso.json"]["REDIS_PREFIX"]
                + "session:upgrade-marker"
            )
            admin.set(marker, "preserved", ex=600)
        (directory / "documentos.json").unlink()
        state["database_owners"].pop("documentos")
        for name, config in before.items():
            if name == "documentos.json":
                continue
            config["SERVICE_PUBLIC_KEYS"].pop("documentos", None)
            config["SERVICE_URLS"].pop("documentos", None)
            (directory / name).write_text(json.dumps(config))
        provision_documents(directory, state)
        upgraded = (directory / "documentos.json").read_bytes()
        provision_documents(directory, state)
        upgrade_acl(directory, state)
        assert (directory / "documentos.json").read_bytes() == upgraded
        config = json.loads(upgraded)
        assert config["SERVICE"] == "documentos" and config["PORT"] == 5112
        with psycopg.connect(config["DATABASE_URL"]) as conn:
            assert conn.execute("SELECT count(*) FROM files").fetchone()[0] == 0
            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                with conn.transaction():
                    conn.execute("SELECT count(*) FROM access_transporte.shipments")
            assert not conn.execute(
                "SELECT has_table_privilege(current_user,'access_documentos.files','DELETE')"
            ).fetchone()[0]
        with redis.Redis.from_url(config["REDIS_URL"]) as client:
            assert client.ping()
            assert client.get(marker) == b"preserved"
        for name, original in before.items():
            if name == "documentos.json":
                continue
            current = json.loads((directory / name).read_text())
            for key in (
                "DATABASE_URL",
                "REDIS_URL",
                "SERVICE_PRIVATE_KEY",
                "JWT_PRIVATE_KEY",
            ):
                assert current.get(key) == original.get(key), (name, key)
            assert (
                current["SERVICE_PUBLIC_KEYS"]["documentos"]
                == config["SERVICE_PUBLIC_KEYS"]["documentos"]
            )
        assert not (directory / "documentos.pending.json").exists()
        # Ejecutar la misma entrada Compose sobre su estructura de secretos, con dump real.
        from scripts.upgrade_compose import main

        compose = tmp_path / "compose"
        (compose / "apps").mkdir(parents=True)
        for name in before:
            shutil.copy2(directory / name, compose / "apps" / name)
        legacy_state = dict(state)
        legacy_state.pop("redis_admin")
        (compose / "redis-password").write_text(urlsplit(state["redis_admin"]).password)
        (compose / "state.json").write_text(json.dumps(legacy_state))
        with psycopg.connect(state["database_admin"], dbname="red_house") as conn:
            conn.execute("REVOKE CREATE ON DATABASE red_house FROM rh_shared_owner")
        (compose / "web.json").write_text(json.dumps({"SERVICE_URLS": {}}))
        params = conninfo_to_dict(state["database_admin"])
        backup = compose / "before.dump"
        binary = (
            Path(state["infrastructure_commands"]["postgres"][0]).parent / "pg_dump"
        )
        subprocess.run(
            [
                str(binary),
                "--host",
                params["host"],
                "--port",
                params["port"],
                "--username",
                params["user"],
                "--dbname",
                "red_house",
                "--format=custom",
                "--file",
                str(backup),
            ],
            env={**os.environ, "PGPASSWORD": params["password"]},
            check=True,
            capture_output=True,
        )
        monkeypatch.setattr(
            sys,
            "argv",
            ["upgrade_compose", "--directory", str(compose), "--backup", str(backup)],
        )
        main()
        main()
        with psycopg.connect(state["database_admin"], dbname="red_house") as conn:
            assert not conn.execute(
                "SELECT has_database_privilege('rh_shared_owner','red_house','CREATE')"
            ).fetchone()[0]
        assert not (compose / "apps/state.json").exists()
        assert json.loads((compose / "web.json").read_text())["SERVICE_URLS"][
            "documentos"
        ].endswith(":5112")
        assert (
            json.loads((compose / "state.json").read_text())["database_owners"][
                "documentos"
            ]
            == state["database_owners"]["documentos"]
        )
        with redis.Redis.from_url(state["redis_admin"]) as admin:
            assert admin.get(marker) == b"preserved"

    finally:
        env.stop()
