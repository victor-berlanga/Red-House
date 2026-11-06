"""Restore a populated schema-14 copy, then upgrade twice without touching installations."""

import os
import subprocess
from pathlib import Path
from uuid import uuid4

import psycopg
import pytest
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict


@pytest.mark.parametrize("starting_version", [14, 15])
def test_schema14_backup_restore_upgrade15_preserves_history_acl(
    p, tmp_path, starting_version
):
    from redhouse.shared_migrations import LATEST_VERSION, upgrade

    root = Path(__file__).resolve().parents[3]
    original = subprocess.check_output(
        ["git", "show", "8909baf:data/database/schema.sql"], cwd=root, text=True
    )
    params = conninfo_to_dict(p.env.state["database_admin"])
    names = ["stage02_" + uuid4().hex, "stage02_restore_" + uuid4().hex]
    binary = Path(p.env.state["infrastructure_commands"]["postgres"][0]).parent
    with psycopg.connect(**params, autocommit=True) as admin:
        for name in names:
            admin.execute(
                sql.SQL("CREATE DATABASE {} OWNER rh_shared_owner").format(
                    sql.Identifier(name)
                )
            )
        try:
            with psycopg.connect(
                **{**params, "dbname": names[0]}, autocommit=True
            ) as conn:
                conn.execute("SET ROLE rh_shared_owner")
                conn.execute(original)
                for version in range(8, starting_version + 1):
                    conn.execute(
                        (
                            root
                            / f"apps/services/redhouse/shared_migrations/{version:03}.sql"
                        ).read_text()
                    )
                tenant, actor, profile, sample, result, unit = [
                    str(uuid4()) for _ in range(6)
                ]
                conn.execute(
                    "INSERT INTO access_identidad_acceso.institutions(id,name,region_id) VALUES(%s,'Institución ficticia',%s)",
                    (tenant, p.env.state["region_id"]),
                )
                conn.execute(
                    "INSERT INTO access_identidad_acceso.users(id,tenant_id,username,password_hash,role) VALUES(%s,%s,'migration_stage02','unusable','MEDICAL')",
                    (actor, tenant),
                )
                conn.execute(
                    "INSERT INTO red_house.resource(resource_id,resource_kind,tenant_id,region_id,folio,current_institution_id,component,blood_group,expires_at) VALUES(%s,'ORGAN',%s,%s,'MIGRATION-02',%s,'KIDNEY','O+',now()+interval '1 day')",
                    (unit, tenant, p.env.state["region_id"], tenant),
                )
                conn.execute(
                    "INSERT INTO red_house.lab_profiles(id,tenant_id,name,kind,component,version,required_tests,source,synthetic,author_id,effective_at) VALUES(%s,%s,'Perfil previo','ORGAN','KIDNEY',1,'[\"HLA\"]','Síntesis anterior',true,%s,now())",
                    (profile, tenant, actor),
                )
                conn.execute(
                    "INSERT INTO red_house.lab_samples(id,tenant_id,resource_id,profile_id,identifier,collected_at,author_id) VALUES(%s,%s,%s,%s,'Muestra anterior',now(),%s)",
                    (sample, tenant, unit, profile, actor),
                )
                conn.execute(
                    "INSERT INTO red_house.lab_results(id,sample_id,tenant_id,test_code,value,method,laboratory,reference,measured_at,author_id,version) VALUES(%s,%s,%s,'HLA','Declaración histórica','Método','Lab','Referencia',now(),%s,1)",
                    (result, sample, tenant, actor),
                )
                historical_tables = ["lab_profiles", "lab_samples", "lab_results"]
                if starting_version == 15:
                    graph, run, action = [str(uuid4()) for _ in range(3)]
                    conn.execute(
                        "INSERT INTO red_house.regional_graphs(id,tenant_id,author_id,name,version,source,observed_at,valid_until,synthetic,region,quality,nodes,edges) VALUES(%s,%s,%s,'Grafo anterior',1,'Síntesis histórica',now(),now()+interval '1 day',true,'Nuevo León','Prueba','[]','[]')",
                        (graph, tenant, actor),
                    )
                    conn.execute(
                        "INSERT INTO red_house.decision_runs(id,tenant_id,author_id,algorithm_version,source,snapshot,result,fingerprint,elapsed_ms,synthetic) VALUES(%s,%s,%s,'REGIONAL-DIJKSTRA-2.0','Historial ficticio','{}','{}','original',1,true)",
                        (run, tenant, actor),
                    )
                    conn.execute(
                        "INSERT INTO red_house.rule_actions(id,profile_id,tenant_id,actor_id,sequence,state,reason) VALUES(%s,%s,%s,%s,1,'IN_REVIEW','Revisión ficticia')",
                        (action, profile, tenant, actor),
                    )
                    historical_tables += [
                        "regional_graphs",
                        "decision_runs",
                        "rule_actions",
                    ]
                historical = {
                    table: conn.execute(
                        "SELECT to_jsonb(t) FROM red_house." + table + " t ORDER BY id"
                    ).fetchall()
                    for table in historical_tables
                }
            backup = tmp_path / "schema14.dump"
            env = dict(os.environ, PGPASSWORD=params.get("password", ""))
            args = [
                "--host",
                params["host"],
                "--port",
                str(params["port"]),
                "--username",
                params["user"],
            ]
            subprocess.run(
                [
                    str(binary / "pg_dump"),
                    *args,
                    "--dbname",
                    names[0],
                    "--format=custom",
                    "--file",
                    str(backup),
                ],
                env=env,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                [str(binary / "pg_restore"), *args, "--dbname", names[1], str(backup)],
                env=env,
                check=True,
                capture_output=True,
            )
            with psycopg.connect(**{**params, "dbname": names[1]}) as conn:
                assert (
                    conn.execute(
                        "SELECT max(version) FROM red_house.schema_migration"
                    ).fetchone()[0]
                    == starting_version
                )
                assert upgrade(conn) == LATEST_VERSION
                assert upgrade(conn) == LATEST_VERSION
                for table, rows in historical.items():
                    after = conn.execute(
                        "SELECT to_jsonb(t) FROM red_house." + table + " t ORDER BY id"
                    ).fetchall()
                    assert len(rows) == len(after)
                    assert all(
                        all(new[0][key] == value for key, value in old[0].items())
                        for old, new in zip(rows, after)
                    )
                assert conn.execute(
                    "SELECT has_table_privilege('rh_compatibilidad','access_compatibilidad.rule_actions','INSERT'),has_table_privilege('rh_compatibilidad','access_compatibilidad.rule_actions','UPDATE')"
                ).fetchone() == (True, False)
                assert conn.execute(
                    "SELECT has_column_privilege('rh_auditoria','access_auditoria.anomaly_reviews','evidence','UPDATE')"
                ).fetchone() == (False,)
            # The original backup restores independently and remains schema 14.
            with psycopg.connect(**{**params, "dbname": names[0]}) as conn:
                assert (
                    conn.execute(
                        "SELECT max(version) FROM red_house.schema_migration"
                    ).fetchone()[0]
                    == starting_version
                )
        finally:
            for name in names:
                admin.execute(sql.SQL("DROP DATABASE {}").format(sql.Identifier(name)))
