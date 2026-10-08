from typing import Annotated

from pydantic import Field

from .models import ID, Model, Text


class Event(Model):
    event_id: ID
    source: Text
    action: Text
    resource_id: Text
    tenant_id: ID
    region_id: ID | None
    actor_id: ID | None
    correlation_id: ID
    occurred_at: Text
    metadata: dict
