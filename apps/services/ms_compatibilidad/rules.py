"""Immutable profiles, separately recorded approval and explicit operational scope."""

from datetime import datetime, timezone
from typing import Annotated, Literal
from uuid import uuid4

from flask import current_app, g
from pydantic import Field
from redhouse.api import atomic, endpoint
from redhouse.client import call
from redhouse.codec import plain
from redhouse.db import get, insert, transaction
from redhouse.errors import APIError
from redhouse.events import emit
from redhouse.extension_contracts import schema
from redhouse.models import ID, Confirm, Model, Text, utc_date
from redhouse.security import own


class CompletenessPolicy(Model):
    version: Literal["COMPLETENESS-2.0"] = "COMPLETENESS-2.0"
    max_age_seconds: Annotated[int, Field(ge=1, le=31536000)] | None = None
    contradictions: Literal["REVIEW"] = "REVIEW"
    require_document: bool = False
    require_hla_catalogue: bool = False
    ranking_order: Literal["URGENCY_WAIT_EXPIRY_TIME_DISTANCE_ID"] | None = None
    urgency_scale: Literal["CAPTURED_1_3_SYNTHETIC"] | None = None


class RuleAction(Confirm):
    sequence: Annotated[int, Field(ge=1)]
    state: Literal["IN_REVIEW", "APPROVED", "RETIRED"]
    competency_reference: Text | None = None
    document_id: ID | None = None


class RecordedAction(Model):
    id: ID
    profile_id: ID
    tenant_id: ID
    actor_id: ID
    sequence: int
    state: Literal["IN_REVIEW", "APPROVED", "RETIRED"]
    reason: Text
    competency_reference: Text | None
    evidence: dict | None
    created_at: Text


class Governance(Model):
    profile_id: ID
    state: Literal["DRAFT", "IN_REVIEW", "APPROVED", "RETIRED"]
    actions: list[RecordedAction]
    invalid_reasons: list[str]
    clinical_enabled: bool
    scope: Literal["ACADEMIC", "CLINICAL"]


def state(conn, profile):
    actions = conn.execute(
        "SELECT * FROM rule_actions WHERE profile_id=%s ORDER BY sequence",
        (profile["id"],),
    ).fetchall()
    status = actions[-1]["state"] if actions else profile["rule_status"]
    return status, plain(actions)


def validity(conn, profile, now=None, *, governance=None):
    now = now or datetime.now(timezone.utc)
    status, _ = state(conn, profile) if governance is None else governance
    from .public_sources import reference_reasons

    reasons = reference_reasons(profile.get("reference_snapshot", []), now)
    if profile["effective_at"] > now:
        reasons.append("PROFILE_FUTURE")
    if profile.get("valid_until") and now >= profile["valid_until"]:
        reasons.append("PROFILE_EXPIRED")
    if status == "RETIRED":
        reasons.append("PROFILE_RETIRED")
    if conn.execute(
        "SELECT 1 FROM lab_profiles WHERE supersedes=%s AND effective_at<=%s",
        (profile["id"], now),
    ).fetchone():
        reasons.append("PROFILE_SUPERSEDED")
    return reasons


def clinically_enabled(profile, actions, reasons):
    if (
        profile["synthetic"]
        or reasons
        or not actions
        or actions[-1]["state"] != "APPROVED"
    ):
        return False
    approval = actions[-1]
    authority = current_app.config["CLINICAL_APPROVERS"].get(approval["actor_id"])
    return bool(
        authority
        and authority.get("tenant_id") == str(profile["tenant_id"])
        and authority.get("reference") == approval["competency_reference"]
        and profile["component"] in authority.get("components", [])
        and utc_date(authority["valid_until"]) > datetime.now(timezone.utc)
    )


def install(app):
    @endpoint(
        app,
        "/api/v1/laboratory/profiles/<identifier>/governance",
        roles=("MEDICAL",),
        result=schema(Governance),
    )
    def rule_governance(identifier):
        with transaction() as conn:
            profile = get(conn, "lab_profiles", identifier)
            own(profile["tenant_id"])
            status, actions = state(conn, profile)
            reasons = validity(conn, profile)
            return {
                "profile_id": identifier,
                "state": status,
                "actions": actions,
                "invalid_reasons": reasons,
                "clinical_enabled": clinically_enabled(profile, actions, reasons),
                "scope": current_app.config["OPERATION_SCOPE"],
            }

    @endpoint(
        app,
        "/api/v1/laboratory/profiles/<identifier>/actions",
        "POST",
        model=RuleAction,
        roles=("MEDICAL",),
        status=201,
        result=schema(RecordedAction),
    )
    def rule_transition(identifier, data):
        evidence = None
        if data["state"] == "APPROVED":
            # Only an administratively provisioned, scoped competency can authorize.
            authority = current_app.config["CLINICAL_APPROVERS"].get(g.actor["id"])
            if (
                not authority
                or authority.get("tenant_id") != g.actor["tenant_id"]
                or authority.get("reference") != data["competency_reference"]
                or utc_date(authority["valid_until"]) <= datetime.now(timezone.utc)
            ):
                raise APIError(
                    "competency_required",
                    "No existe acreditación competente vigente configurada para este actor.",
                    403,
                )
            if not data["document_id"]:
                raise APIError(
                    "evidence_required",
                    "Documento privado de aprobación requerido.",
                    422,
                )
            evidence = call(
                "documentos",
                "GET",
                "/api/v1/documents/" + data["document_id"] + "/verified",
            )
            if (
                evidence["subject_kind"] != "RULE"
                or evidence["subject_id"] != identifier
            ):
                raise APIError("evidence_mismatch", "Documento de otro perfil.", 409)

        def work(conn):
            conn.execute(
                "SELECT pg_advisory_xact_lock(hashtextextended(%s,0))",
                ("profile:" + identifier,),
            )
            profile = get(conn, "lab_profiles", identifier)
            own(profile["tenant_id"])
            status, actions = state(conn, profile)
            if data["sequence"] != len(actions) + 1:
                raise APIError("stale_version", "Secuencia de decisión obsoleta.", 412)
            if (
                data["state"]
                not in {
                    "DRAFT": ("IN_REVIEW", "RETIRED"),
                    "IN_REVIEW": ("APPROVED", "RETIRED"),
                    "APPROVED": ("RETIRED",),
                    "RETIRED": (),
                }[status]
            ):
                raise APIError(
                    "invalid_transition", "Transición de regla no permitida.", 409
                )
            if data["state"] == "APPROVED":
                if profile["synthetic"] or str(profile["author_id"]) == g.actor["id"]:
                    raise APIError(
                        "segregation_required",
                        "No se aprueba perfil propio ni sintético como clínico.",
                        409,
                    )
                if profile["component"] not in authority.get("components", []):
                    raise APIError(
                        "competency_scope", "Competencia no cubre este producto.", 403
                    )
                if validity(conn, profile):
                    raise APIError("invalid_profile", "Perfil fuera de vigencia.", 409)
                if (
                    not profile["policy"]["require_document"]
                    or not profile["valid_until"]
                ):
                    raise APIError(
                        "policy_required",
                        "Perfil clínico requiere documentos y fin de vigencia.",
                        409,
                    )
            row = insert(
                conn,
                "rule_actions",
                {
                    "id": str(uuid4()),
                    "profile_id": identifier,
                    "tenant_id": g.actor["tenant_id"],
                    "actor_id": g.actor["id"],
                    "sequence": data["sequence"],
                    "state": data["state"],
                    "reason": data["reason"],
                    "competency_reference": data["competency_reference"],
                    "evidence": evidence,
                },
            )
            emit(conn, "RULE_GOVERNANCE_RECORDED", identifier, g.actor["tenant_id"])
            return row

        return atomic("rule_transition:" + identifier, data, work)
