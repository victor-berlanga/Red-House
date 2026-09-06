"""Integración real: cada prueba crea y retira SOLO su BD aleatoria recién creada."""
import os
import re
import secrets
import sys
from pathlib import Path
from uuid import uuid4

import psycopg
import pytest
from psycopg import sql
from psycopg.conninfo import make_conninfo
from psycopg.rows import dict_row

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import create_app
from src.cli import seed_demo
from src.data_access.connection import transaction


def pytest_addoption(parser):
    parser.addoption("--browser", action="store_true", help="Ejecutar también el flujo en Chrome mediante Playwright")


def csrf(client, path="/login"):
    response = client.get(path)
    match = re.search(rb'name="csrf_token" value="([^"]+)"', response.data)
    assert match, (response.status_code, response.data[:300])
    return match[1].decode()


@pytest.fixture
def app():
    base = os.getenv("TEST_POSTGRES_URL")
    if not base:
        pytest.skip("Define TEST_POSTGRES_URL hacia un clúster PostgreSQL de pruebas con permiso CREATEDB.")
    name = "red_house_test_" + uuid4().hex
    # Nunca se reutiliza ni se limpia una base indicada por el usuario.
    with psycopg.connect(base, autocommit=True) as control:
        control.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
    test_password = secrets.token_urlsafe(24)
    application = create_app({"TESTING": True, "PRODUCTION": False, "SESSION_COOKIE_SECURE": False,
        "DATABASE_URL": make_conninfo(base, dbname=name), "SECRET_KEY": secrets.token_hex(32),
        "JWT_SECRET_KEY": secrets.token_hex(32), "HIGHCHARTS_ENABLED": False, "DEMO_TEST_PASSWORD": test_password})
    try:
        with application.app_context(), transaction() as conn:
            conn.execute(application.config["SCHEMA_PATH"].read_text(encoding="utf-8"))
            seed_demo(conn, test_password)
        yield application
    finally:
        with psycopg.connect(base, autocommit=True) as control:
            control.execute(sql.SQL("DROP DATABASE {}").format(sql.Identifier(name)))


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def sign_in(app):
    def run(client, role="operador"):
        response = client.post("/login", data={"csrf_token": csrf(client), "login_email": role + "@red-house.test",
                                              "password": app.config["DEMO_TEST_PASSWORD"]})
        assert response.status_code == 302
        return response
    return run


@pytest.fixture
def db(app):
    # No mantener un app_context entre peticiones: g (incluido CSRF) debe ser por petición.
    with psycopg.connect(app.config["DATABASE_URL"], row_factory=dict_row,
                         options="-c search_path=red_house,pg_catalog -c timezone=UTC") as conn:
        yield conn
