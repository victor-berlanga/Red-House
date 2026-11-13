"""Políticas operativas, recordatorio/escalamiento y entrega con reintentos durables."""

from datetime import datetime, timezone, timedelta
from typing import Annotated, Literal
from uuid import uuid4

from flask import g
from pydantic import Field

from redhouse.api import endpoint, atomic, listing
from redhouse.client import call
from redhouse.db import transaction, get, insert, update
from redhouse.delivery import email, push
from redhouse.errors import APIError
from redhouse.events import emit
from redhouse.extension_contracts import schema, install_reads, page_schema
from redhouse.models import ID, Model, Text, Role, Confirm, utc_date


class PolicyCreate(Model):
    message_code: Annotated[str, Field(pattern=r"^[A-Z0-9_]{1,80}$")]
    severity: Literal["INFO", "WARNING", "CRITICAL"]
    reminder_seconds: Annotated[int, Field(ge=1, le=604800)]
    escalate_seconds: Annotated[int, Field(ge=2, le=2592000)]
    escalation_role: Role
    source: Text
    effective_at: Text
    supersedes: ID | None = None
    version: Annotated[int, Field(ge=1)] = 1


class Policy(PolicyCreate):
    id: ID
    tenant_id: ID
    active: bool
    version: int
    created_at: Text
    author_id: ID


class SubscriptionCreate(Model):
    channel: Literal["EMAIL", "PUSH"]
    push_destination: Annotated[str, Field(min_length=10, max_length=1000)] | None = (
        None
    )


class Subscription(Model):
    id: ID
    tenant_id: ID
    user_id: ID
    role: Role
    channel: str
    destination: str
    active: bool
    version: int
    created_at: Text


class Delivery(Model):
    id: ID
    alert_id: ID
    subscription_id: ID
    tenant_id: ID
    stage: str
    status: str
    attempts: int
    next_attempt: Text
    accepted_at: Text | None
    last_error: str | None
    created_at: Text


class Closed(Model):
    id: ID
    status: Literal["CLOSED"]


def allowed(row):
    if (
        str(row["tenant_id"]) != g.actor["tenant_id"]
        or row["target_role"] != g.actor["role"]
        or (row["target_user_id"] and str(row["target_user_id"]) != g.actor["id"])
    ):
        raise APIError("forbidden", "Alerta de otro destinatario.", 403)


def process(limit=100):
    with transaction() as conn:
        alerts = conn.execute(
            "SELECT a.* FROM alerts a JOIN alert_severity s ON s.id=a.id WHERE a.status='OPEN' "
            "ORDER BY s.delivery_checked_at NULLS FIRST,a.created_at FOR UPDATE OF a SKIP LOCKED LIMIT %s",
            (limit,),
        ).fetchall()
        for alert in alerts:
            policy = conn.execute(
                "SELECT * FROM alert_policies WHERE tenant_id=%s AND message_code=%s AND active AND effective_at<=%s ORDER BY version DESC LIMIT 1",
                (alert["tenant_id"], alert["message_code"], alert["created_at"]),
            ).fetchone()
            conn.execute(
                "UPDATE alert_severity SET delivery_checked_at=now(),severity=%s WHERE id=%s",
                (policy["severity"] if policy else "INFO", alert["id"]),
            )
            age = (datetime.now(timezone.utc) - alert["created_at"]).total_seconds()
            stages = ["INITIAL"]
            if policy:
                if age >= policy["reminder_seconds"]:
                    stages.append("REMINDER")
                if age >= policy["escalate_seconds"]:
                    stages.append("ESCALATED")
            for stage in stages:
                role = (
                    policy["escalation_role"]
                    if stage == "ESCALATED"
                    else alert["target_role"]
                )
                if (
                    stage != "INITIAL"
                    and not conn.execute(
                        "SELECT 1 FROM alert_actions WHERE alert_id=%s AND action=%s",
                        (alert["id"], stage),
                    ).fetchone()
                ):
                    insert(
                        conn,
                        "alert_actions",
                        {
                            "id": str(uuid4()),
                            "alert_id": alert["id"],
                            "tenant_id": alert["tenant_id"],
                            "actor_id": None,
                            "action": stage,
                            "reason": "Política operativa configurada",
                        },
                    )
                    insert(
                        conn,
                        "alerts",
                        {
                            "id": str(uuid4()),
                            "event_id": str(uuid4()),
                            "tenant_id": alert["tenant_id"],
                            "region_id": alert["region_id"],
                            "target_role": role,
                            "target_user_id": None
                            if stage == "ESCALATED"
                            else alert["target_user_id"],
                            "message_code": alert["message_code"] + "_" + stage,
                            "resource_id": alert["resource_id"],
                        },
                    )
                subscriptions = conn.execute(
                    "SELECT * FROM alert_subscriptions WHERE tenant_id=%s AND role=%s AND active AND created_at<=%s "
                    "AND (%s::uuid IS NULL OR user_id=%s)",
                    (
                        alert["tenant_id"],
                        role,
                        alert["created_at"],
                        None if stage == "ESCALATED" else alert["target_user_id"],
                        None if stage == "ESCALATED" else alert["target_user_id"],
                    ),
                ).fetchall()
                for subscription in subscriptions:
                    if not conn.execute(
                        "SELECT 1 FROM alert_deliveries WHERE alert_id=%s AND subscription_id=%s AND stage=%s",
                        (alert["id"], subscription["id"], stage),
                    ).fetchone():
                        insert(
                            conn,
                            "alert_deliveries",
                            {
                                "id": str(uuid4()),
                                "alert_id": alert["id"],
                                "subscription_id": subscription["id"],
                                "tenant_id": alert["tenant_id"],
                                "stage": stage,
                            },
                        )
    for _ in range(limit):
        with transaction() as conn:
            delivery = conn.execute(
                "SELECT * FROM alert_deliveries WHERE status='PENDING' AND next_attempt<=now() ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 1"
            ).fetchone()
            if not delivery:
                break
            subscription = get(
                conn, "alert_subscriptions", str(delivery["subscription_id"])
            )
            alert = get(conn, "alerts", str(delivery["alert_id"]))
            if not subscription["active"] or alert["status"] != "OPEN":
                update(
                    conn, "alert_deliveries", delivery["id"], {"status": "CANCELLED"}
                )
                continue
            try:
                user = call(
                    "identidad_acceso",
                    "GET",
                    "/internal/v1/notification-users/" + str(subscription["user_id"]),
                    delegate=False,
                )
                if (
                    not user["active"]
                    or user["role"] != subscription["role"]
                    or user["tenant_id"] != str(subscription["tenant_id"])
                ):
                    update(
                        conn,
                        "alert_deliveries",
                        delivery["id"],
                        {"status": "CANCELLED"},
                    )
                    continue
                if subscription["channel"] == "EMAIL":
                    if user["email"] != subscription["destination"]:
                        raise APIError("contact_changed", "Contacto cambió.", 409)
                    email(
                        subscription["destination"],
                        "Aviso Red House",
                        "Hay un aviso en tu bandeja autorizada. Código: "
                        + alert["message_code"],
                        str(delivery["id"]),
                    )
                else:
                    push(
                        subscription["destination"],
                        alert["message_code"],
                        str(delivery["id"]),
                        alert_id=str(alert["id"]),
                    )
                update(
                    conn,
                    "alert_deliveries",
                    delivery["id"],
                    {
                        "status": "ACCEPTED_BY_ADAPTER",
                        "accepted_at": datetime.now(timezone.utc),
                        "attempts": delivery["attempts"] + 1,
                        "last_error": None,
                    },
                )
            except APIError as exc:
                update(
                    conn,
                    "alert_deliveries",
                    delivery["id"],
                    {
                        "attempts": delivery["attempts"] + 1,
                        "last_error": exc.code,
                        "next_attempt": datetime.now(timezone.utc)
                        + timedelta(
                            seconds=min(3600, 2 ** min(delivery["attempts"] + 1, 11))
                        ),
                    },
                )


def install(app):
    install_reads(
        app,
        "/api/v1/alert-policies",
        "alert_policies",
        Policy,
        ("ADMIN", "COORDINATOR"),
    )

    @endpoint(
        app,
        "/api/v1/alert-policies",
        "POST",
        model=PolicyCreate,
        roles=("ADMIN", "COORDINATOR"),
        status=201,
        result=schema(Policy),
    )
    def alert_policy_create(data):
        if data["escalate_seconds"] <= data["reminder_seconds"]:
            raise APIError(
                "validation", "Escalamiento debe ser posterior al recordatorio.", 422
            )

        def work(conn):
            effective = utc_date(data["effective_at"], "effective_at")
            if effective > datetime.now(timezone.utc):
                raise APIError(
                    "validation", "La política requiere fecha efectiva vigente.", 422
                )
            conn.execute(
                "SELECT pg_advisory_xact_lock(hashtextextended(%s, 83))",
                (g.actor["tenant_id"] + data["message_code"],),
            )
            previous = conn.execute(
                "SELECT * FROM alert_policies WHERE tenant_id=%s AND message_code=%s ORDER BY version DESC LIMIT 1",
                (g.actor["tenant_id"], data["message_code"]),
            ).fetchone()
            if data["supersedes"] != (
                str(previous["id"]) if previous else None
            ) or data["version"] != (previous["version"] + 1 if previous else 1):
                raise APIError(
                    "stale_version",
                    "Referencia a la última política y versión siguiente requeridas.",
                    412,
                )
            if previous and effective < previous["effective_at"]:
                raise APIError(
                    "validation",
                    "La corrección no precede a la política anterior.",
                    422,
                )
            row = insert(
                conn,
                "alert_policies",
                dict(
                    data,
                    id=str(uuid4()),
                    tenant_id=g.actor["tenant_id"],
                    author_id=g.actor["id"],
                    effective_at=effective,
                ),
            )
            emit(conn, "ALERT_POLICY_CREATED", row["id"], row["tenant_id"])
            return row

        return atomic("alert_policy_create", data, work)

    @endpoint(
        app,
        "/api/v1/alert-subscriptions",
        "POST",
        model=SubscriptionCreate,
        status=201,
        result=schema(Subscription),
        summary="Registrar, rotar o reactivar destino propio; una suscripción por cuenta y canal",
    )
    def alert_subscription_create(data):
        if data["channel"] == "EMAIL":
            user = call(
                "identidad_acceso",
                "GET",
                "/internal/v1/notification-users/" + g.actor["id"],
                delegate=False,
            )
            if not user["email"]:
                raise APIError(
                    "contact_required", "Verifica tu correo en Identidad.", 409
                )
            destination = user["email"]
        else:
            if not data["push_destination"]:
                raise APIError("validation", "Destino push requerido.", 422)
            destination = data["push_destination"]

        def work(conn):
            # One destination per account/channel is the existing schema contract.
            # Rotation/reactivation must replace that row, not collide with its unique key.
            conn.execute(
                "SELECT pg_advisory_xact_lock(hashtextextended(%s, 84))",
                (g.actor["id"] + data["channel"],),
            )
            existing = conn.execute(
                "SELECT * FROM alert_subscriptions WHERE user_id=%s AND channel=%s FOR UPDATE",
                (g.actor["id"], data["channel"]),
            ).fetchone()
            if existing:
                row = update(
                    conn,
                    "alert_subscriptions",
                    existing["id"],
                    {
                        "tenant_id": g.actor["tenant_id"],
                        "role": g.actor["role"],
                        "destination": destination,
                        "active": True,
                        "version": existing["version"] + 1,
                    },
                )
                emit(conn, "ALERT_SUBSCRIPTION_ROTATED", row["id"], row["tenant_id"])
                return row
            row = insert(
                conn,
                "alert_subscriptions",
                {
                    "id": str(uuid4()),
                    "tenant_id": g.actor["tenant_id"],
                    "user_id": g.actor["id"],
                    "role": g.actor["role"],
                    "channel": data["channel"],
                    "destination": destination,
                },
            )
            emit(conn, "ALERT_SUBSCRIPTION_CREATED", row["id"], row["tenant_id"])
            return row

        return atomic("alert_subscription_create", data, work)

    @endpoint(
        app,
        "/api/v1/alert-subscriptions",
        result=page_schema(Subscription),
        paginated=True,
        query=("q", "from_at", "until_at", "date_field", "sort"),
    )
    def alert_subscriptions():
        with transaction() as conn:
            return listing(conn, "alert_subscriptions", "user_id=%s", (g.actor["id"],))

    @endpoint(
        app,
        "/api/v1/alert-subscriptions/<identifier>/revoke",
        "POST",
        model=Confirm,
        result=schema(Subscription),
    )
    def alert_subscription_revoke(identifier, data):
        def work(conn):
            row = get(conn, "alert_subscriptions", identifier, True)
            if str(row["user_id"]) != g.actor["id"]:
                raise APIError("forbidden", "Suscripción de otro usuario.", 403)
            emit(conn, "ALERT_SUBSCRIPTION_REVOKED", identifier, row["tenant_id"])
            return update(
                conn,
                "alert_subscriptions",
                identifier,
                {"active": False, "version": row["version"] + 1},
            )

        return atomic("alert_subscription_revoke:" + identifier, data, work)

    @endpoint(
        app,
        "/api/v1/alerts/<identifier>/close",
        "POST",
        model=Confirm,
        result=schema(Closed),
    )
    def alert_close(identifier, data):
        def work(conn):
            row = get(conn, "alerts", identifier, True)
            allowed(row)
            if row["status"] != "ACKNOWLEDGED":
                raise APIError("conflict", "Acusa recibo antes de cerrar.", 409)
            insert(
                conn,
                "alert_actions",
                {
                    "id": str(uuid4()),
                    "alert_id": identifier,
                    "tenant_id": row["tenant_id"],
                    "actor_id": g.actor["id"],
                    "action": "CLOSED",
                    "reason": data["reason"],
                },
            )
            update(conn, "alerts", identifier, {"status": "CLOSED"})
            emit(conn, "ALERT_CLOSED", identifier, row["tenant_id"])
            return {"id": identifier, "status": "CLOSED"}

        return atomic("alert_close:" + identifier, data, work)

    @endpoint(
        app,
        "/api/v1/alerts/<identifier>/deliveries",
        result=page_schema(Delivery),
        paginated=True,
        query=("q", "from_at", "until_at", "date_field", "sort"),
    )
    def alert_deliveries(identifier):
        with transaction() as conn:
            allowed(get(conn, "alerts", identifier))
            return listing(
                conn,
                "alert_deliveries",
                "alert_id=%s AND subscription_id IN (SELECT id FROM alert_subscriptions WHERE user_id=%s)",
                (identifier, g.actor["id"]),
            )
