"""Carga ficticia solo en el clúster aislado creado por local.py."""

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from time import perf_counter
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import psycopg


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--units", type=int, default=5000)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--add-page-index", action="store_true")
    args = parser.parse_args()
    state = json.loads((args.directory / "state.json").read_text())
    if (
        Path(state["directory"]).resolve() != args.directory.resolve()
        or not 0 <= args.units <= 100000
    ):
        raise RuntimeError("Entorno o volumen inválidos.")
    started = perf_counter()
    with psycopg.connect(state["database_owners"]["inventario"]) as conn:
        with conn.cursor() as cursor:
            cursor.executemany(
                "INSERT INTO resources(id,tenant_id,current_institution_id,region_id,folio,kind,component,blood_group,expires_at,status) "
                "VALUES(%s,%s,%s,%s,%s,'BLOOD','RBC',%s,%s,'AVAILABLE')",
                [
                    (
                        str(uuid4()),
                        state["tenants"][i % 2],
                        state["tenants"][i % 2],
                        state["region_id"],
                        "LOAD-" + uuid4().hex[:20],
                        ["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"][i % 8],
                        datetime.now(timezone.utc) + timedelta(days=2 + i % 7),
                    )
                    for i in range(args.units)
                ],
            )
        elapsed = (perf_counter() - started) * 1000
        conn.execute("ANALYZE resources")
        before = conn.execute(
            "EXPLAIN (ANALYZE,FORMAT JSON) SELECT id FROM resources WHERE region_id=%s "
            "AND status='AVAILABLE' AND expires_at>now() ORDER BY expires_at,id LIMIT 20",
            (state["region_id"],),
        ).fetchone()[0]
        if args.add_page_index:
            conn.execute(
                "CREATE INDEX IF NOT EXISTS availability_page ON resources(region_id,expires_at,id) WHERE status='AVAILABLE'"
            )
        plan = conn.execute(
            "EXPLAIN (ANALYZE,FORMAT JSON) SELECT id FROM resources WHERE region_id=%s "
            "AND status='AVAILABLE' AND expires_at>now() ORDER BY expires_at,id LIMIT 20",
            (state["region_id"],),
        ).fetchone()[0]
        count = conn.execute("SELECT count(*) FROM resources").fetchone()[0]
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(
            {
                "synthetic_units": args.units,
                "total_units": count,
                "insertion_ms": round(elapsed, 3),
                "query_plan_before": before,
                "query_plan": plan,
                "notice": "Carga exclusivamente ficticia; no liberación médica de recursos reales.",
            },
            indent=2,
        )
    )
    print("Carga ficticia y plan de consulta registrados en", args.report)


if __name__ == "__main__":
    main()
