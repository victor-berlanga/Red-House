"""Fallos del arnés no deben ocultar sesiones inválidas ni repetir refresh."""

from collections import deque
import json

from lxml import etree
import pytest

from redhouse.codec import xml_value
from scripts.load_client import LoadFailure, LoadSession, isolated_urls

IDENTIFIER = "00000000-0000-4000-8000-000000000001"
URLS = {
    "identidad_acceso": "http://127.0.0.1:19001",
    "donantes": "http://127.0.0.1:19002",
}
PAGE = {"items": [], "page": 1, "page_size": 20, "total": 0}
PATH = "/api/v1/public/campaign-feed?page_size=20"


def tokens(index=1, *, user=False):
    value = {
        "access_token": f"synthetic-access-{index}",
        "refresh_token": f"synthetic-refresh-{index}",
        "token_type": "Bearer",
        "expires_in": 60,
    }
    if user:
        value["user"] = {
            "id": IDENTIFIER,
            "tenant_id": IDENTIFIER,
            "region_id": IDENTIFIER,
            "username": "donor1",
            "role": "DONOR",
            "active": True,
            "version": 1,
        }
    return value


class Reply:
    def __init__(self, data, mime="application/json", status=200):
        self.payload = {
            "data": data,
            "meta": {
                "correlation_id": IDENTIFIER,
                "service": "synthetic",
                "version": "1",
            },
        }
        self.status_code = status
        self.headers = {"Content-Type": mime + "; charset=utf-8"}
        self.failures = []
        if mime == "application/xml":
            root = etree.Element("response")
            xml_value(root, self.payload)
            self.content = etree.tostring(root)
        else:
            self.content = json.dumps(self.payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def json(self):
        return self.payload

    def failure(self, value):
        self.failures.append(value)


class Client:
    def __init__(self, replies):
        self.replies = deque(replies)
        self.calls = []

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        return self.replies.popleft()


@pytest.mark.parametrize(
    "url",
    [
        "https://34.18.186.116:443",
        "https://example.com:443",
        "http://127.0.0.1:8080@34.18.186.116:443",
        "http://user:secret@127.0.0.1:8080",
        "http://127.0.0.1:8080?redirect=x",
        "http://127.0.0.1:8080/services",
        "file:///private/tmp/state",
    ],
)
def test_load_cannot_target_shared_or_ambiguous_destinations(url):
    with pytest.raises(ValueError):
        isolated_urls({"identidad_acceso": url})


@pytest.mark.parametrize("mime", ["application/json", "application/xml"])
def test_load_rotates_then_uses_new_token_and_revokes_latest(mime):
    now = [0]
    client = Client(
        [
            Reply(value, mime)
            for value in (tokens(user=True), PAGE, tokens(2), PAGE, {"revoked": True})
        ]
    )
    session = LoadSession(client, URLS, clock=lambda: now[0], mime=mime, no_cache=True)
    session.login("donor1", "synthetic-password")
    session.request("donantes", PATH, "page")
    now[0] = 31
    session.request("donantes", PATH, "page")
    session.close()
    assert len(client.calls) == 5
    assert client.calls[1][2]["headers"]["Authorization"] == "Bearer synthetic-access-1"
    assert client.calls[3][2]["headers"]["Authorization"] == "Bearer synthetic-access-2"
    for index in (1, 3):
        assert client.calls[index][2]["headers"]["Cache-Control"] == "no-cache"
    for index in (0, 2, 4):
        assert "Cache-Control" not in client.calls[index][2]["headers"]
    for index, refresh in ((2, "synthetic-refresh-1"), (4, "synthetic-refresh-2")):
        args = client.calls[index][2]
        if mime == "application/xml":
            assert etree.fromstring(args["data"]).findtext("refresh_token") == refresh
            assert "json" not in args
        else:
            assert args["json"] == {"refresh_token": refresh}
        assert "Authorization" not in args["headers"]
    assert all(call[2]["allow_redirects"] is False for call in client.calls)
    assert session.access is None and session.refresh is None and session.user is None


def test_uncertain_refresh_is_never_retried_and_cleanup_forgets_credentials():
    now = [0]
    lost = Reply({"private": "must-not-appear"}, status=0)
    revoke = Reply({}, status=503)
    client = Client([Reply(tokens(user=True)), lost, revoke])
    session = LoadSession(client, URLS, clock=lambda: now[0])
    session.login("donor1", "synthetic-password")
    now[0] = 31
    with pytest.raises(LoadFailure, match="^http_0$"):
        session.request("donantes", PATH, "page")
    with pytest.raises(LoadFailure, match="^session_unavailable$"):
        session.request("donantes", PATH, "page")
    assert len(client.calls) == 2
    assert lost.failures == ["http_0"]
    with pytest.raises(LoadFailure, match="^http_503$"):
        session.close()
    assert len(client.calls) == 3
    assert revoke.failures == ["http_503"]
    assert session.access is None and session.refresh is None and session.user is None


def test_load_rejects_wrong_identity_without_recording_response_contents():
    value = tokens(user=True)
    value["user"]["username"] = "another-synthetic-user"
    reply = Reply(value)
    session = LoadSession(Client([reply]), URLS)
    with pytest.raises(LoadFailure, match="^response_contract$"):
        session.login("donor1", "synthetic-password")
    assert reply.failures == ["response_contract"]
    assert session.access is None and session.refresh is None


def test_load_rejects_success_status_with_invalid_contract():
    reply = Reply({"items": [], "page": "invalid"})
    session = LoadSession(Client([reply]), URLS)
    with pytest.raises(LoadFailure, match="^response_contract$"):
        session.request("donantes", PATH, "page", protected=False)
    assert reply.failures == ["response_contract"]
