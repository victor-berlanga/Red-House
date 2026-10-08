from datetime import datetime, timezone
from typing import Annotated, Literal
from uuid import uuid4

from flask import g
from pydantic import Field, model_validator

from redhouse.api import atomic, endpoint, listing
from redhouse.db import get, insert, transaction, update
from redhouse.errors import APIError
from redhouse.events import emit
from redhouse.decisions import history
from redhouse.models import Confirm, Group, ID, Kind, Model, Reason, Text, utc_date
from redhouse.security import own


class DonorCreate(Model):
    restrictions: Reason | None = None
    background: Reason | None = None
    donation_kind: Literal["VOLUNTARY", "REPLACEMENT"] | None = None
    consent_reference: Text | None = None
    consent_at: Text | None = None

    @model_validator(mode="after")
    def consent_document(self):
        if bool(self.consent_at) != bool(self.consent_reference):
            raise ValueError(
                "La referencia y fecha de consentimiento se capturan juntas."
            )
        if self.consent_at and utc_date(self.consent_at) > datetime.now(timezone.utc):
            raise ValueError("El consentimiento no puede ser futuro.")
        return self

    folio: Annotated[
        str, Field(min_length=6, max_length=30, pattern=r"^[A-Za-z0-9_-]+$")
    ]
    display_name: Text
    blood_group: Group
    consent: Literal[True]


class DonorReview(Confirm):
    decision: Literal["ELIGIBLE", "DEFERRED"]
    version: Annotated[int, Field(ge=1)]


class CampaignCreate(Model):
    title: Text
    starts_at: Text
    ends_at: Text
    capacity: Annotated[int, Field(ge=1, le=10000)]


class AppointmentCreate(Model):
    donor_id: ID
    campaign_id: ID


class DonationCreate(Confirm):
    donor_id: ID
    kind: Kind
    component: Text
    collected_at: Text


class DonationStep(Confirm):
    state: Literal["PROCESSED", "REJECTED"]
    version: Annotated[int, Field(ge=1)]


def donor_access(row):
    own(row["tenant_id"])
    if g.actor["role"] == "DONOR" and str(row["user_id"]) != g.actor["id"]:
        raise APIError("forbidden", "Expediente de otro donante.", 403)


def register(app):
    @endpoint(
        app,
        "/api/v1/donors",
        "POST",
        model=DonorCreate,
        roles=("DONOR", "OPERATOR", "MEDICAL"),
        status=201,
        summary="Registro preliminar con consentimiento",
    )
    def donor_create(data):
        def work(conn):
            row = insert(
                conn,
                "donors",
                dict(
                    id=str(uuid4()),
                    tenant_id=g.actor["tenant_id"],
                    user_id=g.actor["id"] if g.actor["role"] == "DONOR" else None,
                    **data,
                ),
            )
            emit(conn, "DONOR_REGISTERED", row["id"], row["tenant_id"])
            return row

        return atomic("donor_create", data, work)

    @endpoint(
        app,
        "/api/v1/donors",
        roles=("DONOR", "OPERATOR", "MEDICAL"),
        paginated=True,
        query=("q", "status"),
        summary="Expedientes autorizados",
    )
    def donors():
        with transaction() as conn:
            condition = "tenant_id=%s" + (
                " AND user_id=%s" if g.actor["role"] == "DONOR" else ""
            )
            values = (
                (g.actor["tenant_id"], g.actor["id"])
                if g.actor["role"] == "DONOR"
                else (g.actor["tenant_id"],)
            )
            return listing(
                conn,
                "donors",
                condition,
                values,
                filters={
                    "q": ("folio", "display_name"),
                    "status": ("status", ("PRELIMINARY", "ELIGIBLE", "DEFERRED")),
                },
            )

    @endpoint(
        app,
        "/api/v1/donors/<identifier>",
        roles=("DONOR", "OPERATOR", "MEDICAL"),
        summary="Expediente y evaluaciones humanas",
    )
    def donor_detail(identifier):
        with transaction() as conn:
            row = get(conn, "donors", identifier)
            donor_access(row)
            row["decisions"] = history(conn, identifier)
            row["reviews"] = conn.execute(
                "SELECT id,decision,reason,actor_id,created_at FROM donor_reviews WHERE donor_id=%s ORDER BY created_at,id",
                (identifier,),
            ).fetchall()
            return row

    @endpoint(
        app,
        "/api/v1/donors/<identifier>/reviews",
        "POST",
        model=DonorReview,
        roles=("MEDICAL",),
        status=201,
        summary="Dictamen humano de elegibilidad",
    )
    def donor_review(identifier, data):
        def work(conn):
            donor = get(conn, "donors", identifier, True)
            own(donor["tenant_id"])
            if donor["version"] != data["version"]:
                raise APIError(
                    "stale_version", "Expediente actualizado; vuelve a revisarlo.", 409
                )
            review = insert(
                conn,
                "donor_reviews",
                dict(
                    id=str(uuid4()),
                    donor_id=identifier,
                    actor_id=g.actor["id"],
                    decision=data["decision"],
                    reason=data["reason"],
                ),
            )
            update(
                conn,
                "donors",
                identifier,
                {"status": data["decision"], "version": donor["version"] + 1},
            )
            emit(
                conn,
                "DONOR_REVIEWED",
                identifier,
                donor["tenant_id"],
                targets=("auditoria", "alertas"),
                metadata={
                    "status": data["decision"],
                    "recipient_user_id": str(donor["user_id"])
                    if donor["user_id"]
                    else None,
                },
            )
            return review

        return atomic("donor_review:" + identifier, data, work)

    @endpoint(
        app,
        "/api/v1/campaigns",
        "POST",
        model=CampaignCreate,
        roles=("OPERATOR",),
        status=201,
        summary="Crear campaña y capacidad de citas",
    )
    def campaign_create(data):
        values = dict(
            data,
            starts_at=utc_date(data["starts_at"]),
            ends_at=utc_date(data["ends_at"]),
        )
        if values["ends_at"] <= values["starts_at"] or values[
            "ends_at"
        ] <= datetime.now(timezone.utc):
            raise APIError("validation", "Intervalo de campaña inválido.")

        def work(conn):
            row = insert(
                conn,
                "campaigns",
                dict(id=str(uuid4()), tenant_id=g.actor["tenant_id"], **values),
            )
            emit(conn, "CAMPAIGN_CREATED", row["id"], row["tenant_id"])
            return row

        return atomic("campaign_create", data, work)

    @endpoint(
        app,
        "/api/v1/campaigns",
        roles=("DONOR", "OPERATOR", "MEDICAL"),
        paginated=True,
        query=("q",),
        summary="Campañas institucionales vigentes",
    )
    def campaigns():
        with transaction() as conn:
            return listing(
                conn,
                "campaigns",
                "tenant_id=%s AND ends_at>now() AND status='OPEN'",
                (g.actor["tenant_id"],),
                order="starts_at,id",
                filters={"q": ("title",)},
            )

    @endpoint(
        app,
        "/api/v1/appointments",
        "POST",
        model=AppointmentCreate,
        roles=("DONOR", "OPERATOR"),
        status=201,
        summary="Reservar cita sin exceder capacidad",
    )
    def appointment_create(data):
        def work(conn):
            donor = get(conn, "donors", data["donor_id"], True)
            donor_access(donor)
            campaign = get(conn, "campaigns", data["campaign_id"], True)
            own(campaign["tenant_id"])
            count = conn.execute(
                "SELECT count(*) AS n FROM appointments WHERE campaign_id=%s AND status='BOOKED'",
                (campaign["id"],),
            ).fetchone()["n"]
            if (
                campaign["status"] != "OPEN"
                or campaign["ends_at"] <= datetime.now(timezone.utc)
                or count >= campaign["capacity"]
            ):
                raise APIError("campaign_full", "Campaña cerrada o sin cupo.", 409)
            row = insert(
                conn,
                "appointments",
                dict(id=str(uuid4()), tenant_id=g.actor["tenant_id"], **data),
            )
            emit(
                conn,
                "APPOINTMENT_BOOKED",
                row["id"],
                row["tenant_id"],
                targets=("auditoria", "alertas"),
                metadata={
                    "recipient_user_id": str(donor["user_id"])
                    if donor["user_id"]
                    else None
                },
            )
            return row

        return atomic("appointment_create", data, work)

    @endpoint(
        app,
        "/api/v1/appointments",
        roles=("DONOR", "OPERATOR"),
        paginated=True,
        summary="Citas propias o institucionales",
    )
    def appointments():
        with transaction() as conn:
            where = "tenant_id=%s" + (
                " AND donor_id IN (SELECT id FROM donors WHERE user_id=%s)"
                if g.actor["role"] == "DONOR"
                else ""
            )
            values = (
                (g.actor["tenant_id"], g.actor["id"])
                if g.actor["role"] == "DONOR"
                else (g.actor["tenant_id"],)
            )
            return listing(conn, "appointments", where, values)

    @endpoint(
        app,
        "/api/v1/appointments/<identifier>/cancel",
        "POST",
        roles=("DONOR", "OPERATOR"),
        summary="Cancelar cita y liberar cupo",
    )
    def appointment_cancel(identifier):
        def work(conn):
            row = get(conn, "appointments", identifier, True)
            donor_access(get(conn, "donors", str(row["donor_id"])))
            if row["status"] != "BOOKED":
                raise APIError("conflict", "Cita sin reserva vigente.", 409)
            result = update(conn, "appointments", identifier, {"status": "CANCELLED"})
            emit(conn, "APPOINTMENT_CANCELLED", identifier, row["tenant_id"])
            return result

        return atomic("appointment_cancel:" + identifier, {}, work)

    @endpoint(
        app,
        "/api/v1/donations",
        "POST",
        model=DonationCreate,
        roles=("MEDICAL",),
        status=201,
        summary="Registrar donación tras elegibilidad y confirmación humana",
    )
    def donation_create(data):
        captured = utc_date(data["collected_at"])
        if captured > datetime.now(timezone.utc):
            raise APIError("validation", "Recolección no puede ser futura.")
        if data["kind"] == "ORGAN" and data["component"] not in (
            "KIDNEY",
            "LIVER",
            "HEART",
        ):
            raise APIError("validation", "Tipo de órgano no soportado.")

        def work(conn):
            donor = get(conn, "donors", data["donor_id"], True)
            own(donor["tenant_id"])
            if donor["status"] != "ELIGIBLE":
                raise APIError(
                    "human_review_required",
                    "Elegibilidad humana vigente requerida.",
                    409,
                )
            row = insert(
                conn,
                "donations",
                dict(
                    id=str(uuid4()),
                    donor_id=donor["id"],
                    tenant_id=donor["tenant_id"],
                    kind=data["kind"],
                    component=data["component"],
                    blood_group=donor["blood_group"],
                    collected_at=captured,
                ),
            )
            insert(
                conn,
                "donation_steps",
                dict(
                    id=str(uuid4()),
                    donation_id=row["id"],
                    state="COLLECTED",
                    actor_id=g.actor["id"],
                    reason=data["reason"],
                ),
            )
            emit(conn, "DONATION_COLLECTED", row["id"], row["tenant_id"])
            return row

        return atomic("donation_create", data, work)

    @endpoint(
        app,
        "/api/v1/donations",
        roles=("MEDICAL", "OPERATOR"),
        paginated=True,
        query=("q", "kind", "status"),
        summary="Donaciones de la institución sin expediente personal",
    )
    def donations_list():
        with transaction() as conn:
            return listing(
                conn,
                "donations",
                "tenant_id=%s",
                (g.actor["tenant_id"],),
                filters={
                    "q": ("id::text",),
                    "kind": ("kind", ("BLOOD", "ORGAN")),
                    "status": ("status", ("COLLECTED", "PROCESSED", "REJECTED")),
                },
            )

    @endpoint(
        app,
        "/api/v1/donations/<identifier>/steps",
        "POST",
        model=DonationStep,
        roles=("OPERATOR", "MEDICAL"),
        summary="Documentar procesamiento o rechazo; no infiere elegibilidad clínica",
    )
    def donation_step(identifier, data):
        def work(conn):
            donation = get(conn, "donations", identifier, True)
            own(donation["tenant_id"])
            if (
                donation["status"] != "COLLECTED"
                or donation["version"] != data["version"]
            ):
                raise APIError("conflict", "Donación procesada u obsoleta.", 409)
            insert(
                conn,
                "donation_steps",
                dict(
                    id=str(uuid4()),
                    donation_id=identifier,
                    state=data["state"],
                    actor_id=g.actor["id"],
                    reason=data["reason"],
                ),
            )
            row = update(
                conn,
                "donations",
                identifier,
                {"status": data["state"], "version": donation["version"] + 1},
            )
            emit(conn, "DONATION_" + data["state"], identifier, donation["tenant_id"])
            return row

        return atomic("donation_step:" + identifier, data, work)

    @endpoint(
        app,
        "/internal/v1/donations/<identifier>",
        internal=("inventario",),
        roles=("OPERATOR",),
        summary="Referencia de procedencia; sin identidad ni estudios del donante",
    )
    def donation_internal(identifier):
        with transaction() as conn:
            row = get(conn, "donations", identifier)
            own(row["tenant_id"])
            return {
                k: row[k]
                for k in (
                    "id",
                    "tenant_id",
                    "kind",
                    "component",
                    "blood_group",
                    "status",
                    "version",
                )
            }
