"""I06-07 local: Chrome, Nginx HTTPS/WSS y continuidad real del monolito.

Ejecución explícita: REDHOUSE_BROWSER_TESTS=1, REDHOUSE_TEST_NGINX=<binario>,
REDHOUSE_BROWSER_RESULTS=<directorio nuevo> y Playwright local instalado.
No acepta cartografía, capacidad, MFA, GCP ni confianza CA del sistema operativo.
"""

import base64
import hashlib
import importlib.util
import json
import os
import queue
import re
import subprocess
import sys
import threading
import time
from pathlib import Path
from uuid import uuid4

import pytest
import requests
import websocket
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from redhouse.events import mongodb
from redhouse.proxy import TrustedProxy
from scripts.local import free_port
from werkzeug.serving import make_server

from .conftest import QuietHandler
from .helpers import iso
from .test_continuity import autonomous as autonomous  # noqa: PLC0414 - expose fixture
from .test_final_tracking import connect, point, receive, send
from .test_final_tracking import tracking as tracking  # noqa: PLC0414 - expose fixture
from .test_nginx_runtime import NGINX, certificate, wait_live

ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "scripts/verify_portal_gateway_tracking.cjs"


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
            "deployment",
            "data/database",
        ],
        cwd=ROOT,
        text=True,
    ).splitlines()
    return {
        name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
        for name in sorted(set(names))
        if (ROOT / name).is_file()
    }


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def stop_process(process):
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def start_process(args, log):
    with log.open("wb") as output:
        return subprocess.Popen(args, cwd=ROOT, stdout=output, stderr=subprocess.STDOUT)


@pytest.mark.skipif(
    not NGINX or not os.environ.get("REDHOUSE_BROWSER_TESTS"),
    reason="Requiere autorización explícita de Chrome y Nginx real",
)
def test_portal_gateway_replica_loss_autonomy_and_recovery(
    p, tracking, request, tmp_path
):
    # tracking is prepared before autonomous stops every fixture API listener.
    output = Path(os.environ["REDHOUSE_BROWSER_RESULTS"]) / "portal-gateway"
    output.mkdir(parents=True, exist_ok=False)
    sources = source_manifest()
    write_json(output / "sources-before.json", sources)
    report = {
        "case": "I06-07",
        "passed": False,
        "checks": [],
        "scope": "Laboratorio local aislado; datos y ubicaciones sintéticos",
        "limits": [
            "No cierra I06 completo ni acredita producción, GCP o capacidad",
            "Fixture TESTING=True; cuotas de prueba 100000; no prueba MFA",
            "DONOR/TRANSPORT sin omitir MFA de roles críticos",
            "TLS Python con CA explícita; Chrome con excepción SPKI del certificado efímero",
            "No prueba confianza CA del sistema; perfiles Chrome privados efímeros",
            "Mosaicos OSM bloqueados para evitar consumo masivo; cartografía no aceptada",
            "Listeners loopback y puertos efímeros; WSGI de prueba con TrustedProxy real",
        ],
    }
    processes = []
    browser = None
    server = None
    session = requests.Session()
    session.trust_env = False
    secrets_to_hide = [p.env.state["password"], tracking["credential"]["credential"]]
    secrets_to_hide.extend(p.tokens.values())

    def sanitized(error):
        value = str(error)
        for secret in secrets_to_hide:
            value = value.replace(secret, "[REDACTED]")
        value = re.sub(
            r"(?:postgres(?:ql)?|redis|mongodb)://\S+", "[PRIVATE_DSN]", value
        )
        value = re.sub(
            r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+", "[JWT]", value
        )
        value = re.sub(r"(https?://[^\s?]+)\?[^\s]+", r"\1?[REDACTED]", value)
        return value[:1500]

    try:
        donor = p.ok(
            "donantes",
            "POST",
            "/api/v1/donors",
            user="donor1",
            data={
                "folio": "GW-" + uuid4().hex[:12],
                "display_name": "Donante sintético gateway",
                "blood_group": "O+",
                "consent": True,
            },
        )
        campaign = p.ok(
            "donantes",
            "POST",
            "/api/v1/campaigns",
            user="operator1",
            data={
                "title": "Continuidad sintética " + uuid4().hex[:8],
                "starts_at": iso(minutes=5),
                "ends_at": iso(days=1),
                "capacity": 5,
            },
        )
        appointment = p.ok(
            "donantes",
            "POST",
            "/api/v1/appointments",
            user="donor1",
            data={"donor_id": donor["id"], "campaign_id": campaign["id"]},
        )
        # The reused tracking fixture starts a direct TLS helper. Close it so the
        # only external Transporte listeners in this case are the two Nginx upstreams.
        tracking["server"].shutdown()
        tracking["server"].server_close()
        assert tracking["server"].socket.fileno() == -1
        web = request.getfixturevalue("autonomous")
        web.config.update(
            PRODUCTION=True, SESSION_COOKIE_SECURE=True, HIGHCHARTS_ENABLED=False
        )
        server = make_server(
            "127.0.0.1",
            0,
            TrustedProxy(web, "127.0.0.1"),
            threaded=True,
            request_handler=QuietHandler,
        )
        threading.Thread(target=server.serve_forever, daemon=True).start()
        spec = importlib.util.spec_from_file_location(
            "portal_gateway_configuration", ROOT / "deployment/gcp/configure_public.py"
        )
        generator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(generator)
        (tmp_path / "apps").mkdir()
        (tmp_path / "web.json").write_text("{}")
        for service in p.urls:
            (tmp_path / "apps" / (service + ".json")).write_text("{}")
        generator.configure(tmp_path, "127.0.0.1")
        certificate(tmp_path / "tls")
        cert_path = tmp_path / "tls/fullchain.pem"
        cert = x509.load_pem_x509_certificate(cert_path.read_bytes())
        spki = base64.b64encode(
            hashlib.sha256(
                cert.public_key().public_bytes(
                    serialization.Encoding.DER,
                    serialization.PublicFormat.SubjectPublicKeyInfo,
                )
            ).digest()
        ).decode()
        # Only ephemeral listeners, upstream addresses, TLS paths and public port change.
        config = (tmp_path / "public.nginx.conf").read_text()
        ports = {}

        def listener(match):
            old = int(match.group(1))
            ports.setdefault(old, free_port())
            return f"listen 127.0.0.1:{ports[old]}"

        config = re.sub(r"listen (\d+)", listener, config)
        origin = f"https://127.0.0.1:{ports[8443]}"
        replica_args = []
        replica_ports = []
        for index in range(2):
            port = free_port()
            replica_ports.append(port)
            replica_config = dict(
                p.env.configs["transporte"],
                TESTING=True,
                RATE_LIMIT=100000,
                INTERNAL_RATE_LIMIT=100000,
                SERVICE_URLS=p.urls,
                WORKER_REQUIRED=False,
                TRUSTED_PROXY_ADDRESS="127.0.0.1",
                TRUSTED_PROXY_HOST="",
                TRACKING_ALLOWED_ORIGINS=[origin],
            )
            config_path = tmp_path / f"transporte-{index}.json"
            write_json(config_path, replica_config)
            config_path.chmod(0o600)
            args = [
                sys.executable,
                str(ROOT / "apps/services/run.py"),
                "transporte",
                "--config",
                str(config_path),
                "--port",
                str(port),
            ]
            replica_args.append(args)
            process = start_process(args, tmp_path / f"transporte-{index}.log")
            processes.append(process)
            wait_live(f"http://127.0.0.1:{port}/health/live", process)

        def backend(match):
            name = match.group(1).removesuffix("-private")
            if name == "web":
                port = server.server_port
            elif name.startswith("transporte-"):
                port = replica_ports[0 if name.endswith("-a") else 1]
            else:
                port = int(p.urls[name[:-2].replace("-", "_")].rsplit(":", 1)[1])
            return f"server 127.0.0.1:{port} resolve"

        config = re.sub(r"server ([a-z-]+):8080 resolve", backend, config)
        config = config.replace("/tmp/", str(tmp_path) + "/")
        config = config.replace("/etc/nginx/tls", str(tmp_path / "tls"))
        config = config.replace(
            "proxy_set_header Host 127.0.0.1;",
            f"proxy_set_header Host 127.0.0.1:{ports[8443]};",
        )
        nginx_path = tmp_path / "runtime.nginx.conf"
        nginx_path.write_text(config)
        result = subprocess.run(
            [NGINX, "-t", "-p", str(tmp_path), "-c", str(nginx_path)],
            capture_output=True,
            timeout=15,
            check=False,
        )
        assert result.returncode == 0, "Nginx rechazó la configuración aislada"
        nginx = start_process(
            [NGINX, "-p", str(tmp_path), "-c", str(nginx_path), "-g", "daemon off;"],
            tmp_path / "nginx.log",
        )
        processes.append(nginx)
        wait_live(f"http://127.0.0.1:{ports[8080]}/health/live", nginx)
        assert (
            session.get(
                origin + "/login", verify=str(cert_path), timeout=10
            ).status_code
            == 200
        )
        report["checks"].append(
            "HTTPS Nginx verificado por Python con certificado explícito"
        )
        report["generated_configuration_sha256"] = hashlib.sha256(
            config.encode()
        ).hexdigest()
        report["certificate_spki_sha256"] = spki
        target = dict(
            tracking,
            url=origin.replace("https:", "wss:")
            + "/services/transporte/ws/v1/tracking/",
            cert=str(cert_path),
        )
        points = []

        def publish(values):
            publisher = connect(target, tracking["credential"]["credential"], "device")
            try:
                receive(publisher, "authenticated")
                acks = []
                for value in values:
                    send(publisher, {"type": "position.publish", "position": value})
                    ack = receive(publisher, "position.ack")
                    assert ack["state"] == "PERSISTED_SQL"
                    assert ack["event_id"] == value["event_id"]
                    assert ack["shipment_id"] == value["shipment_id"]
                    acks.append(
                        {
                            "event_id": ack["event_id"],
                            "cursor": ack["cursor"],
                            "state": ack["state"],
                        }
                    )
                return acks
            finally:
                publisher.close()

        messages = queue.Queue()
        with (tmp_path / "node.stderr").open("wb") as error_log:
            browser = subprocess.Popen(
                ["node", str(RUNNER)],
                cwd=ROOT,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=error_log,
                text=True,
                bufsize=1,
            )

        def read_messages():
            for line in browser.stdout:
                try:
                    messages.put(json.loads(line))
                except (ValueError, TypeError):
                    messages.put({"action": "invalid_protocol"})
            messages.put({"action": "eof"})

        threading.Thread(target=read_messages, daemon=True).start()

        def reply(action, **values):
            browser.stdin.write(json.dumps({"action": action, **values}) + "\n")
            browser.stdin.flush()

        def expect(action):
            try:
                message = messages.get(timeout=90)
            except queue.Empty:
                pytest.fail("Timeout de coordinación del navegador")
            assert message.get("action") == action, "Fase inesperada: " + sanitized(
                message.get("action")
            )

        reply(
            "configure",
            base=origin,
            password=p.env.state["password"],
            shipment=tracking["shipment"]["id"],
            appointment=appointment["id"],
            spki=spki,
            output=str(output),
            profiles=str(tmp_path / "chrome-profiles"),
        )
        expect("initial_publish")
        points.append(point(tracking, sequence=1))
        report["initial_ack"] = publish([points[0]])
        reply("initial_publish", eventId=points[0]["event_id"])
        expect("stop_one")
        stop_process(processes[0])
        report["checks"].append("Réplica A detenida; B conserva proceso vivo")
        reply("stop_one")
        expect("single_publish")
        points.append(point(tracking, sequence=2))
        report["single_replica_ack"] = publish([points[1]])
        reply("single_publish", eventId=points[1]["event_id"])
        expect("stop_all")
        stop_process(processes[1])
        assert processes[0].poll() is not None and processes[1].poll() is not None
        failed_upgrade = session.get(
            origin + "/services/transporte/ws/v1/tracking/json",
            headers={
                "Connection": "Upgrade",
                "Upgrade": "websocket",
                "Sec-WebSocket-Version": "13",
                "Sec-WebSocket-Key": "dGhlIHNhbXBsZSBub25jZQ==",
            },
            verify=str(cert_path),
            timeout=10,
        )
        assert failed_upgrade.status_code == 502
        report["all_down_gateway_status"] = failed_upgrade.status_code
        with pytest.raises((OSError, websocket.WebSocketException)):
            connect(target, p.tokens["transport1"])
        reply("stop_all")
        expect("verify_mutation")
        # The browser submits the real CSRF-protected cancellation while all APIs are off.
        assert all(process.poll() is not None for process in processes[:2])
        assert all(server.socket.fileno() == -1 for server in p.servers.values())
        with p.owner("donantes") as conn:
            status = conn.execute(
                "SELECT status FROM appointments WHERE id=%s", (appointment["id"],)
            ).fetchone()[0]
            assert status == "CANCELLED"
            events = conn.execute(
                "SELECT id,event->>'actor_id' FROM activity_events WHERE event->>'resource_id'=%s "
                "AND event->>'action'='APPOINTMENT_CANCELLED'",
                (appointment["id"],),
            ).fetchall()
            assert len(events) == 1
            assert events[0][1] == p.env.state["accounts"]["donor1"]["id"]
        p.drain(rounds=8)
        with p.owner("auditoria") as conn:
            assert (
                conn.execute(
                    "SELECT count(*) FROM audit_events WHERE id=%s", (events[0][0],)
                ).fetchone()[0]
                == 1
            )
        report["autonomy"] = {
            "appointment_id": appointment["id"],
            "status": status,
            "activity_event_id": str(events[0][0]),
            "audit_count": 1,
            "all_fixture_api_listeners_closed": True,
            "direct_tracking_fixture_listener_closed": True,
        }
        reply("verify_mutation")
        expect("restore")
        restored = start_process(replica_args[1], tmp_path / "transporte-restored.log")
        processes.append(restored)
        wait_live(f"http://127.0.0.1:{replica_ports[1]}/health/live", restored)
        time.sleep(2.1)  # Existing generated fail_timeout=2s, not an altered policy.
        points.append(point(tracking, sequence=3))
        report["recovery_acks"] = publish([points[0], points[1], points[2], points[2]])
        assert [ack["cursor"] for ack in report["recovery_acks"]] == [1, 2, 3, 3]
        reply("restore", eventIds=[value["event_id"] for value in points])
        expect("restore_second")
        restored_a = start_process(
            replica_args[0], tmp_path / "transporte-a-restored.log"
        )
        processes.append(restored_a)
        wait_live(f"http://127.0.0.1:{replica_ports[0]}/health/live", restored_a)
        health = {}
        for name, port, process in zip(
            ("A", "B"), replica_ports, (restored_a, restored), strict=True
        ):
            assert process.poll() is None
            health[name] = {}
            for endpoint in ("live", "ready"):
                response = session.get(
                    f"http://127.0.0.1:{port}/health/{endpoint}", timeout=10
                )
                assert response.status_code == 200
                health[name][endpoint] = response.status_code
        report["restored_replicas_health"] = health
        reply("restore_second")
        expect("complete")
        assert browser.wait(timeout=20) == 0, (
            "Navegador terminó con error; revisar browser.json sanitizado"
        )
        with p.owner("transporte") as conn:
            rows = conn.execute(
                "SELECT id,cursor FROM tracking_points WHERE shipment_id=%s ORDER BY cursor",
                (tracking["shipment"]["id"],),
            ).fetchall()
        assert [(str(row[0]), row[1]) for row in rows] == [
            (value["event_id"], i) for i, value in enumerate(points, 1)
        ]
        report["sql_points"] = [
            {"event_id": str(row[0]), "cursor": row[1]} for row in rows
        ]
        report["checks"].append(
            "Tres puntos SQL únicos; replay de mismos IDs conserva cursores 1,2,3"
        )
        p.drain(rounds=8)
        with p.owner("transporte") as conn:
            pending_positions = conn.execute(
                "SELECT count(*) FROM outbox WHERE target='mongodb' AND delivered_at IS NULL "
                "AND event->'metadata'->'position'->>'shipment_id'=%s",
                (tracking["shipment"]["id"],),
            ).fetchone()[0]
        assert pending_positions == 0
        # Position projections are real documents in Transporte's events collection:
        # tracking.publish queues metadata.position; events.deliver_mongo stores it.
        # shipment_tracking instead projects custody-state sequences, not GPS points.
        with p.apps["transporte"].app_context(), mongodb() as client:
            database = client[p.apps["transporte"].config["MONGODB_DATABASE"]]
            projected = list(
                database.events.find(
                    {
                        "source": "transporte",
                        "metadata.position.shipment_id": tracking["shipment"]["id"],
                    },
                    {
                        "_id": 0,
                        "metadata.position.event_id": 1,
                        "metadata.position.cursor": 1,
                    },
                ).sort("metadata.position.cursor", 1)
            )
        mongo_points = [document["metadata"]["position"] for document in projected]
        assert mongo_points == report["sql_points"]
        report["mongo_projection"] = {
            "collection": "events",
            "position_field": "metadata.position",
            "points": mongo_points,
            "pending_outbox_positions": pending_positions,
        }
        report["checks"].append(
            "Ambas réplicas restauradas y live/ready 200; SQL y Mongo conservan los tres IDs/cursores"
        )
        assert source_manifest() == sources, "Cambió una fuente durante el ensayo"
        report["passed"] = True
    except BaseException as error:
        report["failure"] = {"type": type(error).__name__, "message": sanitized(error)}
        raise
    finally:
        if browser is not None:
            stop_process(browser)
            if browser.stdin is not None:
                browser.stdin.close()
            if browser.stdout is not None:
                browser.stdout.close()
        for process in reversed(processes):
            stop_process(process)
        session.close()
        if server is not None:
            server.shutdown()
            server.server_close()
        write_json(output / "sources-after.json", source_manifest())
        write_json(output / "runtime.json", report)
