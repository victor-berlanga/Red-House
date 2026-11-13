"""Real generated HTTPS/WSS gateway over isolated services and synthetic data."""

import importlib.util
import ipaddress
import json
import os
import re
import subprocess
import sys
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
import requests
import websocket
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from scripts.local import free_port

from .test_final_tracking import connect, point, receive, send
from .test_final_tracking import tracking as tracking  # noqa: PLC0414 - expose fixture

ROOT = Path(__file__).resolve().parents[3]
NGINX = os.environ.get("REDHOUSE_TEST_NGINX", "")


def certificate(directory):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "127.0.0.1")])
    now = datetime.now(UTC)
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=1))
        .not_valid_after(now + timedelta(days=1))
        .add_extension(
            x509.SubjectAlternativeName(
                [
                    x509.IPAddress(ipaddress.ip_address("127.0.0.1")),
                ]
            ),
            critical=False,
        )
        .sign(key, hashes.SHA256())
    )
    (directory / "fullchain.pem").write_bytes(
        cert.public_bytes(serialization.Encoding.PEM)
    )
    private = directory / "privkey.pem"
    private.write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    private.chmod(0o600)


def wait_live(url, process):
    for _ in range(100):
        assert process.poll() is None, "El proceso del ensayo terminó prematuramente."
        try:
            if requests.get(url, timeout=0.3).status_code == 200:
                return
        except requests.RequestException:
            pass
        time.sleep(0.1)
    pytest.fail("El proceso del ensayo no inició.")


@pytest.mark.skipif(not NGINX, reason="REDHOUSE_TEST_NGINX no configurado")
def test_generated_nginx_https_wss_scope_and_replica_recovery(p, tracking, tmp_path):
    spec = importlib.util.spec_from_file_location(
        "public_gateway_test", ROOT / "deployment/gcp/configure_public.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    (tmp_path / "apps").mkdir()
    (tmp_path / "web.json").write_text("{}")
    for service in p.urls:
        (tmp_path / "apps" / (service + ".json")).write_text("{}")
    module.configure(tmp_path, "127.0.0.1")
    certificate(tmp_path / "tls")
    replicas = []
    processes = []
    nginx = None
    session = requests.Session()
    session.trust_env = False
    try:
        for index in range(2):
            port = free_port()
            config = dict(
                p.env.configs["transporte"],
                TESTING=True,
                SERVICE_URLS=p.urls,
                WORKER_REQUIRED=False,
                TRUSTED_PROXY_ADDRESS="127.0.0.1",
                TRUSTED_PROXY_HOST="",
            )
            path = tmp_path / f"replica-{index}.json"
            path.write_text(json.dumps(config))
            path.chmod(0o600)
            args = [
                sys.executable,
                str(ROOT / "apps/services/run.py"),
                "transporte",
                "--config",
                str(path),
                "--port",
                str(port),
            ]
            output = (tmp_path / f"replica-{index}.log").open("wb")
            try:
                process = subprocess.Popen(
                    args, stdout=output, stderr=subprocess.STDOUT
                )
            finally:
                output.close()
            processes.append(process)
            replicas.append((port, args))
            wait_live(f"http://127.0.0.1:{port}/health/live", process)

        config = (tmp_path / "public.nginx.conf").read_text()

        def backend(match):
            name = match.group(1).removesuffix("-private")
            if name.startswith("transporte-"):
                port = replicas[0 if name.endswith("-a") else 1][0]
            else:
                service = (
                    "identidad_acceso" if name == "web" else name[:-2].replace("-", "_")
                )
                port = int(p.urls[service].rsplit(":", 1)[1])
            return f"server 127.0.0.1:{port} resolve"

        config = re.sub(r"server ([a-z-]+):8080 resolve", backend, config)
        ports = {}

        def listener(match):
            old = int(match.group(1))
            ports.setdefault(old, free_port())
            return f"listen 127.0.0.1:{ports[old]}"

        config = re.sub(r"listen (\d+)", listener, config)
        config = config.replace("/etc/nginx/tls", str(tmp_path / "tls"))
        config = config.replace("/tmp/", str(tmp_path) + "/")
        config_path = tmp_path / "runtime.nginx.conf"
        config_path.write_text(config)
        subprocess.run(
            [NGINX, "-t", "-p", str(tmp_path), "-c", str(config_path)],
            check=True,
            capture_output=True,
        )
        with (tmp_path / "nginx.log").open("wb") as output:
            nginx = subprocess.Popen(
                [
                    NGINX,
                    "-p",
                    str(tmp_path),
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
        ca = str(tmp_path / "tls/fullchain.pem")
        headers = {"Authorization": "Bearer " + p.tokens["coordinator1"]}
        me = origin + "/services/identidad-acceso/api/v1/auth/me"
        response = session.get(me, headers=headers, verify=ca, timeout=5)
        assert response.status_code == 200
        assert (
            response.json()["data"]["id"]
            == p.env.state["accounts"]["coordinator1"]["id"]
        )
        response = session.get(
            me, headers={**headers, "Accept": "application/xml"}, verify=ca, timeout=5
        )
        assert response.status_code == 200
        assert response.headers["Content-Type"].startswith("application/xml")
        assert session.get(me, verify=ca, timeout=5).status_code == 401
        assert (
            session.post(
                origin + "/services/documentos/api/v1/documents",
                data=b"x" * 262145,
                verify=ca,
                timeout=5,
            ).status_code
            == 413
        )
        assert (
            session.get(
                origin + "/services/transporte/internal/status", verify=ca, timeout=5
            ).status_code
            == 404
        )

        target = dict(
            tracking,
            url=origin.replace("https:", "wss:")
            + "/services/transporte/ws/v1/tracking/",
            cert=ca,
        )
        publisher = connect(target, tracking["credential"]["credential"], "device")
        subscriber = connect(target, p.tokens["coordinator1"], fmt="xml")
        try:
            receive(publisher, "authenticated")
            receive(subscriber, "authenticated", "xml")
            send(
                subscriber,
                {"type": "subscribe", "shipment_id": tracking["shipment"]["id"]},
                "xml",
            )
            receive(subscriber, "subscribed", "xml")
            first = point(tracking)
            send(publisher, {"type": "position.publish", "position": first})
            assert receive(publisher, "position.ack")["cursor"] == 1
            assert (
                receive(subscriber, "position.updated", "xml")["position"]["event_id"]
                == first["event_id"]
            )
        finally:
            publisher.close()
            subscriber.close()
        processes[0].terminate()
        processes[0].wait(timeout=10)
        subscriber = connect(target, p.tokens["coordinator1"])
        try:
            receive(subscriber, "authenticated")
            send(
                subscriber,
                {
                    "type": "subscribe",
                    "shipment_id": tracking["shipment"]["id"],
                    "cursor": 0,
                },
            )
            receive(subscriber, "subscribed")
            assert receive(subscriber, "position.updated")["position"]["cursor"] == 1
        finally:
            subscriber.close()
        processes[1].terminate()
        processes[1].wait(timeout=10)
        with pytest.raises((OSError, websocket.WebSocketException)):
            connect(target, p.tokens["coordinator1"])
        assert session.get(me, headers=headers, verify=ca, timeout=5).status_code == 200
        # Restore the same isolated replica; the cursor survives both process exits.
        with (tmp_path / "replica-restored.log").open("wb") as output:
            restored = subprocess.Popen(
                replicas[1][1], stdout=output, stderr=subprocess.STDOUT
            )
        processes.append(restored)
        wait_live(f"http://127.0.0.1:{replicas[1][0]}/health/live", restored)
        time.sleep(2.1)  # Existing Nginx fail_timeout is two seconds.
        subscriber = connect(target, p.tokens["coordinator1"])
        try:
            receive(subscriber, "authenticated")
            send(
                subscriber,
                {
                    "type": "subscribe",
                    "shipment_id": tracking["shipment"]["id"],
                    "cursor": 0,
                },
            )
            receive(subscriber, "subscribed")
            assert (
                receive(subscriber, "position.updated")["position"]["event_id"]
                == first["event_id"]
            )
        finally:
            subscriber.close()
        denied = connect(target, p.tokens["donor1"])
        try:
            assert receive(denied, "error")["code"] == "forbidden"
        finally:
            denied.close()
    finally:
        session.close()
        for process in ([nginx] if nginx is not None else []) + processes:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
