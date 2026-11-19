"""Real Chrome, TLS and autonomous modular web with all API listeners stopped."""

import json
import os
import secrets
import subprocess
import threading
import time
from pathlib import Path
from uuid import uuid4

import pytest
from werkzeug.serving import make_server, make_ssl_devcert

from .conftest import QuietHandler
from .helpers import iso
from .test_continuity import stopped_apis
from .test_correction_backend import laboratory
from .test_final_quality import api
from .test_stage02_corrections import graph_body
from .test_web_integration import create_app


# Corrida separada (Operacion_y_reproduccion.md): el enrolamiento MFA revoca las
# sesiones de medical1, medical2 y auditor1 de la plataforma compartida, así que
# en la suite completa dejaría en 401 a todas las pruebas posteriores.
@pytest.mark.skipif(
    not os.environ.get("REDHOUSE_STAGE02_EVIDENCE"),
    reason="Requiere REDHOUSE_STAGE02_EVIDENCE, Chrome y Playwright; se ejecuta en una corrida separada porque el enrolamiento MFA revoca las sesiones compartidas.",
)
def test_stage02_real_browser_autonomous_reinforced(p, tmp_path):
    from ms_identidad_acceso.strong_auth import totp

    unit = api(
        p,
        "inventario",
        "/api/v1/resources",
        {
            "folio": "BR02-" + uuid4().hex[:10],
            "kind": "BLOOD",
            "component": "RBC",
            "blood_group": "O-",
            "expires_at": iso(days=2),
        },
        user="operator1",
    )
    _profile, _body, result = laboratory(p, unit, "json")
    policy = api(
        p,
        "compatibilidad",
        "/api/v1/laboratory/profiles",
        {
            "name": "Política sintética navegador",
            "kind": "BLOOD",
            "component": "RBC",
            "version": 1,
            "required_tests": ["ABO"],
            "source": "Ensayo sintético navegador",
            "synthetic": True,
            "effective_at": iso(minutes=-60),
            "policy": {
                "version": "COMPLETENESS-2.0",
                "ranking_order": "URGENCY_WAIT_EXPIRY_TIME_DISTANCE_ID",
                "urgency_scale": "CAPTURED_1_3_SYNTHETIC",
            },
        },
    )
    rec = api(
        p,
        "receptores",
        "/api/v1/recipients",
        {
            "folio": "BR02-P-" + uuid4().hex[:8],
            "display_name": "Receptor ficticio navegador",
            "kind": "BLOOD",
            "blood_group": "O+",
            "studies": "Datos ficticios",
        },
    )
    req = api(
        p,
        "receptores",
        "/api/v1/requests",
        {"recipient_id": rec["id"], "component": "RBC", "quantity": 1, "urgency": 2},
    )
    api(
        p,
        "priorizacion_geografia",
        "/api/v1/routes",
        {
            "origin_id": p.env.state["tenants"][0],
            "destination_id": p.env.state["tenants"][0],
            "distance_km": 2.0,
            "travel_minutes": 5,
            "source": "Ruta sintética interna",
        },
        user="coordinator1",
    )
    graph = api(p, "priorizacion_geografia", "/api/v1/regional-graphs", graph_body())
    enrollment = api(
        p,
        "identidad_acceso",
        "/api/v1/auth/mfa/enrollment",
        {"username": "medical1", "password": p.env.state["password"]},
        user=None,
    )
    counter = int(time.time()) // 30 - 1
    api(
        p,
        "identidad_acceso",
        "/api/v1/auth/mfa/confirm",
        {
            "challenge": enrollment["challenge"],
            "code": totp(enrollment["secret"], counter),
        },
        user=None,
    )
    other_secrets = {}
    for username in ("medical2", "auditor1"):
        enrolled = api(
            p,
            "identidad_acceso",
            "/api/v1/auth/mfa/enrollment",
            {"username": username, "password": p.env.state["password"]},
            user=None,
        )
        api(
            p,
            "identidad_acceso",
            "/api/v1/auth/mfa/confirm",
            {
                "challenge": enrolled["challenge"],
                "code": totp(enrolled["secret"], int(time.time()) // 30 - 1),
            },
            user=None,
        )
        other_secrets[username] = enrolled["secret"]
    configs = {
        name: dict(
            app.config,
            OPERATION_SCOPE="ACADEMIC",
            MFA_REQUIRED_ROLES=["MEDICAL", "AUDITOR"],
            REAUTH_REQUIRED_OPERATIONS=[
                "resource_release",
                "lab_result_review",
                "evaluation_review",
                "reservation_create",
                "rule_transition",
                "anomaly_resolve",
            ],
            REQUIRE_LAB_PROFILE=True,
            REQUIRE_ORGAN_AUTHORIZATION=True,
        )
        for name, app in p.apps.items()
    }
    web = create_app(
        {
            "SECRET_KEY": secrets.token_hex(32),
            "JWT_SECRET_KEY": secrets.token_hex(32),
            "BACKEND_MODE": "monolith",
            "TESTING": True,
            "PRODUCTION": True,
            "SESSION_COOKIE_SECURE": True,
            "HIGHCHARTS_ENABLED": False,
            "MICROSERVICES_CONFIG": dict(
                SERVICE_URLS=p.urls,
                DOMAIN_CONFIGS=configs,
                **p.env.state["web_sessions"],
            ),
        }
    )
    cert = make_ssl_devcert(str(tmp_path / "web-cert"), host="localhost")
    server = make_server(
        "127.0.0.1",
        0,
        web,
        threaded=True,
        request_handler=QuietHandler,
        ssl_context=cert,
    )
    threading.Thread(target=server.serve_forever, daemon=True).start()
    output = Path(os.environ["REDHOUSE_STAGE02_EVIDENCE"]) / "browser"
    output.mkdir(parents=True, exist_ok=True)
    kernel = web.extensions["application_kernel"]
    stop = threading.Event()
    worker_errors = []

    def drain():
        while not stop.wait(0.5):
            try:
                kernel.drain(100)
            except (RuntimeError, OSError) as exc:
                worker_errors.append(type(exc).__name__)

    worker = threading.Thread(target=drain, daemon=True)
    try:
        with stopped_apis(p):
            worker.start()
            completed = subprocess.run(
                [
                    "node",
                    str(
                        Path(__file__).resolve().parents[3]
                        / "scripts/verify_stage02.cjs"
                    ),
                ],
                input=json.dumps(
                    {
                        "base": "https://localhost:" + str(server.server_port),
                        "output": str(output),
                        "password": p.env.state["password"],
                        "secret": enrollment["secret"],
                        "otherSecrets": other_secrets,
                        "counter": counter,
                        "unit": unit,
                        "result": result,
                        "request": req,
                        "policy": policy,
                        "graph": graph,
                    }
                ),
                text=True,
                capture_output=True,
                timeout=900,
                check=False,
            )
            assert completed.returncode == 0, completed.stdout + completed.stderr
        report = json.loads((output / "results.json").read_text())
        assert report["passed"] and not report["consoleErrors"]
        assert not worker_errors
        with p.owner("priorizacion_geografia") as conn:
            assert (
                conn.execute(
                    "SELECT count(*) FROM decision_runs WHERE id=ANY(%s::uuid[])",
                    (report["runs"],),
                ).fetchone()[0]
                == 6
            )
    finally:
        stop.set()
        worker.join(timeout=5) if worker.is_alive() else None
        server.shutdown()
        server.server_close()
