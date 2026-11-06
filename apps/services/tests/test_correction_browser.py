"""Navegador real con TLS/cookies seguras y las cuatro políticas operativas activas."""

import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import threading
import time
from uuid import uuid4

import pytest
from werkzeug.security import generate_password_hash
from werkzeug.serving import make_server, make_ssl_devcert

from .conftest import QuietHandler
from .helpers import iso, route
from .test_correction_backend import laboratory
from .test_web_integration import web as web


@pytest.mark.skipif(
    not os.environ.get("REDHOUSE_BROWSER_TESTS"),
    reason="Activar REDHOUSE_BROWSER_TESTS=1; requiere Chrome/Playwright y Docker o REDHOUSE_TEST_NGINX para gateway WSS.",
)
def test_operational_browser_corrections(web, p, monkeypatch, tmp_path):
    from ms_identidad_acceso.strong_auth import totp
    from ms_documentos.reports import process

    root = Path(__file__).resolve().parents[3]
    password = secrets.token_urlsafe(28)
    accounts = {}
    for alias, role, tenant in (
        ("origin", "MEDICAL", 0),
        ("destination", "MEDICAL", 1),
        ("coordinator", "COORDINATOR", 0),
        ("admin", "ADMIN", 0),
        ("limited", "OPERATOR", 0),
    ):
        identifier, username = str(uuid4()), "browser_" + alias + "_" + uuid4().hex[:8]
        with p.owner("identidad_acceso") as conn:
            conn.execute(
                "INSERT INTO users(id,tenant_id,username,password_hash,role) VALUES(%s,%s,%s,%s,%s)",
                (
                    identifier,
                    p.env.state["tenants"][tenant],
                    username,
                    generate_password_hash(password),
                    role,
                ),
            )
        account = dict(id=identifier, username=username, role=role)
        if role in ("MEDICAL", "COORDINATOR", "ADMIN"):
            enrollment = p.ok(
                "identidad_acceso",
                "POST",
                "/api/v1/auth/mfa/enrollment",
                user=None,
                data={"username": username, "password": password},
            )
            counter = int(time.time()) // 30 - 1
            p.ok(
                "identidad_acceso",
                "POST",
                "/api/v1/auth/mfa/confirm",
                user=None,
                data={
                    "challenge": enrollment["challenge"],
                    "code": totp(enrollment["secret"], counter),
                },
            )
            account.update(secret=enrollment["secret"], lastCounter=counter)
        accounts[alias] = account
    unit = p.ok(
        "inventario",
        "POST",
        "/api/v1/resources",
        user="operator1",
        data={
            "folio": "BROWSER-" + uuid4().hex[:10],
            "kind": "BLOOD",
            "component": "RBC",
            "blood_group": "O-",
            "expires_at": iso(days=2),
        },
    )
    profile, body, result = laboratory(p, unit, "json")
    recipient = p.ok(
        "receptores",
        "POST",
        "/api/v1/recipients",
        user="medical2",
        data={
            "folio": "BROWSER-P-" + uuid4().hex[:8],
            "display_name": "Paciente sintético navegador",
            "kind": "BLOOD",
            "blood_group": "A+",
            "studies": "Referencia sintética autorizada",
        },
    )
    route(p)
    for app in p.apps.values():
        for key, value in {
            "MFA_REQUIRED_ROLES": ["ADMIN", "MEDICAL", "COORDINATOR"],
            "REAUTH_REQUIRED_OPERATIONS": [
                "resource_release",
                "lab_result_review",
                "reservation_create",
                "resource_destination",
            ],
            "REQUIRE_LAB_PROFILE": True,
            "REQUIRE_ORGAN_AUTHORIZATION": True,
        }.items():
            monkeypatch.setitem(app.config, key, value)
    web.config.update(
        PRODUCTION=True, SESSION_COOKIE_SECURE=True, JWT_COOKIE_SECURE=True
    )
    docapp = p.apps["documentos"]
    if os.environ.get("REDHOUSE_GCS_TEST_BUCKET"):
        monkeypatch.setitem(
            docapp.config, "GCS_BUCKET", os.environ["REDHOUSE_GCS_TEST_BUCKET"]
        )
        monkeypatch.setitem(
            docapp.config, "GCS_PROJECT", os.environ.get("GOOGLE_CLOUD_PROJECT")
        )

    def workers():
        with docapp.app_context():
            process(limit=30)
        p.drain()
        return {"processed": True}

    web.add_url_rule(
        "/test/run-workers",
        "test_run_workers",
        web.extensions["csrf"].exempt(workers),
        methods=["POST"],
    )

    def expire_session():
        from flask import request
        from src.integration import sessions

        sid = request.cookies[web.config["JWT_COOKIE_NAME"]]
        value = sessions.load(sid)
        value["session_expires"] = time.time() - 1
        sessions.redis_client().set(
            sessions.redis_key("session", sessions.key(sid)),
            sessions.cipher().encrypt(json.dumps(value).encode()),
            ex=60,
        )
        return {"expired": True}

    web.add_url_rule(
        "/test/expire-session",
        "test_expire_session",
        web.extensions["csrf"].exempt(expire_session),
        methods=["POST"],
    )
    cert, key = make_ssl_devcert(str(tmp_path / "browser-tls"), host="localhost")
    server = make_server(
        "127.0.0.1",
        0,
        web,
        threaded=True,
        ssl_context=(cert, key),
        request_handler=QuietHandler,
    )
    threading.Thread(target=server.serve_forever, daemon=True).start()
    from werkzeug.middleware.proxy_fix import ProxyFix

    transport = p.apps["transporte"]
    monkeypatch.setattr(
        transport,
        "wsgi_app",
        ProxyFix(transport.wsgi_app, x_proto=1, x_for=0, x_host=0),
    )
    # Nginx real con upstreams del fixture y TLS; binario local o imagen Docker.
    native_nginx = os.environ.get("REDHOUSE_TEST_NGINX")
    local_process = None
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        local_port = sock.getsockname()[1]
    upstream = "127.0.0.1" if native_nginx else "host.docker.internal"
    certificate_path = str(tmp_path) if native_nginx else "/evidence"
    listen = f"127.0.0.1:{local_port}" if native_nginx else "8443"
    gateway_name = "redhouse-correction-" + uuid4().hex[:10]
    nginx = tmp_path / "nginx.conf"
    nginx.write_text(f"""pid nginx.pid;
error_log stderr warn;
events {{ worker_connections 128; }}
http {{ access_log off; server {{ listen {listen} ssl;
ssl_certificate {certificate_path}/browser-tls.crt; ssl_certificate_key {certificate_path}/browser-tls.key;
ssl_protocols TLSv1.2 TLSv1.3;
location /services/transporte/ws/v1/tracking/ {{
 proxy_pass http://{upstream}:{p.servers["transporte"].server_port}/ws/v1/tracking/;
 proxy_http_version 1.1; proxy_set_header Upgrade $http_upgrade; proxy_set_header Connection "upgrade";
 proxy_set_header X-Forwarded-Proto https; proxy_buffering off; proxy_read_timeout 75s; proxy_send_timeout 10s;
}}
location / {{ proxy_pass https://{upstream}:{server.server_port}; proxy_set_header Host $http_host; proxy_read_timeout 180s; }}
}} }}""")
    if native_nginx:
        (tmp_path / "logs").mkdir()
        local_process = subprocess.Popen(
            [
                native_nginx,
                "-p",
                str(tmp_path) + "/",
                "-c",
                str(nginx),
                "-g",
                "daemon off;",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        for _ in range(100):
            assert local_process.poll() is None, "Nginx local no inició"
            try:
                with socket.create_connection(("127.0.0.1", local_port), timeout=0.1):
                    break
            except OSError:
                time.sleep(0.1)
        base = f"https://localhost:{local_port}"
    else:
        subprocess.run(
            [
                "docker",
                "run",
                "--detach",
                "--rm",
                "--name",
                gateway_name,
                "--publish",
                "127.0.0.1::8443",
                "--mount",
                f"type=bind,source={tmp_path},target=/evidence,readonly",
                "--mount",
                f"type=bind,source={nginx},target=/etc/nginx/nginx.conf,readonly",
                "nginx:1.28-alpine",
            ],
            check=True,
            capture_output=True,
            timeout=90,
        )
        published = subprocess.check_output(
            ["docker", "port", gateway_name, "8443"], text=True
        ).strip()
        base = "https://localhost:" + published.rsplit(":", 1)[1]
    monkeypatch.setitem(transport.config, "TRACKING_ALLOWED_ORIGINS", [base])
    output = (
        Path(os.environ.get("REDHOUSE_BROWSER_RESULTS", str(tmp_path / "browser")))
        / "correcciones-operativas"
    )
    output.mkdir(parents=True, exist_ok=True)
    try:
        completed = subprocess.run(
            ["node", str(root / "scripts/verify_backend_corrections.cjs")],
            input=json.dumps(
                {
                    "base": base,
                    "gateway": "Nginx 1.28.0 nativo"
                    if native_nginx
                    else "Nginx 1.28 Docker",
                    "output": str(output),
                    "password": password,
                    "accounts": accounts,
                    "seedPassword": p.env.state["password"],
                    "seedAccounts": p.env.state["accounts"],
                    "unit": unit,
                    "result": result,
                    "recipient": recipient,
                    "urls": p.urls,
                    "tokens": p.tokens,
                    "privateReports": bool(os.environ.get("REDHOUSE_GCS_TEST_BUCKET")),
                }
            ),
            text=True,
            capture_output=True,
            timeout=900,
        )
        assert completed.returncode == 0, completed.stdout + completed.stderr
        report = json.loads((output / "resultados.json").read_text())
        assert report["passed"] and not report["consoleErrors"]
        identifiers = report["records"]
        with p.owner("inventario") as conn:
            assert (
                conn.execute(
                    "SELECT count(*) FROM resource_destinations WHERE resource_id=%s",
                    (unit["id"],),
                ).fetchone()[0]
                == 2
            )
        with p.owner("compatibilidad") as conn:
            assert (
                conn.execute(
                    "SELECT count(*) FROM lab_results WHERE sample_id=%s",
                    (body["sample_id"],),
                ).fetchone()[0]
                == 2
            )
        with p.owner("transporte") as conn:
            assert (
                conn.execute(
                    "SELECT status FROM shipments WHERE id=%s",
                    (identifiers["shipment"],),
                ).fetchone()[0]
                == "ACCEPTED"
            )
        assert report["privateReportDownloaded"] == bool(
            os.environ.get("REDHOUSE_GCS_TEST_BUCKET")
        )
    finally:
        if local_process:
            local_process.terminate()
            local_process.wait(timeout=20)
        else:
            subprocess.run(
                ["docker", "stop", "--time", "2", gateway_name],
                capture_output=True,
                timeout=20,
            )
        server.shutdown()
        server.server_close()
