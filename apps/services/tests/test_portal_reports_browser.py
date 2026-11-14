"""I06-06: tres formatos privados por Chrome, process() y ClamD reales.

Reutiliza el fixture aislado; no inicia servicios fuera de él ni prueba otra vez
la revocación anterior a la extracción. Invoca la función real process(), no el
demonio worker.py continuo. No sustituye antivirus ni almacenamiento.
"""

import csv
import hashlib
import json
import os
import re
import selectors
import subprocess
import threading
import time
from datetime import datetime, timedelta, timezone
from io import BytesIO, StringIO
from pathlib import Path
from uuid import UUID, uuid4
from xml.etree import ElementTree
from zipfile import ZipFile
from zoneinfo import ZoneInfo

import jwt
import pytest
from pypdf import PdfReader
from werkzeug.serving import make_server, make_ssl_devcert

from .conftest import QuietHandler
from .helpers import iso
from .test_continuity import autonomous as autonomous  # noqa: PLC0414
from .test_portal_private_document_browser import owned_clamd


def parsed_download(content, fmt):
    """Oráculos de contenido independientes de render(), sin regenerar bytes."""
    if fmt == "CSV":
        return list(csv.DictReader(StringIO(content.decode("utf-8-sig"))))
    if fmt == "XLSX":
        with ZipFile(BytesIO(content)) as archive:
            sheet = ElementTree.fromstring(archive.read("xl/worksheets/sheet1.xml"))
            namespace = {
                "s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
            }
            matrix = [
                [cell.find("s:is/s:t", namespace).text or "" for cell in row]
                for row in sheet.findall("s:sheetData/s:row", namespace)
            ]
        return [dict(zip(matrix[0], row, strict=True)) for row in matrix[1:]]
    text = "\n".join(page.extract_text() for page in PdfReader(BytesIO(content)).pages)
    identifiers = re.findall(r"^id: ([0-9a-f-]{36})$", text, re.MULTILINE)
    folios = re.findall(r"^folio: (REPORTB-[A-Za-z0-9-]+)$", text, re.MULTILINE)
    records = re.findall(r"^Registro ([0-9]+)$", text, re.MULTILINE)
    assert records == [str(i) for i in range(1, 1004)]
    assert len(identifiers) == len(folios) == 1003
    return [
        {"id": identifier, "folio": folio}
        for identifier, folio in zip(identifiers, folios, strict=True)
    ]


def report_state(p, jobs, expected, prefix, actor):
    """SQL READ ONLY: población, ámbito, archivo, análisis y eventos del actor."""
    receipts = []
    with p.owner("documentos") as conn:
        conn.execute("SET TRANSACTION READ ONLY")
        for job in jobs:
            identifier = str(UUID(job["id"]))
            row = conn.execute(
                "SELECT status,format,user_id::text,tenant_id::text,context,rows,"
                "file_id::text,sealed_authorization,attempts,last_error "
                "FROM export_jobs WHERE id=%s",
                (identifier,),
            ).fetchone()
            assert row and row[:4] == (
                "COMPLETE",
                job["format"],
                actor,
                p.env.state["tenants"][0],
            )
            context, rows, file_id = row[4:7]
            assert row[7:] == (None, 1, None)
            assert context["row_count"] == len(expected) == 1003
            assert context["filters"] == {"q": prefix, "status": "QUARANTINE"}
            assert context["timezone"] == "America/Monterrey"
            assert context["role"] == "OPERATOR" and context["order"] == "ID_ASC"
            assert context["tenant_id"] == p.env.state["tenants"][0]
            assert [(r["id"], r["folio"]) for r in rows] == expected
            file = conn.execute(
                "SELECT status,owner_id::text,size,sha256,generation,mime_type,storage_provider "
                "FROM files WHERE id=%s",
                (file_id,),
            ).fetchone()
            assert file and file[:2] == ("VERIFIED", actor) and file[2] > 0 and file[4]
            assert file[6] == "local"
            scans = conn.execute(
                "SELECT status,generation,sha256,engine,engine_version,signature_version,"
                "signature_at,signature_max_age_seconds FROM file_scans WHERE file_id=%s",
                (file_id,),
            ).fetchall()
            assert len(scans) == 1
            scan = scans[0]
            assert scan[:4] == ("CLEAN", file[4], file[3], "CLAMD_INSTREAM")
            assert scan[4] and scan[5].isdigit() and scan[6] and scan[7] == 172800
            metadata = conn.execute(
                "SELECT category,subject_kind,subject_id::text,tenant_id::text,version "
                "FROM document_metadata WHERE id=%s",
                (file_id,),
            ).fetchone()
            assert metadata == (
                "REPORT",
                "REPORT",
                identifier,
                p.env.state["tenants"][0],
                1,
            )
            events = conn.execute(
                "SELECT event->>'action',event->>'actor_id',event->>'source',count(*) "
                "FROM activity_events WHERE event->>'resource_id'=%s "
                "AND event->>'action' IN ('EXPORT_REQUESTED','EXPORT_COMPLETED') "
                "GROUP BY 1,2,3 ORDER BY 1",
                (identifier,),
            ).fetchall()
            assert events == [
                (action, actor, "documentos", 1)
                for action in ("EXPORT_COMPLETED", "EXPORT_REQUESTED")
            ]
            receipts.append(
                {
                    "job": identifier,
                    "format": job["format"],
                    "file": file_id,
                    "size": file[2],
                    "sha256": file[3],
                    "generation": file[4],
                    "rows": len(rows),
                    "scan": "CLEAN",
                    "actor": actor,
                }
            )
    return receipts


@pytest.mark.skipif(
    os.environ.get("REDHOUSE_BROWSER_TESTS") != "1"
    or os.environ.get("REDHOUSE_TEST_REPORT_BROWSER") != "1",
    reason="Requiere autorización explícita para fixture, Chrome y ClamD propios",
)
def test_report_formats_and_revocation_after_completion_in_browser(
    autonomous, p, tmp_path, monkeypatch
):
    from ms_documentos import files
    from ms_documentos.reports import authorization_cipher, process
    from redhouse.security import key, redis_call

    web = autonomous
    web.config.update(
        PRODUCTION=True,
        SESSION_COOKIE_SECURE=True,
        DEFAULT_DISPLAY_TIMEZONE="America/Monterrey",
    )
    output = Path(os.environ["REDHOUSE_BROWSER_RESULTS"])
    output.mkdir(parents=True, exist_ok=True)
    assert not (output / "browser.json").exists(), "Usar directorio de resultado nuevo"
    prefix = "REPORTB-" + uuid4().hex[:8] + "-"
    actor = p.env.state["accounts"]["operator1"]["id"]
    seed = p.ok(
        "inventario",
        "POST",
        "/api/v1/resources",
        user="operator1",
        data={
            "folio": "SEED-" + uuid4().hex[:12],
            "kind": "BLOOD",
            "component": "RBC",
            "blood_group": "O-",
            "expires_at": iso(days=2),
        },
    )
    with p.owner("inventario") as conn:
        source = conn.execute("SELECT * FROM resources WHERE id=%s", (seed["id"],))
        names = [c.name for c in source.description]
        original = list(source.fetchone())
        population = []
        for n in range(1003):
            row = list(original)
            row[names.index("id")] = uuid4()
            row[names.index("folio")] = prefix + f"{n:04d}"
            row[names.index("status")] = "QUARANTINE"
            population.append(row)
        with conn.cursor() as cursor:
            cursor.executemany(
                "INSERT INTO resources("
                + ",".join(names)
                + ") VALUES("
                + ",".join(["%s"] * len(names))
                + ")",
                population,
            )
        expected = conn.execute(
            "SELECT id::text,folio FROM resources WHERE folio LIKE %s ORDER BY id",
            (prefix + "%",),
        ).fetchall()
        assert len(expected) == 1003
    store = tmp_path / "objects"
    store.mkdir(mode=0o700)
    docapp = p.apps["documentos"]
    signatures = []
    actual_access_url = files.access_url

    def observed_access_url(row, method):
        # Observación del firmante real: no modifica autenticación ni resultado.
        signatures.append((str(row["id"]), method))
        return actual_access_url(row, method)

    monkeypatch.setattr(files, "access_url", observed_access_url)
    with owned_clamd(tmp_path) as (port, _start, _stop, pids):
        for name, value in {
            "STORAGE_PROVIDER": "local",
            "STORAGE_LOCAL_ROOT": str(store),
            "CLAMD_HOST": "127.0.0.1",
            "CLAMD_PORT": port,
            "CLAMD_VERSION_TIMEZONE": "UTC",
        }.items():
            monkeypatch.setitem(docapp.config, name, value)
        cert, cert_key = make_ssl_devcert(
            str(tmp_path / "portal-tls"), host="localhost"
        )
        server = make_server(
            "127.0.0.1",
            0,
            web,
            threaded=True,
            ssl_context=(cert, cert_key),
            request_handler=QuietHandler,
        )
        base = f"https://localhost:{server.server_port}"
        monkeypatch.setitem(docapp.config, "STORAGE_PUBLIC_BASE_URL", base)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        child = None
        try:
            diagnostic = output / "browser.private.log"
            with diagnostic.open("xb") as log:
                diagnostic.chmod(0o600)
                script = os.environ.get(
                    "REDHOUSE_REPORT_BROWSER_SCRIPT",
                    "scripts/verify_portal_reports.cjs",
                )
                child = subprocess.Popen(
                    ["node", script],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=log,
                    text=True,
                )
                local = datetime.now(timezone.utc).astimezone(
                    ZoneInfo("America/Monterrey")
                )
                child.stdin.write(
                    json.dumps(
                        {
                            "base": base,
                            "root": str(Path.cwd()),
                            "password": p.env.state["password"],
                            "output": str(output),
                            "prefix": prefix,
                            "from_local": (local - timedelta(days=1)).strftime(
                                "%Y-%m-%dT%H:%M"
                            ),
                            "until_local": (local + timedelta(days=1)).strftime(
                                "%Y-%m-%dT%H:%M"
                            ),
                        }
                    )
                    + "\n"
                )
                child.stdin.flush()
                receipts, jobs, sid = None, None, None
                deadline = time.monotonic() + 300
                with selectors.DefaultSelector() as selector:
                    selector.register(child.stdout, selectors.EVENT_READ)
                    for stage in (
                        "process-jobs",
                        "revoked-before-download",
                        "downloads-complete",
                    ):
                        assert selector.select(max(0, deadline - time.monotonic())), (
                            "Chrome no pidió el control esperado"
                        )
                        line = child.stdout.readline()
                        assert line, (
                            "Chrome terminó antes del control; conservar browser.json"
                        )
                        message = json.loads(line)
                        assert message["control"] == stage
                        assert [job["format"] for job in message["jobs"]] == [
                            "CSV",
                            "PDF",
                            "XLSX",
                        ]
                        assert (
                            len({str(UUID(job["id"])) for job in message["jobs"]}) == 3
                        )
                        if stage == "process-jobs":
                            jobs = message["jobs"]
                            with p.owner("documentos") as conn:
                                conn.execute("SET TRANSACTION READ ONLY")
                                pending = conn.execute(
                                    "SELECT id::text,sealed_authorization,context->>'row_count' FROM export_jobs WHERE status='PENDING'"
                                ).fetchall()
                            assert {row[0] for row in pending} == {
                                job["id"] for job in jobs
                            }
                            assert all(row[1] and row[2] is None for row in pending)
                            with docapp.app_context():
                                bearer = (
                                    authorization_cipher()
                                    .decrypt(pending[0][1].encode())
                                    .decode()
                                    .split(" ", 1)[1]
                                )
                                sid = jwt.decode(
                                    bearer, options={"verify_signature": False}
                                )["sid"]
                                del bearer
                                process(limit=3)
                            receipts = report_state(p, jobs, expected, prefix, actor)
                            assert not signatures
                            (output / "worker-persistencia.json").write_text(
                                json.dumps(
                                    {
                                        "files": receipts,
                                        "own_clamd_pid": pids[0],
                                        "backend": "monolith_without_api_listeners",
                                    },
                                    indent=2,
                                )
                                + "\n"
                            )
                        else:
                            assert message["jobs"] == jobs
                            assert (
                                report_state(p, jobs, expected, prefix, actor)
                                == receipts
                            )
                            if stage == "revoked-before-download":
                                assert not signatures, (
                                    "La sesión revocada no debe alcanzar el firmante"
                                )
                                with p.owner("identidad_acceso") as conn:
                                    conn.execute("SET TRANSACTION READ ONLY")
                                    assert conn.execute(
                                        "SELECT user_id::text,revoked_at IS NOT NULL FROM sessions WHERE id=%s",
                                        (sid,),
                                    ).fetchone() == (actor, True)
                                with p.apps["identidad_acceso"].app_context():
                                    assert not redis_call(
                                        lambda r, session_id=sid: r.exists(
                                            key("session:" + session_id)
                                        )
                                    )
                                (output / "revocacion.json").write_text(
                                    json.dumps(
                                        {
                                            "after_complete": True,
                                            "before_first_download": True,
                                            "sql_revoked": True,
                                            "redis_session_absent": True,
                                            "signer_calls": 0,
                                            "files_preserved": 3,
                                        },
                                        indent=2,
                                    )
                                    + "\n"
                                )
                            else:
                                assert sorted(signatures) == sorted(
                                    (receipt["file"], "GET") for receipt in receipts
                                )
                                for receipt in receipts:
                                    content = (
                                        output
                                        / ("reporte." + receipt["format"].lower())
                                    ).read_bytes()
                                    assert (
                                        len(content) == receipt["size"]
                                        and hashlib.sha256(content).hexdigest()
                                        == receipt["sha256"]
                                    )
                                    rows = parsed_download(content, receipt["format"])
                                    assert [
                                        (row["id"], row["folio"]) for row in rows
                                    ] == expected
                                    if receipt["format"] != "PDF":
                                        assert all(
                                            row["reporte_row_count"] == "1003"
                                            and row["reporte_timezone"]
                                            == "America/Monterrey"
                                            for row in rows
                                        )
                                (output / "descargas-persistencia.json").write_text(
                                    json.dumps(
                                        {
                                            "rows_per_format": 1003,
                                            "formats": ["CSV", "PDF", "XLSX"],
                                            "exact_sql_identifiers_and_order": True,
                                            "exact_size_and_sha256": True,
                                            "unique_events_with_expected_actor": True,
                                            "downloads_require_new_owner_session": True,
                                        },
                                        indent=2,
                                    )
                                    + "\n"
                                )
                        child.stdin.write(
                            json.dumps(
                                {"control": stage, "passed": True, "files": receipts}
                            )
                            + "\n"
                        )
                        child.stdin.flush()
                child.wait(timeout=max(1, deadline - time.monotonic()))
                assert child.returncode == 0, (
                    "Chrome falló; conservar browser.json y log privado"
                )
                report = json.loads((output / "browser.json").read_text())
                assert (
                    report["passed"]
                    and len(report["downloads"]) == len(report["denied"]) == 3
                )
        finally:
            if child is not None and child.poll() is None:
                child.terminate()
                try:
                    child.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait(timeout=5)
            server.shutdown()
            thread.join(timeout=5)
            server.server_close()
