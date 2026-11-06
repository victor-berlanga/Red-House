"""Current validity is separate from immutable evaluation snapshots."""

import hashlib
import json
from datetime import datetime, timedelta, timezone

from redhouse.client import call
from redhouse.codec import plain
from redhouse.db import get
from redhouse.models import utc_date

from .laboratory import completeness
from .rules import validity


def recipient_laboratory(conn, recipient_id, tenant_id):
    rows = conn.execute(
        "SELECT r.*,s.profile_id,s.status AS sample_status,s.collected_at FROM lab_results r JOIN lab_samples s ON s.id=r.sample_id WHERE s.recipient_id=%s AND s.tenant_id=%s ORDER BY r.id",
        (recipient_id, tenant_id),
    ).fetchall()
    profiles = conn.execute(
        "SELECT DISTINCT p.* FROM lab_profiles p JOIN lab_samples s ON s.profile_id=p.id WHERE s.recipient_id=%s AND s.tenant_id=%s ORDER BY p.id",
        (recipient_id, tenant_id),
    ).fetchall()
    actions = conn.execute(
        "SELECT a.* FROM rule_actions a JOIN lab_samples s ON s.profile_id=a.profile_id WHERE s.recipient_id=%s AND s.tenant_id=%s ORDER BY a.id",
        (recipient_id, tenant_id),
    ).fetchall()
    return {
        "fingerprint": hashlib.sha256(
            json.dumps(plain([rows, profiles, actions]), sort_keys=True).encode()
        ).hexdigest(),
        "profile_ids": [str(p["id"]) for p in profiles],
        "result_ids": [str(r["id"]) for r in rows],
        "completions": [
            completeness(
                conn,
                recipient_id,
                str(p["id"]),
                tenant_id,
                subject_field="recipient_id",
            )
            for p in profiles
        ],
    }


def current(conn, evaluation, only_resource=None):
    req = call(
        "receptores", "GET", "/internal/v1/requests/" + str(evaluation["request_id"])
    )
    reasons = []
    if req["version"] != evaluation["request_version"] or req["status"] not in (
        "OPEN",
        "IN_PROGRESS",
    ):
        reasons.append("REQUEST_CHANGED")
    if (
        req["recipient"]["version"] != evaluation["recipient_version"]
        or req["recipient"]["status"] != "ACTIVE"
    ):
        reasons.append("RECIPIENT_CHANGED")
    captured = evaluation["snapshot"].get("recipient_laboratory")
    recipient_context = recipient_laboratory(
        conn, req["recipient_id"], str(evaluation["tenant_id"])
    )
    if captured is None or captured != recipient_context:
        reasons.append("RECIPIENT_LABORATORY_CHANGED")
    if any(not check["complete"] for check in recipient_context["completions"]):
        reasons.append("RECIPIENT_LABORATORY_INCOMPLETE")
    profile = evaluation["snapshot"].get("execution_profile")
    if profile:
        reasons.extend(validity(conn, get(conn, "lab_profiles", profile["id"])))
        from .rules import state

        if state(conn, get(conn, "lab_profiles", profile["id"]))[1] != evaluation[
            "snapshot"
        ].get("profile_actions", []):
            reasons.append("PROFILE_GOVERNANCE_CHANGED")
    candidates = []
    resources = {
        r["id"]: r
        for r in call("inventario", "GET", "/internal/v1/available-resources")["items"]
    }
    routes = {
        r["id"]: r
        for r in call("priorizacion_geografia", "GET", "/internal/v1/route-options")[
            "items"
        ]
    }
    for candidate in evaluation["candidates"]:
        if only_resource and candidate["resource_id"] != only_resource:
            continue
        context = resources.get(candidate["resource_id"])
        if context is None:
            candidates.append(
                {
                    "resource_id": candidate["resource_id"],
                    "current": False,
                    "reasons": sorted(
                        set(reasons + ["RESOURCE_UNAVAILABLE_OR_EXPIRED"])
                    ),
                }
            )
            continue
        context = dict(context, profile_id=context.get("lab_profile_id"))
        changes = list(reasons)
        if (
            context["version"] != candidate["resource_version"]
            or context["status"] != "AVAILABLE"
        ):
            changes.append("RESOURCE_CHANGED")
        lab = (
            completeness(
                conn,
                candidate["resource_id"],
                context["profile_id"],
                context["tenant_id"],
            )
            if context["profile_id"]
            else None
        )
        if "laboratory" not in candidate or lab != candidate["laboratory"]:
            changes.append("LABORATORY_CHANGED")
        if lab and not lab["complete"]:
            changes.append("LABORATORY_INCOMPLETE")
        route = routes.get(candidate["route_id"])
        if route is None:
            candidates.append(
                {
                    "resource_id": candidate["resource_id"],
                    "current": False,
                    "reasons": sorted(set(changes + ["ROUTE_UNAVAILABLE"])),
                }
            )
            continue
        if route["version"] != candidate["route_version"]:
            changes.append("ROUTE_CHANGED")
        if utc_date(context["expires_at"]) <= datetime.now(timezone.utc) + timedelta(
            minutes=route["travel_minutes"]
        ):
            changes.append("EXPIRED_OR_INSUFFICIENT_TIME")
        candidates.append(
            {
                "resource_id": candidate["resource_id"],
                "current": not changes,
                "reasons": sorted(set(changes)),
            }
        )
    return {
        "current": not reasons and all(x["current"] for x in candidates),
        "reasons": sorted(set(reasons)),
        "candidates": candidates,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }
