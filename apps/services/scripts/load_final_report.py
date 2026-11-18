"""Tablas Markdown y resumen JSON de la carga final (lee raw/*/phase.json y raw/volume.json).

Uso:
  apps/services/.venv/bin/python apps/services/scripts/load_final_report.py \\
    documentation/evidencias/entrega-final/carga-final-20261118/raw
"""

import json
import sys
from pathlib import Path

P95_LIMIT_MS = 2000
ERROR_LIMIT = 0.01
ANONYMOUS = {"donantes / Feed público", "donantes / Feed público página siguiente"}
READ_PROFILE = {
    "inventario / Disponibilidad regional": "Médico (JSON)",
    "receptores / Solicitudes propias": "Médico (JSON)",
    "inventario / Inventario propio": "Operador (XML)",
    "donantes / Campañas": "Operador (XML)",
    "priorizacion_geografia / Rutas": "Coordinador (JSON)",
    "transporte / Traslados": "Coordinador (JSON)",
    "monitoreo / Estado regional": "Coordinador (JSON)",
    "auditoria / Bitácora": "Auditor (JSON)",
    "donantes / Agenda propia": "Donante (JSON)",
    "alertas / Avisos propios": "Donante (JSON)",
    "donantes / Feed público": "Donante (JSON)",
    "donantes / Feed público página siguiente": "Donante (JSON)",
    "transporte / Tareas propias": "Transportista (JSON)",
    "alertas / Avisos de traslado": "Transportista (JSON)",
    "transporte / Detalle autorizado desde listado": "Coordinador/Transportista",
}


def profile(name):
    if " | " in name:
        return name.split(" | ", 1)[0]
    if name.startswith("Citas / "):
        return "Móvil donante"
    if name.startswith("Inventario / "):
        return "Escritorio XML (operador)"
    return READ_PROFILE.get(name, "Otro")


def load(raw):
    phases = []
    for path in sorted(raw.glob("*/phase.json"), key=lambda p: p.stat().st_mtime):
        phases.append(json.loads(path.read_text()))
    return phases


def endpoints(phase):
    return [
        r
        for r in phase.get("measurement", [])
        if r["name"] != "Aggregated" and r["requests"]
    ]


def total(phase):
    return next(
        (r for r in phase.get("measurement", []) if r["name"] == "Aggregated"), {}
    )


def phase_row(phase):
    rows = endpoints(phase)
    agg = total(phase)
    requests = agg.get("requests", 0)
    failures = agg.get("failures", 0)
    rate = failures / requests if requests else 0
    p95 = max((r["p95_ms"] for r in rows), default=0)
    p99 = max((r["p99_ms"] for r in rows), default=0)
    ok = (
        p95 < P95_LIMIT_MS
        and rate < ERROR_LIMIT
        and phase.get("logged_in") == phase.get("users")
    )
    # Cuota anónima por IP: todos los usuarios virtuales comparten 127.0.0.1.
    anon = [r for r in rows if r["name"] in ANONYMOUS]
    auth_requests = requests - sum(r["requests"] for r in anon)
    auth_failures = failures - sum(r["failures"] for r in anon)
    auth_rate = auth_failures / auth_requests if auth_requests else 0
    return {
        "fase": phase["name"],
        "modo": phase.get("mode"),
        "usuarios": phase.get("users"),
        "sesiones": phase.get("logged_in"),
        "identidades_distintas": phase.get("distinct_identities"),
        "peticiones": requests,
        "rps": round(agg.get("requests_per_second", 0), 2),
        "media_ms": round(agg.get("mean_ms", 0), 1),
        "p95_global_ms": agg.get("p95_ms"),
        "p99_global_ms": agg.get("p99_ms"),
        "p95_max_endpoint_ms": p95,
        "p99_max_endpoint_ms": p99,
        "errores": failures,
        "errores_pct": round(rate * 100, 2),
        "cache": phase.get("cache"),
        "http_status": phase.get("http_status"),
        "cumple": ok,
        "errores_sin_feed_anonimo": auth_failures,
        "errores_sin_feed_anonimo_pct": round(auth_rate * 100, 2),
    }


def profile_rows(phase):
    groups = {}
    seconds = phase.get("measurement_seconds") or 1
    for r in endpoints(phase):
        g = groups.setdefault(
            profile(r["name"]),
            {"requests": 0, "failures": 0, "weighted": 0.0, "p95": 0, "p99": 0},
        )
        g["requests"] += r["requests"]
        g["failures"] += r["failures"]
        g["weighted"] += r["mean_ms"] * r["requests"]
        g["p95"] = max(g["p95"], r["p95_ms"])
        g["p99"] = max(g["p99"], r["p99_ms"])
    return {
        name: {
            "peticiones": g["requests"],
            "rps": round(g["requests"] / seconds, 2),
            "media_ms": round(g["weighted"] / g["requests"], 1),
            "p95_max_ms": g["p95"],
            "p99_max_ms": g["p99"],
            "errores": g["failures"],
        }
        for name, g in sorted(groups.items())
    }


def md_table(headers, rows):
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines += ["| " + " | ".join(str(v) for v in row) + " |" for row in rows]
    return "\n".join(lines)


def main():
    raw = Path(sys.argv[1]).resolve()
    phases = [p for p in load(raw) if p.get("stage") == "finished"]
    summary = {
        "criterio": {
            "p95_endpoint_ms_menor_que": P95_LIMIT_MS,
            "errores_menor_que_pct": ERROR_LIMIT * 100,
        }
    }
    summary["fases"] = [phase_row(p) for p in phases]
    summary["perfiles"] = {p["name"]: profile_rows(p) for p in phases}
    summary["mas_lentos"] = {
        p["name"]: [
            {
                k: r[k]
                for k in (
                    "method",
                    "name",
                    "requests",
                    "mean_ms",
                    "p95_ms",
                    "p99_ms",
                    "failures",
                )
            }
            for r in sorted(
                endpoints(p), key=lambda r: (r["p95_ms"], r["mean_ms"]), reverse=True
            )[:8]
        ]
        for p in phases
    }
    summary["errores"] = {
        p["name"]: p.get("errors", []) for p in phases if p.get("errors")
    }
    summary["recursos"] = {p["name"]: p.get("resources", {}) for p in phases}
    (raw.parent / f"resumen-{raw.name}.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n"
    )
    out = []
    out.append(
        md_table(
            [
                "Fase",
                "Usuarios",
                "Sesiones/identidades",
                "Peticiones",
                "RPS",
                "Media ms",
                "p95 global",
                "p99 global",
                "Mayor p95 endpoint",
                "Mayor p99 endpoint",
                "Errores",
                "Errores sin feed anónimo",
                "Cumple",
            ],
            [
                [
                    r["fase"],
                    r["usuarios"],
                    f"{r['sesiones']}/{r['identidades_distintas']}",
                    r["peticiones"],
                    r["rps"],
                    r["media_ms"],
                    r["p95_global_ms"],
                    r["p99_global_ms"],
                    r["p95_max_endpoint_ms"],
                    r["p99_max_endpoint_ms"],
                    f"{r['errores']} ({r['errores_pct']} %)",
                    f"{r['errores_sin_feed_anonimo']} ({r['errores_sin_feed_anonimo_pct']} %)",
                    "Sí" if r["cumple"] else "**No**",
                ]
                for r in summary["fases"]
            ],
        )
    )
    for name, groups in summary["perfiles"].items():
        if not name.startswith("mixta"):
            continue
        out.append(f"\n**{name}**\n")
        out.append(
            md_table(
                [
                    "Perfil",
                    "Peticiones",
                    "RPS",
                    "Media ms",
                    "Mayor p95 ms",
                    "Mayor p99 ms",
                    "Errores",
                ],
                [
                    [
                        k,
                        v["peticiones"],
                        v["rps"],
                        v["media_ms"],
                        v["p95_max_ms"],
                        v["p99_max_ms"],
                        v["errores"],
                    ]
                    for k, v in groups.items()
                ],
            )
        )
    for name, rows in summary["mas_lentos"].items():
        out.append(f"\n**Más lentos — {name}**\n")
        out.append(
            md_table(
                [
                    "Método",
                    "Endpoint",
                    "Peticiones",
                    "Media ms",
                    "p95 ms",
                    "p99 ms",
                    "Errores",
                ],
                [
                    [
                        r["method"],
                        r["name"].replace(" | ", " · "),
                        r["requests"],
                        round(r["mean_ms"], 1),
                        r["p95_ms"],
                        r["p99_ms"],
                        r["failures"],
                    ]
                    for r in rows
                ],
            )
        )
    out.append("\n**Recursos (media / máx. durante la medición)**\n")
    rrows = []
    for name, res in summary["recursos"].items():
        if not res:
            continue

        def cell(group, metric, res=res):
            v = res.get(group, {}).get(metric, {})
            return f"{v.get('mean')} / {v.get('max')}" if v else "n/d"

        rrows.append(
            [
                name,
                cell("servicios_api", "cpu_percent"),
                cell("servicios_api", "rss_mb"),
                cell("workers", "cpu_percent"),
                cell("postgres", "cpu_percent"),
                cell("postgres", "rss_mb"),
                cell("locust", "cpu_percent"),
                cell("sistema", "cpu_percent"),
                str(res.get("sistema", {}).get("available_mb", {}).get("min")),
            ]
        )
    out.append(
        md_table(
            [
                "Fase",
                "APIs CPU %",
                "APIs RSS MB",
                "Workers CPU %",
                "PostgreSQL CPU %",
                "PostgreSQL RSS MB",
                "Locust CPU %",
                "Sistema CPU %",
                "RAM disponible mín. MB",
            ],
            rrows,
        )
    )
    print("\n".join(out))


if __name__ == "__main__":
    main()
