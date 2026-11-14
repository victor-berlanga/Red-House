"""Contratos y correlación puros; no crea QApplication, sesiones ni motores."""

from copy import deepcopy
from pathlib import Path
from uuid import uuid4

import pytest
from lxml import etree
from redhouse_desktop import client
from redhouse_desktop.client import ContractError
from redhouse_desktop.institutional_catalogue import (
    COMMANDS,
    PATCH_OPERATIONS,
    SCHEMAS,
    catalogue_body,
    validate_catalogue_item,
    validate_catalogue_result,
)


def site(tenant):
    return {
        "id": str(uuid4()),
        "tenant_id": tenant,
        "kind": "sites",
        "name": "Sede Norte",
        "municipality": "Monterrey",
        "address": "Domicilio sintético",
        "active": True,
        "version": 3,
        "parent_id": None,
    }


def capacity(tenant):
    return {
        "id": str(uuid4()),
        "tenant_id": tenant,
        "kind": "capacities",
        "name": "Capacidad declarada",
        "component": "Componente documentado",
        "quantity": 0,
        "parent_id": str(uuid4()),
        "active": True,
        "version": 4,
    }


@pytest.mark.parametrize("kind", ["sites", "capacities"])
def test_body_preserves_documented_version_and_parent(kind):
    original = site(str(uuid4())) if kind == "sites" else capacity(str(uuid4()))
    fields = (
        ("name", "municipality", "address")
        if kind == "sites"
        else ("name", "parent_id", "component", "quantity")
    )
    values = {key: original[key] for key in fields}
    untouched = deepcopy(original)
    created = catalogue_body(kind, values)
    assert set(created) == set(fields)
    values.update(
        active=False, reason="Corrección autorizada de prueba", human_confirmation=True
    )
    corrected = catalogue_body(kind, values, original)
    assert corrected["version"] == original["version"]
    assert corrected["active"] is False
    assert original == untouched
    if kind == "capacities":
        with pytest.raises(ValueError):
            catalogue_body(kind, dict(values, parent_id=str(uuid4())), original)
    with pytest.raises(ValueError):
        catalogue_body(kind, dict(values, version=99), original)
    with pytest.raises(ValueError):
        catalogue_body(kind, dict(values, human_confirmation=False), original)


@pytest.mark.parametrize("quantity", [-1, 100001, True, "12"])
def test_capacity_rejects_invalid_contract_quantity(quantity):
    row = capacity(str(uuid4()))
    with pytest.raises(ValueError):
        catalogue_body(
            "capacities",
            {
                key: quantity if key == "quantity" else row[key]
                for key in ("name", "parent_id", "component", "quantity")
            },
        )


@pytest.mark.parametrize("kind", ["sites", "capacities"])
def test_all_four_bodies_validate_existing_owner_xsd(kind, monkeypatch):
    # Solo se leen archivos contractuales; no se importa código del servidor.
    owner = (
        Path(__file__).resolve().parents[2] / "services/ms_identidad_acceso/contracts"
    )
    monkeypatch.setattr(client, "CONTRACTS", owner)
    row = site(str(uuid4())) if kind == "sites" else capacity(str(uuid4()))
    fields = (
        ("name", "municipality", "address")
        if kind == "sites"
        else ("name", "parent_id", "component", "quantity")
    )
    values = {key: row[key] for key in fields}
    for suffix, item in (("create", None), ("edit", row)):
        if item:
            values.update(
                active=True, reason="Corrección documentada", human_confirmation=True
            )
        body = catalogue_body(kind, values, item)
        operation = kind + "_" + suffix
        xml = client.request_xml(body, COMMANDS[operation][2])
        document = etree.fromstring(xml)
        assert document.tag == "request"
        assert document.findtext("version") == (str(row["version"]) if item else None)


@pytest.mark.parametrize("kind", ["sites", "capacities"])
def test_result_requires_same_scope_fields_and_incremented_version(kind):
    tenant = str(uuid4())
    row = site(tenant) if kind == "sites" else capacity(tenant)
    fields = (
        ("name", "municipality", "address")
        if kind == "sites"
        else ("name", "parent_id", "component", "quantity")
    )
    values = {key: row[key] for key in fields}
    values.update(
        active=False, reason="Corrección autorizada de prueba", human_confirmation=True
    )
    body = catalogue_body(kind, values, row)
    result = dict(row, version=row["version"] + 1, active=False)
    assert (
        validate_catalogue_result(kind + "_edit", row["id"], body, result, tenant)
        == result
    )
    for changed in (
        dict(result, id=str(uuid4())),
        dict(result, tenant_id=str(uuid4())),
        dict(result, version=row["version"]),
        dict(result, name="Otro registro"),
        dict(result, active=True),
    ):
        with pytest.raises(ContractError):
            validate_catalogue_result(kind + "_edit", row["id"], body, changed, tenant)


def test_rows_reject_foreign_scope_and_missing_fields():
    tenant = str(uuid4())
    row = site(tenant)
    assert validate_catalogue_item("sites", row, tenant) is row
    for invalid in (
        dict(row, tenant_id=str(uuid4())),
        dict(row, kind="capacities"),
        dict(row, municipality=None),
        dict(row, version=True),
    ):
        with pytest.raises(ContractError):
            validate_catalogue_item("sites", invalid, tenant)


@pytest.mark.parametrize("kind", ["sites", "capacities"])
def test_creation_receipt_does_not_confirm_another_record(kind):
    tenant = str(uuid4())
    row = site(tenant) if kind == "sites" else capacity(tenant)
    row["version"] = 1
    fields = (
        ("name", "municipality", "address")
        if kind == "sites"
        else ("name", "parent_id", "component", "quantity")
    )
    body = catalogue_body(kind, {key: row[key] for key in fields})
    assert validate_catalogue_result(kind + "_create", None, body, row, tenant) == row
    for changed in (
        dict(row, name="Registro distinto"),
        dict(row, tenant_id=str(uuid4())),
        dict(row, version=True),
        dict(row, version=2),
        dict(row, active=False),
    ):
        with pytest.raises(ContractError):
            validate_catalogue_result(kind + "_create", None, body, changed, tenant)


def test_command_handoff_has_only_real_catalogue_routes():
    assert set(COMMANDS) == {
        "sites_create",
        "sites_edit",
        "capacities_create",
        "capacities_edit",
    }
    assert set(SCHEMAS["ms_identidad_acceso"]) == set(COMMANDS)
    assert PATCH_OPERATIONS == {"sites_edit", "capacities_edit"}
    for operation, (service, path, schema, identifier) in COMMANDS.items():
        assert service == "identidad-acceso"
        assert path == "/api/v1/catalogues/" + operation.rsplit("_", 1)[0] + (
            "/{id}" if identifier else ""
        )
        assert schema == operation + ".xsd"
