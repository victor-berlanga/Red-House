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
        return action in {
            "ADMIN": {"dashboard", "administration", "preview"},
            "OPERATOR": {"dashboard", "inventory.read", "inventory.write", "preview"},
            "AUDITOR": {"dashboard", "inventory.read", "audit.read", "preview"},
        }.get(self.role_code, set())

    def includes(self, institution_id, region_name):
        return (str(self.institution_id) == str(institution_id) if self.institution_id
                else self.region_name == region_name)


class BusinessError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.message, self.status = message, status


def require(principal, action):
    if not principal or not principal.can(action):
        raise BusinessError("Tu perfil no tiene permiso para esta operación.", 403)


def check_version(row, value):
    if row is None:
        raise BusinessError("El registro no está disponible en tu ámbito.", 404)
    if row["version_no"] != value:
        raise BusinessError("Este registro cambió mientras lo editabas. Recarga y revisa los cambios.", 409)
