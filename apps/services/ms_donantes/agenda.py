"""Consentimiento versionado y agenda; conserva la única regla de reserva de citas."""

from datetime import UTC, datetime
from typing import Annotated, Literal
from uuid import uuid4

from flask import g
from pydantic import Field

from redhouse.api import atomic, endpoint, listing
from redhouse.client import call
from redhouse.db import get, insert, transaction, update
from redhouse.errors import APIError
from redhouse.events import emit
from redhouse.extension_contracts import page_schema, schema, version
from redhouse.models import ID, Confirm, Model, Text, utc_date
from redhouse.security import own

from .routes import donor_access
from .withdrawal import require_active


class ConsentCreate(Confirm):
    version: Annotated[int, Field(ge=1)]
    policy_version: Text
    reference: Text
    effective_at: Text
    granted: bool


class Consent(Model):
    id: ID
    donor_id: ID
    tenant_id: ID
    author_id: ID
    version: int
    policy_version: Text
    reference: Text
    effective_at: Text
    granted: bool
    supersedes: ID | None
    created_at: Text


class SlotCreate(Model):
    campaign_id: ID
    site_id: ID
    starts_at: Text
    ends_at: Text
    capacity: Annotated[int, Field(ge=1, le=10000)]


class Slot(SlotCreate):
    id: ID
    tenant_id: ID
    active: bool
    version: int
    created_at: Text


class SlotAvailability(Slot):
    occupied: int
    available: int
    attended: int


def slot_availability(conn, row):
    counts = conn.execute(
        "SELECT count(*) FILTER (WHERE a.status='BOOKED') AS occupied, "
        "count(*) FILTER (WHERE s.status='ATTENDED') AS attended "
        "FROM appointment_slots s JOIN appointments a ON a.id=s.id WHERE s.slot_id=%s",
        (row["id"],),
    ).fetchone()
    return dict(row, **counts, available=max(0, row["capacity"] - counts["occupied"]))


def slots_availability(conn, rows):
    """Enrich only the already authorized page; reservation locking is unchanged."""
    if not rows:
        return []
    counts = conn.execute(
        "SELECT s.slot_id,count(*) FILTER (WHERE a.status='BOOKED') AS occupied, "
        "count(*) FILTER (WHERE s.status='ATTENDED') AS attended "
        "FROM appointment_slots s JOIN appointments a ON a.id=s.id "
        "WHERE s.slot_id=ANY(%s::uuid[]) GROUP BY s.slot_id",
        ([row["id"] for row in rows],),
    ).fetchall()
    by_slot = {str(row["slot_id"]): row for row in counts}
    result = []
    for row in rows:
        count = by_slot.get(str(row["id"]), {})
        occupied = count.get("occupied", 0)
        result.append(
            dict(
                row,
                occupied=occupied,
                attended=count.get("attended", 0),
                available=max(0, row["capacity"] - occupied),
            )
        )
    return result


class AppointmentCommand(Confirm):
    version: Annotated[int, Field(ge=1)]
    action: Literal["CONFIRM", "RESCHEDULE", "ATTEND", "CANCEL"]
    slot_id: ID | None = None


class AppointmentSchedule(Model):
    id: ID
    slot_id: ID
    tenant_id: ID
    status: str
    version: int
    created_at: Text


class NextAppointment(Model):
    id: ID
    campaign_id: ID
    title: Text
    slot_id: ID
    site_id: ID
    starts_at: Text
    ends_at: Text
    status: str
    schedule_status: str
    schedule_version: int


class NextAppointmentResult(Model):
    appointment: NextAppointment | None


class AgendaAppointment(Model):
    id: ID
    donor_id: ID
    campaign_id: ID
    title: Text
    slot_id: ID | None
    site_id: ID | None
    starts_at: Text | None
    ends_at: Text | None
    status: str
    schedule_status: str | None
    schedule_version: int | None
    created_at: Text


APPOINTMENT_AGENDA = """(
    SELECT a.id,a.donor_id,a.campaign_id,a.tenant_id,d.user_id,c.title,a.status,
           a.created_at,s.slot_id,t.site_id,t.starts_at,t.ends_at,
           s.status AS schedule_status,s.version AS schedule_version
    FROM appointments a
    JOIN donors d ON d.id=a.donor_id AND d.tenant_id=a.tenant_id
    JOIN campaigns c ON c.id=a.campaign_id AND c.tenant_id=a.tenant_id
    LEFT JOIN appointment_slots s ON s.id=a.id AND s.tenant_id=a.tenant_id
    LEFT JOIN campaign_slots t ON t.id=s.slot_id AND t.tenant_id=a.tenant_id
        AND t.campaign_id=a.campaign_id
) AS agenda"""


def require_consent(conn, donor):
    latest = conn.execute(
        "SELECT granted FROM consent_versions WHERE donor_id=%s ORDER BY version DESC LIMIT 1",
        (donor["id"],),
    ).fetchone()
    if latest and not latest["granted"]:
        raise APIError(
            "consent_withdrawn",
            "Consentimiento retirado; requiere nueva autorización del donante.",
            409,
        )


def validate_slot(conn, slot_id, campaign, exclude=None):
    slot = get(conn, "campaign_slots", slot_id, True)
    own(slot["tenant_id"])
    count = conn.execute(
        "SELECT count(*) AS n FROM appointment_slots s JOIN appointments a ON a.id=s.id "
        "WHERE s.slot_id=%s AND a.status='BOOKED' AND (%s::uuid IS NULL OR s.id<>%s)",
        (slot_id, exclude, exclude),
    ).fetchone()["n"]
    if (
        str(slot["campaign_id"]) != str(campaign["id"])
        or not slot["active"]
        or slot["starts_at"] <= datetime.now(UTC)
        or count >= slot["capacity"]
        or slot["starts_at"] < campaign["starts_at"]
        or slot["ends_at"] > campaign["ends_at"]
    ):
        raise APIError("slot_full", "Horario fuera de agenda, vencido o sin cupo.", 409)
    return slot


def book(conn, data):
    donor = get(conn, "donors", data["donor_id"], True)
    donor_access(donor)
    require_active(donor)
    campaign = get(conn, "campaigns", data["campaign_id"], True)
    own(campaign["tenant_id"])
    count = conn.execute(
        "SELECT count(*) AS n FROM appointments WHERE campaign_id=%s AND status='BOOKED'",
        (campaign["id"],),
    ).fetchone()["n"]
    if (
        campaign["status"] != "OPEN"
        or campaign["ends_at"] <= datetime.now(UTC)
        or count >= campaign["capacity"]
    ):
        raise APIError("campaign_full", "Campaña cerrada o sin cupo.", 409)
    slot_id = data.get("slot_id")
    if slot_id:
        validate_slot(conn, slot_id, campaign)
    elif conn.execute(
        "SELECT 1 FROM campaign_slots WHERE campaign_id=%s AND active",
        (campaign["id"],),
    ).fetchone():
        raise APIError("slot_required", "Selecciona un horario de esta campaña.", 409)
    row = insert(
        conn,
        "appointments",
        {
            "id": str(uuid4()),
            "tenant_id": g.actor["tenant_id"],
            "donor_id": data["donor_id"],
            "campaign_id": data["campaign_id"],
        },
    )
    if slot_id:
        insert(
            conn,
            "appointment_slots",
            {"id": row["id"], "slot_id": slot_id, "tenant_id": row["tenant_id"]},
        )
    emit(
        conn,
        "APPOINTMENT_BOOKED",
        row["id"],
        row["tenant_id"],
        targets=("auditoria", "alertas"),
        metadata={
            "recipient_user_id": str(donor["user_id"]) if donor["user_id"] else None
        },
    )
    return row


def reminders(limit=100):
    with transaction() as conn:
        rows = conn.execute(
            "SELECT a.id,a.tenant_id,d.user_id,s.version FROM appointments a "
            "JOIN appointment_slots s ON s.id=a.id JOIN campaign_slots c ON c.id=s.slot_id JOIN donors d ON d.id=a.donor_id "
            "LEFT JOIN appointment_reminders r ON r.id=a.id WHERE a.status='BOOKED' AND c.starts_at>now() "
            "AND c.starts_at<=now()+interval '24 hours' AND (r.id IS NULL OR r.version<s.version) "
            "ORDER BY c.starts_at FOR UPDATE OF a SKIP LOCKED LIMIT %s",
            (limit,),
        ).fetchall()
        for row in rows:
            conn.execute(
                "INSERT INTO appointment_reminders(id,version) VALUES(%s,%s) ON CONFLICT(id) DO UPDATE SET version=excluded.version,sent_at=now()",
                (row["id"], row["version"]),
            )
            # La región se recupera del evento del dominio, sin copiar instituciones.
            region = conn.execute(
                "SELECT event->>'region_id' AS region FROM activity_events WHERE event->>'resource_id'=%s ORDER BY created_at DESC LIMIT 1",
                (str(row["id"]),),
            ).fetchone()
            if region:
                g.actor = {
                    "id": None,
                    "tenant_id": str(row["tenant_id"]),
                    "region_id": region["region"],
                }
            emit(
                conn,
                "APPOINTMENT_REMINDER",
                row["id"],
                row["tenant_id"],
                targets=("auditoria", "alertas"),
                metadata={
                    "recipient_user_id": str(row["user_id"]) if row["user_id"] else None
                },
            )


def install(app):
    from redhouse.trace_contract import TraceEvent

    @endpoint(
        app,
        "/api/v1/appointments/agenda",
        roles=("DONOR",),
        result=page_schema(AgendaAppointment),
        paginated=True,
        query=("q", "status", "from_at", "until_at", "date_field", "sort"),
    )
    def appointment_agenda():
        """Human-facing page with campaign and schedule in two bounded SQL queries."""
        with transaction() as conn:
            return listing(
                conn,
                APPOINTMENT_AGENDA,
                "tenant_id=%s AND user_id=%s",
                (g.actor["tenant_id"], g.actor["id"]),
                columns="id,donor_id,campaign_id,title,slot_id,site_id,starts_at,ends_at,"
                "status,schedule_status,schedule_version,created_at",
                order="starts_at ASC NULLS LAST,id",
                filters={
                    "q": ("title",),
                    "status": ("status", ("BOOKED", "CANCELLED", "ATTENDED")),
                },
                date_columns=("starts_at", "created_at"),
            )

    @endpoint(
        app,
        "/api/v1/appointments/next",
        roles=("DONOR",),
        result=schema(NextAppointmentResult),
    )
    def next_appointment():
        """Read the nearest owned booking independently of list pagination."""
        with transaction() as conn:
            row = conn.execute(
                "SELECT a.id,a.campaign_id,c.title,s.slot_id,t.site_id,"
                "t.starts_at,t.ends_at,a.status,s.status AS schedule_status,"
                "s.version AS schedule_version FROM appointments a "
                "JOIN donors d ON d.id=a.donor_id AND d.tenant_id=a.tenant_id "
                "JOIN appointment_slots s ON s.id=a.id AND s.tenant_id=a.tenant_id "
                "JOIN campaign_slots t ON t.id=s.slot_id AND t.tenant_id=a.tenant_id "
                "AND t.campaign_id=a.campaign_id "
                "JOIN campaigns c ON c.id=a.campaign_id AND c.tenant_id=a.tenant_id "
                "WHERE a.tenant_id=%s AND d.user_id=%s AND a.status='BOOKED' "
                "AND s.status IN ('BOOKED','CONFIRMED') AND t.starts_at>now() "
                "ORDER BY t.starts_at,a.id LIMIT 1",
                (g.actor["tenant_id"], g.actor["id"]),
            ).fetchone()
            return {"appointment": row}

    class DonationHistory(Model):
        events: list[TraceEvent]

    @endpoint(
        app,
        "/api/v1/donations/<identifier>/history",
        roles=("MEDICAL", "OPERATOR"),
        result=schema(DonationHistory),
    )
    def donation_history(identifier):
        with transaction() as conn:
            donation = get(conn, "donations", identifier)
            own(donation["tenant_id"])
            events = conn.execute(
                "SELECT id,event->>'source' AS source,event->>'action' AS action,event->>'occurred_at' AS occurred_at "
                "FROM activity_events WHERE event->>'resource_id'=%s ORDER BY created_at,id LIMIT 2000",
                (identifier,),
            ).fetchall()
        return {"events": events}

    @endpoint(
        app,
        "/api/v1/campaign-slots",
        roles=("DONOR", "OPERATOR"),
        paginated=True,
        result=page_schema(SlotAvailability),
        query=(
            "campaign_id",
            "site_id",
            "active",
            "from_at",
            "until_at",
            "date_field",
            "sort",
            "q",
        ),
    )
    def campaign_slots_list():
        with transaction() as conn:
            result = listing(
                conn,
                "campaign_slots",
                "tenant_id=%s",
                (g.actor["tenant_id"],),
                filters={
                    "campaign_id": ("campaign_id", ()),
                    "site_id": ("site_id", ()),
                    "active": ("active", {"true": True, "false": False}),
                    "q": ("id::text",),
                },
                date_columns=("starts_at", "ends_at", "created_at"),
                order="starts_at,id",
            )
            result["items"] = slots_availability(conn, result["items"])
            return result

    @endpoint(
        app,
        "/api/v1/campaign-slots/<identifier>",
        roles=("DONOR", "OPERATOR"),
        result=schema(SlotAvailability),
    )
    def campaign_slots_detail(identifier):
        with transaction() as conn:
            row = get(conn, "campaign_slots", identifier)
            own(row["tenant_id"])
            return slot_availability(conn, row)

    @endpoint(
        app,
        "/api/v1/donors/<identifier>/consents",
        "POST",
        model=ConsentCreate,
        roles=("DONOR", "MEDICAL"),
        result=schema(Consent),
        status=201,
    )
    def consent_create(identifier, data):
        effective = utc_date(data["effective_at"], "effective_at")
        if effective > datetime.now(UTC):
            raise APIError("validation", "Consentimiento no puede ser futuro.", 422)

        def work(conn):
            donor = get(conn, "donors", identifier, True)
            donor_access(donor)
            require_active(donor)
            version(donor, data["version"])
            old = conn.execute(
                "SELECT * FROM consent_versions WHERE donor_id=%s ORDER BY version DESC LIMIT 1",
                (identifier,),
            ).fetchone()
            row = insert(
                conn,
                "consent_versions",
                {
                    "id": str(uuid4()),
                    "donor_id": identifier,
                    "tenant_id": donor["tenant_id"],
                    "author_id": g.actor["id"],
                    "version": old["version"] + 1 if old else 1,
                    "supersedes": old["id"] if old else None,
                    "policy_version": data["policy_version"],
                    "reference": data["reference"],
                    "granted": data["granted"],
                    "effective_at": effective,
                },
            )
            fields = {"version": donor["version"] + 1}
            if not data["granted"]:
                fields["status"] = "DEFERRED"
            update(conn, "donors", identifier, fields)
            emit(
                conn,
                "DONOR_CONSENT_RECORDED"
                if data["granted"]
                else "DONOR_CONSENT_WITHDRAWN",
                identifier,
                donor["tenant_id"],
            )
            return row

        return atomic("consent_create:" + identifier, data, work)

    @endpoint(
        app,
        "/api/v1/donors/<identifier>/consents",
        roles=("DONOR", "MEDICAL"),
        paginated=True,
        result=page_schema(Consent),
        query=("q", "from_at", "until_at", "date_field", "sort"),
    )
    def consent_list(identifier):
        with transaction() as conn:
            donor_access(get(conn, "donors", identifier))
            return listing(
                conn,
                "consent_versions",
                "donor_id=%s",
                (identifier,),
                order="version DESC,id",
            )

    @endpoint(
        app,
        "/api/v1/campaign-slots",
        "POST",
        model=SlotCreate,
        roles=("OPERATOR",),
        status=201,
        result=schema(Slot),
    )
    def campaign_slot_create(data):
        site = call(
            "identidad_acceso", "GET", "/api/v1/catalogues/sites/" + data["site_id"]
        )
        if not site["active"]:
            raise APIError("conflict", "Sede inactiva.", 409)
        start, end = utc_date(data["starts_at"]), utc_date(data["ends_at"])

        def work(conn):
            campaign = get(conn, "campaigns", data["campaign_id"], True)
            own(campaign["tenant_id"])
            if not campaign["starts_at"] <= start < end <= campaign[
                "ends_at"
            ] or start <= datetime.now(UTC):
                raise APIError(
                    "validation",
                    "Horario debe estar dentro de la campaña y ser futuro.",
                    422,
                )
            row = insert(
                conn,
                "campaign_slots",
                dict(
                    data,
                    id=str(uuid4()),
                    tenant_id=g.actor["tenant_id"],
                    starts_at=start,
                    ends_at=end,
                ),
            )
            emit(conn, "CAMPAIGN_SLOT_CREATED", row["id"], row["tenant_id"])
            return row

        return atomic("campaign_slot_create", data, work)

    @endpoint(
        app,
        "/api/v1/appointments/<identifier>/schedule",
        roles=("DONOR", "OPERATOR"),
        result=schema(AppointmentSchedule),
    )
    def appointment_schedule(identifier):
        with transaction() as conn:
            row = get(conn, "appointments", identifier)
            donor_access(get(conn, "donors", str(row["donor_id"])))
            schedule = get(conn, "appointment_slots", identifier)
            if row["status"] == "CANCELLED":
                schedule["status"] = "CANCELLED"
            return schedule

    @endpoint(
        app,
        "/api/v1/appointments/<identifier>/commands",
        "POST",
        model=AppointmentCommand,
        roles=("DONOR", "OPERATOR"),
        result=schema(AppointmentSchedule),
    )
    def appointment_command(identifier, data):
        def work(conn):
            original = get(conn, "appointments", identifier)
            donor = get(conn, "donors", str(original["donor_id"]), True)
            donor_access(donor)
            require_active(donor)
            row = get(conn, "appointments", identifier, True)
            campaign = get(conn, "campaigns", str(row["campaign_id"]), True)
            schedule = get(conn, "appointment_slots", identifier, True)
            version(schedule, data["version"])
            if row["status"] != "BOOKED":
                raise APIError("conflict", "Cita sin reserva vigente.", 409)
            fields = {"version": schedule["version"] + 1}
            if data["action"] == "RESCHEDULE":
                if not data["slot_id"]:
                    raise APIError("validation", "Horario nuevo requerido.", 422)
                validate_slot(conn, data["slot_id"], campaign, identifier)
                fields.update(slot_id=data["slot_id"], status="BOOKED")
            elif data["slot_id"]:
                raise APIError(
                    "validation", "Horario solo aplica a reprogramación.", 422
                )
            elif data["action"] == "ATTEND":
                if g.actor["role"] != "OPERATOR":
                    raise APIError(
                        "forbidden", "Asistencia requiere personal de la sede.", 403
                    )
                fields["status"] = "ATTENDED"
                update(conn, "appointments", identifier, {"status": "ATTENDED"})
            elif data["action"] == "CANCEL":
                fields["status"] = "CANCELLED"
                update(conn, "appointments", identifier, {"status": "CANCELLED"})
            else:
                fields["status"] = "CONFIRMED"
            result = update(conn, "appointment_slots", identifier, fields)
            emit(
                conn,
                "APPOINTMENT_" + data["action"],
                identifier,
                row["tenant_id"],
                targets=("auditoria", "alertas"),
            )
            return result

        return atomic("appointment_command:" + identifier, data, work)
