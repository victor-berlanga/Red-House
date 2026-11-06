"""Registro/completitud de laboratorio. No interpreta HLA ni declara aptitud clínica."""

import hashlib
import json
from datetime import datetime, timezone
from typing import Annotated, Literal
from uuid import uuid4

from flask import g
from pydantic import Field, model_validator
from redhouse.api import atomic, endpoint
from redhouse.client import call
from redhouse.codec import plain
from redhouse.db import get, insert, transaction, update
from redhouse.errors import APIError
from redhouse.events import emit
from redhouse.extension_contracts import install_reads, schema, version
from redhouse.models import ID, Confirm, Kind, Model, Text, utc_date
from redhouse.security import own

from .hla import Typing
from .public_sources import resolve as resolve_references
from .reference_catalogue import check as check_catalogue
from .rules import CompletenessPolicy, clinically_enabled, state, validity

ROLES = ("MEDICAL", "OPERATOR")
Code = Annotated[str, Field(min_length=1, max_length=60, pattern=r"^[A-Z0-9_.-]+$")]


class ProfileCreate(Model):
    name: Text
    kind: Kind
    component: Text
    version: Annotated[int, Field(ge=1)]
    required_tests: Annotated[list[Code], Field(min_length=1, max_length=40)]
    source: Text
    evidence_rules: Annotated[list[Text], Field(max_length=20)] = Field(
        default_factory=list
    )
    synthetic: bool
    effective_at: Text
    supersedes: ID | None = None
    valid_until: Text | None = None
    policy: CompletenessPolicy = Field(default_factory=CompletenessPolicy)
    purpose: Text = "Completitud académica, sin aplicación clínica"
    rule_status: Literal["DRAFT", "IN_REVIEW", "RETIRED"] = "DRAFT"
    required_loci: Annotated[list[Code], Field(max_length=80)] = Field(
        default_factory=list
    )
    clinical_enabled: Literal[False] = False

    @model_validator(mode="after")
    def unique_codes(self):
        if len(set(self.required_tests)) != len(self.required_tests):
            raise ValueError("Pruebas repetidas")
        return self


class Profile(ProfileCreate):
    reference_snapshot: list[dict] = Field(default_factory=list)
    id: ID
    tenant_id: ID
    author_id: ID
    created_at: Text


class SampleCreate(Model):
    resource_id: ID | None = None
    recipient_id: ID | None = None
    donation_id: ID | None = None
    profile_id: ID
    request_id: ID | None = None
    identifier: Text
    collected_at: Text

    @model_validator(mode="after")
    def one_subject(self):
        if (
            sum(
                x is not None
                for x in (self.resource_id, self.recipient_id, self.donation_id)
            )
            != 1
        ):
            raise ValueError("Un solo sujeto por muestra")
        return self


class Sample(SampleCreate):
    id: ID
    tenant_id: ID
    received_at: Text | None
    status: str
    version: int
    author_id: ID
    created_at: Text


class SampleReceive(Confirm):
    version: Annotated[int, Field(ge=1)]
    decision: Literal["RECEIVED", "REJECTED"]


class Crossmatch(Model):
    donor_sample_id: ID
    recipient_sample_id: ID
    request_id: ID
    technique: Text
    reported_interpretation: Literal["POSITIVE", "NEGATIVE", "INDETERMINATE", "PENDING"]


class ResultCreate(Model):
    sample_id: ID
    test_code: Code
    value: Annotated[str, Field(min_length=1, max_length=2000)] | None = None
    result_state: Literal[
        "NOT_PERFORMED", "PENDING", "INDETERMINATE", "REPORTED", "CORRECTED"
    ] = "REPORTED"
    hla: Typing | None = None
    crossmatch: Crossmatch | None = None
    issued_at: Text | None = None
    document_id: ID | None = None

    @model_validator(mode="after")
    def documented_state(self):
        if (
            self.test_code == "CROSSMATCH"
            and self.result_state in ("REPORTED", "CORRECTED", "INDETERMINATE")
            and not self.crossmatch
        ):
            raise ValueError(
                "Prueba cruzada informada exige sujetos, muestras e interpretación documentada"
            )
        if self.result_state in ("REPORTED", "CORRECTED") and not (
            self.value or self.hla or self.crossmatch
        ):
            raise ValueError("Resultado informado requiere valor o tipificación")
        if self.result_state in ("PENDING", "NOT_PERFORMED") and (
            self.value or self.hla
        ):
            raise ValueError("Pendiente/no realizado no contiene valor")
        if self.crossmatch:
            interpretation = self.crossmatch.reported_interpretation
            if self.test_code != "CROSSMATCH":
                raise ValueError(
                    "Contrato de prueba cruzada requiere código CROSSMATCH"
                )
            if (
                self.result_state == "INDETERMINATE"
                and interpretation != "INDETERMINATE"
            ):
                raise ValueError(
                    "Estado indeterminado requiere interpretación indeterminada"
                )
            if (
                self.result_state in ("PENDING", "NOT_PERFORMED")
                and interpretation != "PENDING"
            ):
                raise ValueError(
                    "Prueba pendiente/no realizada no contiene interpretación informada"
                )
            if self.result_state in ("REPORTED", "CORRECTED") and (
                interpretation == "PENDING" or not self.issued_at
            ):
                raise ValueError(
                    "Prueba cruzada informada requiere emisión e interpretación documentada"
                )
        if self.hla and not self.issued_at:
            raise ValueError("HLA requiere fecha de emisión")
        if self.result_state == "CORRECTED" and not self.supersedes:
            raise ValueError("Corrección requiere antecedente")
        return self

    unit: Text | None = None
    method: Text
    laboratory: Text
    reference: Text
    measured_at: Text
    supersedes: ID | None = None


class Result(ResultCreate):
    id: ID
    tenant_id: ID
    author_id: ID
    version: int
    status: str
    created_at: Text
    document_snapshot: dict | None = None
    catalogue_check: dict | None = None
    # Historical declarations stay readable even if newer input validators reject them.
    hla: dict | None = None


class ResultReview(Confirm):
    version: Annotated[int, Field(ge=1)]
    decision: Literal["AUTHORIZED", "REJECTED"]


class CompletenessInput(Model):
    profile_id: ID
    tenant_id: ID


class Completeness(Model):
    complete: bool
    missing: list[str]
    profile_id: ID
    profile_version: int
    fingerprint: str
    result_ids: list[ID]
    synthetic: bool
    clinical_approval: Literal[False] = False
    clinical_enabled: bool = False
    conflicts: list[str] = Field(default_factory=list)
    policy_version: str = "COMPLETENESS-2.0"
    satisfied_tests: list[str] = Field(default_factory=list)
    satisfied_loci: list[str] = Field(default_factory=list)


def completeness(
    conn, resource_id, profile_id, tenant_id, *, subject_field="resource_id", now=None
):
    if subject_field not in ("resource_id", "recipient_id", "donation_id"):
        raise ValueError("Unsupported subject")
    now = now or datetime.now(timezone.utc)
    profile = get(conn, "lab_profiles", profile_id)
    if str(profile["tenant_id"]) != tenant_id:
        raise APIError("forbidden", "Perfil ajeno.", 403)
    results = conn.execute(
        "SELECT DISTINCT ON(r.test_code) r.* FROM lab_results r JOIN lab_samples s ON s.id=r.sample_id "
        f"WHERE s.{subject_field}=%s AND s.profile_id=%s AND s.tenant_id=%s AND s.status='RECEIVED' "
        "ORDER BY r.test_code,r.created_at DESC,r.version DESC,r.id",
        (resource_id, profile_id, tenant_id),
    ).fetchall()
    by_code = {r["test_code"]: r for r in results}
    policy = profile["policy"]
    missing = [
        code
        for code in profile["required_tests"]
        if code not in by_code
        or by_code[code]["status"] != "AUTHORIZED"
        or by_code[code]["result_state"] not in ("REPORTED", "CORRECTED")
    ]
    if "HLA" in profile["required_tests"]:
        loci = (by_code.get("HLA", {}).get("hla") or {}).get("loci", [])
        if not loci or any(
            l.get("ambiguous") or l.get("partial") or not l.get("alleles") for l in loci
        ):
            missing.append("HLA:UNRESOLVED_DECLARATION")
    hla_loci = {
        locus["locus"]
        for r in results
        if r["status"] == "AUTHORIZED"
        and r["result_state"] in ("REPORTED", "CORRECTED")
        and (
            not policy.get("require_hla_catalogue")
            or (r.get("catalogue_check") or {}).get("all_alleles_recognized")
        )
        for locus in (r.get("hla") or {}).get("loci", [])
        if not locus["ambiguous"]
        and not locus.get("partial", False)
        and locus.get("alleles")
    }
    missing.extend(
        "HLA:" + locus for locus in profile["required_loci"] if locus not in hla_loci
    )
    governance = state(conn, profile)
    missing.extend(validity(conn, profile, now, governance=governance))
    hla_results = [r for r in results if r.get("hla")]
    if policy.get("require_hla_catalogue") and (
        not hla_results
        or any(
            not (r.get("catalogue_check") or {}).get("all_alleles_recognized")
            for r in hla_results
        )
    ):
        missing.append("HLA:CATALOGUE_UNVERIFIED")
    conflicts = []
    for r in results:
        if (
            policy["max_age_seconds"] is not None
            and (now - r["measured_at"]).total_seconds() > policy["max_age_seconds"]
        ):
            missing.append("STALE:" + r["test_code"])
        if policy["require_document"] and not r.get("document_snapshot"):
            missing.append("DOCUMENT:" + r["test_code"])
    # Two unsuperseded, authorized measurements of the same code on separate samples
    # need review if their declared values differ. No clinical interpretation.
    active = conn.execute(
        f"SELECT r.* FROM lab_results r JOIN lab_samples s ON s.id=r.sample_id WHERE s.{subject_field}=%s AND s.profile_id=%s AND s.tenant_id=%s AND r.status='AUTHORIZED' AND NOT EXISTS(SELECT 1 FROM lab_results n WHERE n.supersedes=r.id)",
        (resource_id, profile_id, tenant_id),
    ).fetchall()
    for code in profile["required_tests"]:
        values = {
            json.dumps(
                plain([r["value"], r.get("hla"), r.get("crossmatch")]), sort_keys=True
            )
            for r in active
            if r["test_code"] == code and r["result_state"] in ("REPORTED", "CORRECTED")
        }
        if len(values) > 1:
            conflicts.append("CONTRADICTORY:" + code)
    missing.extend(conflicts)
    _status, actions = governance
    return {
        "complete": not missing,
        "missing": missing,
        "profile_id": str(profile["id"]),
        "profile_version": profile["version"],
        "fingerprint": hashlib.sha256(
            json.dumps(
                plain([results, active, profile, actions]), sort_keys=True
            ).encode()
        ).hexdigest(),
        "result_ids": [str(r["id"]) for r in results],
        "synthetic": profile["synthetic"],
        "clinical_approval": False,
        "clinical_enabled": clinically_enabled(profile, actions, missing),
        "conflicts": conflicts,
        "policy_version": policy["version"],
        "satisfied_tests": sorted(
            code
            for code, r in by_code.items()
            if r["status"] == "AUTHORIZED"
            and r["result_state"] in ("REPORTED", "CORRECTED")
            and code not in missing
            and not any(
                reason in missing
                for reason in (
                    "STALE:" + code,
                    "DOCUMENT:" + code,
                    "CONTRADICTORY:" + code,
                )
            )
            and not (
                code == "HLA" and any(reason.startswith("HLA:") for reason in missing)
            )
        ),
        "satisfied_loci": sorted(hla_loci),
    }


def install(app):
    from redhouse.trace_contract import TraceEvent

    class History(Model):
        events: list[TraceEvent]

    @endpoint(
        app,
        "/api/v1/laboratory/samples/<identifier>/completeness",
        roles=ROLES,
        result=schema(Completeness),
    )
    def sample_completeness(identifier):
        with transaction() as conn:
            sample = get(conn, "lab_samples", identifier)
            own(sample["tenant_id"])
            subject = next(
                name
                for name in ("resource_id", "recipient_id", "donation_id")
                if sample[name]
            )
            return completeness(
                conn,
                str(sample[subject]),
                str(sample["profile_id"]),
                str(sample["tenant_id"]),
                subject_field=subject,
            )

    @endpoint(
        app,
        "/api/v1/laboratory/resources/<identifier>/history",
        roles=("MEDICAL",),
        result=schema(History),
    )
    def lab_history(identifier):
        resource = call("inventario", "GET", "/api/v1/resources/" + identifier)
        own(resource["current_institution_id"])
        with transaction() as conn:
            rows = conn.execute(
                "SELECT r.id,'compatibilidad' AS source,'RESULT_'||r.status AS action,r.created_at AS occurred_at "
                "FROM lab_results r JOIN lab_samples s ON s.id=r.sample_id WHERE s.resource_id=%s AND s.tenant_id=%s ORDER BY r.created_at,r.id LIMIT 2000",
                (identifier, g.actor["tenant_id"]),
            ).fetchall()
            return {"events": rows}

    install_reads(app, "/api/v1/laboratory/profiles", "lab_profiles", Profile, ROLES)
    install_reads(
        app,
        "/api/v1/laboratory/samples",
        "lab_samples",
        Sample,
        ROLES,
        {
            "q": ("identifier",),
            "status": ("status", ("REQUESTED", "RECEIVED", "REJECTED")),
        },
    )
    install_reads(
        app,
        "/api/v1/laboratory/results",
        "lab_results",
        Result,
        ROLES,
        {
            "sample_id": ("sample_id", ()),
            "status": ("status", ("CAPTURED", "AUTHORIZED", "REJECTED")),
        },
    )

    @endpoint(
        app,
        "/api/v1/laboratory/profiles",
        "POST",
        model=ProfileCreate,
        roles=("MEDICAL",),
        status=201,
        result=schema(Profile),
    )
    def lab_profile_create(data):
        effective = utc_date(data["effective_at"], "effective_at")
        if data["rule_status"] != "DRAFT":
            raise APIError(
                "transition_required",
                "Un perfil inicia en borrador; usa acciones auditables.",
                422,
            )
        if data["valid_until"] and utc_date(data["valid_until"]) <= effective:
            raise APIError(
                "validation", "Fin de vigencia debe ser posterior al inicio.", 422
            )

        def work(conn):
            if data["supersedes"]:
                conn.execute(
                    "SELECT pg_advisory_xact_lock(hashtextextended(%s,0))",
                    ("profile:" + data["supersedes"],),
                )
                old = get(conn, "lab_profiles", data["supersedes"])
                own(old["tenant_id"])
                if (old["kind"], old["component"]) != (data["kind"], data["component"]):
                    raise APIError(
                        "conflict", "La versión conserva el recurso del perfil.", 409
                    )
                if effective < old["effective_at"]:
                    raise APIError(
                        "validation", "Vigencia anterior al perfil sustituido.", 422
                    )
                if conn.execute(
                    "SELECT 1 FROM lab_profiles WHERE supersedes=%s",
                    (data["supersedes"],),
                ).fetchone():
                    raise APIError("stale_version", "Perfil ya sustituido.", 412)
                if data["version"] != old["version"] + 1:
                    raise APIError(
                        "stale_version", "Versión consecutiva requerida.", 412
                    )
            elif data["version"] != 1:
                raise APIError("validation", "La primera versión es 1.", 422)
            row = insert(
                conn,
                "lab_profiles",
                dict(
                    data,
                    id=str(uuid4()),
                    tenant_id=g.actor["tenant_id"],
                    author_id=g.actor["id"],
                    effective_at=effective,
                    reference_snapshot=resolve_references(
                        data["evidence_rules"], data["kind"]
                    ),
                ),
            )
            emit(conn, "LAB_PROFILE_RECORDED", row["id"], row["tenant_id"])
            return row

        return atomic("lab_profile_create", data, work)

    @endpoint(
        app,
        "/api/v1/laboratory/samples",
        "POST",
        model=SampleCreate,
        roles=ROLES,
        status=201,
        result=schema(Sample),
    )
    def lab_sample_create(data):
        for field, service, route in (
            ("resource_id", "inventario", "resources"),
            ("recipient_id", "receptores", "recipients"),
            ("donation_id", "donantes", "donations"),
        ):
            if data[field]:
                subject = call(service, "GET", f"/api/v1/{route}/" + data[field])
                own(subject.get("current_institution_id", subject["tenant_id"]))
        req = None
        if data["request_id"]:
            req = call(
                "receptores", "GET", "/internal/v1/requests/" + data["request_id"]
            )
            own(req["tenant_id"])
            if data["recipient_id"] and req["recipient_id"] != data["recipient_id"]:
                raise APIError("subject_mismatch", "Solicitud de otro receptor.", 409)
        collected = utc_date(data["collected_at"], "collected_at")
        if collected > datetime.now(timezone.utc):
            raise APIError("validation", "Captura futura.", 422)

        def work(conn):
            profile = get(conn, "lab_profiles", data["profile_id"])
            own(profile["tenant_id"])
            if (
                (subject.get("kind") and subject["kind"] != profile["kind"])
                or (
                    subject.get("organ_type", subject.get("component"))
                    and subject.get("organ_type", subject.get("component"))
                    != profile["component"]
                )
                or validity(conn, profile)
                or (
                    req
                    and (req["kind"], req["component"])
                    != (profile["kind"], profile["component"])
                )
            ):
                raise APIError(
                    "profile_mismatch", "Perfil de otro tipo de recurso.", 409
                )
            row = insert(
                conn,
                "lab_samples",
                dict(
                    data,
                    id=str(uuid4()),
                    tenant_id=g.actor["tenant_id"],
                    author_id=g.actor["id"],
                    collected_at=collected,
                ),
            )
            emit(conn, "LAB_SAMPLE_REQUESTED", row["id"], row["tenant_id"])
            return row

        return atomic("lab_sample_create", data, work)

    @endpoint(
        app,
        "/api/v1/laboratory/samples/<identifier>/receive",
        "POST",
        model=SampleReceive,
        roles=ROLES,
        result=schema(Sample),
    )
    def lab_sample_receive(identifier, data):
        def work(conn):
            row = get(conn, "lab_samples", identifier, True)
            own(row["tenant_id"])
            version(row, data["version"])
            if row["status"] != "REQUESTED":
                raise APIError("conflict", "Muestra ya recibida o rechazada.", 409)
            row = update(
                conn,
                "lab_samples",
                identifier,
                {
                    "status": data["decision"],
                    "received_at": datetime.now(timezone.utc),
                    "version": row["version"] + 1,
                },
            )
            emit(conn, "LAB_SAMPLE_" + data["decision"], identifier, row["tenant_id"])
            return row

        return atomic("lab_sample_receive:" + identifier, data, work)

    @endpoint(
        app,
        "/api/v1/laboratory/results",
        "POST",
        model=ResultCreate,
        roles=ROLES,
        result=schema(Result),
        status=201,
    )
    def lab_result_create(data):
        measured = utc_date(data["measured_at"], "measured_at")
        if data["issued_at"]:
            issued = utc_date(data["issued_at"], "issued_at")
            if not measured <= issued <= datetime.now(timezone.utc):
                raise APIError(
                    "validation", "Emisión anterior a medición o futura.", 422
                )
        if data["document_id"]:
            document = call(
                "documentos",
                "GET",
                "/api/v1/documents/" + data["document_id"] + "/verified",
            )
            own(document["tenant_id"])
            if document["subject_kind"] != "RESULT":
                raise APIError(
                    "validation", "Documento de otro tipo de expediente.", 422
                )
            with transaction() as conn:
                documented = get(conn, "lab_results", str(document["subject_id"]))
                own(documented["tenant_id"])
                if str(documented["sample_id"]) != data["sample_id"]:
                    raise APIError("conflict", "Documento de otra muestra.", 409)

        def work(conn):
            sample = get(conn, "lab_samples", data["sample_id"], True)
            own(sample["tenant_id"])
            profile = get(conn, "lab_profiles", str(sample["profile_id"]))
            if (
                data["result_state"] in ("REPORTED", "CORRECTED", "INDETERMINATE")
                and profile["policy"]["require_document"]
                and (not data["document_id"] or not data["issued_at"])
            ):
                raise APIError(
                    "documentation_required",
                    "Emisión y documento verificado requeridos por el perfil; registra primero pendiente.",
                    422,
                )
            if data["crossmatch"]:
                cross = data["crossmatch"]
                donor = get(conn, "lab_samples", cross["donor_sample_id"])
                recipient = get(conn, "lab_samples", cross["recipient_sample_id"])
                own(donor["tenant_id"])
                own(recipient["tenant_id"])
                if (
                    not recipient["recipient_id"]
                    or not (donor["resource_id"] or donor["donation_id"])
                    or data["sample_id"]
                    not in (cross["donor_sample_id"], cross["recipient_sample_id"])
                    or str(recipient["request_id"]) != cross["request_id"]
                    or str(donor["request_id"]) != cross["request_id"]
                ):
                    raise APIError(
                        "crossmatch_subjects",
                        "Prueba cruzada requiere muestras de donante y receptor para la misma solicitud.",
                        409,
                    )
            if sample["status"] != "RECEIVED" or not sample[
                "collected_at"
            ] <= measured <= datetime.now(timezone.utc):
                raise APIError(
                    "sample_required",
                    "Muestra recibida y fecha de resultado válida requeridas.",
                    409,
                )
            conn.execute(
                "SELECT pg_advisory_xact_lock(hashtextextended(%s,0))",
                (
                    "laboratory:"
                    + str(
                        sample["resource_id"]
                        or sample["recipient_id"]
                        or sample["donation_id"]
                    ),
                ),
            )
            old = conn.execute(
                "SELECT * FROM lab_results WHERE sample_id=%s AND test_code=%s ORDER BY version DESC LIMIT 1",
                (data["sample_id"], data["test_code"]),
            ).fetchone()
            if (str(old["id"]) if old else None) != data["supersedes"]:
                raise APIError(
                    "stale_version",
                    "La corrección debe referir al último resultado.",
                    412,
                )
            row = insert(
                conn,
                "lab_results",
                dict(
                    data,
                    id=str(uuid4()),
                    tenant_id=g.actor["tenant_id"],
                    author_id=g.actor["id"],
                    measured_at=measured,
                    document_snapshot=document if data["document_id"] else None,
                    catalogue_check=check_catalogue(data["hla"]),
                    version=old["version"] + 1 if old else 1,
                ),
            )
            emit(conn, "LAB_RESULT_RECORDED", row["id"], row["tenant_id"])
            return row

        return atomic("lab_result_create", data, work)

    @endpoint(
        app,
        "/api/v1/laboratory/results/<identifier>/review",
        "POST",
        model=ResultReview,
        roles=("MEDICAL",),
        result=schema(Result),
    )
    def lab_result_review(identifier, data):
        def work(conn):
            row = get(conn, "lab_results", identifier, True)
            own(row["tenant_id"])
            sample = get(conn, "lab_samples", str(row["sample_id"]))
            conn.execute(
                "SELECT pg_advisory_xact_lock(hashtextextended(%s,0))",
                (
                    "laboratory:"
                    + str(
                        sample["resource_id"]
                        or sample["recipient_id"]
                        or sample["donation_id"]
                    ),
                ),
            )
            version(row, data["version"])
            if (
                row["status"] != "CAPTURED"
                or conn.execute(
                    "SELECT 1 FROM lab_results WHERE supersedes=%s", (identifier,)
                ).fetchone()
            ):
                raise APIError("conflict", "Resultado ya revisado o sustituido.", 409)
            insert(
                conn,
                "lab_actions",
                {
                    "id": str(uuid4()),
                    "result_id": identifier,
                    "author_id": g.actor["id"],
                    "decision": data["decision"],
                    "reason": data["reason"],
                },
            )
            row = update(conn, "lab_results", identifier, {"status": data["decision"]})
            emit(conn, "LAB_RESULT_" + data["decision"], identifier, row["tenant_id"])
            return row

        return atomic("lab_result_review:" + identifier, data, work)

    @endpoint(
        app,
        "/internal/v1/laboratory/resources/<identifier>/check",
        "POST",
        model=CompletenessInput,
        internal=("inventario",),
        delegate=False,
        result=schema(Completeness),
    )
    def lab_resource_check(identifier, data):
        with transaction() as conn:
            return completeness(conn, identifier, data["profile_id"], data["tenant_id"])

    @endpoint(
        app,
        "/api/v1/laboratory/resources/<identifier>/check",
        "POST",
        model=CompletenessInput,
        roles=("MEDICAL",),
        result=schema(Completeness),
    )
    def lab_resource_completeness(identifier, data):
        own(data["tenant_id"])
        subject = call("inventario", "GET", "/api/v1/resources/" + identifier)
        own(subject["current_institution_id"])
        with transaction() as conn:
            return completeness(conn, identifier, data["profile_id"], data["tenant_id"])
