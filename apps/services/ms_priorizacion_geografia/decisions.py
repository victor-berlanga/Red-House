"""Versioned decision support using authorized owner snapshots, never client facts."""

import hashlib
import json
from datetime import datetime, timezone
from time import perf_counter
from typing import Annotated, Literal
from uuid import uuid4

from flask import current_app, g
from pydantic import Field, model_validator
from redhouse.api import atomic, endpoint
from redhouse.client import call
from redhouse.codec import plain
from redhouse.db import get, insert, transaction
from redhouse.errors import APIError
from redhouse.events import emit
from redhouse.extension_contracts import install_reads, schema
from redhouse.models import ID, Model, Text, utc_date
from redhouse.security import own

from .academic import Edge, Output, execute


class Node(Model):
    id: Text
    latitude: Annotated[float, Field(ge=-90, le=90)]
    longitude: Annotated[float, Field(ge=-180, le=180)]


class GraphCreate(Model):
    name: Text
    version: Annotated[int, Field(ge=1)] = 1
    supersedes: ID | None = None
    source: Text
    observed_at: Text
    valid_until: Text
    synthetic: Literal[True] = True
    region: Literal["Nuevo León"] = "Nuevo León"
    quality: Text
    nodes: Annotated[list[Node], Field(min_length=1, max_length=2000)]
    edges: Annotated[list[Edge], Field(max_length=10000)]

    @model_validator(mode="after")
    def coherent(self):
        nodes = {n.id for n in self.nodes}
        if len(nodes) != len(self.nodes) or any(
            e.origin not in nodes or e.destination not in nodes for e in self.edges
        ):
            raise ValueError("Nodos duplicados o aristas sin nodo")
        if not utc_date(self.observed_at) < utc_date(self.valid_until):
            raise ValueError("Vigencia inválida")
        return self


class Graph(GraphCreate):
    synthetic: bool
    provenance: dict | None = None
    id: ID
    tenant_id: ID
    author_id: ID
    created_at: Text


class DecisionCreate(Model):
    branch: Literal["ALG-01", "ALG-02", "ALG-02-GEO", "ALG-03", "ALG-04", "ALG-05"]
    evaluation_ids: Annotated[list[ID], Field(max_length=100)] = Field(
        default_factory=list
    )
    policy_id: ID | None = None
    graph_id: ID | None = None
    origin: Text | None = None
    destination: Text | None = None
    shipment_id: ID | None = None
    component: Literal["RBC", "PLASMA", "PLATELETS", "KIDNEY", "LIVER", "HEART"] = "RBC"
    days: Annotated[int, Field(ge=6, le=365)] = 30


class ExplainedEvaluation(Model):
    id: ID
    profile: dict
    considered: list[dict]
    candidates: list[dict]


class ExplainedResult(Model):
    evaluations: list[ExplainedEvaluation]
    clinical_approval: Literal[False]
    professional_verdict: Literal["NOT_ISSUED"]


class CoverageResult(Model):
    pairs: dict[str, ID]
    slot_count: int
    reservations_created: Literal[0]
    optimization: Literal["MAXIMUM_CARDINALITY_ONLY"]


class PotentialAnomaly(Model):
    code: Text
    identifier: Text
    evidence: dict
    outcome: Literal["POTENTIAL_ANOMALY"]


class AnomalyResult(Model):
    findings: list[PotentialAnomaly]
    clinical_approval: Literal[False]
    automatic_correction: Literal[False]


class InsufficientHistory(Model):
    status: Literal["INSUFFICIENT_RECORDED_USE"]
    clinical_approval: Literal[False]
    limitations: list[str]


class GeographicResult(Output):
    tracking: dict
    road_reference: dict | None = None


AlgorithmResult = (
    ExplainedResult
    | CoverageResult
    | AnomalyResult
    | InsufficientHistory
    | GeographicResult
    | Output
)


class DecisionRun(Model):
    id: ID
    tenant_id: ID
    author_id: ID
    algorithm_version: Text
    source: Text
    snapshot: dict
    result: AlgorithmResult
    fingerprint: Text
    elapsed_ms: float
    synthetic: bool
    created_at: Text


def detect(sources):
    """Each reason is derived from persisted facts and carries minimal evidence."""
    findings = []

    def add(code, identifier, evidence):
        findings.append(
            {
                "code": code,
                "identifier": str(identifier),
                "evidence": plain(evidence),
                "outcome": "POTENTIAL_ANOMALY",
            }
        )

    inv = sources["inventario"]
    donations = {d["id"]: d for d in sources["donantes"]["donations"]}
    seen = {}
    resources = {r["id"]: r for r in inv["resources"]}
    for r in inv["resources"]:
        if r["folio"] in seen:
            add("DUPLICATE_IDENTIFIER", r["id"], {"other_id": seen[r["folio"]]})
        seen[r["folio"]] = r["id"]
        d = donations.get(r["donation_id"])
        if (
            not d
            or not d["subject_tenant_matches"]
            or not d["has_history"]
            or d["status"] != "PROCESSED"
            or d["kind"] != r["kind"]
        ):
            add(
                "INVALID_DONATION_PROVENANCE",
                r["id"],
                {
                    "donation_id": r["donation_id"],
                    "owner": "donantes",
                    "available": bool(d),
                },
            )
    reserved = {}
    for r in inv["reservations"]:
        if r["status"] not in ("CANCELLED", "EXPIRED"):
            reserved.setdefault(r["resource_id"], []).append(r["id"])
    for identifier, ids in reserved.items():
        if len(ids) > 1:
            add("MULTIPLE_RESERVATIONS", identifier, {"reservation_ids": ids})
    for link in inv["lineage"]:
        child = resources.get(link["child_id"])
        parent = resources.get(link["parent_id"])
        if (
            not child
            or not parent
            or child["donation_id"] != link["donation_id"]
            or parent["donation_id"] != link["donation_id"]
            or child["id"] == parent["id"]
        ):
            add(
                "INVALID_LINEAGE",
                link["id"],
                {
                    "parent_id": link["parent_id"],
                    "child_id": link["child_id"],
                    "donation_id": link["donation_id"],
                },
            )
    for row in inv["readings"]:
        if not row["minimum_c"] <= row["temperature_c"] <= row["maximum_c"] or utc_date(
            row["captured_at"]
        ) > utc_date(row["received_at"]):
            add(
                "THERMAL_INCOHERENCE",
                row["resource_id"],
                {
                    "reading_id": row["id"],
                    "temperature_c": row["temperature_c"],
                    "minimum_c": row["minimum_c"],
                    "maximum_c": row["maximum_c"],
                    "profile_id": row["profile_id"],
                },
            )
    for row in sources["compatibilidad"]["results"]:
        cross = row.get("crossmatch")
        if (
            row["tenant_id"] != row["sample_tenant_id"]
            or cross
            and row["sample_id"]
            not in (cross["donor_sample_id"], cross["recipient_sample_id"])
        ):
            add("FOREIGN_SAMPLE", row["id"], {"sample_id": row["sample_id"]})
    for row in sources["transporte"]["shipments"]:
        if row["sequences"] != list(range(1, row["sequence"] + 1)):
            add(
                "BROKEN_SEQUENCE",
                row["id"],
                {"sequences": row["sequences"], "expected_last": row["sequence"]},
            )
        if row["projection_version"] != row["sequence"]:
            add(
                "STALE_PROJECTION",
                row["id"],
                {
                    "source_version": row["sequence"],
                    "projection_version": row["projection_version"],
                },
            )
    for row in sources.get("receptores", {}).get("requests", []):
        if row["allocated"] > row["quantity"]:
            add(
                "INCOMPATIBLE_QUANTITY",
                row["id"],
                {"quantity": row["quantity"], "allocated": row["allocated"]},
            )
    return findings


def forecast(snapshot):
    observations = snapshot["observations"]
    if len(observations) < 6:
        raise APIError(
            "insufficient_history", "Se requieren seis ventanas completas.", 409
        )
    previous = None
    for row in observations:
        start, end = utc_date(row["start_at"]), utc_date(row["end_at"])
        if (
            (end - start).total_seconds() != 86400
            or previous is not None
            and start != previous
            or end > utc_date(snapshot["as_of"])
        ):
            raise APIError(
                "invalid_history",
                "Ventanas duplicadas, desordenadas, discontinuas o futuras.",
                422,
            )
        previous = end
    if not any(x["value"] for x in observations):
        return {
            "status": "INSUFFICIENT_RECORDED_USE",
            "clinical_approval": False,
            "limitations": [
                "No se infiere demanda nula por ausencia de consumo registrado."
            ],
        }
    result = execute(
        {
            "algorithm_version": "DEMAND-SES-1.0",
            "synthetic": True,
            "source": "inventario:destinos vigentes por ventana UTC",
            "as_of": snapshot["as_of"],
            "component": snapshot["component"],
            "profile_version": "RECORDED-DAILY-1",
            "history": [x["value"] for x in observations],
            "stock": len(snapshot["lots"]),
            "lots": snapshot["lots"],
        }
    )
    result["limitations"] = [
        "Estimación operativa sobre registros; no validación clínica.",
        "Ventanas sin eventos cuentan cero bajo RECORDED-DAILY-1; integridad física del registro no certificada.",
        "Sin intervalo calibrado, estacionalidad ni transferencias automáticas.",
    ]
    return result


def reproduce(snapshot):
    branch = snapshot["branch"]
    if branch == "ALG-01":
        return {
            "evaluations": [
                {
                    "id": e["id"],
                    "profile": e["snapshot"]["execution_profile"],
                    "considered": e["snapshot"]["considered"],
                    "candidates": e["candidates"],
                }
                for e in snapshot["evaluations"]
            ],
            "clinical_approval": False,
            "professional_verdict": "NOT_ISSUED",
        }
    if branch == "ALG-02":
        return execute(snapshot["experiment"])
    if branch == "ALG-02-GEO":
        result = execute(snapshot["experiment"])
        result["tracking"] = snapshot["tracking"]
        provenance = snapshot.get("graph", {}).get("provenance")
        if provenance:
            result["limitations"][0] = (
                "Datos viales de OpenStreetMap/OSRM; salida hipotética y duración modelada, no tráfico ni transporte observado."
            )
            pairs = set(zip(result["path"], result["path"][1:]))
            result["road_reference"] = dict(
                provenance,
                segments=[
                    s
                    for s in provenance["segments"]
                    if (s["origin"], s["destination"]) in pairs
                ],
                observed_gps_used=False,
                traffic_measured=False,
                map_age_seconds=None,
                source_age_seconds=(
                    utc_date(snapshot["as_of"]) - utc_date(provenance["retrieved_at"])
                ).total_seconds(),
            )
            result["limitations"].extend(provenance["restrictions"])
        result["limitations"].append(
            "GPS y recorrido observado no cambian pesos ni ETA. ETA desde origen planificado; no medición de tráfico ni entrega."
        )
        return result
    if branch == "ALG-03":
        from .matching import maximum_matching

        graph = {}
        for e in snapshot["evaluations"]:
            reviewed = {
                r["resource_id"] for r in e["reviews"] if r["decision"] == "FAVORABLE"
            }
            for index in range(e["snapshot"]["quantity"]):
                graph[e["request_id"] + ":" + str(index)] = [
                    c["resource_id"]
                    for c in e["candidates"]
                    if c["resource_id"] in reviewed
                ]
        if len(graph) > 500 or sum(map(len, graph.values())) > 100000:
            raise APIError(
                "volume_limit", "Grafo excede 500 cupos o 100000 aristas.", 422
            )
        return {
            "pairs": maximum_matching(graph),
            "slot_count": len(graph),
            "reservations_created": 0,
            "optimization": "MAXIMUM_CARDINALITY_ONLY",
        }
    if branch == "ALG-04":
        return forecast(snapshot["inventory"])
    if branch == "ALG-05":
        return {
            "findings": detect(snapshot["sources"]),
            "clinical_approval": False,
            "automatic_correction": False,
        }
    raise ValueError("Branch not supported")


def collect(data):
    now = datetime.now(timezone.utc).isoformat()
    branch = data["branch"]
    snapshot = {
        "branch": branch,
        "as_of": now,
        "operation_scope": current_app.config["OPERATION_SCOPE"],
    }
    if branch in ("ALG-01", "ALG-02", "ALG-03"):
        if not data["evaluation_ids"]:
            raise APIError(
                "evaluations_required", "Selecciona evaluaciones registradas.", 422
            )
        evaluations = [
            call("compatibilidad", "GET", "/api/v1/evaluations/" + identifier)
            for identifier in data["evaluation_ids"]
        ]
        if any(not e["validity"]["current"] for e in evaluations):
            raise APIError(
                "stale_evaluation",
                "Evaluación obsoleta; consulta razones y evalúa nuevamente.",
                409,
            )
        snapshot["evaluations"] = evaluations
        if branch == "ALG-01" and any(
            not e["snapshot"].get("execution_profile") for e in evaluations
        ):
            raise APIError(
                "profile_required",
                "ALG-01 requiere ejecución con perfil registrado.",
                409,
            )
        if branch == "ALG-02":
            if not data["policy_id"]:
                raise APIError(
                    "policy_required", "Selecciona política operativa registrada.", 422
                )
            policy = call(
                "compatibilidad",
                "GET",
                "/api/v1/laboratory/profiles/" + data["policy_id"],
            )
            governance = call(
                "compatibilidad",
                "GET",
                "/api/v1/laboratory/profiles/" + data["policy_id"] + "/governance",
            )
            if (
                governance["invalid_reasons"]
                or policy["component"] != data["component"]
                or policy["policy"].get("ranking_order")
                != "URGENCY_WAIT_EXPIRY_TIME_DISTANCE_ID"
                or policy["policy"].get("urgency_scale") != "CAPTURED_1_3_SYNTHETIC"
            ):
                raise APIError(
                    "policy_mismatch",
                    "Política fuera de alcance, vigencia o escala soportada.",
                    409,
                )
            snapshot["operative_policy"] = policy
            snapshot["policy_governance"] = governance

            if any(e["kind"] != "BLOOD" for e in evaluations):
                raise APIError(
                    "external_organ_priority",
                    "No se construye prioridad oficial de órganos.",
                    409,
                )
            candidates = []
            for e in evaluations:
                r = e["snapshot"]
                for c in e["candidates"]:
                    candidates.append(
                        {
                            "identifier": e["id"] + ":" + c["resource_id"],
                            "component": r["component"],
                            "available": True,
                            "expired": False,
                            "thermal_incident": False,
                            "urgency": r["urgency"],
                            "urgency_source": "Solicitud "
                            + e["request_id"]
                            + " v"
                            + str(e["request_version"])
                            + "; escala capturada 1..3 por MEDICAL; comparación sintética",
                            "waiting_minutes": max(
                                0,
                                (
                                    utc_date(now) - utc_date(r["created_at"])
                                ).total_seconds()
                                / 60,
                            ),
                            "expiry_minutes": max(
                                0,
                                (
                                    utc_date(c["expires_at"]) - utc_date(now)
                                ).total_seconds()
                                / 60,
                            ),
                            "travel_minutes": c["travel_minutes"],
                            "distance_km": c["distance_km"],
                        }
                    )
            snapshot["experiment"] = {
                "algorithm_version": "LOGISTICS-SIM-2.0",
                "synthetic": True,
                "source": "Solicitudes autorizadas y rutas versionadas",
                "as_of": now,
                "component": data["component"],
                "profile_version": policy["id"] + ":" + str(policy["version"]),
                "candidates": candidates,
            }
        if len({e["request_id"] for e in evaluations}) != len(evaluations):
            raise APIError("duplicate_request", "Una evaluación por solicitud.", 422)
    elif branch == "ALG-02-GEO":
        if not data["graph_id"] or not data["origin"] or not data["destination"]:
            raise APIError(
                "graph_required", "Grafo registrado, origen y destino requeridos.", 422
            )
        with transaction() as conn:
            graph = plain(get(conn, "regional_graphs", data["graph_id"]))
            own(graph["tenant_id"])
        if (
            not utc_date(graph["observed_at"])
            <= utc_date(now)
            < utc_date(graph["valid_until"])
        ):
            raise APIError(
                "graph_unavailable", "Grafo fuera de vigencia; no se inventa ruta.", 409
            )
        nodes = {n["id"] for n in graph["nodes"]}
        if data["origin"] not in nodes or data["destination"] not in nodes:
            raise APIError("unknown_node", "Nodo fuera del grafo registrado.", 422)
        snapshot["graph"] = graph
        tracking = {
            "state": "NOT_REQUESTED",
            "position": None,
            "events": [],
            "source": "transporte",
            "received_via": "OWNER_HISTORY_API",
        }
        if data["shipment_id"]:
            tracking = call(
                "transporte",
                "GET",
                "/api/v1/shipments/" + data["shipment_id"] + "/tracking/snapshot",
            )
            cursor = 0
            events = []
            remaining = False
            for _ in range(20):
                page = call(
                    "transporte",
                    "GET",
                    "/api/v1/shipments/"
                    + data["shipment_id"]
                    + "/tracking/history?limit=100&cursor="
                    + str(cursor)
                    + "&through="
                    + str(tracking["head"]),
                )
                events.extend(page["items"])
                cursor = page["cursor"]
                remaining = page["has_more"]
                if not remaining:
                    break
            tracking["events"] = events
            tracking["history_complete"] = not remaining
            tracking["history_cursor"] = cursor
            tracking["age_checked_at"] = datetime.now(timezone.utc).isoformat()
            tracking["age_seconds"] = (
                (
                    utc_date(tracking["age_checked_at"])
                    - utc_date(tracking["position"]["captured_at"])
                ).total_seconds()
                if tracking["position"]
                else None
            )
            tracking["source"] = "transporte"
            tracking["received_via"] = "OWNER_HISTORY_API"
        snapshot["tracking"] = tracking
        snapshot["experiment"] = {
            "algorithm_version": "ROUTE-DIJKSTRA-1.0",
            "synthetic": True,
            "source": graph["source"],
            "as_of": now,
            "component": data["component"],
            "profile_version": graph["id"] + ":" + str(graph["version"]),
            "origin": data["origin"],
            "destination": data["destination"],
            "edges": graph["edges"],
            "graph_observed_at": graph["observed_at"],
        }
    elif branch == "ALG-04":
        snapshot["inventory"] = call(
            "inventario",
            "GET",
            f"/api/v1/decision-data?component={data['component']}&days={data['days']}",
        )
    else:
        snapshot["sources"] = {
            service: call(service, "GET", "/api/v1/decision-data")
            for service in (
                "inventario",
                "donantes",
                "compatibilidad",
                "transporte",
                "receptores",
            )
        }
    return snapshot


def install(app):
    from .road_sources import install as install_roads

    install_roads(app, Graph)
    install_reads(
        app, "/api/v1/regional-graphs", "regional_graphs", Graph, ("MEDICAL",)
    )
    install_reads(
        app, "/api/v1/decision-runs", "decision_runs", DecisionRun, ("MEDICAL",)
    )

    @endpoint(
        app,
        "/api/v1/regional-graphs",
        "POST",
        model=GraphCreate,
        roles=("MEDICAL",),
        status=201,
        result=schema(Graph),
    )
    def regional_graph_create(data):
        if utc_date(data["observed_at"]) > datetime.now(timezone.utc):
            raise APIError("future_graph", "Fecha de fuente futura.", 422)

        def work(conn):
            if data["supersedes"]:
                conn.execute(
                    "SELECT pg_advisory_xact_lock(hashtextextended(%s,0))",
                    ("regional-graph:" + data["supersedes"],),
                )
                previous = get(conn, "regional_graphs", data["supersedes"])
                own(previous["tenant_id"])
                if (
                    previous["version"] + 1 != data["version"]
                    or conn.execute(
                        "SELECT 1 FROM regional_graphs WHERE supersedes=%s",
                        (data["supersedes"],),
                    ).fetchone()
                ):
                    raise APIError("stale_version", "Sucesor de grafo inválido.", 412)
            elif data["version"] != 1:
                raise APIError("validation", "Versión inicial debe ser 1.", 422)
            row = insert(
                conn,
                "regional_graphs",
                dict(
                    data,
                    id=str(uuid4()),
                    tenant_id=g.actor["tenant_id"],
                    author_id=g.actor["id"],
                ),
            )
            emit(conn, "REGIONAL_GRAPH_RECORDED", row["id"], g.actor["tenant_id"])
            return row

        return atomic("regional_graph_create", data, work)

    @endpoint(
        app,
        "/api/v1/decision-runs",
        "POST",
        model=DecisionCreate,
        roles=("MEDICAL",),
        status=201,
        result=schema(DecisionRun),
    )
    def decision_run_create(data):
        def work(conn):
            start = perf_counter()
            snapshot = plain(collect(data))
            try:
                result = reproduce(snapshot)
            except ValueError as exc:
                raise APIError(
                    "invalid_algorithm_input",
                    "Datos de origen exceden límites o contrato del algoritmo.",
                    422,
                ) from exc
            version = {
                "ALG-01": "EXPLAIN-PROFILE-2.0",
                "ALG-02": "LOGISTICS-OWNER-SIM-3.0",
                "ALG-02-GEO": "REGIONAL-DIJKSTRA-2.0",
                "ALG-03": "COVERAGE-HK-1.0",
                "ALG-04": "DEMAND-OWNER-SES-2.0",
                "ALG-05": "CONSISTENCY-OWNER-2.0",
            }[data["branch"]]
            if data["branch"] == "ALG-02-GEO" and snapshot["graph"].get("provenance"):
                version = "REGIONAL-OSM-DIJKSTRA-3.0"
            row = insert(
                conn,
                "decision_runs",
                {
                    "id": str(uuid4()),
                    "tenant_id": g.actor["tenant_id"],
                    "author_id": g.actor["id"],
                    "algorithm_version": version,
                    "source": "Instantánea de propietarios autorizados",
                    "snapshot": snapshot,
                    "result": result,
                    "fingerprint": hashlib.sha256(
                        json.dumps(snapshot, sort_keys=True).encode()
                    ).hexdigest(),
                    "elapsed_ms": (perf_counter() - start) * 1000,
                    "synthetic": current_app.config["OPERATION_SCOPE"] == "ACADEMIC"
                    or data["branch"] in ("ALG-01", "ALG-02", "ALG-02-GEO"),
                },
            )
            emit(conn, "OWNER_ALGORITHM_EXECUTED", row["id"], g.actor["tenant_id"])
            if data["branch"] == "ALG-05":
                for finding in result["findings"]:
                    digest = hashlib.sha256(
                        json.dumps(finding, sort_keys=True).encode()
                    ).hexdigest()
                    emit(
                        conn,
                        "ANOMALY_REVIEW_REQUESTED",
                        row["id"],
                        g.actor["tenant_id"],
                        metadata={
                            "algorithm_version": version,
                            "finding": finding,
                            "deduplication_key": g.actor["tenant_id"] + ":" + digest,
                            "responsible_id": g.actor["id"],
                        },
                    )
            return row

        return atomic("decision_run_create", data, work)

    @endpoint(
        app,
        "/api/v1/decision-runs/<identifier>/reproduce",
        roles=("MEDICAL",),
        result={"type": "object"},
    )
    def decision_run_reproduce(identifier):
        with transaction() as conn:
            row = get(conn, "decision_runs", identifier)
            own(row["tenant_id"])
            result = reproduce(row["snapshot"])
            return {
                "identical": result == row["result"],
                "fingerprint": row["fingerprint"],
                "result": result,
            }
