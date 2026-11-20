"""Hueco H3: resumen, indicadores y reportes de traslados de TRANSPORT en el móvil.

La app móvil consume tres lecturas que antes usaba la consola de escritorio:
`/api/v1/summary`, `/api/v1/portal-metrics` (Transporte) y los trabajos de
exportación `SHIPMENTS` (Documentos). Estas pruebas fijan que el servidor las
acota a lo propio del transportista y que no abre otros reportes.
"""

from urllib.parse import urlencode

import pytest

from .helpers import evaluation, iso, plan, recipient_request, reservation, resource


def planned(p):
    unit = resource(p)
    _, req = recipient_request(p)
    ev = evaluation(p, req, [unit])
    return plan(p, reservation(p, ev, unit)["reservation"])


def own_ids(p):
    """Identificadores que el servidor entrega a transport1 en su lista de traslados."""
    ids, page = set(), 1
    while True:
        result = p.ok(
            "transporte",
            "GET",
            f"/api/v1/shipments?page={page}&page_size=100",
            user="transport1",
        )
        ids |= {row["id"] for row in result["items"]}
        if page * result["page_size"] >= result["total"]:
            return ids
        page += 1


def db_count(p, transport_user_id):
    with p.owner("transporte") as conn:
        return conn.execute(
            "SELECT count(*) FROM shipments WHERE transport_user_id=%s",
            (transport_user_id,),
        ).fetchone()[0]


def test_summary_and_metrics_only_count_own_assignments(p):
    me = p.env.state["accounts"]["transport1"]["id"]
    other = p.env.state["accounts"]["operator1"]["id"]
    shipment = planned(p)

    summary = p.ok("transporte", "GET", "/api/v1/summary", user="transport1")
    assert summary["total"] == db_count(p, me)
    assert sum(row["value"] for row in summary["statuses"]) == summary["total"]
    window = "?" + urlencode({"from_at": iso(days=-1), "until_at": iso(days=1)})
    metrics = p.ok(
        "transporte", "GET", "/api/v1/portal-metrics" + window, user="transport1"
    )
    assert metrics["scope"] == "Tareas propias"
    stages = next(s for s in metrics["series"] if s["title"] == "Traslados por etapa")
    assert shipment["id"] in own_ids(p)

    # Reasignado a otra cuenta, el traslado sale de las tres lecturas de transport1.
    with p.owner("transporte") as conn:
        conn.execute(
            "UPDATE shipments SET transport_user_id=%s WHERE id=%s",
            (other, shipment["id"]),
        )
    after = p.ok("transporte", "GET", "/api/v1/summary", user="transport1")
    assert after["total"] == summary["total"] - 1 == db_count(p, me)
    after_metrics = p.ok(
        "transporte", "GET", "/api/v1/portal-metrics" + window, user="transport1"
    )
    after_stages = next(
        s for s in after_metrics["series"] if s["title"] == "Traslados por etapa"
    )
    assert after_stages["denominator"] == stages["denominator"] - 1
    assert shipment["id"] not in own_ids(p)
    assert (
        p.request(
            "transporte",
            "GET",
            "/api/v1/shipments/" + shipment["id"],
            user="transport1",
        ).status_code
        == 403
    )


def test_summary_and_metrics_refuse_donor_and_anonymous(p):
    for path in ("/api/v1/summary", "/api/v1/portal-metrics"):
        assert p.request("transporte", "GET", path, user="donor1").status_code == 403
        assert p.request("transporte", "GET", path, user=None).status_code == 401


def test_transport_reports_are_limited_to_own_shipments(p):
    from ms_documentos.reports import hydrate
    from redhouse.db import get, transaction

    me = p.env.state["accounts"]["transport1"]["id"]
    foreign = planned(p)
    with p.owner("transporte") as conn:
        conn.execute(
            "UPDATE shipments SET transport_user_id=%s WHERE id=%s",
            (p.env.state["accounts"]["operator1"]["id"], foreign["id"]),
        )
    mine = planned(p)
    body = dict(
        report="SHIPMENTS",
        format="CSV",
        from_at=iso(days=-1),
        until_at=iso(days=1),
        timezone="America/Monterrey",
    )
    job = p.ok(
        "documentos", "POST", "/api/v1/export-jobs", user="transport1", data=body
    )
    assert job["user_id"] == me and job["report"] == "SHIPMENTS"

    # Solo el reporte de traslados; los demás siguen cerrados para TRANSPORT.
    for report in ("INVENTORY", "EXPIRY", "REQUESTS", "ACTIVITY"):
        denied = p.request(
            "documentos",
            "POST",
            "/api/v1/export-jobs",
            user="transport1",
            data=dict(body, report=report),
        )
        assert denied.status_code == 403, report

    # La extracción corre con la sesión del transportista: solo sus traslados.
    with p.apps["documentos"].app_context(), transaction() as conn:
        hydrated = hydrate(conn, get(conn, "export_jobs", job["id"], True))
    ids = {row["id"] for row in hydrated["rows"]}
    assert mine["id"] in ids and foreign["id"] not in ids
    assert ids <= own_ids(p)

    # Los trabajos de otra persona no se leen ni se listan.
    other = p.ok(
        "documentos", "POST", "/api/v1/export-jobs", user="operator1", data=body
    )
    assert (
        p.request(
            "documentos", "GET", "/api/v1/export-jobs/" + other["id"], user="transport1"
        ).status_code
        == 403
    )
    listed = p.ok("documentos", "GET", "/api/v1/export-jobs", user="transport1")
    assert listed["items"] and {row["user_id"] for row in listed["items"]} == {me}
    assert {row["report"] for row in listed["items"]} == {"SHIPMENTS"}


@pytest.mark.parametrize("report", ["SHIPMENTS"])
def test_report_window_is_bounded(p, report):
    too_long = dict(
        report=report,
        format="CSV",
        from_at=iso(days=-400),
        until_at=iso(days=1),
        timezone="America/Monterrey",
    )
    response = p.request(
        "documentos", "POST", "/api/v1/export-jobs", user="transport1", data=too_long
    )
    assert response.status_code == 422
