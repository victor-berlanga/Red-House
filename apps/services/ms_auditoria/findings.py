"""Hallazgos separados de los eventos originales, con atención y verificación humana."""

from datetime import datetime, timezone
from typing import Annotated, ClassVar, Literal
from uuid import uuid4

from flask import g
from pydantic import ConfigDict, Field, model_validator
from redhouse.api import atomic, endpoint, listing
from redhouse.client import call
from redhouse.db import get, insert, transaction, update
from redhouse.errors import APIError
from redhouse.events import emit
from redhouse.models import ID, Confirm, Model, Reason
from redhouse.validation import invalid

from .queries import BASE, event

STATES = ("OPEN", "IN_PROGRESS", "PENDING_VERIFICATION", "CLOSED")
PRIORITIES = ("LOW", "MEDIUM", "HIGH", "CRITICAL")


class FindingCreate(Model):
    model_config: ClassVar[ConfigDict] = {
        "json_schema_extra": {
            "examples": [
                {
                    "description": "Verificar documentación de la operación",
                    "priority": "MEDIUM",
                    "assignee_id": "00000000-0000-4000-8000-000000000001",
                    "event_ids": ["00000000-0000-4000-8000-000000000002"],
                    "resource_id": None,
                    "evidence": "Referencia documental de prueba",
                }
            ]
        }
    }
    description: Reason
    priority: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    assignee_id: ID
    event_ids: Annotated[list[ID], Field(max_length=20)] = Field(default_factory=list)
    resource_id: ID | None = None
    evidence: Reason | None = None

    @model_validator(mode="after")
    def linked(self):
        if not self.event_ids and not self.resource_id:
            raise invalid(
                "Vincula al menos un evento o indica un recurso presente en la bitácora autorizada.",
                "event_ids",
                "resource_id",
            )
        return self


class FindingAction(Confirm):
    model_config: ClassVar[ConfigDict] = {
        "json_schema_extra": {
            "examples": [
                {
                    "version": 1,
                    "status": "IN_PROGRESS",
                    "reason": "Revisión documental iniciada",
                    "human_confirmation": True,
                    "corrective_action": "Contrastar la documentación y registrar el resultado",
                    "evidence": None,
                }
            ]
        }
    }
    version: Annotated[int, Field(ge=1)]
    status: Literal["IN_PROGRESS", "PENDING_VERIFICATION", "CLOSED"]
    corrective_action: Reason | None = None
    evidence: Reason | None = None


def authorized(conn, identifier, lock=False):
    row = get(conn, "audit_findings", identifier, lock)
    if str(row["region_id"]) != g.actor["region_id"] or (
        g.actor["role"] != "AUDITOR" and str(row["assignee_id"]) != g.actor["id"]
    ):
        raise APIError(
            "not_found", "Hallazgo no disponible en tu ámbito autorizado.", 404
        )
    return row


def history(conn, row, previous, reason, corrective_action=None, evidence=None):
    insert(
        conn,
        "audit_finding_actions",
        {
            "id": str(uuid4()),
            "finding_id": row["id"],
            "actor_id": g.actor["id"],
            "actor_name": g.actor["username"],
            "actor_role": g.actor["role"],
            "previous_status": previous,
            "status": row["status"],
            "reason": reason,
            "corrective_action": corrective_action,
            "evidence": evidence,
            "correlation_id": g.correlation_id,
        },
    )
    action = "AUDIT_FINDING_" + (
        "CREATED"
        if previous is None
        else "REOPENED"
        if previous == "PENDING_VERIFICATION" and row["status"] == "IN_PROGRESS"
        else row["status"]
    )
    reviewing = row["status"] == "PENDING_VERIFICATION"
    emit(
        conn,
        action,
        row["id"],
        row["tenant_id"],
        targets=("auditoria", "alertas"),
        metadata={
            "finding_id": str(row["id"]),
            "state": row["status"],
            "recipient_user_id": str(
                row["created_by"] if reviewing else row["assignee_id"]
            ),
            "recipient_role": "AUDITOR" if reviewing else "COORDINATOR",
            "recipient_tenant_id": str(
                row["tenant_id"] if reviewing else row["assignee_tenant_id"]
            ),
        },
    )


def register(app):
    @endpoint(
        app,
        "/api/v1/findings",
        roles=("AUDITOR", "COORDINATOR"),
        paginated=True,
        query=("status", "priority", "q"),
        summary="Hallazgos regionales para auditor o asignados al responsable",
    )
    def finding_list():
        with transaction() as conn:
            condition, values = "region_id=%s", [g.actor["region_id"]]
            if g.actor["role"] != "AUDITOR":
                condition += " AND assignee_id=%s"
                values.append(g.actor["id"])
            return listing(
                conn,
                "audit_findings",
                condition,
                values,
                filters={
                    "status": ("status", STATES),
                    "priority": ("priority", PRIORITIES),
                    "q": ("description", "assignee_name"),
                },
            )

    @endpoint(
        app,
        "/api/v1/findings",
        "POST",
        model=FindingCreate,
        roles=("AUDITOR",),
        status=201,
        summary="Registrar hallazgo con eventos o recurso autorizado y coordinador responsable",
    )
    def finding_create(data):
        assignee = call(
            "identidad_acceso",
            "GET",
            "/internal/v1/audit-assignees/" + data["assignee_id"],
        )

        def work(conn):
            linked = sorted(set(data["event_ids"]))
            for identifier in linked:
                event(conn, identifier)
            if (
                data["resource_id"]
                and not conn.execute(
                    BASE + "SELECT 1 FROM audit WHERE resource_refs ? %s LIMIT 1",
                    (g.actor["region_id"], data["resource_id"]),
                ).fetchone()
            ):
                raise invalid(
                    "Indica un recurso registrado en la bitácora de tu región.",
                    "resource_id",
                )
            row = insert(
                conn,
                "audit_findings",
                {
                    "id": str(uuid4()),
                    "tenant_id": g.actor["tenant_id"],
                    "region_id": g.actor["region_id"],
                    "description": data["description"],
                    "priority": data["priority"],
                    "assignee_id": assignee["id"],
                    "assignee_tenant_id": assignee["tenant_id"],
                    "assignee_name": assignee["username"],
                    "created_by": g.actor["id"],
                    "resource_id": data["resource_id"],
                    "evidence": data["evidence"],
                },
            )
            for identifier in linked:
                insert(
                    conn,
                    "audit_finding_links",
                    {"id": str(uuid4()), "finding_id": row["id"], "event_id": identifier},
                )
            history(
                conn,
                row,
                None,
                "Registro inicial del hallazgo",
                evidence=data["evidence"],
            )
            return row

        return atomic("finding_create", data, work)

    @endpoint(
        app,
        "/api/v1/findings/<identifier>",
        roles=("AUDITOR", "COORDINATOR"),
        summary="Hallazgo, referencias e historial inmutable de atención",
    )
    def finding_detail(identifier):
        with transaction() as conn:
            row = authorized(conn, identifier)
            row["events"] = conn.execute(
                "SELECT event_id FROM audit_finding_links WHERE finding_id=%s ORDER BY event_id",
                (identifier,),
            ).fetchall()
            row["history"] = conn.execute(
                "SELECT * FROM audit_finding_actions WHERE finding_id=%s ORDER BY created_at,id",
                (identifier,),
            ).fetchall()
            return row

    @endpoint(
        app,
        "/api/v1/findings/<identifier>/actions",
        "POST",
        model=FindingAction,
        roles=("AUDITOR", "COORDINATOR"),
        summary="Atención por responsable; cierre o devolución exclusivamente por auditor",
    )
    def finding_action(identifier, data):
        def work(conn):
            row = authorized(conn, identifier, True)
            if row["version"] != data["version"]:
                raise APIError(
                    "stale_version",
                    "El hallazgo cambió. Vuelve a abrirlo antes de registrar la atención.",
                    409,
                )
            previous, target = row["status"], data["status"]
            auditor = g.actor["role"] == "AUDITOR"
            permitted = (
                (not auditor and previous == "OPEN" and target == "IN_PROGRESS")
                or (
                    not auditor
                    and previous == "IN_PROGRESS"
                    and target in ("IN_PROGRESS", "PENDING_VERIFICATION")
                )
                or (
                    auditor
                    and previous == "PENDING_VERIFICATION"
                    and target in ("IN_PROGRESS", "CLOSED")
                )
            )
            if not permitted:
                raise APIError(
                    "transition_forbidden",
                    "Tu perfil no puede realizar ese cambio desde el estado actual del hallazgo.",
                    403,
                )
            if not auditor and not data["corrective_action"]:
                raise invalid(
                    "Describe la acción correctiva realizada o el plan de atención.",
                    "corrective_action",
                )
            if target in ("PENDING_VERIFICATION", "CLOSED") and not data["evidence"]:
                raise invalid(
                    "Documenta la evidencia que permite verificar la corrección.",
                    "evidence",
                )
            changed = update(
                conn,
                "audit_findings",
                identifier,
                {
                    "status": target,
                    "version": row["version"] + 1,
                    "updated_at": datetime.now(timezone.utc),
                    "evidence": data["evidence"] or row["evidence"],
                },
            )
            history(
                conn,
                changed,
                previous,
                data["reason"],
                data["corrective_action"],
                data["evidence"],
            )
            return changed

        return atomic("finding_action:" + identifier, data, work)
