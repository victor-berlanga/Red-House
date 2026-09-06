from uuid import uuid4

from flask import g, has_request_context

from .common import insert


def record(conn, actor, action, entity, reference, reason, *, institution_id=None,
           region_name=None, outcome="SUCCESS", before=None, after=None):
    event = insert(conn, "audit_event", {
        "actor_id": actor.account_id if actor else None,
        "institution_id": institution_id or (actor.institution_id if actor else None),
        "region_name": region_name or (actor.region_name if actor else None),
        "action": action, "entity_type": entity, "entity_reference": str(reference),
        "outcome": outcome, "reason": reason[:240],
        "correlation_id": g.correlation_id if has_request_context() else uuid4(),
    }, "event_id")
    # Allowlisted by each service. No password, token, login email or request body.
    for field in sorted(set(before or {}) | set(after or {})):
        old, new = (before or {}).get(field), (after or {}).get(field)
        if old != new:
            insert(conn, "audit_change", {
                "event_id": event["event_id"], "field_name": field,
                "previous_value": str(old)[:240] if old is not None else None,
                "new_value": str(new)[:240] if new is not None else None,
            }, "event_id")
    return event
