from datetime import datetime, timedelta, timezone
from time import perf_counter
from typing import Literal
from uuid import uuid4

from flask import g

from redhouse.api import atomic, endpoint
from redhouse.client import call
from redhouse.db import get, insert, transaction
from redhouse.errors import APIError
from redhouse.events import emit
from redhouse.models import Confirm, ID, Model, utc_date
from redhouse.security import own

ABO = {"O": {"O"}, "A": {"O", "A"}, "B": {"O", "B"}, "AB": {"O", "A", "B", "AB"}}
NOTICE = "Filtro ilustrativo; no interpreta HLA, anticuerpos, tamaño ni pruebas cruzadas. Requiere dictamen médico."


def compatible(donor, recipient):
    return donor[:-1] in ABO[recipient[:-1]] and (
        recipient[-1] == "+" or donor[-1] == "-"
    )


class EvaluationCreate(Model):
    request_id: ID


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
        if req["kind"] == "BLOOD" and req["component"] != "RBC":
            raise APIError(
                "manual_review_required",
                "Componente sin regla computacional validada; requiere revisión externa.",
                409,
            )
        resources = call("inventario", "GET", "/internal/v1/available-resources")[
            "items"
        ]
        routes = call("priorizacion_geografia", "GET", "/internal/v1/route-options")[
            "items"
        ]
        options = {(r["origin_id"], r["destination_id"]): r for r in routes}
        candidates, missing = [], {"route": 0, "expired": 0, "other_component": 0}
        now = datetime.now(timezone.utc)
        for resource in resources:
            if (
                resource["kind"] != req["kind"]
                or resource["component"] != req["component"]
            ):
                missing["other_component"] += 1
                continue
            donor, recipient = resource["blood_group"], req["recipient"]["blood_group"]
            if not (
                compatible(donor, recipient)
                if req["kind"] == "BLOOD"
                else donor[:-1] == recipient[:-1]
            ):
                continue
            route = options.get((resource["tenant_id"], req["tenant_id"]))
            if not route:
                missing["route"] += 1
                continue
            if utc_date(resource["expires_at"]) <= now + timedelta(
                minutes=route["travel_minutes"]
            ):
                missing["expired"] += 1
                continue
            candidates.append(
                {
                    "resource_id": resource["id"],
                    "resource_folio": resource.get("folio", resource["id"][:8]),
                    "resource_version": resource["version"],
                    "origin_id": resource["tenant_id"],
                    "expires_at": resource["expires_at"],
                    "route_id": route["id"],
                    "route_version": route["version"],
                    "travel_minutes": route["travel_minutes"],
                    "distance_km": route["distance_km"],
                    "explanation": (
                        "ABO/RhD potencial para eritrocitos. "
                        if req["kind"] == "BLOOD"
                        else "Tipo de órgano y ABO idéntico; RhD no determina esta preselección. "
                    )
                    + NOTICE,
                }
            )
        algorithm = "RBC-1.0" if req["kind"] == "BLOOD" else "ORGAN-1.0"
        elapsed = round((perf_counter() - started) * 1000, 3)
        snapshot = dict(req, missing_data=missing, clinical_notice=NOTICE)

        def work(conn):
            row = insert(
                conn,
                "evaluations",
                dict(
                    id=str(uuid4()),
                    tenant_id=g.actor["tenant_id"],
                    request_id=req["id"],
                    request_version=req["version"],
                    recipient_version=req["recipient"]["version"],
                    kind=req["kind"],
                    algorithm_version=algorithm,
                    snapshot=snapshot,
                    candidates=candidates,
                    elapsed_ms=elapsed,
                ),
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
            return row

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
            review = insert(
                conn,
                "reviews",
                dict(
                    id=str(uuid4()),
                    tenant_id=g.actor["tenant_id"],
                    evaluation_id=identifier,
                    resource_id=data["resource_id"],
                    actor_id=g.actor["id"],
                    decision=data["decision"],
                    reason=data["reason"],
                ),
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
