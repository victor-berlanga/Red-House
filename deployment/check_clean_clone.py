"""Certifica instalación nueva de una instantánea local sin tocar .local/runtime.

Requiere detener previamente el Compose de demostración (usa sus mismos puertos).
No publica commits: crea dos repositorios temporales y volúmenes independientes.
"""

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(args, cwd, env=None, output=None):
    result = subprocess.run(
        args,
        cwd=cwd,
        env=env,
        stdout=output or subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=output is None,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(
            "Falló " + " ".join(args[:4]) + ": " + str(result.stderr)[-1500:]
        )
    return result.stdout


def main():
    directory = Path(
        tempfile.mkdtemp(
            prefix="redhouse-clean-", dir=os.environ.get("REDHOUSE_TEST_ROOT")
        )
    )
    source, clone = directory / "snapshot", directory / "clone"
    source.mkdir()
    paths = run(["git", "ls-files", "-co", "--exclude-standard", "-z"], ROOT).split(
        "\0"
    )
    digest = hashlib.sha256()
    for relative in sorted(set(paths) - {""}):
        path = ROOT / relative
        if not path.is_file():
            continue
        # The tracked CodeGraph ignore marker is configuration, not its cache.
        if path.name == ".env" or (
            relative != ".codegraph/.gitignore"
            and any(x in path.parts for x in (".local", ".venv", ".codegraph"))
        ):
            raise RuntimeError(
                "Archivo privado en la selección de Git; revisar antes de clonar."
            )
        target = source / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        digest.update(relative.encode() + path.read_bytes())
    run(["git", "init", "-q"], source)
    run(["git", "add", "."], source)
    run(
        [
            "git",
            "-c",
            "user.name=Red House validation",
            "-c",
            "user.email=validation@example.invalid",
            "commit",
            "-qm",
            "Local working-tree snapshot for clean installation",
        ],
        source,
    )
    run(["git", "clone", "--no-hardlinks", str(source), str(clone)], directory)
    commit = run(["git", "rev-parse", "HEAD"], clone).strip()
    assert not run(["git", "status", "--porcelain"], clone)
    project_name = (
        "redhouse-clean-" + hashlib.sha256(str(directory).encode()).hexdigest()[:8]
    )
    environment = dict(
        os.environ,
        COMPOSE_PROJECT_NAME=project_name,
        REDHOUSE_COMPOSE_DIR=str(clone / ".local/compose"),
    )
    compose = ["docker", "compose", "-f", str(clone / "compose.yaml")]
    log = directory / "installation.log"
    steps = []
    commands = [
        ["python3", "deployment/prepare.py"],
        compose + ["--profile", "install", "build", "bootstrap"],
        compose + ["up", "-d", "--wait", "postgres", "redis", "mongodb"],
        compose + ["--profile", "install", "run", "--rm", "bootstrap"],
        compose + ["--parallel", "2", "build"],
        ["python3", "deployment/start.py"],
        [
            str(ROOT / "apps/services/.venv/bin/python"),
            "deployment/verify.py",
            "--phase",
            "smoke",
            "--output",
            str(directory / "business"),
        ],
        compose + ["--profile", "install", "run", "--rm", "bootstrap"],
    ]
    destination = ROOT / "documentation/evidencias/segundo-parcial/clean-clone.json"
    result = {
        "date": datetime.now(timezone.utc).isoformat(),
        "status": "running",
        "snapshot_commit": commit,
        "compose_project": project_name,
        "files_sha256": digest.hexdigest(),
        "source": "Instantánea del árbol de trabajo en commit local temporal; no publicada",
        "steps": steps,
        "private_environment": str(directory),
    }

    def save():
        destination.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")

    save()
    try:
        with log.open("wb") as stream:
            for command in commands:
                label = " ".join(command).replace(str(clone), "<clean-clone>")
                result["stage"] = label
                save()
                print(json.dumps({"stage": label}), flush=True)
                run(command, clone, environment, stream)
                steps.append(
                    {
                        "command": label,
                        "status": "passed",
                    }
                )
                save()
        result["business"] = json.loads(
            (directory / "business/docker-results.json").read_text()
        )
    except Exception as error:
        result.update(status="failed", error_type=type(error).__name__)
        save()
        raise
    finally:
        # Keep volumes and files available for diagnosis; never use down -v.
        try:
            run(compose + ["stop"], clone, environment)
            result["containers_stopped"] = True
        except Exception:
            result.update(status="failed", containers_stopped=False)
            raise
        finally:
            save()
    result.update(status="passed", stage="complete")
    result["completed_at"] = datetime.now(timezone.utc).isoformat()
    save()
    print(
        json.dumps(
            {
                "status": "passed",
                "evidence": str(destination),
                "temporary_environment": str(directory),
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
