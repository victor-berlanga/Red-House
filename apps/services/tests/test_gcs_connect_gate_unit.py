"""Guardas puras: sin sockets, ADC, servicios ni acceso al bucket."""

import pytest

from .test_portal_gcs_failure_browser import BUCKET, GCSGate, gcs_signed_target


@pytest.mark.parametrize(
    "authority",
    [
        "storage.googleapis.com",
        "storage.googleapis.com:80",
        "storage.googleapis.com:443@evil.test",
        "evil.test:443",
        "storage.googleapis.com.:443",
        "localhost:443",
    ],
)
def test_connect_rejects_every_other_authority(authority):
    gate = GCSGate()
    assert gate.admit(authority) is None
    assert gate.rejected == 1 and gate.accepted == 0


def test_block_closes_both_ends_and_denies_reuse():
    class Connection:
        def __init__(self):
            self.closed = False
            self.shutdown_called = False

        def shutdown(self, _how):
            self.shutdown_called = True

        def close(self):
            self.closed = True

    gate = GCSGate()
    pair = (Connection(), Connection())
    epoch = gate.admit("storage.googleapis.com:443")
    assert gate.attach(epoch, pair)
    gate.block()
    assert all(item.closed and item.shutdown_called for item in pair)
    assert not gate.tunnels and gate.closed == 1
    assert gate.admit("storage.googleapis.com:443") is None
    gate.detach(pair)  # El handler que se despierta puede retirar el par ya cerrado.
    gate.allow()
    assert gate.admit("storage.googleapis.com:443") == 1


def test_pending_connect_cannot_survive_deny_then_allow():
    gate = GCSGate()
    epoch = gate.admit("storage.googleapis.com:443")
    gate.block()
    gate.allow()
    assert not gate.attach(epoch, (object(), object()))
    assert not gate.tunnels and gate.accepted == 0 and gate.rejected == 1


def test_signed_target_is_exact_object_and_bounded_ttl():
    object_path = "documents/synthetic-tenant/synthetic-file"
    url = f"https://storage.googleapis.com/{BUCKET}/{object_path}?X-Goog-Expires=300"
    gcs_signed_target(url, object_path)
    for invalid in (
        url.replace("https:", "http:"),
        url.replace("storage.googleapis.com", "storage.googleapis.com.evil.test"),
        url.replace("/synthetic-file?", "/historical-file?"),
        url.replace("=300", "=301"),
        url + "&X-Goog-Expires=300",
        url + "#fragment",
        url.replace("https://", "https://user:secret@"),
    ):
        with pytest.raises(RuntimeError, match="Destino o TTL GCS inválido"):
            gcs_signed_target(invalid, object_path)
