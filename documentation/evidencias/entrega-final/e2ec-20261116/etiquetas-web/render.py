"""Render estático del template real y sus estilos; no crea aplicación ni conexiones."""

import hashlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

from flask import Flask
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / "apps/web"))
from src.integration.routes.common import display_html

OUTPUT = ROOT / ".local/artifacts/lineage-labels-20261116"
OUTPUT.mkdir(parents=True, exist_ok=True)
templates = ROOT / "apps/web/src/presentation/templates"
static = ROOT / "apps/web/src/presentation/static"
environment = Environment(loader=FileSystemLoader(templates), autoescape=select_autoescape())
environment.filters["portal_html"] = display_html


def local_url(endpoint, **values):
    if endpoint == "static":
        return (static / values["filename"]).as_uri()
    return "#synthetic-" + endpoint.replace(".", "-")


environment.globals.update(
    url_for=local_url,
    csrf_token=lambda: "synthetic-not-a-session",
    get_flashed_messages=lambda **_kwargs: [],
)
principal = SimpleNamespace(
    party_name="Operador sintético", role_name="Operador", role_code="OPERATOR",
    institution_name="Institución sintética", institution_id="synthetic",
    region_name="Región sintética", can=lambda _permission: True,
)
children = [
    {"id": "synthetic-a", "folio": "SINTETICO-DER-01", "component": "RBC",
     "status": "AVAILABLE", "expires_at": "2026-11-20T18:00:00+00:00"},
    {"id": "synthetic-b", "folio": "SINTETICO-DER-02", "component": "RBC",
     "status": "QUARANTINE", "expires_at": "2026-11-20T18:00:00+00:00"},
]
app = Flask("lineage-template-render-only")
app.config["DEFAULT_DISPLAY_TIMEZONE"] = "America/Monterrey"
with app.test_request_context("/inventario/synthetic/linaje"):
    rendered = environment.get_template("integration/lineage.html").render(
        title="Linaje · SINTETICO-ORIGEN", active="inventory", principal=principal,
        integration_mode=True, display_timezone="America/Monterrey",
        timezone_choices={"UTC": "UTC", "America/Monterrey": "Monterrey"},
        navigation=[("Operación", "inventory", "Inventario", "package", "inventory.index", {}, "inventory", False)],
        request=SimpleNamespace(full_path="/inventario/synthetic/linaje"),
        unit={"id": "synthetic-parent", "donation_id": "DONACION-SINTETICA"},
        children=children,
    )
assert ">RBC<" not in rendered and ">AVAILABLE<" not in rendered and ">QUARANTINE<" not in rendered
assert rendered.count(">Eritrocitos<") == 2
assert ">Disponible<" in rendered and ">Cuarentena<" in rendered
assert 'datetime="2026-11-20T18:00:00+00:00"' in rendered
assert "20/11/2026 · 12:00" in rendered
(OUTPUT / "lineage.html").write_text(rendered)
files = [templates / name for name in ("integration/lineage.html", "base.html", "integration/row_actions.html", "macros.html")]
files += [static / name for name in ("css/app.css", "css/integration.css")]
files += [ROOT / "apps/web/src/integration/routes/common.py"]
(OUTPUT / "render.json").write_text(json.dumps({
    "passed": True, "synthetic_rows": 2, "real_template": True,
    "database": False, "authenticated_flow": False, "links_exercised": False,
    "timezone": "America/Monterrey", "utc_datetime_preserved": True,
    "hashes": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
}, indent=2) + "\n")
print("Render sintético aprobado; sin bases ni peticiones HTTP.")
