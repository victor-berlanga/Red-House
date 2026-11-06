"""Repeated bounded microbenchmarks, independent from HTTP and sustained capacity."""

import json
import os
import platform
import resource
import statistics
import sys
import time
import tracemalloc
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ms_compatibilidad.replay import considered
from ms_priorizacion_geografia.academic import execute
from ms_priorizacion_geografia.decisions import detect, forecast
from ms_priorizacion_geografia.matching import maximum_matching


def measure(name, size, shape, fn):
    samples = []
    for _ in range(5):
        tracemalloc.start()
        start = time.perf_counter()
        fn()
        elapsed = (time.perf_counter() - start) * 1000
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        samples.append({"elapsed_ms": elapsed, "python_peak_bytes": peak})
    durations = sorted(x["elapsed_ms"] for x in samples)
    return {
        "algorithm": name,
        "size": size,
        "shape": shape,
        "repetitions": 5,
        "samples": samples,
        "median_ms": statistics.median(durations),
        "p95_nearest_rank_ms": durations[-1],
    }


def main():
    rows = []
    for n in (10, 100, 1000):
        facts = {
            "inventario": {
                "resources": [
                    {
                        "id": str(i),
                        "folio": str(i),
                        "donation_id": None,
                        "kind": "BLOOD",
                    }
                    for i in range(n)
                ],
                "reservations": [],
                "lineage": [],
                "readings": [],
            },
            "donantes": {"donations": []},
            "compatibilidad": {"results": []},
            "transporte": {"shipments": []},
            "receptores": {"requests": []},
        }
        rows.append(
            measure(
                "CONSISTENCY-OWNER-2.0",
                n,
                "authoritative snapshot facts",
                lambda facts=facts: detect(facts),
            )
        )
        snapshot = {
            "kind": "BLOOD",
            "component": "RBC",
            "as_of": "2026-11-01T00:00:00Z",
            "execution_profile": None,
            "considered": [
                {
                    "resource_id": str(i),
                    "resource_version": 1,
                    "inputs": {
                        "kind": "BLOOD",
                        "component": "RBC",
                        "blood_group": "O-",
                        "recipient_group": "O+",
                        "expires_at": "2026-11-02T00:00:00Z",
                        "route": {"travel_minutes": 5},
                    },
                }
                for i in range(n)
            ],
        }
        rows.append(
            measure(
                "EXPLAIN-PROFILE-2.0-REPLAY",
                n,
                "immutable snapshot",
                lambda snapshot=snapshot: considered(snapshot),
            )
        )
    for n in (10, 100, 365):
        begin = datetime(2025, 1, 1, tzinfo=timezone.utc)
        snapshot = {
            "as_of": (begin + timedelta(days=n)).isoformat(),
            "component": "RBC",
            "lots": [],
            "observations": [
                {
                    "start_at": (begin + timedelta(days=i)).isoformat(),
                    "end_at": (begin + timedelta(days=i + 1)).isoformat(),
                    "value": i % 8,
                }
                for i in range(n)
            ],
        }
        rows.append(
            measure(
                "DEMAND-OWNER-SES-2.0",
                n,
                "UTC daily windows",
                lambda snapshot=snapshot: forecast(snapshot),
            )
        )
    for n in (10, 100, 1000):
        base = {
            "synthetic": True,
            "source": "Benchmark sintético",
            "as_of": "2026-11-01T00:00:00Z",
            "component": "RBC",
            "profile_version": "BENCHMARK-1",
        }
        for algorithm, fields in [
            (
                "EXPLAIN-ACADEMIC-1.0",
                {
                    "required_tests": ["ABO", "HLA"],
                    "candidates": [
                        {
                            "identifier": str(i),
                            "component": "RBC",
                            "available": True,
                            "expired": False,
                            "thermal_incident": False,
                            "tests": ["ABO"],
                        }
                        for i in range(n)
                    ],
                },
            ),
            (
                "LOGISTICS-SIM-2.0",
                {
                    "candidates": [
                        {
                            "identifier": str(i),
                            "component": "RBC",
                            "available": True,
                            "expired": False,
                            "thermal_incident": False,
                            "urgency": i % 3 + 1,
                            "urgency_source": "Synthetic",
                            "waiting_minutes": i,
                            "expiry_minutes": n - i,
                            "travel_minutes": 5,
                            "distance_km": 3,
                        }
                        for i in range(n)
                    ]
                },
            ),
            (
                "DEMAND-SES-1.0",
                {"history": [float(i % 8) for i in range(n)], "stock": n},
            ),
            (
                "CONSISTENCY-1.0",
                {
                    "records": [
                        {
                            "identifier": str(i),
                            "resource_id": str(i),
                            "provenance": "Synthetic",
                        }
                        for i in range(n)
                    ]
                },
            ),
            (
                "ROUTE-DIJKSTRA-1.0",
                {
                    "origin": "0",
                    "destination": str(n),
                    "graph_observed_at": base["as_of"],
                    "edges": [
                        {
                            "origin": str(i),
                            "destination": str(i + 1),
                            "minutes": 1,
                            "distance_km": 1,
                        }
                        for i in range(n)
                    ],
                },
            ),
        ]:
            data = dict(base, algorithm_version=algorithm, **fields)
            rows.append(
                measure(algorithm, n, "sparse/list", lambda data=data: execute(data))
            )
        graph = {str(i): [str(i), str(i + 1)] for i in range(min(n, 500))}
        rows.append(
            measure(
                "COVERAGE-HK-1.0",
                len(graph),
                "sparse",
                lambda graph=graph: maximum_matching(graph),
            )
        )
    for nodes in (10, 50, 100):
        edges = [
            {"origin": str(a), "destination": str(b), "minutes": 1, "distance_km": 1}
            for a in range(nodes)
            for b in range(nodes)
            if a != b
        ]
        data = dict(
            base,
            algorithm_version="ROUTE-DIJKSTRA-1.0",
            origin="0",
            destination=str(nodes - 1),
            graph_observed_at=base["as_of"],
            edges=edges,
        )
        rows.append(
            measure(
                "ROUTE-DIJKSTRA-1.0",
                len(edges),
                "dense",
                lambda data=data: execute(data),
            )
        )
    graph = {str(i): [str(j) for j in range(1000)] for i in range(100)}
    rows.append(
        measure(
            "COVERAGE-HK-1.0",
            100000,
            "dense edge limit",
            lambda graph=graph: maximum_matching(graph),
        )
    )
    print(
        json.dumps(
            {
                "environment": {
                    "python": platform.python_version(),
                    "platform": platform.platform(),
                    "logical_cpus": os.cpu_count(),
                    "process_maxrss_platform_units": resource.getrusage(
                        resource.RUSAGE_SELF
                    ).ru_maxrss,
                },
                "limits": "Tiempo algorítmico y asignaciones Python; sin HTTP, RSS ni carga sostenida. Cinco repeticiones no estiman capacidad productiva.",
                "runs": rows,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
