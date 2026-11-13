"""The web never follows a storage capability to an arbitrary server or route."""

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from flask import Flask

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "web"))
from src.access import BusinessError
from src.integration.storage_client import storage_target, upload_object


@pytest.mark.parametrize(
    "url",
    [
        "http://redhouse.test/storage/v1/objects/token",
        "https://redhouse.test.attacker.invalid/storage/v1/objects/token",
        "https://redhouse.test:444/storage/v1/objects/token",
        "https://attacker.invalid@redhouse.test/storage/v1/objects/token",
        "https://redhouse.test/services/identidad-acceso/api/v1/users",
        "https://redhouse.test/storage/v1/objects/token?next=attacker",
        "https://redhouse.test/storage/v1/objects/token#fragment",
        "https://redhouse.test/storage/v1/objects/../token",
        "https://storage.googleapis.com.attacker.invalid/bucket/file",
        "https://storage.googleapis.com:444/bucket/file",
    ],
)
def test_storage_url_rejects_other_origins_and_paths(url):
    app = Flask(__name__)
    app.config["STORAGE_PUBLIC_BASE_URL"] = "https://redhouse.test"
    with app.app_context(), pytest.raises(BusinessError):
        storage_target(url)


def test_local_upload_uses_modular_owner_without_network(monkeypatch):
    app = Flask(__name__)
    calls = []

    class Reply:
        status_code = 201

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    def invoke(*args, **kwargs):
        calls.append((args, kwargs))
        return Reply()

    app.extensions["application_kernel"] = SimpleNamespace(
        apps={
            "documentos": SimpleNamespace(
                config={
                    "STORAGE_PUBLIC_BASE_URL": "https://redhouse.test:443",
                }
            )
        },
        request=invoke,
    )
    monkeypatch.setattr(
        "src.integration.storage_client.http_client",
        lambda: pytest.fail("Modular local upload used network"),
    )
    with app.app_context():
        assert (
            storage_target("https://storage.googleapis.com/bucket/file?signature=test")
            is False
        )
        assert (
            upload_object(
                "https://redhouse.test/portal-storage/v1/objects/token==",
                b"synthetic",
                {"Content-Type": "application/pdf"},
            )
            == 201
        )
    assert calls == [
        (
            ("documentos", "PUT", "/storage/v1/objects/token=="),
            {"data": b"synthetic", "headers": {"Content-Type": "application/pdf"}},
        )
    ]
