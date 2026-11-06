"""Exportación de instantáneas minimizadas. Propietarios conservan las consultas."""

import hashlib
from urllib.parse import urlencode
from uuid import NAMESPACE_URL, uuid4, uuid5

from flask import g
from redhouse.api import atomic, endpoint, listing
from redhouse.client import call
from redhouse.db import get, insert, transaction, update
from redhouse.errors import APIError
from redhouse.events import emit
from redhouse.extension_contracts import page_schema, schema
from redhouse.models import Confirm, utc_date
from redhouse.report_formats import MIMES, render
from redhouse.security import own
from redhouse.storage import bucket

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
        key: value for key, value in row.items() if key not in ("rows", "region_id")
    }


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
                content = render(job["rows"], job["format"])
                digest = hashlib.sha256(content).hexdigest()
                file_id = str(uuid5(NAMESPACE_URL, "redhouse:export:" + str(job["id"])))
                path = f"reports/{job['tenant_id']}/{file_id}"
                blob = bucket().blob(path)
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
                        "status": status,
                        "engine": "CLAMD_INSTREAM",
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
        start, end = utc_date(data["from_at"]), utc_date(data["until_at"])
        if start >= end or (end - start).days > 366:
            raise APIError("validation", "Ventana inválida o mayor de un año.", 422)
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
            for page in range(1, 11):
                result = call(
                    service,
                    "GET",
                    path + "?" + urlencode({"page": page, "page_size": 100, **filters}),
                )
                if result["total"] > 1000:
                    raise APIError(
                        "report_limit",
                        "Consulta supera 1000 registros; exportación masiva requiere proceso autorizado.",
                        422,
                    )
                rows.extend(result["items"])
                if len(rows) >= result["total"]:
                    break
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
                    "rows": rows,
                },
            )
            emit(
                conn,
                "EXPORT_REQUESTED",
                row["id"],
                row["tenant_id"],
                metadata={
                    "rows": len(rows),
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
                update(conn, "export_jobs", identifier, {"status": "PENDING"})
            )

        return atomic("export_retry:" + identifier, data, work)


# DTO compartido con el adaptador v1; no contiene acceso a datos.
from redhouse.document_contracts import Job, ReportCreate
