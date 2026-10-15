"""Pruebas del almacenamiento común, permisos y monitoreo independiente."""

from uuid import uuid4

import psycopg
import pytest
from psycopg.conninfo import conninfo_to_dict


def test_all_services_use_same_database_and_physical_tables(p):
    databases = {
        conninfo_to_dict(p.env.configs[s]["DATABASE_URL"])["dbname"] for s in p.apps
    }
    assert databases == {"red_house"}
    with p.owner("identidad_acceso") as c:
        assert (
            c.execute(
                "SELECT count(*) FROM pg_tables WHERE schemaname LIKE 'access_%'"
            ).fetchone()[0]
            == 0
        )
        assert (
            c.execute("SELECT count(*) FROM red_house.institution").fetchone()[0] >= 2
        )
        assert c.execute("SELECT count(*) FROM red_house.donor").fetchone()[0] >= 0


def test_service_credentials_cannot_read_other_service_or_base_tables(p):
    dsn = p.env.configs["donantes"]["DATABASE_URL"]
    for query in (
        "SELECT * FROM red_house.user_account",
        "SELECT * FROM access_identidad_acceso.users",
        "UPDATE access_donantes.donor_reviews SET reason=reason",
        "INSERT INTO access_donantes.schema_version(version) VALUES(999)",
    ):
        with psycopg.connect(dsn) as conn:
            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                conn.execute(query)


def test_shared_fk_rejects_orphan_and_rolls_back_other_module_write(p):
    identity = str(uuid4())
    with p.owner("identidad_acceso") as conn:
        with pytest.raises(psycopg.errors.ForeignKeyViolation):
            with conn.transaction():
                conn.execute(
                    "INSERT INTO access_identidad_acceso.institutions(id,name,region_id) VALUES(%s,%s,%s)",
                    (identity, "Transacción revertida", p.env.state["region_id"]),
                )
                conn.execute(
                    "INSERT INTO access_donantes.appointments(id,tenant_id,donor_id,campaign_id) VALUES(%s,%s,%s,%s)",
                    (str(uuid4()), identity, str(uuid4()), str(uuid4())),
                )
        assert not conn.execute(
            "SELECT 1 FROM institutions WHERE id=%s", (identity,)
        ).fetchone()


def test_common_inbox_is_scoped_by_service(p):
    from redhouse.events import consume
    from redhouse.db import transaction

    event = {"event_id": str(uuid4()), "payload": "same event, two consumers"}
    for service in ("auditoria", "custodia"):
        with p.apps[service].app_context(), transaction() as conn:
            assert consume(conn, event)
            assert not consume(conn, event)


def test_monitor_records_and_serves_status_when_postgres_unavailable(p):
    from servicio_monitoreo.routes import poll

    app = p.apps["monitoreo"]
    original = app.config["DATABASE_URL"]
    app.config["DATABASE_URL"] = "postgresql://invalid@127.0.0.1:1/unavailable"
    try:
        with app.app_context():
            result = poll()
            assert len(result["items"]) == 11
        response = p.request("monitoreo", "GET", "/api/v1/status", user="auditor1")
        assert response.status_code == 200, response.text
        assert len(response.json()["data"]["latest"]) == 11
    finally:
        app.config["DATABASE_URL"] = original


def test_migration_preserves_rows_and_repoints_all_services():
    import json
    from pathlib import Path
    import subprocess
    import tempfile
    import types
    from psycopg.types.json import Jsonb
    from scripts.migrate_shared import migrate_shared

    root = Path(__file__).resolve().parents[1]
    source = subprocess.check_output(
        [
            "git",
            "-C",
            str(root),
            "show",
            "3dcc0bb2c88ba2d1316e31859c558ed8484b78b1:apps/services/scripts/local.py",
        ],
        text=True,
    )
    module = types.ModuleType("legacy_migration_fixture")
    module.__file__ = str(root / "scripts/local.py")
    exec(compile(source, module.__file__, "exec"), module.__dict__)
    directory = Path(tempfile.mkdtemp(prefix="rh-migration-test-", dir="/tmp"))
    env = module.Environment(directory)
    try:
        env.init()
        tenant = env.state["tenants"][0]
        donor = str(uuid4())
        event = str(uuid4())
        with psycopg.connect(env.state["database_owners"]["donantes"]) as conn:
            conn.execute("SET search_path=api,pg_catalog")
            conn.execute(
                "INSERT INTO donors(id,tenant_id,folio,display_name,blood_group,consent) VALUES(%s,%s,'COPY-01','Donante ficticio','O+',true)",
                (donor, tenant),
            )
            conn.execute(
                "INSERT INTO activity_events(id,tenant_id,event) VALUES(%s,%s,%s)",
                (event, tenant, Jsonb({"type": "MIGRATION_TEST"})),
            )
        migrate_shared(directory)
        state = json.loads((directory / "state.json").read_text())
        assert state["database_layout"] == "shared-v6"
        with psycopg.connect(state["database_owners"]["donantes"]) as conn:
            assert (
                str(
                    conn.execute(
                        "SELECT id FROM donors WHERE folio='COPY-01'"
                    ).fetchone()[0]
                )
                == donor
            )
            assert conn.execute(
                "SELECT event FROM activity_events WHERE id=%s", (event,)
            ).fetchone()[0] == {"type": "MIGRATION_TEST"}
        for service in state["database_owners"]:
            config = json.loads((directory / (service + ".json")).read_text())
            assert conninfo_to_dict(config["DATABASE_URL"])["dbname"] == "red_house"
            with psycopg.connect(config["DATABASE_URL"]) as conn:
                assert (
                    conn.execute("SELECT count(*) FROM schema_version").fetchone()[0]
                    >= 2
                )
        with psycopg.connect(env.state["database_owners"]["donantes"]) as conn:
            assert conn.execute("SELECT count(*) FROM api.donors").fetchone()[0] == 1
        report = json.loads(
            (Path(state["shared_migration_backup"]) / "comparison.json").read_text()
        )
        assert report["donantes.donors"]["rows"] == 1
    finally:
        env.stop()
