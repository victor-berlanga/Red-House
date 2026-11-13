"""Navegador real con TLS/cookies seguras y las cuatro políticas operativas activas."""

import json
import hashlib
import os
from pathlib import Path
import secrets
import socket
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from werkzeug.security import generate_password_hash
from werkzeug.serving import make_server, make_ssl_devcert

from .conftest import QuietHandler
from .helpers import iso, route
from .test_correction_backend import laboratory
from .test_web_integration import web as web
from .test_continuity import autonomous as autonomous


@pytest.mark.skipif(
    not os.environ.get("REDHOUSE_BROWSER_TESTS"),
    reason="Activar REDHOUSE_BROWSER_TESTS=1; requiere Chrome/Playwright y Docker o REDHOUSE_TEST_NGINX para gateway WSS.",
)
@pytest.mark.parametrize("backend", ["http", "monolith"])
def test_operational_browser_corrections(
    web, p, monkeypatch, tmp_path, request, backend
):
    from ms_identidad_acceso.strong_auth import totp
    from ms_documentos.reports import process
    from .final_receivers import smtp_receiver
    from .test_final_identity import email_token
    from ms_identidad_acceso.strong_auth import deliver_pending

    if backend == "monolith":
        web = request.getfixturevalue("autonomous")

    root = Path(__file__).resolve().parents[3]
    password = secrets.token_urlsafe(28)
    accounts = {}
    for alias, role, tenant in (
        ("origin", "MEDICAL", 0),
        ("destination", "MEDICAL", 1),
        ("coordinator", "COORDINATOR", 0),
        ("admin", "ADMIN", 0),
        ("limited", "OPERATOR", 0),
        ("donor", "DONOR", 0),
        ("donor_race", "DONOR", 0),
        ("map_viewer", "OPERATOR", 0),
        ("other_transport", "TRANSPORT", 0),
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
    from .portal_security_probe import install as install_security_probe

    install_security_probe(web, p, accounts)
    smtp = smtp_receiver()
    smtp_port, messages = smtp.__enter__()
    identity = p.apps["identidad_acceso"]
    for key, value in {
        "SMTP_HOST": "127.0.0.1",
        "SMTP_PORT": smtp_port,
        "SMTP_TEST_RECEIVER": True,
        "SMTP_FROM": "portal@redhouse.invalid",
    }.items():
        monkeypatch.setitem(identity.config, key, value)
    donor_account = accounts["donor"]
    auth = p.ok(
        "identidad_acceso",
        "POST",
        "/api/v1/auth/login",
        user=None,
        data={"username": donor_account["username"], "password": password},
    )
    p.tokens[donor_account["username"]] = auth["access_token"]
    p.ok(
        "identidad_acceso",
        "POST",
        "/api/v1/auth/contact",
        user=donor_account["username"],
        data={
            "email": donor_account["username"] + "@example.invalid",
            "password": password,
        },
    )
    with identity.app_context():
        deliver_pending()
    p.ok(
        "identidad_acceso",
        "POST",
        "/api/v1/auth/contact/verify",
        user=donor_account["username"],
        data={"token": email_token(messages[-1])},
    )
    p.tokens.pop(donor_account["username"])
    messages.clear()

    def mailbox():
        with identity.app_context():
            deliver_pending()
        return {"token": email_token(messages[-1]) if messages else None}

    web.add_url_rule(
        "/test/mailbox",
        "test_mailbox",
        web.extensions["csrf"].exempt(mailbox),
        methods=["POST"],
    )
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
    from .portal_organ_seed import prepare

    organ = prepare(p)
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
    for index, alias in enumerate(("admin1", "admin2")):
        path = "/api/v1/institutions/" + p.env.state["tenants"][index] + "/presentation"
        old = p.ok("identidad_acceso", "GET", path, user=alias)
        p.ok(
            "identidad_acceso",
            "POST",
            path,
            user=alias,
            data=dict(
                version=old["version"],
                published=False,
                description="",
                latitude=25.6866 + index * 0.01,
                longitude=-100.3161 + index * 0.01,
                coordinate_source="Coordenadas ficticias del ensayo",
                coordinate_recorded_at=iso(),
                synthetic=True,
                human_confirmation=True,
                reason="Preparación aislada",
            ),
        )
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
        PRODUCTION=True,
        SESSION_COOKIE_SECURE=True,
        JWT_COOKIE_SECURE=True,
        HIGHCHARTS_ENABLED=True,
    )
    from src.integration.routes import common
    from src.access import BusinessError
    from ms_inventario import routes as inventory_routes
    from redhouse.errors import APIError

    failures = {"armed": False}
    original_call, original_internal = common.call, inventory_routes.call

    def lose_write_response(service, path, method="GET", *args, **kwargs):
        result = original_call(service, path, method, *args, **kwargs)
        if (
            failures["armed"]
            and service == "inventario"
            and path == "/api/v1/reservations"
            and method == "POST"
        ):
            failures["armed"] = False
            raise BusinessError(
                "Respuesta perdida después de persistir, ensayo aislado", 503
            )
        return result

    def lose_internal_confirmation(service, method, path, data=None, **kwargs):
        result = original_internal(service, method, path, data, **kwargs)
        if (
            failures["armed"]
            and service == "receptores"
            and data
            and data.get("action") == "CONFIRM"
        ):
            raise APIError(
                "dependency_unavailable", "Confirmación perdida en ensayo aislado", 503
            )
        return result

    monkeypatch.setattr(common, "call", lose_write_response)
    monkeypatch.setattr(inventory_routes, "call", lose_internal_confirmation)

    def arm_loss():
        failures["armed"] = True
        return {"armed": True}

    web.add_url_rule(
        "/test/lose-reservation-response",
        "test_lose_reservation_response",
        web.extensions["csrf"].exempt(arm_loss),
        methods=["POST"],
    )
    docapp = p.apps["documentos"]
    if os.environ.get("REDHOUSE_GCS_TEST_BUCKET"):
        monkeypatch.setitem(
            docapp.config, "GCS_BUCKET", os.environ["REDHOUSE_GCS_TEST_BUCKET"]
        )
        monkeypatch.setitem(
            docapp.config, "GCS_PROJECT", os.environ.get("GOOGLE_CLOUD_PROJECT")
        )

    worker_stop = threading.Event()
    worker_lock = threading.Lock()
    worker_errors = []

    def drain_owner(name):
        from redhouse.events import dispatch

        with p.apps[name].app_context():
            return dispatch(25)

    def drain_round():
        with worker_lock, ThreadPoolExecutor(max_workers=4) as pool:
            return list(pool.map(drain_owner, tuple(p.apps)))

    def background_worker():
        while not worker_stop.is_set():
            try:
                drain_round()
            except Exception as exc:
                worker_errors.append(type(exc).__name__)
            worker_stop.wait(1)

    worker_thread = threading.Thread(target=background_worker, daemon=True)

    def workers():
        with docapp.app_context():
            process(limit=30)
        # El worker corre durante el recorrido, como en el despliegue. Estas
        # rondas esperan las proyecciones recién emitidas sin acumular toda la sesión.
        for _ in range(3):
            drain_round()
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
    embedded_gateway = os.environ.get("REDHOUSE_TEST_GATEWAY") == "embedded"
    serving_app = web
    if embedded_gateway:
        from werkzeug.middleware.dispatcher import DispatcherMiddleware

        serving_app = DispatcherMiddleware(
            web, {"/services/transporte": p.apps["transporte"]}
        )
    if backend == "monolith":
        # Solo arnés de aceptación: observaciones del fixture por el mismo kernel.
        # Los listeners de todas las API siguen detenidos durante el navegador.
        from flask import request as incoming

        def test_owner(service, path):
            result = web.extensions["application_kernel"].request(
                service,
                incoming.method,
                "/"
                + path
                + (
                    "?" + incoming.query_string.decode()
                    if incoming.query_string
                    else ""
                ),
                data=incoming.get_data(),
                headers=dict(incoming.headers),
            )
            return result.content, result.status_code, dict(result.headers)

        web.add_url_rule(
            "/test/owner/<service>/<path:path>",
            "test_owner",
            web.extensions["csrf"].exempt(test_owner),
            methods=["GET", "POST"],
        )
    server = make_server(
        "127.0.0.1",
        0,
        serving_app,
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
    if embedded_gateway:
        base = f"https://localhost:{server.server_port}"
    elif native_nginx:
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
    # Ventana reducida únicamente en el fixture para ensayar cursor caducado
    # sin producir diez mil posiciones ni cambiar el contrato productivo.
    monkeypatch.setitem(transport.config, "TRACKING_REPLAY_WINDOW", 1)
    output = Path(
        os.environ.get("REDHOUSE_BROWSER_RESULTS", str(tmp_path / "browser"))
    ) / ("correcciones-operativas-" + backend)
    output.mkdir(parents=True, exist_ok=True)

    def source_manifest():
        names = subprocess.check_output(
            [
                "git",
                "ls-files",
                "--cached",
                "--others",
                "--exclude-standard",
                "--",
                "apps/services",
                "apps/web",
                "scripts",
                "data/database",
            ],
            cwd=root,
            text=True,
        ).splitlines()
        return {
            name: hashlib.sha256((root / name).read_bytes()).hexdigest()
            for name in sorted(set(names))
            if (root / name).is_file()
        }

    sources_before = source_manifest()
    (output / "sources-before.json").write_text(
        json.dumps(sources_before, indent=2) + "\n"
    )
    worker_thread.start()
    try:
        completed = subprocess.run(
            ["node", str(root / "scripts/verify_backend_corrections.cjs")],
            input=json.dumps(
                {
                    "base": base,
                    "commit": subprocess.check_output(
                        ["git", "rev-parse", "HEAD"], cwd=root, text=True
                    ).strip(),
                    "gateway": "WSGI TLS aislado; no acredita proxy productivo"
                    if embedded_gateway
                    else "Nginx 1.28.0 nativo"
                    if native_nginx
                    else "Nginx 1.28 Docker",
                    "output": str(output),
                    "password": password,
                    "accounts": accounts,
                    "seedPassword": p.env.state["password"],
                    "seedAccounts": p.env.state["accounts"],
                    "unit": unit,
                    "profile": profile,
                    "organ": organ,
                    "result": result,
                    "recipient": recipient,
                    "urls": {name: base + "/test/owner/" + name for name in p.urls}
                    if backend == "monolith"
                    else p.urls,
                    "backend": backend,
                    "axe": os.environ.get("REDHOUSE_AXE_PATH"),
                    "tokens": p.tokens,
                    "privateReports": bool(os.environ.get("REDHOUSE_GCS_TEST_BUCKET")),
                }
            ),
            text=True,
            capture_output=True,
            timeout=1800,
        )
        assert completed.returncode == 0, completed.stdout + completed.stderr
        report = json.loads((output / "resultados.json").read_text())
        assert report["passed"] and not report["consoleErrors"]
        assert source_manifest() == sources_before, (
            "El código cambió durante la aceptación; repetir con fuentes congeladas."
        )
        assert not worker_errors, worker_errors
        identifiers = report["records"]
        with p.owner("inventario") as conn:
            assert (
                conn.execute(
                    "SELECT count(*) FROM resource_destinations WHERE resource_id=%s",
                    (unit["id"],),
                ).fetchone()[0]
                == 2
            )
            assert (
                conn.execute(
                    "SELECT count(*) FROM reservations WHERE resource_id=%s",
                    (unit["id"],),
                ).fetchone()[0]
                == 1
            )
            assert (
                conn.execute(
                    "SELECT destination FROM resource_destinations WHERE resource_id=%s",
                    (organ["unit"]["id"],),
                ).fetchone()[0]
                == "TRANSPLANTED"
            )
            assert (
                conn.execute(
                    "SELECT count(*) FROM reservations WHERE resource_id=%s",
                    (organ["unit"]["id"],),
                ).fetchone()[0]
                == 1
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
        with p.owner("auditoria") as conn:
            assert (
                conn.execute(
                    "SELECT status FROM audit_findings WHERE id=%s",
                    (identifiers["finding"],),
                ).fetchone()[0]
                == "CLOSED"
            )
        (output / "persistencia.json").write_text(
            json.dumps(
                {
                    "blood_destinations": 2,
                    "blood_reservations": 1,
                    "organ_destination": "TRANSPLANTED",
                    "organ_reservations": 1,
                    "finding": "CLOSED",
                    "identifiers": identifiers,
                },
                indent=2,
            )
            + "\n"
        )
    finally:
        (output / "sources-after.json").write_text(
            json.dumps(source_manifest(), indent=2) + "\n"
        )
        worker_stop.set()
        worker_thread.join(timeout=60)
        smtp.__exit__(None, None, None)
        if local_process:
            local_process.terminate()
            local_process.wait(timeout=20)
        elif not embedded_gateway:
            subprocess.run(
                ["docker", "stop", "--time", "2", gateway_name],
                capture_output=True,
                timeout=20,
            )
        server.shutdown()
        server.server_close()
