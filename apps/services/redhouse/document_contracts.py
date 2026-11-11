"""Contratos de Documentos y del adaptador v1 de Transporte, sin reglas de negocio."""

from typing import Annotated, Literal

from pydantic import Field

from redhouse.models import ID, Model, Text, Confirm


class Upload(Model):
    mime_type: Literal["image/jpeg", "image/png", "application/pdf"]
    size: Annotated[int, Field(ge=1, le=10485760)]
    sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]


class DocumentCreate(Upload):
    subject_kind: Literal["DONOR", "RESULT", "ACCREDITATION", "REQUEST", "RULE"]
    subject_id: ID
    category: Literal[
        "CONSENT", "LAB_RESULT", "ACCREDITATION", "AUTHORIZATION", "RULE_APPROVAL"
    ]
    supersedes: ID | None = None
    retention_until: Text | None = None
    policy_reference: Text


class Metadata(Model):
    id: ID
    tenant_id: ID
    category: Text
    subject_kind: Text
    subject_id: ID
    version: int
    supersedes: ID | None
    privacy: Literal["PRIVATE"]
    retention_until: Text | None
    legal_hold: bool
    policy_reference: Text
    created_at: Text
    policy_version: int = 1


class Prepared(Model):
    id: ID
    metadata: Metadata
    upload_url: str
    expires_in: int
    upload_headers: dict[str, str]


class VerifiedMetadata(Metadata):
    generation: Text
    sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    analysis: Literal["CLEAN"]
    file_status: Literal["VERIFIED"]


class DocumentStatus(Metadata):
    file_status: str
    analysis: str
    policy_version: int


class ConservationChange(Confirm):
    policy_version: Annotated[int, Field(ge=1)]
    retention_until: Text | None = None
    legal_hold: bool
    policy_reference: Text


class ReportCreate(Model):
    report: Literal[
        "INVENTORY",
        "EXPIRY",
        "REQUESTS",
        "SHIPMENTS",
        "ACTIVITY",
        "CUSTODY",
        "TRACEABILITY",
    ]
    subject_id: ID | None = None
    format: Literal["CSV", "PDF", "XLSX"]
    from_at: Text
    until_at: Text
    order: Literal["ID_ASC", "DATE_DESC"] = "DATE_DESC"
    filters: dict[str, Text] = Field(default_factory=dict)
    timezone: Text = "UTC"


class Job(Model):
    id: ID
    tenant_id: ID
    user_id: ID
    report: Text
    format: Text
    status: Text
    file_id: ID | None
    last_error: Text | None
    attempts: int
    created_at: Text
    context: dict = Field(default_factory=dict)
