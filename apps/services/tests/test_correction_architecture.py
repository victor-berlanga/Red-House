"""Independencia documental, familias de reportes y migración con restauración real."""

import os
import subprocess
import threading
from pathlib import Path
from uuid import uuid4

import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict
from psycopg.types.json import Jsonb
import pytest
from werkzeug.serving import make_server

from .conftest import QuietHandler
from .helpers import (
    resource,
    recipient_request,
    evaluation,
    reservation,
    plan,
    move,
    iso,
)
from .test_final_quality import api
from .test_final_delivery_documents import TestBucket
from .final_receivers import clamd_receiver


def test_document_owner_permissions_and_outage_isolation(p):
    for service, table in (
        ("transporte", "access_transporte.files"),
        ("documentos", "access_transporte.shipments"),
    ):
        with psycopg.connect(p.apps[service].config["DATABASE_URL"]) as conn:
            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                conn.execute("SELECT * FROM " + table)
    server = p.servers["documentos"]
    port = server.server_port
    server.shutdown()
    server.server_close()
    try:
        assert (
            p.request("transporte", "GET", "/health/ready", user=None).status_code
            == 200
        )
        assert (
            p.request(
                "transporte", "GET", "/api/v1/shipments", user="coordinator1"
            ).status_code
            == 200
        )
        assert (
            p.request(
                "transporte", "GET", "/api/v1/export-jobs", user="medical1"
            ).status_code
            == 503
        )
        assert (
            p.request(
                "inventario", "GET", "/api/v1/resources", user="operator1"
            ).status_code
            == 200
        )
    finally:
        replacement = make_server(
            "127.0.0.1",
            port,
            p.apps["documentos"],
            threaded=True,
            request_handler=QuietHandler,
        )
        p.servers["documentos"] = replacement
        threading.Thread(target=replacement.serve_forever, daemon=True).start()
    assert p.request("documentos", "GET", "/health/ready", user=None).status_code == 200


@pytest.mark.parametrize("representation", ["json", "xml"])
def test_all_report_families_formats_private_jobs_and_retries(
    p, monkeypatch, representation
):
    from ms_documentos.reports import process

    unit = resource(p)
    _, demand = recipient_request(p)
    shipment = plan(
        p, reservation(p, evaluation(p, demand, [unit]), unit)["reservation"]
    )
    for state, user in (
        ("PREPARED", "operator1"),
        ("COLLECTED", "transport1"),
        ("IN_TRANSIT", "transport1"),
        ("DELIVERED", "transport1"),
        ("ACCEPTED", "operator2"),
    ):
        shipment = move(p, shipment, state, user)
    p.drain()
    app = p.apps["documentos"]
    storage = (
        TestBucket()
    )  # Doble SDK explícito; la integración nube tiene otra prueba.
    monkeypatch.setitem(app.config, "GCS_BUCKET", "private-test")
    monkeypatch.setitem(app.extensions, "gcs_client", storage)
    jobs = []
    with clamd_receiver() as (
        port,
        received,
    ):  # Receptor TCP de protocolo, no firmas reales.
        monkeypatch.setitem(app.config, "CLAMD_HOST", "127.0.0.1")
        monkeypatch.setitem(app.config, "CLAMD_PORT", port)
        for family in (
            "INVENTORY",
            "REQUESTS",
            "EXPIRY",
            "SHIPMENTS",
            "CUSTODY",
            "ACTIVITY",
            "TRACEABILITY",
        ):
            user = "auditor1" if family == "ACTIVITY" else "medical2"
            for fmt in ("PDF", "CSV", "XLSX"):
                body = dict(
                    report=family,
                    format=fmt,
                    from_at=iso(days=-1),
                    until_at=iso(days=4),
                )
                if family in ("CUSTODY", "TRACEABILITY"):
                    body["subject_id"] = (
                        shipment["id"] if family == "CUSTODY" else unit["id"]
                    )
                job = api(
                    p, "documentos", "/api/v1/export-jobs", body, user, representation
                )
                filtered = api(
                    p,
                    "documentos",
                    "/api/v1/export-jobs?"
                    + "q="
                    + job["id"]
                    + "&report="
                    + family
                    + "&format="
                    + fmt
                    + "&status=PENDING&sort=DATE_ASC&page_size=1",
                    user=user,
                    fmt=representation,
                    method="GET",
                )
                assert (
                    filtered["total"] == 1 and filtered["items"][0]["id"] == job["id"]
                )
                assert (
                    p.request(
                        "documentos",
                        "GET",
                        "/api/v1/export-jobs/" + job["id"],
                        user="medical1",
                    ).status_code
                    == 403
                )
                # La extracción ocurre en el worker (ms_documentos.reports.hydrate):
                # al crear el trabajo solo se guarda la credencial sellada.
                with p.owner("documentos") as conn:
                    rows, sealed = conn.execute(
                        "SELECT rows, sealed_authorization FROM export_jobs WHERE id=%s",
                        (job["id"],),
                    ).fetchone()
                assert rows == [] and sealed, family
                with app.app_context():
                    process(limit=100)
                    process(limit=100)
                with p.owner("documentos") as conn:
                    rows, sealed = conn.execute(
                        "SELECT rows, sealed_authorization FROM export_jobs WHERE id=%s",
                        (job["id"],),
                    ).fetchone()
                assert rows and sealed is None, family
                assert not any(
                    set(row)
                    & {"display_name", "value", "studies", "password_hash", "latitude"}
                    for row in rows
                )
                if family == "SHIPMENTS":
                    observed = next(row for row in rows if row["id"] == shipment["id"])
                    assert float(observed["observed_seconds"]) >= 0
                ready = api(
                    p,
                    "documentos",
                    "/api/v1/export-jobs/" + job["id"],
                    user=user,
                    fmt=representation,
                    method="GET",
                )
                assert ready["status"] == "COMPLETE", ready
                assert ready["attempts"] == 1
                api(
                    p,
                    "transporte",
                    f"/api/v1/files/{ready['file_id']}/download",
                    user=user,
                    fmt=representation,
                    method="GET",
                )
                assert (
                    p.request(
                        "transporte",
                        "GET",
                        f"/api/v1/files/{ready['file_id']}/download",
                        user="medical1",
                    ).status_code
                    == 403
                )
                jobs.append(ready)
        assert len(jobs) == 21 and len({job["file_id"] for job in jobs}) == 21
        # Dos entradas del mismo contrato comparten exactamente la misma clave.
        body = dict(
            report="INVENTORY", format="CSV", from_at=iso(days=-1), until_at=iso(days=1)
        )
        key = uuid4().hex
        old = p.ok(
            "transporte",
            "POST",
            "/api/v1/export-jobs",
            user="medical2",
            data=body,
            key=key,
        )
        current = p.ok(
            "documentos",
            "POST",
            "/api/v1/export-jobs",
            user="medical2",
            data=body,
            key=key,
        )
        assert old == current
        with monkeypatch.context() as unavailable:
            unavailable.setitem(app.config, "CLAMD_PORT", 1)
            with app.app_context():
                process(limit=100)
        failed = p.ok(
            "documentos", "GET", "/api/v1/export-jobs/" + current["id"], user="medical2"
        )
        assert failed["status"] == "RETRYABLE"
        retry_key = uuid4().hex
        body = {"human_confirmation": True, "reason": "Recuperación sintética"}
        for service in ("documentos", "transporte"):
            assert (
                p.ok(
                    service,
                    "POST",
                    f"/api/v1/export-jobs/{current['id']}/retry",
                    data=body,
                    user="medical2",
                    key=retry_key,
                )["status"]
                == "PENDING"
            )
        with app.app_context():
            process(limit=100)
        done = p.ok(
            "documentos", "GET", "/api/v1/export-jobs/" + current["id"], user="medical2"
        )
        assert done["status"] == "COMPLETE" and done["attempts"] == 2
        with p.owner("documentos") as conn:
            assert (
                conn.execute(
                    "SELECT count(*) FROM files WHERE id=%s", (done["file_id"],)
                ).fetchone()[0]
                == 1
            )


def test_schema_11_extraction_backup_restore_and_idempotency(p, tmp_path):
    from redhouse.shared_migrations import LATEST_VERSION, upgrade

    root = Path(__file__).resolve().parents[3]
    source = subprocess.check_output(
        ["git", "show", "8909baf:data/database/schema.sql"], cwd=root, text=True
    )
    params = conninfo_to_dict(p.env.state["database_admin"])
    databases = ["correction_" + uuid4().hex, "restored_" + uuid4().hex]
    binary = Path(p.env.state["infrastructure_commands"]["postgres"][0]).parent
    with psycopg.connect(**params, autocommit=True) as admin:
        for name in databases:
            admin.execute(
                sql.SQL("CREATE DATABASE {} OWNER rh_shared_owner").format(
                    sql.Identifier(name)
                )
            )
        try:
            with psycopg.connect(
                **{**params, "dbname": databases[0]}, autocommit=True
            ) as conn:
                conn.execute("SET ROLE rh_shared_owner")
                conn.execute(source)
                for version in range(8, 12):
                    conn.execute(
                        (
                            root
                            / f"apps/services/redhouse/shared_migrations/{version:03}.sql"
                        ).read_text()
                    )
                # En v11 estas vistas eran de Transporte; no duplicar sus tablas.
                for table in ("document_metadata", "file_scans", "export_jobs"):
                    conn.execute(
                        f"CREATE VIEW access_transporte.{table} AS SELECT * FROM red_house.{table}"
                    )
                tenant, user, job, file, event = [str(uuid4()) for _ in range(5)]
                conn.execute(
                    "INSERT INTO access_identidad_acceso.institutions(id,name,region_id) VALUES(%s,'Migración sintética',%s)",
                    (tenant, p.env.state["region_id"]),
                )
                conn.execute(
                    "INSERT INTO access_identidad_acceso.users(id,tenant_id,username,password_hash,role) VALUES(%s,%s,'migration-test','unusable','MEDICAL')",
                    (user, tenant),
                )
                conn.execute(
                    "INSERT INTO access_transporte.files(id,owner_id,object_path,mime_type,size,sha256) VALUES(%s,%s,'synthetic/preserved.pdf','application/pdf',10,%s)",
                    (file, user, "a" * 64),
                )
                conn.execute(
                    "INSERT INTO red_house.export_jobs(id,tenant_id,user_id,report,format,rows) VALUES(%s,%s,%s,'INVENTORY','CSV','[]')",
                    (job, tenant, user),
                )
                payload = dict(
                    event_id=event,
                    source="transporte",
                    action="EXPORT_REQUESTED",
                    resource_id=job,
                    tenant_id=tenant,
                    region_id=p.env.state["region_id"],
                    metadata={},
                    occurred_at=iso(),
                )
                conn.execute(
                    "INSERT INTO access_transporte.activity_events(id,tenant_id,event) VALUES(%s,%s,%s)",
                    (event, tenant, Jsonb(payload)),
                )
                conn.execute(
                    "INSERT INTO access_transporte.outbox(id,event_id,target,event) VALUES(%s,%s,'auditoria',%s)",
                    (str(uuid4()), event, Jsonb(payload)),
                )
                conn.execute(
                    "INSERT INTO access_transporte.idempotency(id,user_id,key,operation,fingerprint,result) VALUES(%s,%s,'migration-key','export_create',%s,%s)",
                    (str(uuid4()), user, "b" * 64, Jsonb({"id": job})),
                )
                before = conn.execute(
                    "SELECT row_to_json(f) FROM access_transporte.files f WHERE id=%s",
                    (file,),
                ).fetchone()[0]
                backup = tmp_path / "before-13.dump"
                arguments = [
                    "--host",
                    params["host"],
                    "--port",
                    str(params["port"]),
                    "--username",
                    params["user"],
                ]
                env = dict(os.environ, PGPASSWORD=params.get("password", ""))
                subprocess.run(
                    [
                        str(binary / "pg_dump"),
                        *arguments,
                        "--dbname",
                        databases[0],
                        "--format=custom",
                        "--file",
                        str(backup),
                    ],
                    env=env,
                    check=True,
                    capture_output=True,
                )
                for _ in range(2):
                    with conn.transaction():
                        assert upgrade(conn) == LATEST_VERSION
                # Migración 019: las filas previas conservan su proveedor GCS.
                assert conn.execute(
                    "SELECT row_to_json(f) FROM access_documentos.files f WHERE id=%s",
                    (file,),
                ).fetchone()[0] == {**before, "storage_provider": "gcs"}
                assert conn.execute(
                    "SELECT result FROM access_documentos.idempotency WHERE key='migration-key'"
                ).fetchone()[0] == {"id": job}
                assert (
                    conn.execute(
                        "SELECT event FROM access_transporte.outbox WHERE event_id=%s",
                        (event,),
                    ).fetchone()[0]
                    == payload
                )
                assert (
                    conn.execute(
                        "SELECT region_id::text FROM access_documentos.export_jobs WHERE id=%s",
                        (job,),
                    ).fetchone()[0]
                    == p.env.state["region_id"]
                )
                assert not conn.execute(
                    "SELECT has_table_privilege('rh_transporte','access_transporte.files','SELECT')"
                ).fetchone()[0]
                subprocess.run(
                    [
                        str(binary / "pg_restore"),
                        *arguments,
                        "--dbname",
                        databases[1],
                        "--exit-on-error",
                        str(backup),
                    ],
                    env=env,
                    check=True,
                    capture_output=True,
                )
            with psycopg.connect(**{**params, "dbname": databases[1]}) as restored:
                assert (
                    restored.execute(
                        "SELECT max(version) FROM red_house.schema_migration"
                    ).fetchone()[0]
                    == 11
                )
                assert (
                    restored.execute(
                        "SELECT row_to_json(f) FROM access_transporte.files f WHERE id=%s",
                        (file,),
                    ).fetchone()[0]
                    == before
                )
                assert restored.execute(
                    "SELECT result FROM access_transporte.idempotency WHERE key='migration-key'"
                ).fetchone()[0] == {"id": job}
        finally:
            for name in databases:
                admin.execute(
                    sql.SQL("DROP DATABASE {} WITH (FORCE)").format(
                        sql.Identifier(name)
                    )
                )
