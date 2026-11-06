"""Explicit, bounded reference acquisition; no downloads during clinical requests."""

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ms_compatibilidad.reference_catalogue import catalogues
from ms_priorizacion_geografia.road_sources import manifest


def download(url):
    # Requests validates TLS with its CA bundle and honors REQUESTS_CA_BUNDLE.
    with requests.get(
        url,
        headers={"User-Agent": "RedHouse-Academic-Reference-Importer/0.4.4"},
        timeout=(5, 30),
        stream=True,
    ) as response:
        response.raise_for_status()
        parts, size = [], 0
        for chunk in response.iter_content(65536):
            size += len(chunk)
            if size > 2_000_000:
                raise ValueError("Reference exceeds 2 MB")
            parts.append(chunk)
    return b"".join(parts)


def save_new(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != raw:
            raise ValueError("Refusing to overwrite an existing reference version")
        return
    with path.open("xb") as stream:
        stream.write(raw)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    hla = sub.add_parser("hla")
    hla.add_argument("--version", default="3.66.0")
    hla.add_argument(
        "--directory", type=Path, default=Path(".local/reference-data/hla")
    )
    roads = sub.add_parser("roads")
    roads.add_argument(
        "--output",
        type=Path,
        required=True,
        help="New reviewed snapshot directory; does not modify installed sources",
    )
    args = parser.parse_args()
    if args.command == "hla":
        spec = next((r for r in catalogues() if r["version"] == args.version), None)
        if not spec:
            parser.error("Unsupported reference release")
        raw = download(spec["url"])
        if hashlib.sha256(raw).hexdigest() != spec["sha256"]:
            raise ValueError("Upstream content differs from the reviewed digest")
        target = args.directory / spec["version"] / spec["filename"]
        save_new(target, raw)
        print(
            json.dumps(
                {
                    "version": spec["version"],
                    "sha256": spec["sha256"],
                    "bytes": len(raw),
                    "path": str(target),
                }
            )
        )
    else:
        if args.output.exists():
            parser.error(
                "Use a new output directory; historical snapshots are retained"
            )
        spec = manifest()
        now = datetime.now(timezone.utc)
        spec.update(
            id="NL-OSRM-" + now.strftime("%Y%m%dT%H%M%SZ"),
            retrieved_at=now.isoformat(),
            valid_until=(now + timedelta(days=30)).isoformat(),
        )
        for segment in spec["segments"]:
            raw = download(segment["url"])
            response = json.loads(raw)
            if response.get("code") != "Ok":
                raise ValueError("Provider did not return a route")
            segment.update(
                sha256=hashlib.sha256(raw).hexdigest(),
                data_version=response.get("data_version"),
            )
            save_new(args.output / segment["file"], raw)
            time.sleep(1.1)  # Demo policy: less than one request per second.
        spec["data_age"] = (
            "PROVIDER_DATES_RECORDED_PER_SEGMENT"
            if all(s["data_version"] for s in spec["segments"])
            else "UNKNOWN_PROVIDER_DID_NOT_REPORT_DATE"
        )
        save_new(
            args.output / "manifest.json",
            (json.dumps(spec, ensure_ascii=False, indent=2) + "\n").encode(),
        )
        print(
            json.dumps(
                {
                    "snapshot": spec["id"],
                    "path": str(args.output),
                    "requires_review_before_install": True,
                }
            )
        )


if __name__ == "__main__":
    main()
