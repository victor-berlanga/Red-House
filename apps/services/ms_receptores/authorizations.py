"""Constancia externa capturada por personal autorizado; no expide autorizaciones."""

from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4
from flask import g

from redhouse.api import endpoint, atomic, listing
from redhouse.db import transaction, get, insert
from redhouse.errors import APIError
from redhouse.events import emit
from redhouse.extension_contracts import schema, page_schema
from redhouse.models import Model, ID, Text, Confirm, utc_date
from redhouse.security import own


class Create(Confirm):
    authority: Text
    reference: Text
    valid_from: Text
    valid_until: Text
    effective_at: Text
    supersedes: ID | None = None
    decision: Literal["RECORDED", "WITHDRAWN"]


class Authorization(Model):
    id: ID
    request_id: ID
    tenant_id: ID
    authority: Text
    reference: Text
    valid_from: Text
    valid_until: Text
    effective_at: Text
    supersedes: ID | None
    decision: Text
    version: int
    author_id: ID
    created_at: Text


def require_authorization(conn, req):
    if req["kind"] != "ORGAN":
        return
    from flask import current_app

    row = conn.execute(
        "SELECT * FROM external_authorizations WHERE request_id=%s ORDER BY version DESC LIMIT 1",
        (req["id"],),
    ).fetchone()
    # Las demostraciones anteriores no son asignaciones oficiales. En modo reforzado,
    # toda reserva nueva de órgano exige constancia, incluso si faltaban registros previos.
    if not row and not current_app.config.get("REQUIRE_ORGAN_AUTHORIZATION", True):
        return
    now = datetime.now(timezone.utc)
    if (
        not row
        or row["decision"] != "RECORDED"
        or not row["valid_from"] <= now < row["valid_until"]
    ):
        raise APIError(
            "external_authorization_required",
            "Constancia externa vigente requerida; no se autoriza asignación automática.",
            409,
        )


def install(app):
    @endpoint(
        app,
        "/api/v1/requests/<identifier>/external-authorizations",
        "POST",
        model=Create,
        roles=("MEDICAL",),
        status=201,
        result=schema(Authorization),
    )
    def external_authorization_create(identifier, data):
        dates = {
            k: utc_date(data[k]) for k in ("valid_from", "valid_until", "effective_at")
        }
        if dates["valid_until"] <= dates["valid_from"] or dates[
            "effective_at"
        ] > datetime.now(timezone.utc):
            raise APIError("validation", "Fechas de constancia inválidas.", 422)

        def work(conn):
            req = get(conn, "requests", identifier, True)
            own(req["tenant_id"])
            if req["kind"] != "ORGAN":
                raise APIError(
                    "conflict", "Constancia corresponde a solicitudes de órgano.", 409
                )
            old = conn.execute(
                "SELECT * FROM external_authorizations WHERE request_id=%s ORDER BY version DESC LIMIT 1",
                (identifier,),
            ).fetchone()
            if (str(old["id"]) if old else None) != data["supersedes"]:
                raise APIError("stale_version", "Constancia anterior cambió.", 412)
            row = insert(
                conn,
                "external_authorizations",
                {
                    "id": str(uuid4()),
                    "request_id": identifier,
                    "tenant_id": req["tenant_id"],
                    "author_id": g.actor["id"],
                    "version": old["version"] + 1 if old else 1,
                    **dates,
                    **{
                        k: data[k]
                        for k in ("authority", "reference", "supersedes", "decision")
                    },
                },
            )
            emit(
                conn,
                "EXTERNAL_AUTHORIZATION_RECORDED",
                identifier,
                req["tenant_id"],
                metadata={"document_id": str(row["id"]), "decision": row["decision"]},
            )
            return row

        return atomic("external_authorization:" + identifier, data, work)

    @endpoint(
        app,
        "/api/v1/requests/<identifier>/external-authorizations",
        roles=("MEDICAL",),
        result=page_schema(Authorization),
        paginated=True,
        query=("q", "from_at", "until_at", "date_field", "sort"),
    )
    def external_authorizations(identifier):
        with transaction() as conn:
            own(get(conn, "requests", identifier)["tenant_id"])
            return listing(
                conn,
                "external_authorizations",
                "request_id=%s",
                (identifier,),
                order="version DESC,id",
            )
