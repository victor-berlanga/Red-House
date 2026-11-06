"""Version-pinned public reference data. Membership is not a medical verdict."""

import csv
import hashlib
import json
import os
from functools import lru_cache
from pathlib import Path

from flask import current_app
from redhouse.errors import APIError

DATA = Path(__file__).resolve().parents[1] / "redhouse/reference_data"


def catalogues():
    return json.loads((DATA / "hla_catalogues.json").read_text())


def catalogue_path(version):
    root = current_app.config.get("HLA_REFERENCE_DIR") or os.environ.get(
        "HLA_REFERENCE_DIR", str(Path.cwd() / ".local/reference-data/hla")
    )
    return Path(root) / version / "Allelelist.txt"


@lru_cache(maxsize=4)
def index(content):
    rows = csv.DictReader(
        x for x in content.decode().splitlines() if not x.startswith("#")
    )
    exact, prefixes = {}, {}
    for row in rows:
        allele = row["Allele"]
        if allele in exact:
            raise ValueError("Duplicated allele in reference source")
        exact[allele] = row["AlleleID"]
        suffix = allele[-1] if allele[-1].isalpha() else ""
        fields = allele.rstrip("NLSCAQ").split(":")
        for size in range(2, len(fields)):
            key = ":".join(fields[:size]) + suffix
            prefixes[key] = prefixes.get(key, 0) + 1
    return exact, prefixes


def check(typing):
    if not typing or not typing.get("catalogue_version"):
        return {"status": "NOT_CHECKED", "clinical_approval": False, "entries": []}
    spec = next(
        (s for s in catalogues() if s["version"] == typing["catalogue_version"]), None
    )
    if not spec:
        raise APIError(
            "unknown_catalogue", "Versión de catálogo HLA no soportada.", 422
        )
    try:
        content = catalogue_path(spec["version"]).read_bytes()
        if hashlib.sha256(content).hexdigest() != spec["sha256"]:
            raise ValueError("Reference digest mismatch")
        exact, prefixes = index(content)
    except (OSError, ValueError, KeyError, UnicodeError):
        raise APIError(
            "reference_unavailable",
            "Catálogo HLA ausente o con integridad incorrecta; instale la versión fijada.",
            503,
        ) from None
    entries = []
    for locus in typing["loci"]:
        for allele in locus["alleles"]:
            status = (
                "EXACT"
                if allele in exact
                else "LOW_RESOLUTION"
                if allele in prefixes
                else "NOT_FOUND"
            )
            entries.append(
                {
                    "value": allele,
                    "status": status,
                    "allele_id": exact.get(allele),
                    "matching_entries": 1
                    if allele in exact
                    else prefixes.get(allele, 0),
                }
            )
        entries.extend(
            {
                "value": group,
                "status": "GROUP_NOT_ALLELE",
                "allele_id": None,
                "matching_entries": 0,
            }
            for group in locus.get("groups", [])
        )
    return {
        "status": "CHECKED",
        "catalogue": spec,
        "clinical_approval": False,
        "all_alleles_recognized": bool(entries)
        and all(e["status"] in ("EXACT", "LOW_RESOLUTION") for e in entries),
        "entries": entries,
        "limitation": "Coincidencia de referencia a la resolución declarada; no demuestra compatibilidad, existencia en otra edición ni aptitud clínica.",
    }
