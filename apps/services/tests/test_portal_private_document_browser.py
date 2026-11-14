"""Documentos privados en Chrome y monolito autónomo, con ClamD real."""

import hashlib
import json
import os
import selectors
import socket
import subprocess
import threading
import time
from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

import pytest
from PIL import Image
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, NameObject
from werkzeug.serving import make_server, make_ssl_devcert

from .conftest import QuietHandler
from .helpers import iso
from .test_continuity import autonomous as autonomous  # noqa: PLC0414 - fixture pytest
from .test_final_operations import CONFIRM


@pytest.mark.skipif(
    not os.environ.get("REDHOUSE_BROWSER_TESTS")
    or not os.environ.get("REDHOUSE_TEST_CLAMD_PORT"),
    reason="Requiere Chrome y ClamD real explícitos; no admite doble de antivirus",
)
def test_private_versions_download_and_scope_in_browser(
    autonomous, p, tmp_path, monkeypatch
):
    web = autonomous
    web.config.update(PRODUCTION=True, SESSION_COOKIE_SECURE=True)
    output = Path(os.environ["REDHOUSE_BROWSER_RESULTS"])
    output.mkdir(parents=True, exist_ok=True)
    store = tmp_path / "objects"
    store.mkdir(mode=0o700)
    docapp = p.apps["documentos"]
    for key, value in {
        "STORAGE_PROVIDER": "local",
        "STORAGE_LOCAL_ROOT": str(store),
        "CLAMD_HOST": "127.0.0.1",
        "CLAMD_PORT": int(os.environ["REDHOUSE_TEST_CLAMD_PORT"]),
        "CLAMD_VERSION_TIMEZONE": "UTC",
    }.items():
        monkeypatch.setitem(docapp.config, key, value)
    from redhouse.malware import scan

    with docapp.app_context():
        assert (
            scan(
                b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
            )
            == "INFECTED"
        )
    subject = p.ok(
        "identidad_acceso",
        "POST",
        "/api/v1/accreditations",
        user="admin1",
        data=dict(
            CONFIRM,
            issuer="Emisor sintético del ensayo",
            category="LICENSE",
            reference="BROWSER-" + uuid4().hex,
            valid_from=iso(days=-1),
            valid_until=iso(days=2),
        ),
    )
    files = []
    for index, color in enumerate(("red", "blue"), 1):
        path = tmp_path / f"version-{index}.png"
        Image.new("RGB", (16, 16), color).save(path, format="PNG")
        files.append(
            {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        )
    cert, key = make_ssl_devcert(str(tmp_path / "portal-tls"), host="localhost")
    server = make_server(
        "127.0.0.1",
        0,
        web,
        threaded=True,
        ssl_context=(cert, key),
        request_handler=QuietHandler,
    )
    base = f"https://localhost:{server.server_port}"
    monkeypatch.setitem(docapp.config, "STORAGE_PUBLIC_BASE_URL", base)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        result = subprocess.run(
            ["node", "scripts/verify_portal_private_documents.cjs"],
            input=json.dumps(
                {
                    "base": base,
                    "password": p.env.state["password"],
                    "subject": subject["id"],
                    "files": files,
                    "output": str(output),
                    "root": str(Path.cwd()),
                }
            ),
            text=True,
            capture_output=True,
            timeout=180,
            check=False,
        )
        diagnostic = tmp_path / "browser.private.log"
        diagnostic.write_text(result.stderr)
        diagnostic.chmod(0o600)
        # Browser output contains only fixed codes, never login inputs or signed URLs.
        assert result.returncode == 0, result.stdout[-1000:]
        report = json.loads((output / "browser.json").read_text())
        assert report["passed"]
        ids = report["documents"]
        assert len(ids) == len(set(ids)) == 2
        with p.owner("documentos") as conn:
            conn.execute("SET TRANSACTION READ ONLY")
            versions = conn.execute(
                "SELECT id::text,version,supersedes::text FROM document_metadata "
                "WHERE subject_id=%s ORDER BY version",
                (subject["id"],),
            ).fetchall()
            assert versions == [(ids[0], 1, None), (ids[1], 2, ids[0])]
            for identifier, source in zip(ids, files, strict=True):
                row = conn.execute(
                    "SELECT status,size,sha256,mime_type,generation FROM files WHERE id=%s",
                    (identifier,),
                ).fetchone()
                assert row[:4] == (
                    "VERIFIED",
                    Path(source["path"]).stat().st_size,
                    source["sha256"],
                    "image/png",
                )
                assert row[4]
                for action in ("DOCUMENT_PREPARED", "FILE_VERIFIED"):
                    assert (
                        conn.execute(
                            "SELECT count(*) FROM activity_events WHERE "
                            "event->>'resource_id'=%s AND event->>'action'=%s",
                            (identifier, action),
                        ).fetchone()[0]
                        == 1
                    )
        for identifier in ids:
            status = p.ok(
                "documentos",
                "GET",
                f"/api/v1/documents/{identifier}/verified",
                user="admin1",
            )
            assert status["analysis"] == "CLEAN"
        (output / "persistencia.json").write_text(
            json.dumps(
                {
                    "versions": 2,
                    "files_verified": 2,
                    "exact_bytes_downloaded": True,
                    "unique_prepared_and_verified_events": True,
                    "real_scanner_control": True,
                    "backend": "monolith_without_api_listeners",
                },
                indent=2,
            )
            + "\n"
        )
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


@contextmanager
def owned_clamd(tmp_path):
    """Detiene exclusivamente el Popen creado aquí; nunca usa el PID compartido."""
    root = Path(__file__).resolve().parents[3]
    executable = root / ".local/tools/clamav-1.5.4/sbin/clamd"
    database = Path(
        os.environ.get(
            "REDHOUSE_TEST_CLAMD_DATABASE",
            str(root / ".local/clamav-vigencia-20261113/database"),
        )
    ).resolve(strict=True)
    assert executable.is_file() and database.is_dir(), "Falta ClamD o su base local"
    directory = tmp_path / "scanner"
    directory.mkdir(mode=0o700)
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    pidfile = directory / "clamd.pid"
    configuration = directory / "clamd.conf"
    configuration.write_text(
        f"DatabaseDirectory {database}\nLogFile {directory / 'clamd.log'}\n"
        f"LogTime yes\nPidFile {pidfile}\nTCPAddr 127.0.0.1\nTCPSocket {port}\n"
        "Foreground yes\nMaxThreads 1\nStreamMaxLength 10M\n"
        "MaxFileSize 10M\nMaxScanSize 25M\n"
    )
    configuration.chmod(0o600)
    process = None
    pids = []

    def stop():
        nonlocal process
        if process is not None:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
            assert process.poll() is not None
            process = None
        with socket.socket() as probe:
            probe.settimeout(1)
            assert probe.connect_ex(("127.0.0.1", port)) != 0

    def start():
        nonlocal process
        assert process is None
        with socket.socket() as probe:
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            probe.bind(("127.0.0.1", port))
        with (directory / "stdout.private.log").open("ab") as log:
            process = subprocess.Popen(
                [str(executable), "--config-file", str(configuration)],
                stdout=log,
                stderr=subprocess.STDOUT,
                env={**os.environ, "TZ": "UTC"},
            )
        (directory / "stdout.private.log").chmod(0o600)
        pids.append(process.pid)
        deadline = time.monotonic() + 120
        while time.monotonic() < deadline:
            assert process.poll() is None, "ClamD propio terminó durante el arranque"
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=1) as client:
                    client.settimeout(1)
                    client.sendall(b"zPING\0")
                    ready = client.recv(32) == b"PONG\0"
                if ready:
                    assert int(pidfile.read_text().strip()) == process.pid
                    return
            except OSError:
                pass
            time.sleep(0.1)
        raise AssertionError("ClamD propio no quedó listo")

    try:
        start()
        yield port, start, stop, pids
    finally:
        stop()


def scanner_document_state(p, subject_id, identifier, source, status, scan_states):
    """Oráculo READ ONLY antes de cada corte y después de recuperar el mismo objeto."""
    assert str(UUID(identifier)) == identifier
    with p.owner("documentos") as conn:
        conn.execute("SET TRANSACTION READ ONLY")
        row = conn.execute(
            "SELECT f.status,f.size,f.sha256,f.mime_type,f.generation,f.owner_id::text "
            "FROM files f JOIN document_metadata d ON d.id=f.id "
            "WHERE f.id=%s AND d.subject_kind='ACCREDITATION' AND d.subject_id=%s",
            (identifier, subject_id),
        ).fetchone()
        assert row and row[:4] == (
            status,
            Path(source["path"]).stat().st_size,
            source["sha256"],
            source["mime"],
        )
        assert row[5] == p.env.state["accounts"]["admin1"]["id"]
        scans = conn.execute(
            "SELECT status,generation,sha256,engine,engine_version,signature_version,"
            "signature_at,signature_max_age_seconds FROM file_scans WHERE file_id=%s "
            "ORDER BY created_at,id",
            (identifier,),
        ).fetchall()
        assert [scan[0] for scan in scans] == scan_states
        assert len({scan[1] for scan in scans}) == 1
        for scan in scans:
            assert scan[1] and scan[2:4] == (source["sha256"], "CLAMD_INSTREAM")
            if scan[0] != "ERROR":
                assert scan[4] and scan[5].isdigit() and scan[6]
                assert scan[7] == 172800
        if status == "VERIFIED":
            assert row[4] == scans[-1][1]
        actions = Counter(
            action
            for (action,) in conn.execute(
                "SELECT event->>'action' FROM activity_events "
                "WHERE event->>'resource_id'=%s AND event->>'action' IN "
                "('DOCUMENT_PREPARED','FILE_VERIFIED','FILE_ERROR','FILE_REJECTED')",
                (identifier,),
            ).fetchall()
        )
        expected = Counter(DOCUMENT_PREPARED=1)
        expected.update({"FILE_" + status: 1})
        if status == "VERIFIED":
            expected.update(FILE_ERROR=1)
        assert actions == expected
    return {"status": status, "scans": scan_states, "generation": scans[-1][1]}


def conservation_state(p, identifier, policy):
    """Una decisión y un evento; los rechazos posteriores no cambian la política."""
    actor = p.env.state["accounts"]["admin1"]["id"]
    action = "DOCUMENT_CONSERVATION_CHANGED"
    until = datetime.fromisoformat(policy["until_utc"])
    with p.owner("documentos") as conn:
        conn.execute("SET TRANSACTION READ ONLY")
        metadata = conn.execute(
            "SELECT policy_version,retention_until,legal_hold,policy_reference "
            "FROM document_metadata WHERE id=%s",
            (identifier,),
        ).fetchone()
        assert metadata == (2, until, True, policy["reference"])
        decisions = conn.execute(
            "SELECT id::text,actor_id::text,reason,changes FROM decisions "
            "WHERE resource_id=%s AND action=%s ORDER BY id",
            (identifier, action),
        ).fetchall()
        assert len(decisions) == 1
        assert decisions[0][1:3] == (actor, policy["reason"])
        changes = decisions[0][3]
        assert changes == {
            "policy_version": 2,
            "retention_until": until.isoformat(),
            "legal_hold": True,
            "policy_reference": policy["reference"],
        }
        events = conn.execute(
            "SELECT id::text,event->>'source',event->>'actor_id',"
            "event->'metadata'->'audit'->>'reason' FROM activity_events "
            "WHERE event->>'resource_id'=%s AND event->>'action'=%s ORDER BY id",
            (identifier, action),
        ).fetchall()
        assert len(events) == 1 and events[0][1:] == (
            "documentos",
            actor,
            policy["reason"],
        )
    return {"policy": metadata, "decisions": decisions, "events": events}


@pytest.mark.skipif(
    not os.environ.get("REDHOUSE_BROWSER_TESTS")
    or os.environ.get("REDHOUSE_TEST_SCANNER_FAILURES") != "1",
    reason="Requiere Chrome y autorización explícita para el ClamD propio",
)
def test_infected_document_and_scanner_restart_in_browser(
    autonomous, p, tmp_path, monkeypatch
):
    web = autonomous
    web.config.update(PRODUCTION=True, SESSION_COOKIE_SECURE=True)
    display_zone = web.config.get("DEFAULT_DISPLAY_TIMEZONE", "UTC")
    assert display_zone in ("UTC", "America/Monterrey")
    until = (
        (datetime.now(timezone.utc) + timedelta(days=7))
        .astimezone(ZoneInfo(display_zone))
        .replace(second=0, microsecond=0)
    )
    policy = {
        "timezone": display_zone,
        "until_local": until.strftime("%Y-%m-%dT%H:%M"),
        "until_utc": until.astimezone(timezone.utc).isoformat(),
        "shorter_local": (until - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M"),
        "reference": "I06-03-sintetica-" + uuid4().hex,
        "reason": "Ensayo sintético I06-03: conservación autorizada; sin plazo normativo real.",
    }
    output = Path(os.environ["REDHOUSE_BROWSER_RESULTS"])
    output.mkdir(parents=True, exist_ok=True)
    assert not (output / "browser.json").exists(), "Conservar evidencia anterior"
    store = tmp_path / "objects"
    store.mkdir(mode=0o700)
    docapp = p.apps["documentos"]
    from redhouse.file_validation import inspect_content
    from redhouse.malware import scan

    # Misma muestra PDF comprobada con ClamD real en test_malware_documents_pdf_real.
    eicar = b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
    writer = PdfWriter()
    page = writer.add_blank_page(width=200, height=200)
    stream = DecodedStreamObject()
    stream.set_data(eicar)
    page[NameObject("/Contents")] = writer._add_object(stream.flate_encode())
    content = BytesIO()
    writer.write(content)
    infected_path = tmp_path / "infected.pdf"
    infected_path.write_bytes(content.getvalue())
    clean_path = tmp_path / "clean.png"
    Image.new("RGB", (4, 4), "red").save(clean_path, format="PNG")
    files = []
    for path, mime in ((infected_path, "application/pdf"), (clean_path, "image/png")):
        body = path.read_bytes()
        digest = hashlib.sha256(body).hexdigest()
        inspect_content(body, mime, digest)
        files.append({"path": str(path), "sha256": digest, "mime": mime})

    with owned_clamd(tmp_path) as (port, start_scanner, stop_scanner, scanner_pids):
        for key, value in {
            "STORAGE_PROVIDER": "local",
            "STORAGE_LOCAL_ROOT": str(store),
            "CLAMD_HOST": "127.0.0.1",
            "CLAMD_PORT": port,
            "CLAMD_VERSION_TIMEZONE": "UTC",
        }.items():
            monkeypatch.setitem(docapp.config, key, value)
        with docapp.app_context():
            infected_scan = scan(Path(files[0]["path"]).read_bytes())
            assert infected_scan == "INFECTED", (
                "La muestra PDF validada debe detectarse antes de Chrome"
            )
            assert scan(Path(files[1]["path"]).read_bytes()) == "CLEAN"
        subject = p.ok(
            "identidad_acceso",
            "POST",
            "/api/v1/accreditations",
            user="admin1",
            data=dict(
                CONFIRM,
                issuer="Ensayo sintético de antivirus",
                category="LICENSE",
                reference="SCANNER-" + uuid4().hex,
                valid_from=iso(days=-1),
                valid_until=iso(days=2),
            ),
        )
        cert, key = make_ssl_devcert(str(tmp_path / "portal-tls"), host="localhost")
        server = make_server(
            "127.0.0.1",
            0,
            web,
            threaded=True,
            ssl_context=(cert, key),
            request_handler=QuietHandler,
        )
        base = f"https://localhost:{server.server_port}"
        monkeypatch.setitem(docapp.config, "STORAGE_PUBLIC_BASE_URL", base)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        process = None
        observed = []
        policy_receipts = []
        try:
            diagnostic = output / "browser.private.log"
            with diagnostic.open("xb") as log:
                diagnostic.chmod(0o600)
                process = subprocess.Popen(
                    ["node", "scripts/verify_portal_private_documents.cjs"],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=log,
                    text=True,
                )
                process.stdin.write(
                    json.dumps(
                        {
                            "scenario": "scanner-failure",
                            "base": base,
                            "password": p.env.state["password"],
                            "subject": subject["id"],
                            "files": files,
                            "conservation": policy,
                            "output": str(output),
                            "root": str(Path.cwd()),
                        }
                    )
                    + "\n"
                )
                process.stdin.flush()
                deadline = time.monotonic() + 360
                with selectors.DefaultSelector() as selector:
                    selector.register(process.stdout, selectors.EVENT_READ)
                    for action in (
                        "scanner-stop",
                        "scanner-start",
                        "scanner-complete",
                        "conservation-saved",
                        "conservation-rejected",
                    ):
                        assert selector.select(max(0, deadline - time.monotonic())), (
                            "Chrome no pidió el control esperado"
                        )
                        message = json.loads(process.stdout.readline())
                        assert (
                            set(message) == {"control", "document"}
                            and message["control"] == action
                        )
                        identifier = message["document"]
                        if action == "scanner-stop":
                            assert not observed
                            scanner_document_state(
                                p,
                                subject["id"],
                                identifier,
                                files[0],
                                "REJECTED",
                                ["INFECTED"],
                            )
                            observed.append(identifier)
                            stop_scanner()
                        elif action == "scanner-start":
                            assert len(observed) == 1 and identifier not in observed
                            scanner_document_state(
                                p,
                                subject["id"],
                                identifier,
                                files[1],
                                "ERROR",
                                ["ERROR"],
                            )
                            observed.append(identifier)
                            start_scanner()
                            with docapp.app_context():
                                assert (
                                    scan(Path(files[1]["path"]).read_bytes()) == "CLEAN"
                                )
                        else:
                            assert len(observed) == 2 and identifier == observed[1]
                            if action == "scanner-complete":
                                scanner_receipt = {
                                    "infected": scanner_document_state(
                                        p,
                                        subject["id"],
                                        observed[0],
                                        files[0],
                                        "REJECTED",
                                        ["INFECTED"],
                                    ),
                                    "recovered": scanner_document_state(
                                        p,
                                        subject["id"],
                                        observed[1],
                                        files[1],
                                        "VERIFIED",
                                        ["ERROR", "CLEAN"],
                                    ),
                                    "scope": ["I06-04", "I06-05"],
                                    "conservation_pending": True,
                                }
                                (output / "persistencia-scanner.json").write_text(
                                    json.dumps(scanner_receipt, indent=2) + "\n"
                                )
                            else:
                                policy_receipts.append(
                                    conservation_state(p, identifier, policy)
                                )
                                if action == "conservation-rejected":
                                    assert (
                                        len(policy_receipts) == 2
                                        and policy_receipts[0] == policy_receipts[1]
                                    )
                        process.stdin.write(
                            json.dumps({"control": action, "passed": True}) + "\n"
                        )
                        process.stdin.flush()
                process.wait(timeout=max(1, deadline - time.monotonic()))
                assert process.returncode == 0, (
                    "Chrome falló; conservar browser.json y log privado"
                )
            report = json.loads((output / "browser.json").read_text())
            assert report["passed"] and report["scenario"] == "scanner-failure"
            assert report["documents"] == observed and len(set(observed)) == 2
            assert report["mutations"] == {"prepare": 2, "verify": 1}
            assert report["scanner_passed"] and report["conservation"] == {
                "passed": True,
                "stale_status": 412,
                "hold_status": 409,
            }
            assert (
                len(policy_receipts) == 2 and policy_receipts[0] == policy_receipts[1]
            )
            rejected = scanner_document_state(
                p, subject["id"], observed[0], files[0], "REJECTED", ["INFECTED"]
            )
            recovered = scanner_document_state(
                p, subject["id"], observed[1], files[1], "VERIFIED", ["ERROR", "CLEAN"]
            )
            with p.owner("documentos") as conn:
                conn.execute("SET TRANSACTION READ ONLY")
                assert (
                    conn.execute(
                        "SELECT count(*) FROM document_metadata WHERE subject_id=%s",
                        (subject["id"],),
                    ).fetchone()[0]
                    == 2
                )
            assert len(scanner_pids) == 2 and scanner_pids[0] != scanner_pids[1]
            (output / "persistencia.json").write_text(
                json.dumps(
                    {
                        "infected": rejected,
                        "recovered": recovered,
                        "same_document_recovered": True,
                        "unique_prepared_events": True,
                        "real_scanner_restarted": True,
                        "scanner_identity": infected_scan.metadata,
                        "conservation": policy_receipts[-1],
                        "display_timezone": display_zone,
                        "scope": ["I06-03", "I06-04", "I06-05"],
                        "backend": "monolith_without_api_listeners",
                    },
                    indent=2,
                    default=str,
                )
                + "\n"
            )
        finally:
            if process is not None:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=5)
                process.stdin.close()
                process.stdout.close()
            server.shutdown()
            thread.join(timeout=5)
            server.server_close()
