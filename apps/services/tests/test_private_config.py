"""Mounted web secrets must be validated after loading, including invalid ones."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "web"))
from src import create_app
from redhouse.config import SERVICES


@pytest.mark.parametrize("secret,accepted", [("a" * 64, True), ("short", False)])
def test_web_loads_and_validates_mounted_configuration(
    tmp_path, monkeypatch, secret, accepted
):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    config = {
        "SECRET_KEY": secret,
        "JWT_SECRET_KEY": "b" * 64,
        "SERVICE_URLS": {
            name: "http://127.0.0.1:" + str(port) for name, port in SERVICES.items()
        },
        "WEB_REDIS_URL": "redis://127.0.0.1:1/0",
        "WEB_REDIS_PREFIX": "test:web:",
        "WEB_DATABASE_URL": "postgresql://127.0.0.1:1/unused",
        "PRODUCTION": False,
        "SESSION_COOKIE_SECURE": False,
    }
    path = tmp_path / "config.json"
    path.write_text(json.dumps(config))
    if not accepted:
        with pytest.raises(RuntimeError, match="SECRET_KEY"):
            create_app({"MICROSERVICES_CONFIG": path})
    else:
        app = create_app({"MICROSERVICES_CONFIG": path})
        assert app.config["SECRET_KEY"] == secret
        assert app.test_client().get("/health/live").status_code == 200
