import importlib
import json
import logging
import sys
import tempfile
import threading
from pathlib import Path
from uuid import uuid4

import psycopg
import pytest
import requests
from werkzeug.serving import WSGIRequestHandler, make_server

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from redhouse.config import SERVICES
from redhouse.events import dispatch
from scripts.local import Environment


class QuietHandler(WSGIRequestHandler):
    def log_request(self, *_args, **_kwargs):
        pass


class Platform:
    def __init__(self, env, apps, servers):
        self.env, self.apps, self.servers = env, apps, servers
        self.urls = {
            s: f"http://127.0.0.1:{server.server_port}" for s, server in servers.items()
        }
        self.tokens = {}

    def request(
        self,
        service,
        method,
        path,
        *,
        user="medical2",
        data=None,
        key=None,
        headers=None,
    ):
        hdr = {"Accept": "application/json", "Idempotency-Key": key or uuid4().hex}
        if user:
            hdr["Authorization"] = "Bearer " + self.tokens[user]
        hdr.update(headers or {})
        return requests.request(
            method, self.urls[service] + path, json=data, headers=hdr, timeout=20
        )

    def ok(self, service, method, path, **kwargs):
        response = self.request(service, method, path, **kwargs)
        assert response.status_code < 300, (response.status_code, response.text)
        return response.json()["data"]

    def owner(self, service):
        return psycopg.connect(
            self.env.state["database_owners"][service],
            options="-c search_path=api,pg_catalog",
        )

    def drain(self, rounds=8):
        for _ in range(rounds):
            delivered = 0
            for service, app in self.apps.items():
                with app.app_context():
                    result = dispatch(200)
                    delivered += result["delivered"]
            if not delivered:
                break


@pytest.fixture(scope="session")
def platform():
    import os
    import shutil

    mongo_bin = (
        os.environ.get("REDHOUSE_TEST_MONGOD")
        or shutil.which("mongod")
        or "/private/tmp/red-house-mongodb-tools/bin/mongod"
    )
    directory = tempfile.mkdtemp(
        prefix="red-house-ms-tests-", dir=os.environ.get("REDHOUSE_TEST_ROOT", "/tmp")
    )
    env = Environment(directory, mongo_bin)
    apps, servers, threads = {}, {}, []
    try:
        env.init()
        for service in SERVICES:
            module = "servicio_monitoreo" if service == "monitoreo" else "ms_" + service
            config = dict(
                env.configs[service],
                TESTING=True,
                RATE_LIMIT=100000,
                INTERNAL_RATE_LIMIT=100000,
                WORKER_REQUIRED=False,
            )
            app = importlib.import_module(module).create_app(config)
            apps[service] = app
            servers[service] = make_server(
                "127.0.0.1", 0, app, threaded=True, request_handler=QuietHandler
            )
        urls = {
            s: f"http://127.0.0.1:{server.server_port}" for s, server in servers.items()
        }
        for app in apps.values():
            app.config["SERVICE_URLS"] = urls
        for server in servers.values():
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            threads.append(thread)
        instance = Platform(env, apps, servers)
        for username in env.state["accounts"]:
            result = requests.post(
                urls["identidad_acceso"] + "/api/v1/auth/login",
                json={"username": username, "password": env.state["password"]},
                timeout=10,
            )
            assert result.status_code == 200, (result.status_code, result.text)
            instance.tokens[username] = result.json()["data"]["access_token"]
        yield instance
    finally:
        for server in servers.values():
            server.shutdown()
            server.server_close()
        env.stop()


@pytest.fixture
def p(platform):
    return platform
