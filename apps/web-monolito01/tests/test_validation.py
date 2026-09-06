from datetime import timezone
from uuid import uuid4

import pytest

from src.business import validators as v
from src.business.access import BusinessError, Principal


@pytest.mark.parametrize("data", [{"code":""}, {"code":"a b"}, {"code":"<script>"}, {"code":"x"}])
def test_invalid_codes(data):
    with pytest.raises(BusinessError):
        v.code(data, "code", "código")


def test_atomic_validation():
    assert v.code({"code":" rh-demo-9 "}, "code", "código") == "RH-DEMO-9"
    assert v.timestamp({"date":"2026-01-02T12:00"}, "date").tzinfo == timezone.utc
    for value in ("NaN", "1.5", "0", "-1", "7201"):
        with pytest.raises(BusinessError):
            v.integer({"hours":value}, "hours", 1, 720)


def test_permissions_do_not_imply_hierarchy():
    admin = Principal(uuid4(), "TEST", "ADMIN", "Admin", None, "TEST", "TEST")
    assert admin.can("administration")
    assert not admin.can("inventory.write")
    assert not admin.can("audit.read")
    assert not admin.can("unknown")


def test_institution_scope_does_not_grant_region():
    institution_id = uuid4()
    principal = Principal(uuid4(), "TEST", "OPERATOR", "Operator", institution_id, "TEST", "TEST")
    assert principal.includes(institution_id, "TEST")
    assert not principal.includes(uuid4(), "TEST")
