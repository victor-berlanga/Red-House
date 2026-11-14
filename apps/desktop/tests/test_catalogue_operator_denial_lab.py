"""Negativa XML independiente de alta institucional por operador."""
from uuid import uuid4

import pytest
from redhouse_desktop.client import ApiError, Client
from test_real_lab import gateway as gateway  # noqa: PLC0414 - fixture compartido
from tests.conftest import platform as platform  # noqa: PLC0414 - fixture compartido


def test_operator_cannot_create_site_xml(platform, gateway):
    client = Client(gateway)
    try:
        client.login('operator1', platform.env.state['password'], '')
        with pytest.raises(ApiError) as denied:
            client.authorized(
                'identidad-acceso', '/api/v1/catalogues/sites', 'sites_create',
                method='POST', body={'name': 'No autorizado', 'municipality': 'Monterrey', 'address': 'Sintética'},
                request_schema='sites_create.xsd', key=str(uuid4()),
            )
        assert denied.value.status == 403
    finally:
        client.logout()
