from urllib.parse import parse_qs, urlsplit

import pytest
from flask import Flask
from google.auth.credentials import AnonymousCredentials, Signing
from google.cloud.storage import Client
from redhouse.errors import APIError
from redhouse.storage import signed_url


class SyntheticSigning(Signing):
    @property
    def signer_email(self):
        return "synthetic@example.invalid"

    @property
    def signer(self):
        return self

    def sign_bytes(self, message):
        return b"synthetic-signature"


def context():
    app = Flask(__name__)
    app.extensions["gcs_signing"] = SyntheticSigning()
    return app.app_context()


def blob(generation=None):
    client = Client(project="synthetic", credentials=AnonymousCredentials())
    return client.bucket("synthetic-private-bucket").blob(
        "documents/synthetic-object", generation=generation
    )


def test_download_sdk_url_pins_verified_generation_and_requests_attachment():
    with context():
        url = signed_url(blob(123456789), "GET")
    query = parse_qs(urlsplit(url).query)
    assert query["generation"] == ["123456789"]
    assert query["response-content-disposition"] == ["attachment"]
    assert query["X-Goog-Expires"] == ["300"]


def test_upload_sdk_url_preserves_create_only_precondition():
    with context():
        url = signed_url(blob(), "PUT", "image/png")
    query = parse_qs(urlsplit(url).query)
    assert "generation" not in query
    assert "response-content-disposition" not in query
    assert "x-goog-if-generation-match" in query["X-Goog-SignedHeaders"][0].split(";")


def test_download_without_verified_generation_fails_closed():
    with context(), pytest.raises(APIError) as result:
        signed_url(blob(), "GET")
    assert result.value.code == "storage_unavailable"
    assert result.value.status == 503
