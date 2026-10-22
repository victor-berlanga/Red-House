"""Ediciones previas a historia operativa; nunca reescribe dictámenes."""

from datetime import datetime, timezone
from typing import Annotated
from pydantic import Field
from redhouse.api import atomic, endpoint
from redhouse.db import get, update
from redhouse.decisions import record
from redhouse.errors import APIError
from redhouse.events import emit
from redhouse.models import Confirm, Text, utc_date
from redhouse.security import own
from .routes import DonorCreate, CampaignCreate
from .withdrawal import require_active
from redhouse.validation import invalid


class DonorEdit(DonorCreate, Confirm):
    version: Annotated[int, Field(ge=1)]


class DonationEdit(Confirm):
    collected_at: Text
    version: Annotated[int, Field(ge=1)]


class CampaignEdit(CampaignCreate, Confirm):
    version: Annotated[int, Field(ge=1)]


def install(app):
    @endpoint(
        app,
        "/api/v1/donors/<identifier>",
        "PATCH",
        model=DonorEdit,
        roles=("OPERATOR", "MEDICAL"),
        summary="Corregir expediente sin dictámenes ni donaciones",
    )
    def donor_edit(identifier, data):
        def work(conn):
            row = get(conn, "donors", identifier, True)
            own(row["tenant_id"])
            require_active(row)
            if (
                row["version"] != data["version"]
                or conn.execute(
                    "SELECT 1 FROM donor_reviews WHERE donor_id=%s UNION ALL SELECT 1 FROM donations WHERE donor_id=%s LIMIT 1",
                    (identifier, identifier),
                ).fetchone()
            ):
                raise APIError(
                    "conflict",
                    "Expediente obsoleto o con historia; no se permiten correcciones retrospectivas.",
                    409,
                )
            fields = {
                k: data[k]
                for k in (
                    "folio",
                    "display_name",
                    "blood_group",
                    "consent",
                    "restrictions",
                    "background",
                    "donation_kind",
                    "consent_reference",
                    "consent_at",
                )
            }
            fields["version"] = row["version"] + 1
            record(
                conn,
                identifier,
                row["tenant_id"],
                "DONOR_UPDATED",
                data["reason"],
                fields,
            )
            result = update(conn, "donors", identifier, fields)
            emit(conn, "DONOR_UPDATED", identifier, row["tenant_id"])
            return result

        return atomic("donor_edit:" + identifier, data, work)

    @endpoint(
        app,
        "/api/v1/donations/<identifier>",
        "PATCH",
        model=DonationEdit,
        roles=("MEDICAL",),
        summary="Corregir fecha antes de procesamiento, conservando motivo",
    )
    def donation_edit(identifier, data):
        captured = utc_date(data["collected_at"], "collected_at")
        if captured > datetime.now(timezone.utc):
            raise invalid(
                "La recolección no puede ser posterior al momento actual.",
                "collected_at",
                code="future_date",
            )

        def work(conn):
            row = get(conn, "donations", identifier, True)
            own(row["tenant_id"])
            if row["version"] != data["version"] or row["status"] != "COLLECTED":
                raise APIError("conflict", "Donación obsoleta o ya procesada.", 409)
            record(
                conn,
                identifier,
                row["tenant_id"],
                "DONATION_UPDATED",
                data["reason"],
                {"collected_at": captured.isoformat()},
            )
            result = update(
                conn,
                "donations",
                identifier,
                {"collected_at": captured, "version": row["version"] + 1},
            )
            emit(conn, "DONATION_UPDATED", identifier, row["tenant_id"])
            return result

        return atomic("donation_edit:" + identifier, data, work)

    @endpoint(
        app,
        "/api/v1/campaigns/<identifier>",
        "PATCH",
        model=CampaignEdit,
        roles=("OPERATOR",),
        summary="Editar campaña sin reducir cupos ya ocupados",
    )
    def campaign_edit(identifier, data):
        start, end = (
            utc_date(data["starts_at"], "starts_at"),
            utc_date(data["ends_at"], "ends_at"),
        )
        if start >= end:
            raise invalid(
                "La fecha final debe ser posterior al inicio.",
                "starts_at",
                "ends_at",
                code="date_order",
            )
        if end <= datetime.now(timezone.utc):
            raise invalid(
                "La fecha final ya venció; utiliza una fecha futura.",
                "ends_at",
                code="expired_date",
            )

        def work(conn):
            row = get(conn, "campaigns", identifier, True)
            own(row["tenant_id"])
            booked = conn.execute(
                "SELECT count(*) AS n FROM appointments WHERE campaign_id=%s AND status='BOOKED'",
                (identifier,),
            ).fetchone()["n"]
            if row["version"] != data["version"]:
                raise APIError(
                    "stale_version",
                    "La campaña cambió. Vuelve a abrirla y revisa los cambios antes de guardar.",
                    409,
                )
            if data["capacity"] < booked:
                raise invalid(
                    f"El cupo mínimo permitido es {booked}: ya existen {booked} citas reservadas.",
                    "capacity",
                    code="reserved_capacity",
                    status=409,
                    ge=booked,
                )
            fields = dict(
                title=data["title"],
                starts_at=start,
                ends_at=end,
                capacity=data["capacity"],
                version=row["version"] + 1,
            )
            record(
                conn, identifier, row["tenant_id"], "CAMPAIGN_UPDATED", data["reason"]
            )
            result = update(conn, "campaigns", identifier, fields)
            emit(conn, "CAMPAIGN_UPDATED", identifier, row["tenant_id"])
            return result

        return atomic("campaign_edit:" + identifier, data, work)
