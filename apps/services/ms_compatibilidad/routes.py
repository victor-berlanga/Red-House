from datetime import datetime, timedelta, timezone
from time import perf_counter
from typing import Literal
from uuid import uuid4

from flask import current_app, g
from redhouse.api import atomic, endpoint
from redhouse.client import call
from redhouse.codec import plain
from redhouse.db import get, insert, transaction
from redhouse.errors import APIError
from redhouse.events import emit
from redhouse.models import ID, Confirm, Model, utc_date
from redhouse.security import own

ABO = {"O": {"O"}, "A": {"O", "A"}, "B": {"O", "B"}, "AB": {"O", "A", "B", "AB"}}
NOTICE = "Filtro ilustrativo; no interpreta HLA, anticuerpos, tamaño ni pruebas cruzadas. Requiere dictamen médico."


def compatible(donor, recipient):
    return donor[:-1] in ABO[recipient[:-1]] and (
        recipient[-1] == "+" or donor[-1] == "-"
    )


class EvaluationCreate(Model):
    request_id: ID
    profile_id: ID | None = None


class ReviewCreate(Confirm):
    resource_id: ID
    decision: Literal["FAVORABLE", "UNFAVORABLE"]


def register(app):
    @endpoint(
        app,
        "/api/v1/evaluations",
        "POST",
        model=EvaluationCreate,
        roles=("MEDICAL",),
        status=201,
        summary="Preselección ilustrativa con datos y reglas versionados",
    )
    def evaluation_create(data):
        started = perf_counter()
        req = call("receptores", "GET", "/internal/v1/requests/" + data["request_id"])
        if (
            req["status"] not in ("OPEN", "IN_PROGRESS")
            or req["recipient"]["status"] != "ACTIVE"
        ):
            raise APIError("conflict", "Solicitud o receptor inactivos.", 409)
        manual = req["kind"] == "BLOOD" and req["component"] != "RBC"
        if req["kind"] == "BLOOD" and req["component"] not in (
            "RBC",
            "PLASMA",
            "PLATELETS",
        ):
            raise APIError("unknown_product", "Producto sin flujo registrado.", 422)
        with transaction() as conn:
            from .freshness import recipient_laboratory
            from .rules import state, validity

            rec_lab = recipient_laboratory(
                conn, req["recipient_id"], g.actor["tenant_id"]
            )
            execution_profile = (
                get(conn, "lab_profiles", data["profile_id"])
                if data["profile_id"]
                else None
            )
            profile_actions = []
            if execution_profile:
                own(execution_profile["tenant_id"])
                if (execution_profile["kind"], execution_profile["component"]) != (
                    req["kind"],
                    req["component"],
                ) or validity(conn, execution_profile):
                    raise APIError(
                        "profile_mismatch", "Perfil no aplicable o no vigente.", 409
                    )
                profile_actions = state(conn, execution_profile)[1]
            if manual and not execution_profile:
                raise APIError(
                    "manual_profile_required",
                    "La revisión manual requiere perfil registrado de datos exigidos.",
                    409,
                )
        if current_app.config["OPERATION_SCOPE"] == "CLINICAL":
            if not execution_profile:
                raise APIError(
                    "clinical_profile_required",
                    "Evaluación clínica requiere perfil institucional registrado y aprobación competente.",
                    409,
                )
            from .rules import clinically_enabled

            if not clinically_enabled(execution_profile, profile_actions, []):
                raise APIError(
                    "clinical_policy_disabled",
                    "Perfil sin aprobación competente vigente.",
                    409,
                )
            manual = True  # Academic RBC/ABO filters never become clinical rules by configuration.
        resources = call("inventario", "GET", "/internal/v1/available-resources")[
            "items"
        ]
        routes = call("priorizacion_geografia", "GET", "/internal/v1/route-options")[
            "items"
        ]
        options = {(r["origin_id"], r["destination_id"]): r for r in routes}
        considered = []
        candidates, missing = [], {"route": 0, "expired": 0, "other_component": 0}
        now = datetime.now(timezone.utc)
        for resource in resources:
            trace = {
                "resource_id": resource["id"],
                "resource_version": resource["version"],
                "source": "inventario",
                "outcome": "EXCLUDED",
                "reasons": [],
                "inputs": {
                    "kind": resource["kind"],
                    "component": resource["component"],
                    "blood_group": resource["blood_group"],
                    "recipient_group": req["recipient"]["blood_group"],
                    "expires_at": resource["expires_at"],
                },
            }
            considered.append(trace)
            if (
                resource["kind"] != req["kind"]
                or resource["component"] != req["component"]
            ):
                trace["reasons"].append("OTHER_COMPONENT")
                missing["other_component"] += 1
                continue
            donor, recipient = resource["blood_group"], req["recipient"]["blood_group"]
            if not manual and not (
                compatible(donor, recipient)
                if req["kind"] == "BLOOD"
                else donor[:-1] == recipient[:-1]
            ):
                trace["reasons"].append(
                    "ABO_RHD_FILTER" if req["kind"] == "BLOOD" else "ABO_FILTER"
                )
                continue
            route = options.get((resource["tenant_id"], req["tenant_id"]))
            trace["inputs"]["route"] = route
            if not route:
                trace["reasons"].append("MISSING_ROUTE")
                missing["route"] += 1
                continue
            if utc_date(resource["expires_at"]) <= now + timedelta(
                minutes=route["travel_minutes"]
            ):
                trace["reasons"].append("INSUFFICIENT_TIME")
                missing["expired"] += 1
                continue
            from .laboratory import completeness

            laboratory = None
            if resource.get("lab_profile_id"):
                with transaction() as conn:
                    laboratory = completeness(
                        conn,
                        resource["id"],
                        resource["lab_profile_id"],
                        resource["tenant_id"],
                    )
            trace["outcome"] = (
                "REVIEW_PENDING"
                if manual or laboratory and not laboratory["complete"]
                else "PRESELECTED"
            )
            trace["reasons"] = (
                list(laboratory["missing"])
                if laboratory
                else ["LAB_PROFILE_NOT_LINKED"]
            )
            trace["inputs"]["laboratory"] = laboratory
            trace["inputs"]["route"] = route
            if execution_profile:
                trace["reasons"] += [
                    "PROFILE_MISSING:" + code
                    for code in execution_profile["required_tests"]
                    if not laboratory or code not in laboratory["satisfied_tests"]
                ]
                trace["reasons"] += [
                    "PROFILE_HLA_MISSING:" + code
                    for code in execution_profile["required_loci"]
                    if not laboratory or code not in laboratory["satisfied_loci"]
                ]
            if execution_profile and (
                not laboratory
                or not laboratory["complete"]
                or any(x.startswith("PROFILE_") for x in trace["reasons"])
            ):
                trace["outcome"] = "EXCLUDED"
                continue
            candidates.append(
                {
                    "resource_id": resource["id"],
                    "laboratory": laboratory,
                    "resource_folio": resource.get("folio", resource["id"][:8]),
                    "resource_version": resource["version"],
                    "origin_id": resource["tenant_id"],
                    "expires_at": resource["expires_at"],
                    "route_id": route["id"],
                    "route_version": route["version"],
                    "travel_minutes": route["travel_minutes"],
                    "distance_km": route["distance_km"],
                    "explanation": (
                        "Revisión manual: no se ejecutó filtro clínico de compatibilidad. "
                        if manual
                        else "ABO/RhD potencial para eritrocitos. "
                        if req["kind"] == "BLOOD"
                        else "Tipo de órgano y ABO idéntico; RhD no determina esta preselección. "
                    )
                    + NOTICE,
                }
            )
        algorithm = (
            "EXPLAIN-PROFILE-2.0"
            if execution_profile
            else ("RBC-1.0" if req["kind"] == "BLOOD" else "ORGAN-1.0")
        )
        elapsed = round((perf_counter() - started) * 1000, 3)
        snapshot = dict(
            req,
            missing_data=missing,
            clinical_notice=NOTICE,
            recipient_laboratory=rec_lab,
            execution_profile=plain(execution_profile),
            profile_actions=profile_actions,
            considered=considered,
            manual_review=manual,
            preselection_only=True,
            operation_scope=current_app.config["OPERATION_SCOPE"],
            source="Propietarios autorizados, universo de recursos regionales disponibles no vencidos",
            as_of=now.isoformat(),
        )

        def work(conn):
            row = insert(
                conn,
                "evaluations",
                {
                    "id": str(uuid4()),
                    "tenant_id": g.actor["tenant_id"],
                    "request_id": req["id"],
                    "request_version": req["version"],
                    "recipient_version": req["recipient"]["version"],
                    "kind": req["kind"],
                    "algorithm_version": algorithm,
                    "snapshot": snapshot,
                    "candidates": candidates,
                    "elapsed_ms": elapsed,
                },
            )
            emit(
                conn,
                "EVALUATION_CREATED",
                row["id"],
                row["tenant_id"],
                metadata={
                    "algorithm_version": algorithm,
                    "candidate_count": len(candidates),
                },
            )
            return row

        return atomic("evaluation_create", data, work)

    @endpoint(
        app,
        "/api/v1/evaluations/<identifier>",
        roles=("MEDICAL",),
        summary="Consultar evaluación, explicación y dictámenes",
    )
    def evaluation_detail(identifier):
        with transaction() as conn:
            row = get(conn, "evaluations", identifier)
            own(row["tenant_id"])
            row["reviews"] = conn.execute(
                "SELECT * FROM reviews WHERE evaluation_id=%s ORDER BY created_at,id",
                (identifier,),
            ).fetchall()
            from .freshness import current

            row["validity"] = current(conn, row)
            return row

    @endpoint(
        app,
        "/api/v1/evaluations/<identifier>/reproduce",
        roles=("MEDICAL",),
        result={"type": "object"},
    )
    def evaluation_reproduce(identifier):
        with transaction() as conn:
            row = get(conn, "evaluations", identifier)
            own(row["tenant_id"])
            if "considered" not in row["snapshot"]:
                raise APIError(
                    "legacy_snapshot",
                    "Instantánea anterior al contrato de reproducción; historia conservada.",
                    409,
                )
            from .replay import considered

            result = considered(row["snapshot"])
            return {
                "identical": result == row["snapshot"]["considered"],
                "considered": result,
                "algorithm_version": row["algorithm_version"],
                "clinical_approval": False,
            }

    @endpoint(
        app,
        "/api/v1/evaluations/<identifier>/reviews",
        "POST",
        model=ReviewCreate,
        roles=("MEDICAL",),
        status=201,
        summary="Registrar dictamen humano inmutable de un candidato",
    )
    def evaluation_review(identifier, data):
        def work(conn):
            row = get(conn, "evaluations", identifier)
            own(row["tenant_id"])
            if not any(
                c["resource_id"] == data["resource_id"] for c in row["candidates"]
            ):
                raise APIError("not_found", "Recurso ajeno a esta evaluación.", 404)
            candidate = next(
                c for c in row["candidates"] if c["resource_id"] == data["resource_id"]
            )
            context = call(
                "inventario",
                "GET",
                "/internal/v1/resources/" + data["resource_id"] + "/laboratory-context",
                delegate=False,
            )
            from .laboratory import completeness

            current = (
                completeness(
                    conn,
                    data["resource_id"],
                    context["profile_id"],
                    context["tenant_id"],
                )
                if context["profile_id"]
                else None
            )
            if (
                "laboratory" not in candidate
                or current != candidate["laboratory"]
                or (current and not current["complete"])
            ):
                raise APIError(
                    "stale_laboratory",
                    "Laboratorio incompleto o modificado; evalúa nuevamente.",
                    409,
                )
            from redhouse.operational import (
                require_clinical_policy,
                require_execution_scope,
            )

            from .freshness import current as freshness

            require_clinical_policy(current)
            require_execution_scope(row["snapshot"])
            validity_now = freshness(conn, row, data["resource_id"])
            if not validity_now["current"]:
                raise APIError(
                    "stale_evaluation",
                    "Entradas críticas modificadas; consulta vigencia y evalúa nuevamente.",
                    409,
                )
            review = insert(
                conn,
                "reviews",
                {
                    "id": str(uuid4()),
                    "tenant_id": g.actor["tenant_id"],
                    "evaluation_id": identifier,
                    "resource_id": data["resource_id"],
                    "actor_id": g.actor["id"],
                    "decision": data["decision"],
                    "operation_scope": current_app.config["OPERATION_SCOPE"],
                    "reason": data["reason"],
                },
            )
            emit(
                conn,
                "EVALUATION_REVIEWED",
                identifier,
                row["tenant_id"],
                metadata={"status": data["decision"]},
            )
            return review

        return atomic("evaluation_review:" + identifier, data, work)

    @endpoint(
        app,
        "/internal/v1/evaluations/<identifier>",
        internal=("inventario", "priorizacion_geografia"),
        roles=("MEDICAL",),
        summary="Instantánea y dictámenes para reservar o priorizar",
    )
    def evaluation_internal(identifier):
        return evaluation_detail(identifier)
