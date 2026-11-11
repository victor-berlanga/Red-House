"""Aceptación del portal corregido, con propietarios y almacenes aislados reales."""

import hashlib
import json

from .helpers import resource, recipient_request, evaluation
from .test_web_integration import web as web, login, form
from .test_web_integration import post
from .helpers import iso
from uuid import uuid4
from .test_continuity import autonomous as autonomous


def test_publication_without_api_listeners(autonomous, p):
    client = login(autonomous, p, "admin1")
    description = "Institución publicada " + uuid4().hex
    post(
        client,
        "/configuracion/institucion",
        dict(
            published="on",
            synthetic="on",
            description=description,
            human_confirmation="on",
            reason="Publicación sintética",
        ),
    )
    current = p.ok(
        "identidad_acceso",
        "GET",
        "/api/v1/institutions/" + p.env.state["tenants"][0] + "/presentation",
        user="admin1",
    )
    assert current["published"] and current["description"] == description
    assert description in client.get("/").text


def test_configuration_publication_privacy_versions_and_metrics(p, web):
    admin = login(web, p, "admin1")
    post(
        admin,
        "/configuracion/politica",
        dict(
            timezone="America/Monterrey",
            tracking_interval_seconds=10,
            tracking_stale_seconds=30,
            reference="Política sintética de aceptación",
            human_confirmation="on",
            reason="Verificación local",
        ),
    )
    saved = p.ok("identidad_acceso", "GET", "/api/v1/portal-policy", user="admin1")
    assert saved["version"] == 1
    assert login(web, p, "donor1").get("/configuracion/politica").status_code == 403
    assert admin.get("/configuracion").status_code == 200
    for owner, user in (
        ("donantes", "operator1"),
        ("inventario", "operator1"),
        ("receptores", "medical1"),
        ("compatibilidad", "operator1"),
        ("transporte", "transport1"),
    ):
        result = p.ok(owner, "GET", "/api/v1/portal-metrics", user=user)
        assert result["series"] and all(s["denominator"] >= 0 for s in result["series"])
        assert (
            p.request(owner, "GET", "/api/v1/portal-metrics", user="donor1").status_code
            == 403
        )
    assert login(web, p, "medical1").get("/laboratorio/muestras").status_code == 200
    unit = resource(p)
    assert (
        b"data:image/svg+xml;base64,"
        in login(web, p, "operator1")
        .get("/inventario/" + unit["id"] + "/etiqueta")
        .data
    )


def test_paginated_export_over_thousand_filters_context_and_foreign_denial(p):
    from redhouse.report_formats import render
    import csv
    import io

    unit = resource(p)
    prefix = "EXPORT-" + uuid4().hex[:8]
    with p.owner("inventario") as conn:
        cursor = conn.execute("SELECT * FROM resources WHERE id=%s", (unit["id"],))
        names = [c.name for c in cursor.description]
        original = list(cursor.fetchone())
        rows = []
        for n in range(1003):
            row = list(original)
            row[names.index("id")] = uuid4()
            row[names.index("folio")] = prefix + str(n)
            # Volumen de exportación, no candidatos liberados para otros casos
            # que comparten el fixture de sesión.
            row[names.index("status")] = "QUARANTINE"
            rows.append(row)
        with conn.cursor() as cursor:
            cursor.executemany(
                "INSERT INTO resources("
                + ",".join(names)
                + ") VALUES("
                + ",".join(["%s"] * len(names))
                + ")",
                rows,
            )
    job = p.ok(
        "documentos",
        "POST",
        "/api/v1/export-jobs",
        user="operator1",
        data=dict(
            report="INVENTORY",
            format="CSV",
            from_at=iso(days=-1),
            until_at=iso(days=1),
            filters={"q": prefix},
            timezone="America/Monterrey",
            order="ID_ASC",
        ),
    )
    assert job["context"]["row_count"] is None
    from ms_documentos.reports import hydrate
    from redhouse.db import transaction, get

    with p.apps["documentos"].app_context(), transaction() as conn:
        hydrated = hydrate(conn, get(conn, "export_jobs", job["id"], True))
        assert hydrated["context"]["row_count"] == 1003
        assert hydrated["sealed_authorization"] is None
    assert (
        p.request(
            "documentos", "GET", "/api/v1/export-jobs/" + job["id"], user="operator2"
        ).status_code
        == 403
    )
    with p.owner("documentos") as conn:
        rows, context = conn.execute(
            "SELECT rows,context FROM export_jobs WHERE id=%s", (job["id"],)
        ).fetchone()
    parsed = list(
        csv.DictReader(io.StringIO(render(rows, "CSV", context).decode("utf-8-sig")))
    )
    assert len(parsed) == 1003 and all(
        r["reporte_timezone"] == "America/Monterrey" for r in parsed
    )
    assert all(
        r["folio"].startswith(prefix) and r["created_at"].endswith("-06:00")
        for r in parsed
    )


def test_pending_confirmation_web_recovers_same_command_without_false_success(
    p, web, monkeypatch
):
    from ms_inventario import routes
    from redhouse.errors import APIError

    unit = resource(p)
    _, req = recipient_request(p)
    ev = evaluation(p, req, [unit])
    client = login(web, p, "medical2")
    path = f"/evaluaciones/{ev['id']}/reservar/{unit['id']}"
    values = form(client, path)
    values.update(
        human_confirmation="on", reason="Reserva sintética con respuesta perdida"
    )
    real = routes.call
    blocked = True

    def lose_confirmation(service, method, path, data=None, **kwargs):
        result = real(service, method, path, data, **kwargs)
        if (
            blocked
            and service == "receptores"
            and data
            and data.get("action") == "CONFIRM"
        ):
            raise APIError("dependency_unavailable", "Respuesta perdida de prueba", 503)
        return result

    monkeypatch.setattr(routes, "call", lose_confirmation)
    response = client.post(path, data=values, follow_redirects=True)
    assert response.status_code == 200
    assert "pendiente de confirmación" in response.text
    assert "operación completada" not in response.text
    assert "Operación finalizada y confirmada" not in response.text
    with p.owner("inventario") as conn:
        row = conn.execute(
            "SELECT id,status FROM operations WHERE key=%s",
            (values["idempotency_key"],),
        ).fetchone()
        assert row[1] == "PENDING"
    # Reenvío consulta el mismo comando; no intenta confirmarlo otra vez.
    duplicate = client.post(path, data=values, follow_redirects=True)
    assert duplicate.status_code == 200
    altered = client.post(
        path, data={**values, "reason": "Contenido distinto con la misma clave"}
    )
    assert altered.status_code == 409
    blocked = False
    resume = f"/operaciones/{row[0]}/reanudar"
    response = client.post(resume, data=form(client, resume), follow_redirects=True)
    assert "Operación finalizada y confirmada" in response.text
    with p.owner("inventario") as conn:
        assert (
            conn.execute(
                "SELECT count(*) FROM reservations WHERE operation_id=%s", (row[0],)
            ).fetchone()[0]
            == 1
        )
    data = dict(
        evaluation_id=ev["id"],
        resource_id=unit["id"],
        reason=values["reason"],
        human_confirmation=True,
    )
    digest = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
    assert (
        p.request(
            "inventario",
            "GET",
            f"/api/v1/operations/by-key/{values['idempotency_key']}?fingerprint={digest}",
            user="medical1",
        ).status_code
        == 404
    )


def test_export_worker_rechecks_revoked_session_before_extraction(p):
    from ms_documentos.reports import process

    name = "export-worker-" + uuid4().hex[:10]
    created = p.ok(
        "identidad_acceso",
        "POST",
        "/api/v1/users",
        user="admin1",
        data={
            "username": name,
            "password": p.env.state["password"],
            "tenant_id": p.env.state["tenants"][0],
            "role": "OPERATOR",
        },
    )
    auth = p.ok(
        "identidad_acceso",
        "POST",
        "/api/v1/auth/login",
        user=None,
        data={"username": name, "password": p.env.state["password"]},
    )
    p.tokens[name] = auth["access_token"]
    job = p.ok(
        "documentos",
        "POST",
        "/api/v1/export-jobs",
        user=name,
        data={
            "report": "INVENTORY",
            "format": "CSV",
            "from_at": iso(days=-1),
            "until_at": iso(days=1),
        },
    )
    p.ok(
        "identidad_acceso",
        "POST",
        "/api/v1/users/" + created["id"] + "/role",
        user="admin1",
        data={
            "version": created["version"],
            "role": "DONOR",
            "reason": "Retirar facultad de exportación",
            "human_confirmation": True,
        },
    )
    with p.apps["documentos"].app_context():
        process(limit=10)
    with p.owner("documentos") as conn:
        state, file_id, context = conn.execute(
            "SELECT status,file_id,context FROM export_jobs WHERE id=%s", (job["id"],)
        ).fetchone()
    assert state == "RETRYABLE" and file_id is None and context["row_count"] is None
    assert (
        p.request(
            "documentos", "GET", "/api/v1/export-jobs/" + job["id"], user=name
        ).status_code
        == 401
    )


def test_web_lost_entire_write_response_queries_result_without_second_post(
    p, web, monkeypatch
):
    from src.integration.routes import common
    from src.access import BusinessError

    unit = resource(p)
    _, req = recipient_request(p)
    ev = evaluation(p, req, [unit])
    client = login(web, p, "medical2")
    path = f"/evaluaciones/{ev['id']}/reservar/{unit['id']}"
    values = form(client, path)
    values.update(
        human_confirmation="on", reason="Respuesta completa perdida después de escribir"
    )
    real = common.call
    writes = []

    def lose(service, path, method="GET", *args, **kwargs):
        result = real(service, path, method, *args, **kwargs)
        if path == "/api/v1/reservations" and method == "POST":
            writes.append(result["operation_id"])
            raise BusinessError("Respuesta incierta", 503)
        return result

    monkeypatch.setattr(common, "call", lose)
    response = client.post(path, data=values, follow_redirects=True)
    assert response.status_code == 200
    assert "Operación finalizada y confirmada" in response.text
    assert len(writes) == 1
    client.post(path, data=values)
    assert len(writes) == 1


def test_coordinator_reads_regional_proposal_without_clinical_authority(p):
    unit = resource(p)
    _, req = recipient_request(p)
    ev = evaluation(p, req, [unit])
    proposal = p.ok(
        "priorizacion_geografia",
        "POST",
        "/api/v1/allocation-proposals",
        data={"evaluation_ids": [ev["id"]]},
    )
    path = "/api/v1/allocation-proposals/" + proposal["id"]
    logistics = p.ok("priorizacion_geografia", "GET", path, user="coordinator1")
    assert logistics["snapshots"] == {} and logistics["matched_count"] == 1
    rows = p.ok(
        "priorizacion_geografia",
        "GET",
        "/api/v1/allocation-proposals",
        user="coordinator1",
    )
    assert any(row["id"] == proposal["id"] for row in rows["items"])
    assert (
        p.request("priorizacion_geografia", "GET", path, user="medical1").status_code
        == 403
    )
    assert (
        p.request(
            "priorizacion_geografia",
            "POST",
            "/api/v1/allocation-proposals",
            user="coordinator1",
            data={"evaluation_ids": [ev["id"]]},
        ).status_code
        == 403
    )


def test_organ_authorization_form_keeps_history(p, web):
    _, req = recipient_request(p, kind="ORGAN", component="KIDNEY", group="O+")
    client = login(web, p, "medical2")
    path = "/solicitudes/" + req["id"] + "/constancias/nueva"
    assert client.get(path).status_code == 200
    post(
        client,
        path,
        dict(
            authority="Autoridad ficticia",
            reference="Constancia sintética",
            decision="RECORDED",
            valid_from="2026-11-01T00:00",
            valid_until="2027-01-01T00:00",
            effective_at="2026-11-01T00:00",
            human_confirmation="on",
            reason="Ensayo del formulario",
        ),
    )
    history = p.ok(
        "receptores",
        "GET",
        "/api/v1/requests/" + req["id"] + "/external-authorizations",
    )
    assert len(history["items"]) == 1 and history["items"][0]["decision"] == "RECORDED"


def test_page_csv_distinguishes_account_institution_from_authorized_scope(web, p):
    import csv
    import io

    unit = resource(p)
    coordinator = login(web, p, "coordinator1")
    response = coordinator.get("/inventario?format=csv&q=" + unit["folio"])
    assert response.status_code == 200
    rows = list(csv.DictReader(io.StringIO(response.data.decode("utf-8-sig"))))
    assert len(rows) == 1 and rows[0]["Folio"] == unit["folio"]
    scope = json.loads(rows[0]["Ámbito"])
    assert scope["perfil"] == "COORDINATOR"
    assert scope["institucion_de_cuenta"] and scope["region"]
    assert "autorizados" in scope["criterio"]
    assert json.loads(rows[0]["Filtros"])["q"] == unit["folio"]
    assert rows[0]["Total filtrado"] == "1"
    foreign = login(web, p, "operator2").get(
        "/inventario?format=csv&q=" + unit["folio"]
    )
    assert foreign.status_code == 200
    assert not list(csv.DictReader(io.StringIO(foreign.data.decode("utf-8-sig"))))
    assert login(web, p, "donor1").get("/inventario?format=csv").status_code == 403
