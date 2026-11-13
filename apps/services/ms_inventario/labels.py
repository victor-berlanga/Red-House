"""Authorize traceable label issuance without claiming a physical print occurred."""

from typing import Annotated, Literal

from pydantic import Field

from redhouse.api import atomic, endpoint
from redhouse.db import get, transaction
from redhouse.decisions import record
from redhouse.errors import APIError
from redhouse.events import emit
from redhouse.extension_contracts import schema
from redhouse.models import ID, Confirm, Model, Text
from redhouse.security import own


class LabelRequest(Confirm):
    version: Annotated[int, Field(ge=1)]
    action: Literal["EXPORT_PDF", "PRINT"]


class LabelIssuance(Model):
    issuance_id: ID
    resource_id: ID
    resource_version: int
    action: Literal["EXPORT_PDF", "PRINT"]
    issued_at: Text
    reissue: bool


def install(app):
    @endpoint(
        app,
        "/api/v1/resources/<identifier>/label-issuances",
        "POST",
        model=LabelRequest,
        roles=("OPERATOR", "MEDICAL"),
        status=201,
        result=schema(LabelIssuance),
    )
    def label_issue(identifier, data):
        def work(conn):
            resource = get(conn, "resources", identifier, True)
            own(resource["current_institution_id"])
            if resource["version"] != data["version"]:
                raise APIError(
                    "stale_version",
                    "La unidad cambió. Actualiza antes de emitir su etiqueta.",
                    412,
                )
            # The resource lock serializes concurrent issuances. Existing durable
            # domain events are the source of truth; no second label store is needed.
            reissue = (
                conn.execute(
                    "SELECT 1 FROM activity_events WHERE tenant_id=%s "
                    "AND event->>'resource_id'=%s "
                    "AND event->>'action'='LABEL_ISSUANCE_AUTHORIZED' LIMIT 1",
                    (resource["current_institution_id"], identifier),
                ).fetchone()
                is not None
            )
            record(
                conn,
                identifier,
                resource["current_institution_id"],
                "LABEL_ISSUANCE_AUTHORIZED",
                data["reason"],
                {"label_action": data["action"], "version": resource["version"]},
            )
            event = emit(
                conn,
                "LABEL_ISSUANCE_AUTHORIZED",
                identifier,
                resource["current_institution_id"],
                metadata={
                    "label_action": data["action"],
                    "resource_version": resource["version"],
                    "reissue": reissue,
                },
            )
            return {
                "issuance_id": event["event_id"],
                "resource_id": identifier,
                "resource_version": resource["version"],
                "action": data["action"],
                "issued_at": event["occurred_at"],
                "reissue": reissue,
            }

        result = atomic("label_issue:" + identifier, data, work)
        # An idempotent response may predate a transfer or correction. It does
        # not grant the old institution permission to issue the label again.
        with transaction() as conn:
            current = get(conn, "resources", identifier)
            own(current["current_institution_id"])
            if current["version"] != data["version"]:
                raise APIError(
                    "stale_version",
                    "La unidad cambió. Actualiza antes de emitir su etiqueta.",
                    412,
                )
        return result
