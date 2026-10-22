from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class Principal:
    account_id: UUID
    party_name: str
    role_code: str
    role_name: str
    institution_id: UUID | None
    region_name: str
    institution_name: str

    @classmethod
    def from_row(cls, row):
        return cls(**{field: row[field] for field in cls.__dataclass_fields__})

    def can(self, action):
        # Los permisos concretos los define RemotePrincipal y los valida la API.
        return False


class BusinessError(Exception):
    def __init__(self, message, status=400, *, field=None, details=None, code=None):
        super().__init__(message)
        self.message, self.status, self.field = message, status, field
        self.details, self.code = details or [], code


def require(principal, action):
    if not principal or not principal.can(action):
        raise BusinessError("Tu perfil no tiene permiso para esta operación.", 403)
