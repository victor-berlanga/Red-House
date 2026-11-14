"""Documentos privados en Chrome y monolito autónomo, con ClamD real."""

import hashlib
import json
import os
import subprocess
import threading
from pathlib import Path
from uuid import uuid4

import pytest
from PIL import Image
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
