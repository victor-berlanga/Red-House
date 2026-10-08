"""Comparación alternada del mismo endpoint, manteniendo seguridad Redis activa."""

import argparse
import json
import statistics
from pathlib import Path
from time import perf_counter

import requests
import psutil


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--pairs", type=int, default=30)
    args = parser.parse_args()
    state = json.loads(args.state.read_text())
    urls = state["urls"]
    session = requests.Session()
    login = session.post(
        urls["identidad_acceso"] + "/api/v1/auth/login",
        json={"username": "medical2", "password": state["password"]},
        timeout=10,
    )
    login.raise_for_status()
    token = login.json()["data"]["access_token"]
    results = {"cache": [], "without_cache": []}
    hits, failures = {}, []
    processes = {}
    for group in ("infrastructure_pids", "service_pids", "worker_pids"):
        for name, pid in state[group].items():
            try:
                process = psutil.Process(pid)
                processes[f"{group}:{name}"] = (process, sum(process.cpu_times()[:2]))
            except psutil.Error:
                pass
    measurement_start = perf_counter()
    for _ in range(args.pairs):
        for mode in ("without_cache", "cache"):
            headers = {"Authorization": "Bearer " + token, "Accept": "application/json"}
            if mode == "without_cache":
                headers["Cache-Control"] = "no-cache"
            start = perf_counter()
            response = session.get(
                urls["inventario"] + "/api/v1/availability", headers=headers, timeout=10
            )
            elapsed = (perf_counter() - start) * 1000
            if response.status_code != 200:
                failures.append({"mode": mode, "status": response.status_code})
                continue
            status = response.headers.get("X-Cache", "UNKNOWN")
            hits[status] = hits.get(status, 0) + 1
            results[mode].append(elapsed)
    summary = {}
    for mode, values in results.items():
        ordered = sorted(values)
        summary[mode] = {
            "samples": len(values),
            "mean_ms": round(statistics.mean(values), 3) if values else None,
            "median_ms": round(statistics.median(values), 3) if values else None,
            "p95_ms": round(ordered[min(len(ordered) - 1, int(len(ordered) * 0.95))], 3)
            if values
            else None,
        }
    duration = perf_counter() - measurement_start
    resources = {}
    for name, (process, before) in processes.items():
        try:
            resources[name] = {
                "rss_mb": round(process.memory_info().rss / 1048576, 2),
                "cpu_percent_during_sample": round(
                    100 * (sum(process.cpu_times()[:2]) - before) / duration, 2
                ),
            }
        except psutil.Error:
            pass
    args.report.write_text(
        json.dumps(
            {
                "results": summary,
                "cache_status": hits,
                "errors": failures,
                "duration_seconds": round(duration, 3),
                "process_resources": resources,
                "method": "Pares alternados, misma cuenta y endpoint; autenticación y auditoría activas en ambos modos.",
                "limitation": "Muestra pequeña local con procesos compartidos; no demuestra escalabilidad ni causalidad estadística.",
            },
            indent=2,
        )
    )
    print("Comparación registrada en", args.report)


if __name__ == "__main__":
    main()
