"""Metadatos generales sobre los mismos stored_file y objetos privados GCS."""

from datetime import datetime, timezone
from uuid import uuid4

from flask import g
from redhouse.api import atomic, endpoint, listing
from redhouse.client import call
from redhouse.db import get, insert, transaction
from redhouse.errors import APIError
from redhouse.events import emit
from redhouse.extension_contracts import page_schema, schema
from redhouse.models import ID, Model, utc_date
from redhouse.security import own
from redhouse.storage import access_url, object_bucket, provider, upload_headers

ROLES = ("ADMIN", "MEDICAL", "OPERATOR", "COORDINATOR", "TRANSPORT", "DONOR")
SUBJECTS = {
    "RULE": ("compatibilidad", "/api/v1/laboratory/profiles/"),
    "DONOR": ("donantes", "/api/v1/donors/"),
    "RESULT": ("compatibilidad", "/api/v1/laboratory/results/"),
    "ACCREDITATION": ("identidad_acceso", "/api/v1/accreditations/"),
    "REQUEST": ("receptores", "/api/v1/requests/"),
}
CATEGORIES = {
    "RULE": "RULE_APPROVAL",
    "DONOR": "CONSENT",
    "RESULT": "LAB_RESULT",
    "ACCREDITATION": "ACCREDITATION",
    "REQUEST": "AUTHORIZATION",
}


def subject_access(kind, identifier):
    service, path = SUBJECTS[kind]
    row = call(service, "GET", path + identifier)
    own(row["tenant_id"])
    return row


def shipment_access(identifier):
    # El propietario valida JWT, institución, perfil y responsable actual.
    return call("transporte", "GET", "/api/v1/shipments/" + str(identifier))


def file_access(conn, row, shipment_access):
    if row["shipment_id"]:
        return shipment_access(str(row["shipment_id"]))
    metadata = get(conn, "document_metadata", str(row["id"]))
    own(metadata["tenant_id"])
    if metadata["subject_kind"] == "REPORT":
        job = get(conn, "export_jobs", str(metadata["subject_id"]))
        if str(job["user_id"]) != g.actor["id"]:
            raise APIError("forbidden", "Exportación de otro usuario.", 403)
        from .reports import report_authorized

        report_authorized(job["report"])
    else:
        subject_access(metadata["subject_kind"], str(metadata["subject_id"]))
    return {"origin_id": metadata["tenant_id"], "status": "DOCUMENT"}


def require_clean(conn, row):
    found = conn.execute(
        "SELECT status FROM file_scans WHERE file_id=%s AND generation=%s AND sha256=%s ORDER BY created_at DESC,id DESC LIMIT 1",
        (row["id"], row["generation"], row["sha256"]),
    ).fetchone()
    if not found or found["status"] != "CLEAN":
        raise APIError(
            "analysis_required",
            "Documento sin análisis limpio de esta generación.",
            409,
        )


class TransportCheck(Model):
    shipment_id: ID


def install(app):
    from redhouse.document_contracts import DocumentStatus, ConservationChange
    from redhouse.db import update
    from redhouse.decisions import record

    @endpoint(
        app,
        "/api/v1/documents/<identifier>/status",
        roles=ROLES,
        result=schema(DocumentStatus),
    )
    def document_status(identifier):
        with transaction() as conn:
            file = get(conn, "files", identifier)
            file_access(conn, file, shipment_access)
            metadata = get(conn, "document_metadata", identifier)
            scan = conn.execute(
                "SELECT status FROM file_scans WHERE file_id=%s AND generation=%s AND sha256=%s ORDER BY created_at DESC,id DESC LIMIT 1",
                (identifier, file["generation"], file["sha256"]),
            ).fetchone()
            return dict(
                metadata,
                file_status=file["status"],
                analysis=scan["status"] if scan else "PENDING",
            )

    @endpoint(
        app,
        "/api/v1/documents/<identifier>/conservation",
        "POST",
        roles=("ADMIN", "MEDICAL"),
        model=ConservationChange,
        result=schema(Metadata),
    )
    def document_conservation(identifier, data):
        until = utc_date(data["retention_until"]) if data["retention_until"] else None
        if until and until < datetime.now(timezone.utc):
            raise APIError("validation", "La conservación debe ser futura.", 422)

        def work(conn):
            file_access(conn, get(conn, "files", identifier), shipment_access)
            meta = get(conn, "document_metadata", identifier, True)
            if meta["policy_version"] != data["policy_version"]:
                raise APIError(
                    "stale_version", "Política de conservación modificada.", 412
                )
            if (
                meta["legal_hold"]
                and meta["retention_until"]
                and (until is None or until < meta["retention_until"])
            ):
                raise APIError(
                    "legal_hold", "El bloqueo vigente impide reducir conservación.", 409
                )
            values = dict(
                retention_until=until,
                legal_hold=data["legal_hold"],
                policy_reference=data["policy_reference"],
                policy_version=meta["policy_version"] + 1,
            )
            row = update(conn, "document_metadata", identifier, values)
            record(
                conn,
                identifier,
                meta["tenant_id"],
                "DOCUMENT_CONSERVATION_CHANGED",
                data["reason"],
                {**values, "retention_until": until.isoformat() if until else None},
            )
            emit(conn, "DOCUMENT_CONSERVATION_CHANGED", identifier, meta["tenant_id"])
            return row

        return atomic("document_conservation:" + identifier, data, work)

    @endpoint(
        app,
        "/internal/v1/files/<identifier>/transport-check",
        "POST",
        model=TransportCheck,
        internal=("transporte",),
        delegate=False,
        result={
            "type": "object",
            "properties": {"verified": {"type": "boolean"}},
            "required": ["verified"],
        },
    )
    def file_transport_check(identifier, data):
        # No callback a Transporte: evita recursión mientras este bloquea su orden.
        with transaction() as conn:
            row = get(conn, "files", identifier)
            if (
                str(row["shipment_id"]) != data["shipment_id"]
                or row["status"] != "VERIFIED"
            ):
                raise APIError(
                    "conflict", "Evidencia no verificada para este traslado.", 409
                )
            require_clean(conn, row)
            return {"verified": True}

    @endpoint(
        app,
        "/api/v1/documents",
        "POST",
        model=DocumentCreate,
        roles=ROLES,
        status=201,
        result=schema(Prepared),
    )
    def document_prepare(data):
        subject_access(data["subject_kind"], data["subject_id"])
        if CATEGORIES[data["subject_kind"]] != data["category"]:
            raise APIError(
                "validation", "Categoría incompatible con el propietario.", 422
            )
        retention = (
            utc_date(data["retention_until"]) if data["retention_until"] else None
        )
        if retention and retention < datetime.now(timezone.utc):
            raise APIError(
                "validation", "Retención no puede ser anterior a la preparación.", 422
            )
        selected = provider()
        object_bucket(selected)

        def work(conn):
            conn.execute(
                "SELECT pg_advisory_xact_lock(hashtextextended(%s,73))",
                (data["subject_id"],),
            )
            previous = (
                get(conn, "document_metadata", data["supersedes"])
                if data["supersedes"]
                else None
            )
            if previous:
                own(previous["tenant_id"])
                if (
                    str(previous["subject_id"]) != data["subject_id"]
                    or previous["subject_kind"] != data["subject_kind"]
                    or conn.execute(
                        "SELECT 1 FROM document_metadata WHERE supersedes=%s",
                        (previous["id"],),
                    ).fetchone()
                ):
                    raise APIError(
                        "stale_version",
                        "Sustitución documental incompatible u obsoleta.",
                        412,
                    )
            identifier = str(uuid4())
            row = insert(
                conn,
                "files",
                {
                    "id": identifier,
                    "owner_id": g.actor["id"],
                    "shipment_id": None,
                    "object_path": f"documents/{g.actor['tenant_id']}/{identifier}",
                    "storage_provider": selected,
                    **{k: data[k] for k in ("mime_type", "size", "sha256")},
                },
            )
            meta = insert(
                conn,
                "document_metadata",
                {
                    "id": identifier,
                    "tenant_id": g.actor["tenant_id"],
                    "version": previous["version"] + 1 if previous else 1,
                    "retention_until": retention,
                    **{
                        k: data[k]
                        for k in (
                            "category",
                            "subject_kind",
                            "subject_id",
                            "supersedes",
                            "policy_reference",
                        )
                    },
                },
            )
            emit(conn, "DOCUMENT_PREPARED", identifier, g.actor["tenant_id"])
            return {"row": row, "metadata": meta}

        result = atomic("document_prepare", data, work)
        # Resultados idempotentes históricos preceden al campo de proveedor.
        with transaction() as conn:
            result["row"] = get(conn, "files", result["row"]["id"])
        return {
            "id": result["row"]["id"],
            "metadata": result["metadata"],
            "upload_url": access_url(result["row"], "PUT"),
            "expires_in": 300,
            "upload_headers": upload_headers(result["row"]),
        }

    @endpoint(
        app,
        "/api/v1/documents/<identifier>/verified",
        roles=ROLES,
        result=schema(VerifiedMetadata),
    )
    def document_verified(identifier):
        with transaction() as conn:
            file = get(conn, "files", identifier)
            file_access(conn, file, shipment_access)
            if file["status"] != "VERIFIED":
                raise APIError(
                    "verification_required", "Documento pendiente o rechazado.", 409
                )
            require_clean(conn, file)
            metadata = get(conn, "document_metadata", identifier)
            return dict(
                metadata,
                generation=file["generation"],
                sha256=file["sha256"],
                analysis="CLEAN",
                file_status=file["status"],
            )

    @endpoint(
        app, "/api/v1/documents/<identifier>", roles=ROLES, result=schema(Metadata)
    )
    def document_detail(identifier):
        with transaction() as conn:
            file_access(conn, get(conn, "files", identifier), shipment_access)
            return get(conn, "document_metadata", identifier)

    @endpoint(
        app,
        "/api/v1/documents",
        roles=ROLES,
        paginated=True,
        query=(
            "subject_kind",
            "subject_id",
            "category",
            "legal_hold",
            "q",
            "from_at",
            "until_at",
            "date_field",
            "sort",
        ),
        result=page_schema(Metadata),
    )
    def document_list():
        from flask import request
        from redhouse.models import validate_id

        kind = request.args.get("subject_kind")
        identifier = validate_id(request.args.get("subject_id", ""))
        if kind not in SUBJECTS:
            raise APIError("validation", "Propietario documental requerido.", 422)
        subject_access(kind, identifier)
        with transaction() as conn:
            return listing(
                conn,
                "document_metadata",
                "tenant_id=%s AND subject_kind=%s AND subject_id=%s",
                (g.actor["tenant_id"], kind, identifier),
                filters={
                    "subject_kind": ("subject_kind", tuple(SUBJECTS)),
                    "subject_id": ("subject_id", ()),
                    "category": ("category", tuple(CATEGORIES.values())),
                    "legal_hold": ("legal_hold", {"true": True, "false": False}),
                    "q": ("policy_reference", "id::text"),
                },
            )


# DTO compartido con el adaptador v1; no contiene acceso a datos.
from redhouse.document_contracts import (
    DocumentCreate,
    Metadata,
    Prepared,
    VerifiedMetadata,
)
