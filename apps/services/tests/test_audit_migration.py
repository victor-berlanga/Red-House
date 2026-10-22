"""Migración de una copia estructural v6 con registros ficticios, nunca la instalación real."""

import subprocess
from pathlib import Path
from uuid import uuid4

import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict
from psycopg.types.json import Jsonb
from redhouse.shared_migrations import upgrade


def test_v6_migration_preserves_records_and_is_repeatable(p):
    root = Path(__file__).resolve().parents[3]
    original = subprocess.check_output(
        [
            "git",
            "-C",
            str(root),
            "show",
            "e03db262294ac9d143c71132a8c842cb6802c794:data/database/schema.sql",
        ],
        text=True,
    )
    name = "audit_migration_" + uuid4().hex
    params = conninfo_to_dict(p.env.state["database_admin"])
    with psycopg.connect(**params, autocommit=True) as admin:
        admin.execute(
            sql.SQL("CREATE DATABASE {} OWNER rh_shared_owner").format(
                sql.Identifier(name)
            )
        )
        try:
            with psycopg.connect(**{**params, "dbname": name}, autocommit=True) as conn:
                conn.execute("SET ROLE rh_shared_owner")
                conn.execute(original)
                assert (
                    conn.execute(
                        "SELECT max(version) FROM red_house.schema_migration"
                    ).fetchone()[0]
                    == 6
                )
                tenant, donor, event, region = [str(uuid4()) for _ in range(4)]
                conn.execute(
                    "INSERT INTO access_identidad_acceso.institutions(id,name,region_id) VALUES(%s,'Institución ficticia',%s)",
                    (tenant, region),
                )
                conn.execute(
                    "INSERT INTO access_donantes.donors(id,tenant_id,folio,display_name,blood_group,consent) VALUES(%s,%s,'MIGRA-01','Persona ficticia','O+',true)",
                    (donor, tenant),
                )
                payload = {
                    "resource_id": donor,
                    "occurred_at": "2026-01-01T12:00:00+00:00",
                    "metadata": {"legacy": True},
                }
                conn.execute(
                    "INSERT INTO access_auditoria.audit_events(id,tenant_id,region_id,source,action,event) VALUES(%s,%s,%s,'donantes','DONOR_REGISTERED',%s)",
                    (event, tenant, region, Jsonb(payload)),
                )

                def records():
                    return (
                        conn.execute(
                            "SELECT row_to_json(d) FROM access_donantes.donors d WHERE id=%s",
                            (donor,),
                        ).fetchone()[0],
                        conn.execute(
                            "SELECT row_to_json(e) FROM access_auditoria.audit_events e WHERE id=%s",
                            (event,),
                        ).fetchone()[0],
                    )

                before = records()
                for _ in range(2):
                    with conn.transaction():
                        assert upgrade(conn) == 7
                    assert records() == before
                assert (
                    conn.execute(
                        "SELECT count(*) FROM red_house.schema_migration WHERE version=7"
                    ).fetchone()[0]
                    == 1
                )
                assert (
                    conn.execute(
                        "SELECT count(*) FROM access_auditoria.audit_findings"
                    ).fetchone()[0]
                    == 0
                )
                assert conn.execute(
                    "SELECT has_table_privilege('rh_auditoria','access_auditoria.audit_findings','UPDATE')"
                ).fetchone()[0]
                assert not conn.execute(
                    "SELECT has_table_privilege('rh_auditoria','access_auditoria.audit_finding_actions','UPDATE')"
                ).fetchone()[0]
        finally:
            admin.execute(
                sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(name))
            )


def test_backup_inventory_includes_finding_history(p, monkeypatch):
    import importlib.util
    import json

    root = Path(__file__).resolve().parents[3]
    monkeypatch.syspath_prepend(str(root / "deployment"))
    spec = importlib.util.spec_from_file_location(
        "audit_backup_verification", root / "deployment/backup.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Sustituir solo el transporte Docker; ambas consultas se ejecutan en PostgreSQL real.
    def query(command):
        params = {
            **conninfo_to_dict(p.env.state["database_admin"]),
            "dbname": "red_house",
        }
        with psycopg.connect(**params) as conn:
            return json.dumps(conn.execute(command[-1]).fetchone()[0]).encode()

    monkeypatch.setattr(module, "command", query)
    rows = module.sql_state([])
    assert len(rows) == 75
    assert {
        "audit_findings",
        "audit_finding_actions",
        "audit_finding_links",
        "web_runtime.session_revocations",
    } <= {row["name"] for row in rows}
