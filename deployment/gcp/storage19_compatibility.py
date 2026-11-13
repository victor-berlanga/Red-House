"""Build minimal GCS-only compatibility sources from the reviewed Git baseline.

The resulting modules omit the schema-19 internal provider field from existing
responses. They do not support local objects and must never be used after local
writes. Runtime images must also be checked against the exact baseline hashes.
"""

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path

REVISION = "6d8b88d0c8e5de6e1c9267c68fac2a6a8a4cd837"
MODULES = ("files.py", "reports.py")


def replace_once(source, old, new):
    if source.count(old) != 1:
        raise ValueError("El código base no coincide con el parche revisado.")
    return source.replace(old, new, 1)


def build(output):
    output = Path(output)
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    hashes = {}
    for name in MODULES:
        source = subprocess.check_output(
            ["git", "show", f"{REVISION}:apps/services/ms_documentos/{name}"]
        ).decode()
        original = source.encode()
        if name == "files.py":
            source = replace_once(
                source,
                "\n\ndef register_files(app, access):",
                '\n\ndef public_file(row):\n    return {key: value for key, value in row.items() if key != "storage_provider"}\n\n\ndef register_files(app, access):',
            )
            source = replace_once(
                source,
                '            "file": row,',
                '            "file": public_file(row),',
            )
            source = replace_once(
                source,
                "                    return row\n                except APIError:",
                "                    return public_file(row)\n                except APIError:",
            )
            source = replace_once(
                source,
                '        return atomic("file_verify:" + identifier, {}, work)',
                '        return public_file(atomic("file_verify:" + identifier, {}, work))',
            )
            source = replace_once(
                source,
                '            return listing(conn, "files", "shipment_id=%s", (identifier,))',
                '            result = listing(conn, "files", "shipment_id=%s", (identifier,))\n            result["items"] = [public_file(row) for row in result["items"]]\n            return result',
            )
        else:
            source = replace_once(
                source,
                'if key not in ("rows", "region_id", "sealed_authorization")',
                'if key not in ("rows", "region_id", "sealed_authorization", "storage_provider")',
            )
        compile(source, name, "exec")
        target = output / name
        with target.open("x") as file:
            file.write(source)
        target.chmod(0o644)
        hashes[name] = {
            "base_sha256": hashlib.sha256(original).hexdigest(),
            "compat_sha256": hashlib.sha256(source.encode()).hexdigest(),
        }
    with (output / "manifest.json").open("x") as file:
        json.dump(
            {"revision": REVISION, "files": hashes, "provider": "gcs-only"},
            file,
            indent=2,
        )
        file.write("\n")
    os.chmod(output / "manifest.json", 0o600)
    return hashes


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(build(args.output), indent=2))
