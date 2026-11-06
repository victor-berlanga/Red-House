"""Adaptador canónico de conciliación. No representa una conexión hospitalaria."""

from typing import Annotated
from uuid import uuid4

from flask import g
from pydantic import Field

from redhouse.api import endpoint, atomic
from redhouse.db import get, insert, transaction
from redhouse.events import emit
from redhouse.errors import APIError
from redhouse.extension_contracts import schema, install_reads, version
from redhouse.models import ID, Model, Text, Confirm
from redhouse.security import own


class Reconcile(Confirm):
    system: Annotated[str, Field(pattern=r"^[a-zA-Z0-9_.-]{1,80}$")]
    external_id: Text
    resource_id: ID
    resource_version: Annotated[int, Field(ge=1)]
    folio: Text
    kind: Text
    component: Text


class Mapping(Model):
    id: ID
    tenant_id: ID
    system: Text
    external_id: Text
    resource_id: ID
    author_id: ID
    created_at: Text


class Export(Model):
    mapping: Mapping
    resource_id: ID
    version: int
    folio: Text
    kind: Text
    component: Text
    status: Text
    expires_at: Text
    schema_version: int
    clinical_authorization: bool


def install(app):
    install_reads(
        app,
        "/api/v1/external-mappings",
        "external_mappings",
        Mapping,
        ("OPERATOR", "MEDICAL"),
    )

    @endpoint(
        app,
        "/api/v1/interoperability/reconcile",
        "POST",
        model=Reconcile,
        roles=("OPERATOR",),
        status=201,
        result=schema(Mapping),
    )
    def external_reconcile(data):
        def work(conn):
            row = get(conn, "resources", data["resource_id"], True)
            own(row["current_institution_id"])
            version(row, data["resource_version"])
            if any(row[k] != data[k] for k in ("folio", "kind", "component")):
                raise APIError(
                    "reconciliation_conflict",
                    "Datos externos difieren del registro canónico; revisión requerida.",
                    409,
                )
            mapping = insert(
                conn,
                "external_mappings",
                {
                    "id": str(uuid4()),
                    "tenant_id": g.actor["tenant_id"],
                    "author_id": g.actor["id"],
                    "system": data["system"],
                    "external_id": data["external_id"],
                    "resource_id": row["id"],
                },
            )
            emit(
                conn, "EXTERNAL_IDENTIFIER_RECONCILED", row["id"], g.actor["tenant_id"]
            )
            return mapping

        return atomic("external_reconcile", data, work)

    @endpoint(
        app,
        "/api/v1/interoperability/export/<identifier>",
        roles=("OPERATOR", "MEDICAL"),
        result=schema(Export),
    )
    def external_export(identifier):
        with transaction() as conn:
            mapping = get(conn, "external_mappings", identifier)
            own(mapping["tenant_id"])
            row = get(conn, "resources", str(mapping["resource_id"]))
            own(row["current_institution_id"])
            return dict(
                mapping=mapping,
                resource_id=row["id"],
                schema_version=1,
                clinical_authorization=False,
                **{
                    k: row[k]
                    for k in (
                        "version",
                        "folio",
                        "kind",
                        "component",
                        "status",
                        "expires_at",
                    )
                },
            )
