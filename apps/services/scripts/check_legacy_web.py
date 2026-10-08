"""Regresión del modo anterior usando bases aleatorias en el clúster aislado de MS."""

import argparse
import json
import os
import sys
from pathlib import Path

import pytest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    state = json.loads((args.directory / "state.json").read_text())
    if Path(state["directory"]).resolve() != args.directory.resolve():
        raise RuntimeError("Entorno aislado inválido.")
    os.environ["TEST_POSTGRES_URL"] = state["database_admin"]
    os.environ["BACKEND_MODE"] = "local"
    folder = Path(__file__).resolve().parents[2] / "web-monolito01"
    sys.path.insert(0, str(folder))
    raise SystemExit(
        pytest.main(
            [
                str(folder / "tests"),
                "-q",
                "--maxfail=1",
                "--junitxml=" + str(args.report),
            ]
        )
    )


if __name__ == "__main__":
    main()
