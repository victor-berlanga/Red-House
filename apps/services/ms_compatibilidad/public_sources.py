"""Cited documentary constraints, separate from institutional approval."""

import hashlib
import json
from datetime import datetime, timezone

from pydantic import Field
from redhouse.api import endpoint
from redhouse.errors import APIError
from redhouse.extension_contracts import schema
from redhouse.models import Model, utc_date

from .reference_catalogue import DATA, catalogue_path, catalogues


def rules():
    return json.loads((DATA / "public_rules_v1.json").read_text())


def reference_reasons(snapshots, now):
    reasons = []
    for ref in snapshots:
        if now < utc_date(ref["valid_from"]):
            reasons.append("REFERENCE_FUTURE:" + ref["id"])
        if ref["valid_until"] and now >= utc_date(ref["valid_until"]):
            reasons.append("REFERENCE_EXPIRED:" + ref["id"])
    return reasons


def resolve(ids, kind):
    known = {r["id"]: r for r in rules()}
    if len(set(ids)) != len(ids) or any(i not in known for i in ids):
        raise APIError("unknown_reference", "Referencia desconocida o repetida.", 422)
    refs = [known[i] for i in ids]
    if any(r["kind"] not in (kind, "REFERENCE") for r in refs):
        raise APIError(
            "reference_scope", "La fuente no aplica a este tipo de recurso.", 422
        )
    return [
        dict(
            r, sha256=hashlib.sha256(json.dumps(r, sort_keys=True).encode()).hexdigest()
        )
        for r in refs
    ]


class Sources(Model):
    rules: list[dict] = Field(default_factory=list)
    catalogues: list[dict] = Field(default_factory=list)
    clinical_approval: bool = False


def install(app):
    @endpoint(
        app,
        "/api/v1/laboratory/reference-sources",
        roles=("MEDICAL", "OPERATOR"),
        result=schema(Sources),
    )
    def reference_sources():
        now = datetime.now(timezone.utc)
        releases = []
        for spec in catalogues():
            try:
                valid = (
                    hashlib.sha256(
                        catalogue_path(spec["version"]).read_bytes()
                    ).hexdigest()
                    == spec["sha256"]
                )
            except OSError:
                valid = False
            releases.append(dict(spec, available=valid))
        return {
            "rules": [
                dict(r, invalid_reasons=reference_reasons([r], now)) for r in rules()
            ],
            "catalogues": releases,
            "clinical_approval": False,
        }
