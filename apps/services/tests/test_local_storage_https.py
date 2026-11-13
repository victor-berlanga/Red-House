"""Public generated Nginx, TLS, autonomous portal and real local ClamD."""

import hashlib
import importlib.util
import os
import random
import re
import subprocess
import threading
from io import BytesIO
from pathlib import Path
from urllib.parse import urlsplit
from uuid import uuid4

import pytest
import requests
from PIL import Image
from scripts.local import free_port
from werkzeug.serving import make_server

from .conftest import QuietHandler
from .helpers import iso
from .test_continuity import autonomous  # noqa: F401
from .test_final_operations import CONFIRM
from .test_nginx_runtime import certificate, wait_live

ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.skipif(
    not os.environ.get("REDHOUSE_TEST_NGINX")
    or not os.environ.get("REDHOUSE_TEST_CLAMD_PORT"),
    reason="Requiere Nginx y ClamD reales para TLS y análisis",
)
def test_local_storage_https_large_body_and_revocation(p, tmp_path, monkeypatch):
    document = p.apps["documentos"]
    directory = tmp_path / "files"
    directory.mkdir(mode=0o700)
    monkeypatch.setitem(document.config, "STORAGE_PROVIDER", "local")
    monkeypatch.setitem(document.config, "STORAGE_LOCAL_ROOT", str(directory))
    monkeypatch.setitem(document.config, "CLAMD_HOST", "127.0.0.1")
    monkeypatch.setitem(
        document.config, "CLAMD_PORT", int(os.environ["REDHOUSE_TEST_CLAMD_PORT"])
    )
    subject = p.ok(
        "identidad_acceso",
        "POST",
        "/api/v1/accreditations",
        user="admin1",
        data=dict(
            CONFIRM,
            issuer="Ensayo TLS",
            category="LICENSE",
            reference=uuid4().hex,
            valid_from=iso(days=-1),
            valid_until=iso(days=2),
        ),
    )
    # Un listener web real se detiene antes de emitir o usar capacidades API.
    from flask import Flask

    web = make_server(
        "127.0.0.1",
        0,
        Flask("stopped_web"),
        threaded=True,
        request_handler=QuietHandler,
    )
    thread = threading.Thread(target=web.serve_forever, daemon=True)
    thread.start()
    web_port = web.server_port
    web.shutdown()
    web.server_close()
    thread.join(timeout=5)
    assert not thread.is_alive()
    nginx = None
    try:
        spec = importlib.util.spec_from_file_location(
            "public_storage_test", ROOT / "deployment/gcp/configure_public.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        config_root = tmp_path / "gateway"
        config_root.mkdir()
        (config_root / "apps").mkdir()
        (config_root / "web.json").write_text("{}")
        for service in p.urls:
            (config_root / "apps" / (service + ".json")).write_text("{}")
        module.configure(config_root, "127.0.0.1")
        certificate(config_root / "tls")
        config = (config_root / "public.nginx.conf").read_text()

        def upstream(match):
            name = match.group(1)
            port = (
                p.servers["documentos"].server_port
                if name.startswith("documentos-")
                else web_port
            )
            return f"server 127.0.0.1:{port} resolve"

        config = re.sub(r"server ([a-z-]+):8080 resolve", upstream, config)
        ports = {}

        def listener(match):
            old = int(match.group(1))
            if old not in ports:
                ports[old] = free_port()
            return f"listen 127.0.0.1:{ports[old]}"

        config = re.sub(r"listen (\d+)", listener, config)
        config = config.replace("/etc/nginx/tls", str(config_root / "tls")).replace(
            "/tmp/", str(config_root) + "/"
        )
        config_path = config_root / "runtime.nginx.conf"
        config_path.write_text(config)
        binary = os.environ["REDHOUSE_TEST_NGINX"]
        subprocess.run(
            [binary, "-t", "-p", str(config_root), "-c", str(config_path)],
            check=True,
            capture_output=True,
        )
        with (config_root / "nginx.log").open("wb") as output:
            nginx = subprocess.Popen(
                [
                    binary,
                    "-p",
                    str(config_root),
                    "-c",
                    str(config_path),
                    "-g",
                    "daemon off;",
                ],
                stdout=output,
                stderr=subprocess.STDOUT,
            )
        wait_live(f"http://127.0.0.1:{ports[8080]}/health/live", nginx)
        origin = f"https://127.0.0.1:{ports[8443]}"
        monkeypatch.setitem(document.config, "STORAGE_PUBLIC_BASE_URL", origin)
        source = random.Random(3107).randbytes(512 * 512 * 3)
        image = BytesIO()
        Image.frombytes("RGB", (512, 512), source).save(image, format="PNG")
        content = image.getvalue()
        assert 262144 < len(content) <= 10 * 1024 * 1024
        item = p.ok(
            "documentos",
            "POST",
            "/api/v1/documents",
            user="admin1",
            data={
                "subject_kind": "ACCREDITATION",
                "subject_id": subject["id"],
                "category": "ACCREDITATION",
                "mime_type": "image/png",
                "size": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
                "policy_reference": "TLS sintético",
            },
        )
        assert urlsplit(item["upload_url"]).path.startswith("/storage/v1/objects/")
        ca = str(config_root / "tls/fullchain.pem")
        session = requests.Session()
        session.trust_env = False
        try:
            sent = session.put(
                item["upload_url"],
                data=content,
                headers=item["upload_headers"],
                verify=ca,
                timeout=20,
                allow_redirects=False,
            )
            assert sent.status_code == 201, sent.text
            assert (
                session.put(
                    item["upload_url"],
                    data=content,
                    headers=item["upload_headers"],
                    verify=ca,
                    timeout=20,
                ).status_code
                == 412
            )
            assert (
                p.ok(
                    "documentos",
                    "POST",
                    "/api/v1/files/" + item["id"] + "/verify",
                    user="admin1",
                )["status"]
                == "VERIFIED"
            )
            download = p.ok(
                "documentos",
                "GET",
                "/api/v1/files/" + item["id"] + "/download",
                user="admin1",
            )["download_url"]
            received = session.get(
                download, verify=ca, timeout=20, allow_redirects=False
            )
            assert received.status_code == 200 and received.content == content
            assert (
                p.request(
                    "identidad_acceso", "POST", "/api/v1/auth/logout", user="admin1"
                ).status_code
                == 200
            )
            assert session.get(download, verify=ca, timeout=20).status_code == 401
            renewed = p.ok(
                "identidad_acceso",
                "POST",
                "/api/v1/auth/login",
                user=None,
                data={"username": "admin1", "password": p.env.state["password"]},
            )
            p.tokens["admin1"] = renewed["access_token"]
        finally:
            session.close()
        log = (config_root / "nginx.log").read_text(errors="replace")
        assert (
            urlsplit(item["upload_url"]).path not in log
            and urlsplit(download).path not in log
        )
    finally:
        if nginx is not None and nginx.poll() is None:
            nginx.terminate()
            nginx.wait(timeout=10)
