"""Conserva estado público del despliegue sin publicar configuraciones privadas."""

import hashlib
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def capture(*args):
    return subprocess.check_output(args, text=True).strip()


def main():
    ids = capture(
        "docker",
        "ps",
        "-aq",
        "--filter",
        "label=com.docker.compose.project=redhouse-parcial2",
    ).splitlines()
    containers = json.loads(capture("docker", "inspect", *ids))
    assert len(containers) == 27
    public_path = ROOT / ".local/compose/public.json"
    public = json.loads(public_path.read_text()) if public_path.exists() else None
    result = {"date": datetime.now(timezone.utc).isoformat(), "containers": []}
    public_ports = set()
    for item in containers:
        assert item["State"]["Running"]
        assert item["State"]["Health"]["Status"] == "healthy"
        ports = item["NetworkSettings"]["Ports"]
        for bindings in ports.values():
            for binding in bindings or []:
                if binding["HostIp"] != "127.0.0.1":
                    assert public and item["Name"].endswith("-gateway-1")
                    assert binding["HostIp"] == "0.0.0.0"
                    assert binding["HostPort"] in ("80", "443")
                    public_ports.add(binding["HostPort"])
        result["containers"].append(
            {
                "name": item["Name"].lstrip("/"),
                "health": "healthy",
                "image_id": item["Image"],
                "ports": ports,
            }
        )
    result["systemd_active"] = capture("systemctl", "is-active", "redhouse")
    result["systemd_enabled"] = capture("systemctl", "is-enabled", "redhouse")
    assert (
        result["systemd_active"] == "active" and result["systemd_enabled"] == "enabled"
    )
    if public:
        assert public_ports == {"80", "443"}
        result["public"] = public
        result["certificate_timer"] = capture(
            "systemctl", "is-active", "redhouse-certbot.timer"
        )
        assert result["certificate_timer"] == "active"
    result["logical_cpus"] = os.cpu_count()
    result["os"] = Path("/etc/centos-release").read_text().strip()
    usage = shutil.disk_usage(ROOT)
    result["disk"] = {
        "total_bytes": usage.total,
        "used_bytes": usage.used,
        "free_bytes": usage.free,
    }
    result["restoration"] = json.loads(
        (ROOT / ".local/compose/gcp-restoration.json").read_text()
    )
    result["source_hashes"] = {
        name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
        for name in (
            "compose.yaml",
            "deployment/start.py",
            "apps/services/redhouse/storage.py",
            "apps/web/src/integration/sessions.py",
            "apps/web/scripts/run_web.py",
            "apps/services/redhouse/openapi.py",
        )
    }
    web = next(item for item in containers if item["Name"].endswith("-web-1"))
    assert not any("gcs_adc" in mount["Destination"] for mount in web["Mounts"])
    code = "import hashlib,json; print(json.dumps({p:hashlib.sha256(open('/app/'+p,'rb').read()).hexdigest() for p in ['apps/services/redhouse/storage.py','apps/web/src/integration/sessions.py']}))"
    hashes = json.loads(capture("docker", "exec", web["Id"], "python", "-c", code))
    assert all(
        result["source_hashes"][name] == digest for name, digest in hashes.items()
    )
    result["web_image_matches_sources"] = True
    result["result"] = "passed"
    path = ROOT / (
        "documentation/evidencias/gcp/public/runtime.json"
        if public
        else "documentation/evidencias/gcp/runtime.json"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                "result": "passed",
                "healthy_containers": len(containers),
                "systemd": result["systemd_active"],
                "ports": "public 80/443; others loopback"
                if public
                else "loopback only",
                "disk_free_gb": round(usage.free / 10**9, 2),
            }
        )
    )


if __name__ == "__main__":
    main()
