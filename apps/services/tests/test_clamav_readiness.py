"""Boundary tests for the read-only shell probe; no daemon or Docker."""

import os
from pathlib import Path
import subprocess
import sys

import pytest


SCRIPT = Path(__file__).resolve().parents[3] / "deployment/gcp/clamav_readiness.sh"
NOW = 1794551068


def install_tool_adapters(tools):
    """Provide BusyBox-compatible test adapters on the macOS runner."""
    if sys.platform == "darwin":
        (tools / "stat").write_text(
            "#!/bin/sh\nexec /usr/bin/stat -f '%d:%i:%z:%m:%c' \"$3\"\n"
        )
    (tools / "timeout").write_text(
        f"#!{sys.executable}\n"
        "import subprocess,sys\n"
        "try:\n"
        " result=subprocess.run(sys.argv[2:], timeout=int(sys.argv[1]))\n"
        " sys.exit(result.returncode)\n"
        "except subprocess.TimeoutExpired:\n"
        " sys.exit(124)\n"
    )
    for tool in tools.iterdir():
        tool.chmod(0o755)


@pytest.mark.parametrize(
    ("age", "disk_version", "loaded", "expected"),
    [
        (0, "28182", "28182", "healthy: signatures current"),
        (172800, "28182", "28182", "healthy: signatures current"),
        (172801, "28182", "28182", "degraded: signature age"),
        (-300, "28182", "28182", "healthy: signatures current"),
        (-301, "28182", "28182", "degraded: signature age"),
        (0, "28182", "28181", "degraded: version mismatch"),
        (0, "28182", "invalid", "degraded: invalid scanner version"),
    ],
)
def test_readiness_boundaries(tmp_path, age, disk_version, loaded, expected):
    header = f"ClamAV-VDB:date:{disk_version}:1:90:X:X:builder:{NOW - age}"
    (tmp_path / "daily.cld").write_bytes(header.ljust(512).encode())
    tools = tmp_path / "bin"
    tools.mkdir()
    (tools / "date").write_text(f"#!/bin/sh\necho {NOW}\n")
    (tools / "nc").write_text(
        f"#!/bin/sh\necho 'ClamAV 1.4/{loaded}/Fri Nov 13 06:24:28 2026'\n"
    )
    install_tool_adapters(tools)
    result = subprocess.run(
        ["/bin/sh", str(SCRIPT)],
        env={
            **os.environ,
            "PATH": f"{tools}:/usr/bin:/bin",
            "CLAMAV_DATABASE_DIR": str(tmp_path),
        },
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.stdout.strip() == expected
    assert result.returncode == (0 if expected.startswith("healthy") else 1)
    assert not result.stderr


def test_missing_database_is_degraded_without_path_disclosure(tmp_path):
    result = subprocess.run(
        ["/bin/sh", str(SCRIPT)],
        env={**os.environ, "CLAMAV_DATABASE_DIR": str(tmp_path)},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert result.stdout.strip() == "degraded: database unavailable"
    assert not result.stderr


def test_truncated_header_and_ambiguous_database_fail_closed(tmp_path):
    (tmp_path / "daily.cld").write_bytes(b"ClamAV-VDB:short")
    tools = tmp_path / "bin"
    tools.mkdir()
    (tools / "nc").write_text(
        "#!/bin/sh\necho 'ClamAV 1.4/1/Fri Nov 13 06:24:28 2026'\n"
    )
    (tools / "nc").chmod(0o755)
    install_tool_adapters(tools)
    env = {
        **os.environ,
        "PATH": f"{tools}:/usr/bin:/bin",
        "CLAMAV_DATABASE_DIR": str(tmp_path),
    }
    result = subprocess.run(
        ["/bin/sh", str(SCRIPT)], env=env, capture_output=True, text=True
    )
    assert result.returncode == 1
    assert result.stdout.strip() == "degraded: invalid database header"
    (tmp_path / "daily.cvd").write_bytes(b"ambiguous")
    result = subprocess.run(
        ["/bin/sh", str(SCRIPT)], env=env, capture_output=True, text=True
    )
    assert result.returncode == 1
    assert result.stdout.strip() == "degraded: database unavailable"


def test_invalid_policy_and_unavailable_scanner(tmp_path):
    header = f"ClamAV-VDB:date:1:1:90:X:X:builder:{NOW}"
    (tmp_path / "daily.cld").write_bytes(header.ljust(512).encode())
    tools = tmp_path / "bin"
    tools.mkdir()
    (tools / "nc").write_text("#!/bin/sh\nexit 1\n")
    (tools / "nc").chmod(0o755)
    install_tool_adapters(tools)
    env = {
        **os.environ,
        "PATH": f"{tools}:/usr/bin:/bin",
        "CLAMAV_DATABASE_DIR": str(tmp_path),
        "CLAMD_SIGNATURE_MAX_AGE_SECONDS": "00048",
    }
    result = subprocess.run(
        ["/bin/sh", str(SCRIPT)], env=env, capture_output=True, text=True
    )
    assert result.returncode == 1
    assert result.stdout.strip() == "degraded: invalid policy"
    env["CLAMD_SIGNATURE_MAX_AGE_SECONDS"] = "172800"
    result = subprocess.run(
        ["/bin/sh", str(SCRIPT)], env=env, capture_output=True, text=True
    )
    assert result.returncode == 1
    assert result.stdout.strip() == "degraded: scanner unavailable"


@pytest.mark.parametrize(
    "change", ["version", "header", "inode", "extension", "oversize"]
)
def test_detects_changes_during_check_and_bounded_response(tmp_path, change):
    header = f"ClamAV-VDB:date:1:1:90:X:X:builder:{NOW}".ljust(512).encode()
    (tmp_path / "daily.cld").write_bytes(header)
    tools = tmp_path / "bin"
    tools.mkdir()
    commands = {
        "version": 'if [ -f "$PROBE_TEST_DIR/seen" ]; then v=2; else v=1; fi',
        "header": 'printf X | dd of="$PROBE_TEST_DIR/daily.cld" bs=1 seek=10 conv=notrunc 2>/dev/null; v=1',
        "inode": 'cp "$PROBE_TEST_DIR/daily.cld" "$PROBE_TEST_DIR/new"; mv "$PROBE_TEST_DIR/new" "$PROBE_TEST_DIR/daily.cld"; v=1',
        "extension": 'mv "$PROBE_TEST_DIR/daily.cld" "$PROBE_TEST_DIR/daily.cvd"; v=1',
        "oversize": "head -c 512 /dev/zero | tr '\\0' X; exit 0",
    }
    (tools / "nc").write_text(
        "#!/bin/sh\n"
        f'if [ ! -f "$PROBE_TEST_DIR/seen" ]; then {commands[change]}; '
        f"else v={'2' if change == 'version' else '1'}; fi\n"
        'touch "$PROBE_TEST_DIR/seen"\n'
        'echo "ClamAV 1.4/$v/Fri Nov 13 06:24:28 2026"\n'
    )
    (tools / "date").write_text(f"#!/bin/sh\necho {NOW}\n")
    install_tool_adapters(tools)
    env = {
        **os.environ,
        "PATH": f"{tools}:/usr/bin:/bin",
        "CLAMAV_DATABASE_DIR": str(tmp_path),
        "PROBE_TEST_DIR": str(tmp_path),
    }
    result = subprocess.run(
        ["/bin/sh", str(SCRIPT)], env=env, capture_output=True, text=True
    )
    assert result.returncode == 1
    assert result.stdout.strip() == (
        "degraded: scanner unavailable"
        if change == "oversize"
        else "degraded: update in progress"
    )
    assert not result.stderr
