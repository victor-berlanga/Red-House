from datetime import datetime, timedelta, timezone
from time import perf_counter
from typing import Annotated
from uuid import uuid4

from flask import g
from pydantic import Field

from redhouse.api import atomic, endpoint, listing
from redhouse.client import call
from redhouse.db import get, insert, transaction, update
from redhouse.errors import APIError
from redhouse.events import emit
from redhouse.models import ID, Model, Reason
from redhouse.security import own


class RouteCreate(Model):
    origin_id: ID
    destination_id: ID
    distance_km: Annotated[float, Field(ge=0, le=20000)]
    travel_minutes: Annotated[int, Field(ge=0, le=10080)]
    source: Reason


class RouteUpdate(Model):
    distance_km: Annotated[float, Field(ge=0, le=20000)]
    travel_minutes: Annotated[int, Field(ge=0, le=10080)]
    source: Reason
    version: Annotated[int, Field(ge=1)]


class RankingCreate(Model):
    evaluation_id: ID


class ProposalCreate(Model):
    evaluation_ids: Annotated[list[ID], Field(min_length=1, max_length=100)]


def route_access(row):
    if str(row["region_id"]) != g.actor["region_id"]:
        raise APIError("forbidden", "Ruta fuera de la región.", 403)


def register(app):
    @endpoint(
        app,
        "/api/v1/routes",
        "POST",
        model=RouteCreate,
        roles=("COORDINATOR",),
        status=201,
        summary="Registrar estimación logística con procedencia",
    )
    def route_create(data):
        for identifier in (data["origin_id"], data["destination_id"]):
            call("identidad_acceso", "GET", "/internal/v1/institutions/" + identifier)

        def work(conn):
            row = insert(
                conn,
                "routes",
                dict(id=str(uuid4()), region_id=g.actor["region_id"], **data),
            )
            emit(conn, "ROUTE_CREATED", row["id"], g.actor["tenant_id"])
            return row

        return atomic("route_create", data, work)

    @endpoint(
        app,
        "/api/v1/routes",
        roles=("COORDINATOR", "MEDICAL", "OPERATOR", "TRANSPORT"),
        paginated=True,
        summary="Rutas autorizadas de la región",
    )
    def routes_list():
        with transaction() as conn:
            return listing(
                conn,
                "routes",
                "region_id=%s",
                (g.actor["region_id"],),
                order="origin_id,destination_id,id",
            )

    @endpoint(
        app,
        "/api/v1/routes/<identifier>",
        "PATCH",
        model=RouteUpdate,
        roles=("COORDINATOR",),
        summary="Actualizar ruta con control de versión",
    )
    def route_update(identifier, data):
        def work(conn):
            row = get(conn, "routes", identifier, True)
            route_access(row)
            if row["version"] != data["version"]:
                raise APIError("stale_version", "Ruta modificada.", 409)
            result = update(
                conn,
                "routes",
                identifier,
                dict(
                    data,
                    version=row["version"] + 1,
                    updated_at=datetime.now(timezone.utc),
                ),
            )
            emit(conn, "ROUTE_UPDATED", identifier, g.actor["tenant_id"])
            return result

        return atomic("route_update:" + identifier, data, work)

    @endpoint(
        app,
        "/internal/v1/routes/<identifier>",
        internal=("inventario", "compatibilidad", "transporte"),
        roles=("MEDICAL", "COORDINATOR"),
        summary="Revalidar una ruta conocida",
    )
    def route_internal(identifier):
        with transaction() as conn:
            row = get(conn, "routes", identifier)
            route_access(row)
            return row

    @endpoint(
        app,
        "/internal/v1/route-options",
        internal=("compatibilidad",),
        roles=("MEDICAL",),
        summary="Estimaciones regionales para filtrar candidatos",
    )
    def routes_internal():
        with transaction() as conn:
            rows = conn.execute(
                "SELECT * FROM routes WHERE region_id=%s ORDER BY id",
                (g.actor["region_id"],),
            ).fetchall()
            return {"items": rows}

    @endpoint(
        app,
        "/api/v1/rankings",
        "POST",
        model=RankingCreate,
        roles=("MEDICAL",),
        status=201,
        summary="Ranking operativo explicable y versionado, no decisión clínica",
    )
    def ranking_create(data):
        evaluation = call(
            "compatibilidad", "GET", "/internal/v1/evaluations/" + data["evaluation_id"]
        )
        own(evaluation["tenant_id"])
        start = perf_counter()
        # Orden lexicográfico explícito: no ponderaciones clínicas inventadas.
        candidates = evaluation["candidates"]
        ordered = sorted(
            candidates,
            key=lambda c: (
                c["expires_at"],
                c["travel_minutes"],
                c["distance_km"],
                c["resource_id"],
            ),
        )
        result = [
            dict(
                c,
                rank=i,
                explanation="Orden operativo DEMO: límite capturado, minutos, distancia e identificador estable; requiere dictamen humano.",
            )
            for i, c in enumerate(ordered, 1)
        ]
        elapsed = round((perf_counter() - start) * 1000, 3)

        def work(conn):
            row = insert(
                conn,
                "rankings",
                dict(
                    id=str(uuid4()),
                    tenant_id=g.actor["tenant_id"],
                    evaluation_id=data["evaluation_id"],
                    algorithm_version="LOGISTICS-DEMO-1.0",
                    factors={
                        "order": [
                            "expires_at",
                            "travel_minutes",
                            "distance_km",
                            "resource_id",
                        ],
                        "urgency": evaluation["snapshot"]["urgency"],
                        "request_created_at": evaluation["snapshot"]["created_at"],
                    },
                    result=result,
                    elapsed_ms=elapsed,
                ),
            )
            emit(
                conn,
                "RANKING_CREATED",
                row["id"],
                row["tenant_id"],
                metadata={"algorithm_version": "LOGISTICS-DEMO-1.0"},
            )
            return row

        return atomic("ranking_create", data, work)

    @endpoint(
        app,
        "/api/v1/rankings/<identifier>",
        roles=("MEDICAL",),
        summary="Factores, explicación y resultados del ranking",
    )
    def ranking_detail(identifier):
        with transaction() as conn:
            row = get(conn, "rankings", identifier)
            own(row["tenant_id"])
            return row

    @endpoint(
        app,
        "/api/v1/allocation-proposals",
        "POST",
        model=ProposalCreate,
        roles=("MEDICAL",),
        status=201,
        summary="Matching máximo de candidatos con dictamen favorable; propuesta sin reservas",
    )
    def proposal_create(data):
        from .matching import maximum_matching

        evaluations = [
            call("compatibilidad", "GET", "/internal/v1/evaluations/" + identifier)
            for identifier in data["evaluation_ids"]
        ]
        if len({e["request_id"] for e in evaluations}) != len(evaluations):
            raise APIError("validation", "Usa una evaluación por solicitud.")
        graph, slots, details = {}, {}, {}
        for evaluation in evaluations:
            own(evaluation["tenant_id"])
            favorable = {
                r["resource_id"]
                for r in evaluation["reviews"]
                if r["decision"] == "FAVORABLE"
            }
            candidates = [
                c for c in evaluation["candidates"] if c["resource_id"] in favorable
            ]
            for number in range(evaluation["snapshot"]["quantity"]):
                slot = f"{evaluation['request_id']}:{number}"
                graph[slot] = [c["resource_id"] for c in candidates]
                slots[slot] = evaluation["request_id"]
            details[evaluation["request_id"]] = {
                "evaluation_id": evaluation["id"],
                "request_version": evaluation["request_version"],
                "algorithm_version": evaluation["algorithm_version"],
            }
        if len(graph) > 500 or sum(map(len, graph.values())) > 100000:
            raise APIError(
                "volume_limit",
                "Propuesta supera el límite operativo; divide el conjunto.",
                422,
            )
        started = perf_counter()
        selected = maximum_matching(graph)
        result = [
            {
                "request_id": slots[slot],
                "resource_id": resource,
                "slot": slot,
                "explanation": "Candidato con dictamen favorable en la instantánea; matching máximo evita duplicar recursos. Requiere revalidación y autorización de reserva.",
            }
            for slot, resource in selected.items()
        ]
        elapsed = round((perf_counter() - started) * 1000, 3)

        def work(conn):
            row = insert(
                conn,
                "proposals",
                dict(
                    id=str(uuid4()),
                    tenant_id=g.actor["tenant_id"],
                    algorithm_version="COVERAGE-DEMO-HK-1.0",
                    snapshots=details,
                    result=result,
                    elapsed_ms=elapsed,
                    slot_count=len(graph),
                    matched_count=len(result),
                ),
            )
            emit(
                conn,
                "ALLOCATION_PROPOSAL_CREATED",
                row["id"],
                row["tenant_id"],
                metadata={"algorithm_version": row["algorithm_version"]},
            )
            return row

        return atomic("proposal_create", data, work)

    @endpoint(
        app,
        "/api/v1/allocation-proposals/<identifier>",
        roles=("MEDICAL",),
        summary="Consultar propuesta, límites y versiones originales",
    )
    def proposal_detail(identifier):
        with transaction() as conn:
            row = get(conn, "proposals", identifier)
            own(row["tenant_id"])
            return row
