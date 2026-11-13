"""Network-peer trust and anonymous quota isolation behind the delivery gateway."""

import json
import threading

import pytest
import requests
from flask import Flask, request
from waitress import create_server

from redhouse.proxy import TrustedProxy, trusted_peer, waitress_proxy_options
from redhouse.security import rate_limit


def application(monkeypatch):
    app = Flask(__name__)
    app.config.update(SERVICE="proxy-test", REDIS_PREFIX="test:", RATE_LIMIT=2)
    counts = {}

    class Counters:
        def eval(self, _script, _number, key):
            counts[key] = counts.get(key, 0) + 1
            return counts[key]

    monkeypatch.setattr("redhouse.security.redis_call", lambda fn: fn(Counters()))

    @app.get("/")
    def index():
        rate_limit()
        return {
            "address": request.remote_addr,
            "scheme": request.scheme,
            "host": request.host,
        }

    from redhouse.errors import APIError

    @app.errorhandler(APIError)
    def failure(exc):
        return {"error": exc.code}, exc.status

    return app


def test_untrusted_peer_cannot_change_address_scheme_or_host(monkeypatch):
    app = application(monkeypatch)
    app.wsgi_app = TrustedProxy(app.wsgi_app, "192.0.2.10")
    client = app.test_client()
    response = client.get(
        "/",
        headers={
            "X-Forwarded-For": "198.51.100.25",
            "X-Forwarded-Proto": "https",
            "X-Forwarded-Host": "attacker.invalid",
            "Forwarded": "for=198.51.100.25;host=attacker.invalid",
        },
        environ_overrides={"REMOTE_ADDR": "203.0.113.20"},
    )
    assert response.json == {
        "address": "203.0.113.20",
        "scheme": "http",
        "host": "localhost",
    }


def test_gevent_policy_uses_one_proxy_hop_and_separates_client_quotas(monkeypatch):
    app = application(monkeypatch)
    app.wsgi_app = TrustedProxy(app.wsgi_app, "192.0.2.10")
    client = app.test_client()

    def get(address):
        return client.get(
            "/",
            headers={
                "X-Forwarded-For": "198.51.100.99, " + address,
                "X-Forwarded-Proto": "https",
                "X-Forwarded-Host": "attacker.invalid",
            },
            environ_overrides={"REMOTE_ADDR": "192.0.2.10"},
        )

    assert get("203.0.113.1").json == {
        "address": "203.0.113.1",
        "scheme": "https",
        "host": "localhost",
    }
    assert get("203.0.113.1").status_code == 200
    assert get("203.0.113.1").status_code == 429
    assert get("203.0.113.2").status_code == 200


@pytest.mark.parametrize("trusted", [True, False])
def test_real_waitress_boundary_drops_untrusted_headers(monkeypatch, trusted):
    app = application(monkeypatch)
    config = {"TRUSTED_PROXY_ADDRESS": "127.0.0.1"} if trusted else {}
    server = create_server(
        app, host="127.0.0.1", port=0, threads=1, **waitress_proxy_options(config)
    )
    stopping = threading.Event()

    def serve_until_stopped():
        while not stopping.is_set():
            server.asyncore.loop(timeout=0.05, count=1, map=server._map)

    thread = threading.Thread(target=serve_until_stopped, daemon=True)
    thread.start()
    session = requests.Session()
    session.trust_env = False
    try:
        url = f"http://127.0.0.1:{server.effective_port}/"
        for address in ("203.0.113.1", "203.0.113.2"):
            response = session.get(
                url,
                headers={
                    "X-Forwarded-For": address,
                    "X-Forwarded-Proto": "https",
                    "X-Forwarded-Host": "attacker.invalid",
                    "Forwarded": "for=198.51.100.1",
                },
                timeout=3,
            )
            assert response.status_code == 200
            assert response.json()["address"] == (address if trusted else "127.0.0.1")
            assert response.json()["scheme"] == ("https" if trusted else "http")
            assert response.json()["host"].startswith("127.0.0.1:")
    finally:
        session.close()
        stopping.set()
        thread.join(timeout=2)
        assert not thread.is_alive()
        server.task_dispatcher.shutdown()
        server.asyncore.close_all(map=server._map)


def test_proxy_configuration_fails_closed_on_wildcard_or_ambiguous_dns(monkeypatch):
    with pytest.raises(ValueError):
        trusted_peer({"TRUSTED_PROXY_ADDRESS": "*"})
    with pytest.raises(ValueError):
        trusted_peer(
            {"TRUSTED_PROXY_ADDRESS": "127.0.0.1", "TRUSTED_PROXY_HOST": "gateway"}
        )
    monkeypatch.setattr(
        "redhouse.proxy.socket.getaddrinfo",
        lambda *_args, **_kwargs: [
            (2, 1, 6, "", ("192.0.2.1", 0)),
            (2, 1, 6, "", ("192.0.2.2", 0)),
        ],
    )
    with pytest.raises(ValueError):
        trusted_peer({"TRUSTED_PROXY_HOST": "gateway"})


def test_public_generator_applies_same_sanitization_to_http_and_wss(tmp_path):
    import importlib.util
    from pathlib import Path

    root = Path(__file__).resolve().parents[3]
    spec = importlib.util.spec_from_file_location(
        "configure_public_under_test", root / "deployment/gcp/configure_public.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    (tmp_path / "apps").mkdir()
    (tmp_path / "web.json").write_text("{}")
    services = json.loads((root / "compose.yaml").read_text())["services"]
    for name in services:
        if name.endswith("-a"):
            (tmp_path / "apps" / (name[:-2].replace("-", "_") + ".json")).write_text(
                "{}"
            )
    module.configure(tmp_path, "192.0.2.10")
    config = (tmp_path / "public.nginx.conf").read_text()
    wss = config.split("location /services/transporte/ws/v1/tracking/ {", 1)[1].split(
        "}", 1
    )[0]
    for header in (
        "X-Forwarded-For $remote_addr",
        'X-Forwarded-Host ""',
        'X-Forwarded-Prefix ""',
        'Forwarded ""',
    ):
        assert f"proxy_set_header {header};" in wss
    assert (
        json.loads((tmp_path / "apps/donantes.json").read_text())["TRUSTED_PROXY_HOST"]
        == "gateway-private"
    )
    assert (
        json.loads((tmp_path / "web.json").read_text())["TRUSTED_PROXY_HOST"]
        == "gateway-private"
    )


def test_every_internal_gateway_location_overwrites_forwarded_headers():
    from pathlib import Path

    config = (Path(__file__).resolve().parents[3] / "deployment/nginx.conf").read_text()
    locations = config.split("proxy_set_header Host $http_host;")[1:]
    assert len(locations) == 13
    for location in locations:
        body = location.split("}", 1)[0]
        assert "proxy_set_header X-Forwarded-For $remote_addr;" in body
        assert "proxy_set_header X-Forwarded-Proto $scheme;" in body
        for header in (
            "Forwarded",
            "X-Forwarded-Host",
            "X-Forwarded-Port",
            "X-Forwarded-Prefix",
            "X-Forwarded-By",
        ):
            assert f'proxy_set_header {header} "";' in body


def test_proxy_and_upstreams_use_aliases_on_only_the_private_network():
    """Dual-network containers must never make the trusted peer ambiguous."""
    import re
    from pathlib import Path

    root = Path(__file__).resolve().parents[3]
    services = json.loads((root / "compose.yaml").read_text())["services"]
    expected = {
        name + "-private"
        for name in services
        if name.endswith(("-a", "-b")) or name in ("web", "gateway")
    }
    for name, service in services.items():
        if name + "-private" not in expected:
            continue
        networks = service["networks"]
        assert networks["data"]["aliases"] == [name + "-private"]
        assert all(
            name + "-private" not in (options or {}).get("aliases", [])
            for network, options in networks.items()
            if network != "data"
        )
    upstreams = set(
        re.findall(
            r"server ([a-z-]+):8080 resolve",
            (root / "deployment/nginx.conf").read_text(),
        )
    )
    assert upstreams == expected - {"web-private", "gateway-private"}
