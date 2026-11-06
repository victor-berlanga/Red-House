"""Synthetic sizes; emits reproducible timing/peak Python allocations, no PHI."""

import json
import platform
import sys
import tracemalloc
from pathlib import Path
from time import perf_counter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ms_priorizacion_geografia.academic import execute
from ms_priorizacion_geografia.matching import maximum_matching

rows = []
for n in (10, 100, 1000):
    data = {
        "algorithm_version": "ROUTE-DIJKSTRA-1.0",
        "synthetic": True,
        "source": "Synthetic linear graph",
        "as_of": "2026-10-31T12:00:00Z",
        "component": "RBC",
        "profile_version": "SYNTHETIC-1",
        "graph_observed_at": "2026-10-31T10:00:00Z",
        "origin": "0",
        "destination": str(n),
        "edges": [
            {
                "origin": str(i),
                "destination": str(i + 1),
                "minutes": 1,
                "distance_km": 1,
            }
            for i in range(n)
        ],
    }
    candidate = {
        "component": "RBC",
        "available": True,
        "expired": False,
        "thermal_incident": False,
        "urgency": 1,
        "urgency_source": "Synthetic scale",
        "waiting_minutes": 10,
        "expiry_minutes": 100,
        "travel_minutes": 5,
        "distance_km": 3,
    }
    experiments = [
        dict(
            data,
            algorithm_version=version,
            edges=[],
            candidates=[dict(candidate, identifier=str(i)) for i in range(n)],
        )
        for version in ("EXPLAIN-ACADEMIC-1.0", "LOGISTICS-SIM-2.0")
    ]
    experiments += [
        dict(
            data,
            algorithm_version="DEMAND-SES-1.0",
            edges=[],
            history=[float(i % 5) for i in range(n)],
        ),
        dict(
            data,
            algorithm_version="CONSISTENCY-1.0",
            edges=[],
            records=[
                {"identifier": str(i), "resource_id": str(i), "provenance": "Synthetic"}
                for i in range(n)
            ],
        ),
    ]
    for name, fn in [
        ("DIJKSTRA", lambda data=data: execute(data)),
        (
            "HK",
            lambda n=n: maximum_matching(
                {str(i): [str(i), str(i + 1)] for i in range(n)}
            ),
        ),
    ] + [
        (item["algorithm_version"], lambda item=item: execute(item))
        for item in experiments
    ]:
        tracemalloc.start()
        start = perf_counter()
        result = fn()
        elapsed = perf_counter() - start
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        rows.append(
            {
                "algorithm": name,
                "n": n,
                "elapsed_ms": elapsed * 1000,
                "peak_python_bytes": peak,
            }
        )
print(
    json.dumps(
        {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "synthetic": True,
            "measurements": rows,
        },
        indent=2,
    )
)
