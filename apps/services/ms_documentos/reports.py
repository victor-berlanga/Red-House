"""Exportación de instantáneas minimizadas. Propietarios conservan las consultas."""

import hashlib
from datetime import datetime, timezone
from urllib.parse import urlencode
from uuid import NAMESPACE_URL, uuid4, uuid5
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from flask import current_app, g, request
from redhouse.api import atomic, endpoint, listing
from redhouse.client import call
from redhouse.db import get, insert, transaction, update
from redhouse.errors import APIError
from redhouse.events import emit
from redhouse.extension_contracts import page_schema, schema
from redhouse.models import Confirm, utc_date
from redhouse.report_formats import MIMES, render
from redhouse.security import own
from redhouse.storage import object_bucket, provider

SOURCES = {
    "INVENTORY": (
        "inventario",
        "/api/v1/resources",
        ("OPERATOR", "MEDICAL", "COORDINATOR"),
    ),
    "EXPIRY": (
        "inventario",
        "/api/v1/resources",
        ("OPERATOR", "MEDICAL", "COORDINATOR"),
    ),
    "REQUESTS": ("receptores", "/api/v1/requests", ("OPERATOR", "MEDICAL")),
    "SHIPMENTS": (
        "transporte",
        "/api/v1/shipments",
        ("OPERATOR", "MEDICAL", "COORDINATOR", "TRANSPORT"),
    ),
    "ACTIVITY": ("auditoria", "/api/v1/events", ("AUDITOR",)),
    "CUSTODY": (
        "custodia",
        "/api/v1/chains/",
        ("OPERATOR", "MEDICAL", "COORDINATOR", "TRANSPORT", "AUDITOR"),
    ),
    "TRACEABILITY": ("inventario", "/api/v1/resources/", ("MEDICAL",)),
}
FIELDS = (
    "id",
    "folio",
    "kind",
    "component",
    "status",
    "expires_at",
    "created_at",
    "departure_at",
    "eta",
    "action",
    "source",
    "collected_at",
    "accepted_at",
    "observed_seconds",
)


def report_authorized(report):
    if g.actor["role"] not in SOURCES[report][2]:
        raise APIError("forbidden", "Perfil no autorizado para este reporte.", 403)


def public(row):
    return {
        key: value
        for key, value in row.items()
        if key not in ("rows", "region_id", "sealed_authorization", "storage_provider")
    }


def authorization_cipher():
    import base64

    from cryptography.fernet import Fernet

    secret = current_app.config["SERVICE_PRIVATE_KEY"]
    return Fernet(
        base64.urlsafe_b64encode(
            hashlib.sha256(("export-job:" + secret).encode()).digest()
        )
    )


def seal_authorization():
    return (
        authorization_cipher()
        .encrypt(request.headers["Authorization"].encode())
        .decode()
    )


def hydrate(conn, job):
    """Extracción paginada en worker, con sesión vigente y credencial cifrada."""
    if job["context"] and job["context"].get("row_count") is None:
        try:
            g.worker_authorization = (
                authorization_cipher()
                .decrypt(job["sealed_authorization"].encode())
                .decode()
            )
            actor = call("identidad_acceso", "GET", "/api/v1/auth/me")
            g.actor = actor
            if (
                str(job["user_id"]) != actor["id"]
                or str(job["tenant_id"]) != actor["tenant_id"]
            ):
                raise APIError(
                    "forbidden", "El ámbito cambió; solicite otro reporte.", 403
                )
            report_authorized(job["report"])
            rows = collect(job["context"])
            context = dict(
                job["context"],
                row_count=len(rows),
                extracted_at=datetime.now(timezone.utc).isoformat(),
            )
            job = update(
                conn,
                "export_jobs",
                job["id"],
                {"rows": rows, "context": context, "sealed_authorization": None},
            )
        finally:
            g.worker_authorization = None
    return job


def process(limit=3):
    from google.api_core.exceptions import PreconditionFailed
    from redhouse.malware import scan

    for _ in range(limit):
        with transaction() as conn:
            job = conn.execute(
                "SELECT * FROM export_jobs WHERE status='PENDING' ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 1"
            ).fetchone()
            if not job:
                break
            g.actor = {
                "id": str(job["user_id"]),
                "role": None,
                "tenant_id": str(job["tenant_id"]),
                "region_id": str(job["region_id"]) if job["region_id"] else None,
            }
            try:
                job = hydrate(conn, job)
                content = render(job["rows"], job["format"], job["context"])
                digest = hashlib.sha256(content).hexdigest()
                file_id = str(uuid5(NAMESPACE_URL, "redhouse:export:" + str(job["id"])))
                path = f"reports/{job['tenant_id']}/{file_id}"
                selected = job["storage_provider"]
                blob = object_bucket(selected).blob(path)
                try:
                    blob.upload_from_string(
                        content,
                        content_type=MIMES[job["format"]],
                        if_generation_match=0,
                        timeout=8,
                        retry=None,
                    )
                except PreconditionFailed:
                    blob.reload(timeout=8, retry=None)
                    if (
                        hashlib.sha256(
                            blob.download_as_bytes(
                                if_generation_match=blob.generation,
                                timeout=8,
                                retry=None,
                            )
                        ).hexdigest()
                        != digest
                    ):
                        raise APIError(
                            "export_conflict",
                            "Objeto existente no coincide con esta exportación.",
                            409,
                        )
                status = scan(content)
                if status != "CLEAN":
                    raise APIError(
                        "malware_detected", "Exportación rechazada por el motor.", 422
                    )
                insert(
                    conn,
                    "files",
                    {
                        "id": file_id,
                        "shipment_id": None,
                        "owner_id": job["user_id"],
                        "object_path": path,
                        "storage_provider": selected,
                        "mime_type": MIMES[job["format"]],
                        "size": len(content),
                        "sha256": digest,
                        "generation": str(blob.generation),
                        "status": "VERIFIED",
                    },
                )
                insert(
                    conn,
                    "document_metadata",
                    {
                        "id": file_id,
                        "tenant_id": job["tenant_id"],
                        "category": "REPORT",
                        "subject_kind": "REPORT",
                        "subject_id": job["id"],
                        "version": 1,
                        "policy_reference": "OPERATIVE-EXPORT-1; retención pendiente de política institucional",
                    },
                )
                insert(
                    conn,
                    "file_scans",
                    {
                        "id": str(uuid4()),
                        "file_id": file_id,
                        "generation": str(blob.generation),
                        "sha256": digest,
                        "status": str(status),
                        "engine": "CLAMD_INSTREAM",
                        **status.metadata,
                    },
                )
                update(
                    conn,
                    "export_jobs",
                    job["id"],
                    {
                        "status": "COMPLETE",
                        "file_id": file_id,
                        "attempts": job["attempts"] + 1,
                        "last_error": None,
                    },
                )
                emit(conn, "EXPORT_COMPLETED", job["id"], job["tenant_id"])
            except Exception as exc:
                # Dependencias externas pueden fallar tras subir el objeto. Su ruta
                # determinista permite recuperar sin crear otro objeto ni confirmar antes.
                code = (
                    exc.code
                    if isinstance(exc, APIError)
                    else "export_dependency_unavailable"
                )
                update(
                    conn,
                    "export_jobs",
                    job["id"],
                    {
                        "status": "RETRYABLE",
                        "last_error": code,
                        "attempts": job["attempts"] + 1,
                    },
                )


def collect(data):
    start, end = utc_date(data["from_at"]), utc_date(data["until_at"])
    service, path, _ = SOURCES[data["report"]]
    rows = []
    date_key = (
        "expires_at"
        if data["report"] == "EXPIRY"
        else "departure_at"
        if data["report"] == "SHIPMENTS"
        else "created_at"
    )
    # Consultas de los propietarios: mismas reglas de visibilidad que JSON/XML.
    if data["report"] in ("CUSTODY", "TRACEABILITY"):
        if not data["subject_id"]:
            raise APIError(
                "validation", "Identificador de cadena o recurso requerido.", 422
            )
        result = call(
            service,
            "GET",
            path
            + data["subject_id"]
            + ("/trace" if data["report"] == "TRACEABILITY" else ""),
        )
        for item in result["events"]:
            event = item.get("event", item)
            rows.append(
                {
                    "id": item["id"],
                    "source": event["source"],
                    "action": event["action"],
                    "created_at": event["occurred_at"],
                }
            )
    else:
        if data["subject_id"]:
            raise APIError(
                "validation",
                "Este reporte no admite identificador individual.",
                422,
            )
        filters = (
            {"from": data["from_at"], "to": data["until_at"]}
            if data["report"] == "ACTIVITY"
            else {
                "from_at": data["from_at"],
                "until_at": data["until_at"],
                "date_field": date_key,
                "sort": data["order"],
            }
        )
        filters.update(data["filters"])
        total = None
        for page in range(1, 501):
            result = call(
                service,
                "GET",
                path + "?" + urlencode({"page": page, "page_size": 100, **filters}),
            )
            if result["total"] > 50000:
                raise APIError(
                    "report_limit",
                    "Consulta supera 50000 registros; reduzca el periodo. No se generó un reporte parcial.",
                    422,
                )
            if total is not None and total != result["total"]:
                raise APIError(
                    "conflict",
                    "La población cambió durante la extracción; repita la consulta.",
                    409,
                )
            total = result["total"]
            rows.extend(result["items"])
            if len(rows) >= result["total"]:
                break
        if len(rows) != total or len({r["id"] for r in rows}) != len(rows):
            raise APIError(
                "conflict",
                "Extracción inconsistente; no se generó un reporte parcial.",
                409,
            )
    if data["report"] == "ACTIVITY":
        rows = [{**row, "created_at": row["event"]["occurred_at"]} for row in rows]
    date_key = (
        "expires_at"
        if data["report"] == "EXPIRY"
        else "departure_at"
        if data["report"] == "SHIPMENTS"
        else "created_at"
    )
    rows = [
        {k: str(r[k]) for k in FIELDS if k in r and r[k] is not None}
        for r in rows
        if r.get(date_key) and start <= utc_date(r[date_key]) < end
    ]
    rows.sort(
        key=lambda r: (
            r.get("id", "") if data["order"] == "ID_ASC" else r.get(date_key, "")
        ),
        reverse=data["order"] == "DATE_DESC",
    )

    return rows


def install(app):
    @endpoint(
        app,
        "/api/v1/export-jobs",
        "POST",
        model=ReportCreate,
        status=202,
        result=schema(Job),
    )
    def export_create(data):
        report_authorized(data["report"])
        try:
            ZoneInfo(data["timezone"])
        except (ValueError, ZoneInfoNotFoundError):
            raise APIError("validation", "Zona horaria desconocida.", 422)
        allowed_filters = {
            "INVENTORY": {"q", "status", "kind", "component"},
            "EXPIRY": {"q", "status", "kind", "component"},
            "REQUESTS": {"q", "status", "kind"},
            "SHIPMENTS": {"q", "status"},
            "ACTIVITY": {"source", "action"},
        }.get(data["report"], set())
        if set(data["filters"]) - allowed_filters:
            raise APIError("validation", "Filtro no admitido por este reporte.", 422)
        start, end = utc_date(data["from_at"]), utc_date(data["until_at"])
        if start >= end or (end - start).days > 366:
            raise APIError("validation", "Ventana inválida o mayor de un año.", 422)
        service, path, _ = SOURCES[data["report"]]
        if data["report"] in ("CUSTODY", "TRACEABILITY"):
            if not data["subject_id"]:
                raise APIError(
                    "validation", "Identificador de cadena o recurso requerido.", 422
                )
            call(
                service,
                "GET",
                path
                + data["subject_id"]
                + ("/trace" if data["report"] == "TRACEABILITY" else ""),
            )
        else:
            if data["subject_id"]:
                raise APIError(
                    "validation", "Este reporte no admite sujeto individual.", 422
                )
            call(
                service,
                "GET",
                path + "?" + urlencode({"page_size": 1, **data["filters"]}),
            )

        def work(conn):
            row = insert(
                conn,
                "export_jobs",
                {
                    "id": str(uuid4()),
                    "tenant_id": g.actor["tenant_id"],
                    "user_id": g.actor["id"],
                    "region_id": g.actor["region_id"],
                    "report": data["report"],
                    "format": data["format"],
                    "storage_provider": provider(),
                    "rows": [],
                    "sealed_authorization": seal_authorization(),
                    "context": {
                        "render_version": 2,
                        "report": data["report"],
                        "filters": data["filters"],
                        "subject_id": data["subject_id"],
                        "order": data["order"],
                        "from_at": data["from_at"],
                        "until_at": data["until_at"],
                        "timezone": data["timezone"],
                        "tenant_id": g.actor["tenant_id"],
                        "region_id": g.actor["region_id"],
                        "role": g.actor["role"],
                        "extracted_at": datetime.now(timezone.utc).isoformat(),
                        "row_count": None,
                        "date_field": "expires_at"
                        if data["report"] == "EXPIRY"
                        else "departure_at"
                        if data["report"] == "SHIPMENTS"
                        else "created_at",
                    },
                },
            )
            emit(
                conn,
                "EXPORT_REQUESTED",
                row["id"],
                row["tenant_id"],
                metadata={
                    "rows": None,
                    "format": data["format"],
                    "regulatory_certification": False,
                },
            )
            return public(row)

        return atomic("export_create", data, work)

    @endpoint(
        app,
        "/api/v1/export-jobs",
        result=page_schema(Job),
        paginated=True,
        query=(
            "q",
            "report",
            "format",
            "status",
            "from_at",
            "until_at",
            "date_field",
            "sort",
        ),
    )
    def export_list():
        allowed = [
            name for name, (_, _, roles) in SOURCES.items() if g.actor["role"] in roles
        ]
        with transaction() as conn:
            result = listing(
                conn,
                "export_jobs",
                "user_id=%s AND tenant_id=%s AND report=ANY(%s)",
                (g.actor["id"], g.actor["tenant_id"], allowed),
                filters={
                    "q": ("id::text",),
                    "report": ("report", tuple(SOURCES)),
                    "format": ("format", tuple(MIMES)),
                    "status": ("status", ("PENDING", "COMPLETE", "FAILED")),
                },
            )
            result["items"] = [public(r) for r in result["items"]]
            return result

    def authorized(conn, identifier):
        row = get(conn, "export_jobs", identifier, True)
        own(row["tenant_id"])
        if str(row["user_id"]) != g.actor["id"]:
            raise APIError("forbidden", "Trabajo de otro usuario.", 403)
        report_authorized(row["report"])
        return row

    @endpoint(app, "/api/v1/export-jobs/<identifier>", result=schema(Job))
    def export_detail(identifier):
        with transaction() as conn:
            return public(authorized(conn, identifier))

    @endpoint(
        app,
        "/api/v1/export-jobs/<identifier>/retry",
        "POST",
        model=Confirm,
        result=schema(Job),
        status=202,
    )
    def export_retry(identifier, data):
        def work(conn):
            row = authorized(conn, identifier)
            if row["status"] != "RETRYABLE":
                raise APIError("conflict", "El trabajo no requiere reintento.", 409)
            emit(conn, "EXPORT_RETRY_REQUESTED", identifier, row["tenant_id"])
            return public(
                update(
                    conn,
                    "export_jobs",
                    identifier,
                    {"status": "PENDING", "sealed_authorization": seal_authorization()},
                )
            )

        return atomic("export_retry:" + identifier, data, work)


# DTO compartido con el adaptador v1; no contiene acceso a datos.
from redhouse.document_contracts import Job, ReportCreate
