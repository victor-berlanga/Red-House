"""Diagnostic failures must not disclose emulator authentication metadata."""

import runpy
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


def test_rpc_failure_hides_server_details_and_closes_channel(tmp_path, monkeypatch, capsys):
    token = "synthetic-emulator-credential-never-print"
    config = tmp_path / "emulator.ini"
    config.write_text("grpc.port=8580\ngrpc.token=" + token + "\n")

    class RpcError(Exception):
        def code(self):
            return SimpleNamespace(name="UNAUTHENTICATED")

    class Channel:
        closed = False

        def unary_unary(self, _path):
            def request(_body, **_kwargs):
                raise RpcError("Server echoed credential: " + token)

            return request

        def close(self):
            self.closed = True

    channel = Channel()
    monkeypatch.setitem(sys.modules, "grpc", SimpleNamespace(
        RpcError=RpcError, insecure_channel=lambda _: channel,
    ))
    script = Path(__file__).with_name("aim_virtual_camera.py")
    monkeypatch.setattr(sys, "argv", [str(script), str(config)])
    with pytest.raises(SystemExit) as stopped:
        runpy.run_path(str(script), run_name="__main__")
    captured = capsys.readouterr()
    assert stopped.value.code == 1
    assert channel.closed
    assert captured.err == "camera_rpc_failed: UNAUTHENTICATED\n"
    assert token not in captured.out + captured.err
    assert "Server echoed" not in captured.out + captured.err
