import os
from pathlib import Path
from uuid import uuid4

import psycopg
from psycopg import sql
from psycopg.conninfo import make_conninfo
from psycopg.rows import dict_row
import pytest

from src.cli import seed_demo
from src.data_access.migrations import migrate


@pytest.fixture
def legacy_database():
    base=os.getenv('TEST_POSTGRES_URL')
    if not base: pytest.skip('Requiere clúster exclusivo de pruebas.')
    name='red_house_migration_'+uuid4().hex
    with psycopg.connect(base,autocommit=True) as conn:
        conn.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(name)))
    try:
        with psycopg.connect(make_conninfo(base,dbname=name),row_factory=dict_row,
            options='-c search_path=red_house,pg_catalog') as conn:
            source=Path(__file__).resolve().parents[3]/'data/database/schema.sql'
            conn.execute(source.read_text())
            seed_demo(conn,'Synthetic-Migration-Only-Password')
            conn.commit()
            yield conn
    finally:
        with psycopg.connect(base,autocommit=True) as conn:
            conn.execute(sql.SQL('DROP DATABASE {}').format(sql.Identifier(name)))


def snapshot(conn):
    return {table:conn.execute(sql.SQL('SELECT * FROM {} ORDER BY {}').format(sql.Identifier(table),sql.Identifier(key))).fetchall()
        for table,key in [('user_account','account_id'),('blood_unit','resource_id'),('blood_movement','movement_id'),('audit_event','event_id')]}


def test_upgrade_preserves_existing_accounts_units_and_history(legacy_database):
    conn=legacy_database
    before=snapshot(conn)
    assert migrate(conn)==['002_regional.sql']
    assert snapshot(conn)==before
    conn.commit()
    assert migrate(conn)==[]
    assert conn.execute("SELECT count(*) AS n FROM information_schema.tables WHERE table_schema='red_house' AND table_type='BASE TABLE'").fetchone()['n']==38
    assert snapshot(conn)==before


def test_failed_upgrade_rolls_back_all_schema_changes(legacy_database):
    conn=legacy_database
    # Dato legado posible bajo el esquema anterior, incompatible con el ámbito nuevo.
    conn.execute("UPDATE account_role SET role_code='MEDICAL' WHERE role_code='ADMIN'")
    conn.commit()
    before=snapshot(conn)
    with pytest.raises(psycopg.errors.CheckViolation):
        with conn.transaction(): migrate(conn)
    assert conn.execute("SELECT to_regclass('red_house.donor') AS x").fetchone()['x'] is None
    assert conn.execute("SELECT to_regclass('red_house.schema_migration') AS x").fetchone()['x'] is None
    assert snapshot(conn)==before
    assert not conn.execute("SELECT is_enabled FROM role WHERE role_code='MEDICAL'").fetchone()['is_enabled']
