"""Bounded, deterministic academic algorithms; no clinical or allocation effects."""

import hashlib
import heapq
import json
from datetime import timedelta
from time import perf_counter
from typing import Annotated, Literal
from uuid import uuid4

from flask import g
from pydantic import Field, model_validator
from redhouse.api import atomic, endpoint
from redhouse.db import insert
from redhouse.events import emit
from redhouse.extension_contracts import install_reads, schema
from redhouse.models import ID, Model, Text, utc_date

Number = Annotated[float, Field(ge=0, allow_inf_nan=False)]


class Edge(Model):
    origin: Text
    destination: Text
    minutes: Number
    distance_km: Number
    blocked: bool = False


class Candidate(Model):
    identifier: Text
    component: Text
    available: bool
    expired: bool
    thermal_incident: bool
    tests: Annotated[list[Text], Field(max_length=80)] = Field(default_factory=list)
    urgency: Number | None = None
    urgency_source: Text | None = None
    waiting_minutes: Number | None = None
    expiry_minutes: Number | None = None
    travel_minutes: Number | None = None
    distance_km: Number | None = None


class Observation(Model):
    latitude: Annotated[float, Field(ge=-90, le=90, allow_inf_nan=False)]
    longitude: Annotated[float, Field(ge=-180, le=180, allow_inf_nan=False)]
    captured_at: Text
    received_at: Text
    source: Text
    accuracy_m: Number
    simulated: bool

    @model_validator(mode="after")
    def dates(self):
        if utc_date(self.captured_at) > utc_date(self.received_at):
            raise ValueError("Fechas GPS UTC y secuencia requeridas")
        return self


class Record(Model):
    identifier: Text
    resource_id: Text
    reserved: bool = False
    quantity: Number = 1
    available_quantity: Number = 1
    sequence: Annotated[int, Field(ge=1)] = 1
    provenance: Text | None = None
    sample_subject: Text | None = None
    subject: Text | None = None
    thermal_incoherent: bool = False
    projection_version: int = 1
    source_version: int = 1


class Lot(Model):
    identifier: Text
    quantity: Number
    expires_at: Text


class Experiment(Model):
    algorithm_version: Literal[
        "EXPLAIN-ACADEMIC-1.0",
        "LOGISTICS-SIM-2.0",
        "ROUTE-DIJKSTRA-1.0",
        "DEMAND-SES-1.0",
        "CONSISTENCY-1.0",
    ]
    synthetic: Literal[True]
    source: Text
    as_of: Text
    component: Text
    profile_version: Text
    required_tests: Annotated[list[Text], Field(max_length=80)] = Field(
        default_factory=list
    )
    candidates: Annotated[list[Candidate], Field(max_length=2000)] = Field(
        default_factory=list
    )
    edges: Annotated[list[Edge], Field(max_length=10000)] = Field(default_factory=list)
    origin: Text | None = None
    destination: Text | None = None
    graph_observed_at: Text | None = None
    observation: Observation | None = None
    websocket_track: Annotated[list[Observation], Field(max_length=2000)] = Field(
        default_factory=list
    )
    history: Annotated[list[Number], Field(max_length=10000)] = Field(
        default_factory=list
    )
    window_days: Annotated[int, Field(ge=1, le=365)] = 1
    stock: Number = 0
    lots: Annotated[list[Lot], Field(max_length=2000)] = Field(default_factory=list)
    records: Annotated[list[Record], Field(max_length=10000)] = Field(
        default_factory=list
    )

    @model_validator(mode="after")
    def valid(self):
        utc_date(self.as_of)
        for lot in self.lots:
            utc_date(lot.expires_at)
        if len({lot.identifier for lot in self.lots}) != len(self.lots):
            raise ValueError("Lotes duplicados")
        if (
            self.lots
            and abs(sum(lot.quantity for lot in self.lots) - self.stock) > 1e-8
        ):
            raise ValueError("Stock debe coincidir con suma de lotes")
        if len({c.identifier for c in self.candidates}) != len(self.candidates):
            raise ValueError("Candidatos duplicados")
        for point in [
            *self.websocket_track,
            *([self.observation] if self.observation else []),
        ]:
            if utc_date(point.received_at) > utc_date(self.as_of):
                raise ValueError("Posición posterior al corte")
        if self.graph_observed_at and utc_date(self.graph_observed_at) > utc_date(
            self.as_of
        ):
            raise ValueError("Fecha de grafo inválida")
        return self


class Finding(Model):
    identifier: str
    outcome: str
    reasons: list[str]


class Metric(Model):
    name: str
    value: float


class Output(Model):
    findings: list[Finding] = Field(default_factory=list)
    path: list[str] = Field(default_factory=list)
    metrics: list[Metric] = Field(default_factory=list)
    clinical_approval: Literal[False] = False
    estimated_arrival_at: str | None = None
    eta_basis: str = "UNAVAILABLE"
    professional_verdict: Literal["NOT_ISSUED"] = "NOT_ISSUED"
    limitations: list[str]


def _explain(x, out, metric):
    for c in x.candidates:
        reasons = [f"MISSING:{t}" for t in sorted(set(x.required_tests) - set(c.tests))]
        reasons += [
            name
            for yes, name in [
                (c.component != x.component, "OTHER_COMPONENT"),
                (not c.available, "UNAVAILABLE"),
                (c.expired, "EXPIRED"),
                (c.thermal_incident, "THERMAL_REVIEW"),
            ]
            if yes
        ]
        out.findings.append(
            Finding(
                identifier=c.identifier,
                outcome="REVIEW_PENDING" if reasons else "TECHNICALLY_COMPLETE",
                reasons=reasons or ["NO_CLINICAL_INFERENCE"],
            )
        )


def _logistics(x, out, metric):
    if x.component.upper() not in ("RBC", "PLASMA", "PLATELETS"):
        raise ValueError(
            "Órganos requieren procedimiento externo; simulación operativa solo sangre"
        )
    fields = (
        "urgency",
        "waiting_minutes",
        "expiry_minutes",
        "travel_minutes",
        "distance_km",
    )
    eligible = []
    for c in x.candidates:
        missing = [f"MISSING:{f}" for f in fields if getattr(c, f) is None]
        if not c.urgency_source:
            missing.append("MISSING:urgency_source")
        if (
            not c.available
            or c.expired
            or c.thermal_incident
            or c.component != x.component
        ):
            missing.append("RESOURCE_REVIEW")
        if missing:
            out.findings.append(
                Finding(identifier=c.identifier, outcome="EXCLUDED", reasons=missing)
            )
        else:
            eligible.append(c)
    for i, c in enumerate(
        sorted(
            eligible,
            key=lambda c: (
                -c.urgency,
                -c.waiting_minutes,
                c.expiry_minutes,
                c.travel_minutes,
                c.distance_km,
                c.identifier,
            ),
        ),
        1,
    ):
        out.findings.append(
            Finding(
                identifier=c.identifier,
                outcome=f"SIMULATED_RANK:{i}",
                reasons=[f"{f}:{getattr(c, f)}" for f in fields],
            )
        )
    out.limitations.append(
        "Escala y orden sintéticos; urgencia no validada para aplicación oficial."
    )


def _route(x, out, metric):
    if not x.origin or not x.destination or not x.graph_observed_at:
        raise ValueError("Origen, destino y fecha del grafo requeridos")
    graph = {}
    for e in x.edges:
        if not e.blocked:
            graph.setdefault(e.origin, []).append(e)
    best, parent = {x.origin: (0, 0)}, {}
    queue = [(0, 0, x.origin)]
    while queue:
        minutes, km, node = heapq.heappop(queue)
        if (minutes, km) != best[node]:
            continue
        if node == x.destination:
            break
        for e in sorted(
            graph.get(node, []),
            key=lambda e: (e.destination, e.minutes, e.distance_km),
        ):
            cost = (minutes + e.minutes, km + e.distance_km)
            if cost < best.get(e.destination, (float("inf"), float("inf"))):
                best[e.destination], parent[e.destination] = cost, node
                heapq.heappush(queue, (*cost, e.destination))
    if x.destination in best:
        node = x.destination
        while node != x.origin:
            out.path.append(node)
            node = parent[node]
        out.path = [x.origin] + out.path[::-1]
        out.estimated_arrival_at = (
            utc_date(x.as_of) + timedelta(minutes=best[x.destination][0])
        ).isoformat()
        out.eta_basis = "SIMULATED_DEPARTURE_AT_AS_OF_FROM_GRAPH_ORIGIN"
        metric("planned_minutes", best[x.destination][0])
        metric("planned_distance_km", best[x.destination][1])
    else:
        out.findings.append(
            Finding(
                identifier=x.destination,
                outcome="UNREACHABLE",
                reasons=["NO_AVAILABLE_PATH"],
            )
        )
    metric(
        "graph_age_seconds",
        (utc_date(x.as_of) - utc_date(x.graph_observed_at)).total_seconds(),
    )
    metric("declared_track_points", len(x.websocket_track))
    if x.observation:
        metric(
            "observed_gps_age_seconds",
            (utc_date(x.as_of) - utc_date(x.observation.captured_at)).total_seconds(),
        )
        metric("observed_gps_accuracy_m", x.observation.accuracy_m)
    out.limitations.append(
        "Ruta de grafo declarado, sin tráfico actual. Puntos declarados en HTTP no acreditan recepción WSS. GPS y recorrido no se extrapolan; ETA desde posición no disponible sin ajuste al grafo."
    )


def _demand(x, out, metric):
    if len(x.history) < 6:
        raise ValueError("Se requieren al menos seis ventanas históricas completas")
    split = max(3, len(x.history) * 2 // 3)
    train, test = x.history[:split], x.history[split:]

    def fit(alpha):
        level, error = train[0], 0
        for value in train[1:]:
            error += abs(value - level)
            level = alpha * value + (1 - alpha) * level
        return error, alpha, level

    _, alpha, level = min(fit(a) for a in (0.2, 0.5, 0.8))
    errors, baseline = [], []
    previous = train[-1]
    for value in test:
        errors.append(abs(value - level))
        baseline.append(abs(value - previous))
        level = alpha * value + (1 - alpha) * level
        previous = value
    for name, value in [
        ("alpha", alpha),
        ("train_windows", split),
        ("test_windows", len(test)),
        ("mae", sum(errors) / len(errors)),
        ("naive_mae", sum(baseline) / len(baseline)),
        ("forecast_next_window", level),
        ("stock_excess_next_window", max(0, x.stock - level)),
    ]:
        metric(name, value)
    consumed = 0.0
    for lot in sorted(
        x.lots, key=lambda lot: (utc_date(lot.expires_at), lot.identifier)
    ):
        days = max(
            0.0,
            (utc_date(lot.expires_at) - utc_date(x.as_of)).total_seconds() / 86400,
        )
        expected = min(lot.quantity, max(0.0, level * days / x.window_days - consumed))
        consumed += expected
        out.findings.append(
            Finding(
                identifier=lot.identifier,
                outcome="ROTATION_REVIEW",
                reasons=[
                    f"quantity:{lot.quantity}",
                    f"expected_consumption_before_expiry:{expected}",
                    f"estimated_unused_at_expiry:{lot.quantity - expected}",
                    "CONSTANT_RATE_SYNTHETIC_ASSUMPTION",
                ],
            )
        )
    out.limitations.append(
        "Ventanas contiguas de igual duración y mismo componente/institución. Exceso de stock no prueba caducidad; revisión de lotes requerida. Sin intervalo probabilístico calibrado."
    )


def _anomalies(x, out, metric):
    seen, reserved, sequences = set(), set(), {}
    for r in x.records:
        reasons = []
        for condition, reason in [
            (r.identifier in seen, "DUPLICATE_IDENTIFIER"),
            (r.reserved and r.resource_id in reserved, "MULTIPLE_RESERVATIONS"),
            (r.quantity > r.available_quantity, "QUANTITY_MISMATCH"),
            (not r.provenance, "MISSING_PROVENANCE"),
            (
                r.sample_subject is not None and r.sample_subject != r.subject,
                "FOREIGN_SAMPLE",
            ),
            (r.thermal_incoherent, "THERMAL_REVIEW"),
            (r.projection_version != r.source_version, "STALE_PROJECTION"),
            (r.sequence != sequences.get(r.resource_id, 0) + 1, "BROKEN_SEQUENCE"),
        ]:
            if condition:
                reasons.append(reason)
        seen.add(r.identifier)
        if r.reserved:
            reserved.add(r.resource_id)
        sequences[r.resource_id] = r.sequence
        if reasons:
            out.findings.append(
                Finding(
                    identifier=r.identifier,
                    outcome="POTENTIAL_ANOMALY",
                    reasons=reasons,
                )
            )
    out.limitations.append(
        "Hallazgos sobre instantánea sintética ordenada; revisión pendiente, sin corrección automática."
    )


def execute(data):
    """Pure evaluation: all time references and parameters belong to the input."""
    x = Experiment.model_validate(data)
    out = Output(
        limitations=[
            "Datos sintéticos; no reserva, libera ni asigna.",
            "Registro, completitud, preselección y dictamen son niveles distintos.",
        ]
    )

    def metric(name, value):
        out.metrics.append(Metric(name=name, value=value))

    implementations = {
        "EXPLAIN-ACADEMIC-1.0": _explain,
        "LOGISTICS-SIM-2.0": _logistics,
        "ROUTE-DIJKSTRA-1.0": _route,
        "DEMAND-SES-1.0": _demand,
    }
    implementations.get(x.algorithm_version, _anomalies)(x, out, metric)
    return out.model_dump()


class Run(Model):
    id: ID
    tenant_id: ID
    author_id: ID
    algorithm_version: Text
    source: Text
    snapshot: Experiment
    result: Output
    fingerprint: Text
    elapsed_ms: float
    synthetic: Literal[True]
    created_at: Text


def install(app):
    install_reads(
        app, "/api/v1/algorithm-runs", "algorithm_runs", Run, ("MEDICAL", "COORDINATOR")
    )

    @endpoint(
        app,
        "/api/v1/algorithm-runs",
        "POST",
        model=Experiment,
        roles=("MEDICAL", "COORDINATOR"),
        result=schema(Run),
        status=201,
    )
    def algorithm_run(data):
        from redhouse.errors import APIError

        started = perf_counter()
        try:
            result = execute(data)
        except ValueError as exc:
            raise APIError("validation", str(exc), 422) from None
        elapsed = (perf_counter() - started) * 1000
        fingerprint = hashlib.sha256(
            json.dumps(data, sort_keys=True).encode()
        ).hexdigest()

        def work(conn):
            row = insert(
                conn,
                "algorithm_runs",
                {
                    "id": str(uuid4()),
                    "tenant_id": g.actor["tenant_id"],
                    "author_id": g.actor["id"],
                    "algorithm_version": data["algorithm_version"],
                    "source": data["source"],
                    "snapshot": data,
                    "result": result,
                    "elapsed_ms": elapsed,
                    "fingerprint": fingerprint,
                    "synthetic": True,
                },
            )
            emit(conn, "ACADEMIC_ALGORITHM_EXECUTED", row["id"], row["tenant_id"])
            return row

        return atomic("academic_algorithm_run", data, work)
