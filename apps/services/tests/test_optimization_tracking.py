"""Real WSS/Redis lease cost; data polling and authorization are counted separately."""

import os
from time import perf_counter, sleep

from .test_final_tracking import connect, receive, send
from .test_final_tracking import tracking as tracking  # noqa: PLC0414 - pytest fixture
from .test_optimization import evidence


def test_connection_leases_do_not_repeat_for_every_heartbeat(p, tracking, monkeypatch):
    from ms_transporte import tracking_socket

    counts = {"leases": 0, "authorization": 0}
    lease, authorize = tracking_socket.lease, tracking_socket.authorize

    def counted_lease(*args, **kwargs):
        counts["leases"] += 1
        return lease(*args, **kwargs)

    def counted_authorize(*args, **kwargs):
        counts["authorization"] += 1
        return authorize(*args, **kwargs)

    monkeypatch.setattr(tracking_socket, "lease", counted_lease)
    monkeypatch.setattr(tracking_socket, "authorize", counted_authorize)
    started = perf_counter()
    ws = connect(tracking, p.tokens["coordinator1"])
    try:
        receive(ws, "authenticated")
        for _ in range(20):
            send(ws, {"type": "heartbeat"})
            receive(ws, "heartbeat")
        elapsed = perf_counter() - started
        assert counts["authorization"] >= 21
        baseline = os.environ.get("OPT_TRACKING_BASELINE") == "1"
        evidence(
            "tracking-leases-" + ("before" if baseline else "after"),
            dict(
                counts,
                heartbeats=20,
                elapsed_seconds=elapsed,
                transport="real WSS, TLS verified; no subscription",
            ),
        )
        if not baseline:
            assert counts["leases"] <= 2 + 2 * (int(elapsed / 10) + 1)
            # Exercise renewal with a live connection, without changing the clock
            # or the authorization/expiry settings of the service.
            deadline = perf_counter() + 12
            while counts["leases"] < 4 and perf_counter() < deadline:
                sleep(1)
                send(ws, {"type": "heartbeat"})
                receive(ws, "heartbeat")
            assert counts["leases"] >= 4
    finally:
        ws.close()
