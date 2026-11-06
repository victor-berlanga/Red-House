"""El verificador Compose consume los contratos vigentes contra servicios reales.

El transporte HTTP y los almacenes son los temporales del fixture. Solo se
adapta la lectura psql del contenedor a una conexión de comprobación local.
No acredita un despliegue Compose completo ni políticas clínicas productivas.
"""

import importlib.util
from pathlib import Path

from psycopg.rows import dict_row
import pytest


@pytest.mark.parametrize("kind,component", [("BLOOD", "RBC"), ("ORGAN", "KIDNEY")])
def test_compose_verifier_uses_current_custody_contract(p, kind, component):
    path = Path(__file__).resolve().parents[3] / "deployment/verify.py"
    spec = importlib.util.spec_from_file_location("correction_deployment_verify", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    verifier = object.__new__(module.Deployment)
    verifier.env = p.env
    verifier.request = p.request
    verifier.checks = []

    def query(service, statement, params=()):
        p.drain()
        with p.owner(service) as conn:
            with conn.cursor(row_factory=dict_row) as cursor:
                cursor.execute(statement, params)
                return cursor.fetchall()

    verifier.query = query
    unit = verifier.flow(kind, component)
    verifier.business_reads()
    assert verifier.checks[0]["persistence"][0]["status"] == "RECEIVED"
    assert verifier.checks[0]["resource_id"] == unit["id"]
    chain = p.ok(
        "custodia",
        "GET",
        "/api/v1/chains/" + verifier.shipment["id"],
        user="transport1",
    )
    assert len(chain["events"]) == 6
