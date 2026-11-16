"""Selección y repetición de la migración 21, sin arrancar PostgreSQL."""

from pathlib import Path
from unittest.mock import Mock

import pytest
from redhouse import extension_schema, shared_migrations


@pytest.fixture
def migration_context(monkeypatch):
    views, grants = Mock(), Mock()
    monkeypatch.setattr(extension_schema, "views", views)
    monkeypatch.setattr(extension_schema, "grants", grants)
    migration = (
        Path(shared_migrations.__file__).parent / "shared_migrations/021.sql"
    ).read_text()
    return views, grants, migration


def test_upgrade_20_applies_21_once_and_skips_it_on_resume(migration_context):
    views, grants, migration = migration_context
    installed = set(range(6, 21))
    statements = []

    def execute(statement):
        statements.append(statement)
        if statement == "SELECT version FROM red_house.schema_migration":
            return [(version,) for version in sorted(installed)]
        if statement == migration:
            installed.add(21)
        return Mock(fetchone=lambda: None)

    connection = Mock(execute=execute)
    assert shared_migrations.upgrade(connection) == 21
    assert shared_migrations.upgrade(connection) == 21
    assert statements[0] == "SELECT pg_advisory_xact_lock(72182027)"
    assert statements.count(migration) == 1
    assert installed == set(range(6, 22))
    assert views.call_count == grants.call_count == 2


def test_failed_index_creation_propagates_before_view_or_grant_updates(migration_context):
    views, grants, migration = migration_context

    def execute(statement):
        if statement == "SELECT version FROM red_house.schema_migration":
            return [(version,) for version in range(6, 21)]
        if statement == migration:
            raise RuntimeError("index creation failed")
        return Mock(fetchone=lambda: None)

    with pytest.raises(RuntimeError, match="index creation failed"):
        shared_migrations.upgrade(Mock(execute=execute))
    views.assert_not_called()
    grants.assert_not_called()


def test_unknown_newer_schema_is_rejected_before_changes(migration_context):
    views, grants, migration = migration_context
    connection = Mock()
    connection.execute.side_effect = [None, [(6,), (22,)]]
    with pytest.raises(RuntimeError, match="Versión compartida no compatible"):
        shared_migrations.upgrade(connection)
    assert migration not in [call.args[0] for call in connection.execute.call_args_list]
    views.assert_not_called()
    grants.assert_not_called()
