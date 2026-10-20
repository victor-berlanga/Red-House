"""Empaqueta código y un respaldo autorizado; excluye ADC personal y archivos locales."""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=ROOT / ".local/gcp-transfer")
    args = parser.parse_args()
    os.umask(0o077)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True, mode=0o700)
    report = json.loads(args.report.read_text())
    backup = Path(report["private_path"])
    snapshot = output / "snapshot"
    snapshot.mkdir()
    for name in ("postgres.dump", "roles.sql", "mongo.archive.gz", "dump.rdb"):
        shutil.copy2(backup / name, snapshot / name)
    configuration = snapshot / "configuration"
    configuration.mkdir()
    for name in (
        "apps",
        "postgres-password",
        "mongo-password",
        "redis-password",
        "web.json",
        "state.json",
        "installation.json",
    ):
        source = backup / "configuration" / name
        if source.is_dir():
            shutil.copytree(source, configuration / name)
        else:
            shutil.copy2(source, configuration / name)
    shutil.copy2(backup / "redis.acl", configuration / "redis.acl")
    shutil.copy2(backup.parent.parent / "redis.conf", configuration / "redis.conf")
    (snapshot / "expected.json").write_text(json.dumps(report["before"]) + "\n")

    names = (
        subprocess.check_output(
            ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
            cwd=ROOT,
        )
        .decode()
        .split("\0")
    )
    manifest = {}
    with tarfile.open(output / "project.tar.gz", "w:gz") as archive:
        for name in sorted(set(names) - {""}):
            relative = Path(name)
            if any(
                part in {".git", ".codegraph", ".local", ".venv", "__pycache__"}
                for part in relative.parts
            ):
                continue
            if (
                relative.name == ".env"
                or relative.name.startswith(".env.")
                and relative.name != ".env.example"
            ):
                continue
            path = ROOT / relative
            if path.is_symlink():
                raise ValueError(f"Revisar enlace antes de transferir: {name}")
            if not path.is_file():
                continue
            manifest[name] = hashlib.sha256(path.read_bytes()).hexdigest()
            archive.add(path, arcname=name, recursive=False)
    (output / "source-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    with tarfile.open(output / "data.tar.gz", "w:gz") as archive:
        archive.add(snapshot, arcname="snapshot")
    print(
        json.dumps(
            {
                "source_files": len(manifest),
                "archives": {
                    name: {
                        "bytes": (output / name).stat().st_size,
                        "sha256": hashlib.sha256(
                            (output / name).read_bytes()
                        ).hexdigest(),
                    }
                    for name in ("project.tar.gz", "data.tar.gz")
                },
                "personal_adc_included": False,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
