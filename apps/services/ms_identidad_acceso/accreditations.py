"""Registro documental institucional; no expide acreditación sanitaria."""

from datetime import datetime, timezone
from uuid import uuid4

from flask import g

from redhouse.api import endpoint, atomic
from redhouse.db import get, insert
from redhouse.events import emit
from redhouse.errors import APIError
from redhouse.extension_contracts import schema, install_reads
from redhouse.models import Model, ID, Text, Confirm, utc_date
from redhouse.security import own


class AccreditationCreate(Confirm):
    issuer: Text
    category: Text
    reference: Text
    valid_from: Text
    valid_until: Text
    supersedes: ID | None = None


class Accreditation(Model):
    id: ID
    tenant_id: ID
    issuer: Text
    category: Text
    reference: Text
    valid_from: Text
    valid_until: Text
    author_id: ID
    supersedes: ID | None
    version: int
    created_at: Text


def install(app):
    install_reads(
        app,
        "/api/v1/accreditations",
        "accreditations",
        Accreditation,
        ("ADMIN", "COORDINATOR", "AUDITOR"),
    )

    @endpoint(
        app,
        "/api/v1/accreditations",
        "POST",
        model=AccreditationCreate,
        roles=("ADMIN",),
        result=schema(Accreditation),
        status=201,
    )
    def accreditation_create(data):
        start, end = utc_date(data["valid_from"]), utc_date(data["valid_until"])
        if end <= start or end <= datetime.now(timezone.utc):
            raise APIError("validation", "Vigencia documental inválida.", 422)

        def work(conn):
            # Institución bloqueada serializa las revisiones de documentos.
            get(conn, "institutions", g.actor["tenant_id"], True)
            old = (
                get(conn, "accreditations", data["supersedes"])
                if data["supersedes"]
                else None
            )
            if old:
                own(old["tenant_id"])
                if conn.execute(
                    "SELECT 1 FROM accreditations WHERE supersedes=%s", (old["id"],)
                ).fetchone():
                    raise APIError("stale_version", "Documento ya sustituido.", 412)
            row = insert(
                conn,
                "accreditations",
                {
                    "id": str(uuid4()),
                    "tenant_id": g.actor["tenant_id"],
                    "author_id": g.actor["id"],
                    "issuer": data["issuer"],
                    "category": data["category"],
                    "reference": data["reference"],
                    "valid_from": start,
                    "valid_until": end,
                    "version": old["version"] + 1 if old else 1,
                    "supersedes": data["supersedes"],
                },
            )
            emit(
                conn,
                "ACCREDITATION_DOCUMENT_RECORDED",
                row["id"],
                row["tenant_id"],
                metadata={"certified": False},
            )
            return row

        return atomic("accreditation_create", data, work)
