"""Índice de capturas nativas de Swagger; no genera ni altera imágenes."""

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "documentation/evidencias/gcp/swagger-endpoints"
manifest = json.loads((OUTPUT / "manifest.json").read_text())
inventory = json.loads((OUTPUT / "inventory.json").read_text())
captures = manifest["captures"]
rows = []
coverage = {}
for service, operations in inventory.items():
    public = [op for op in operations if not op["internal"]]
    successful = [c for c in captures if c["service"] == service and c["result"] == "success"]
    errors = [c for c in captures if c["service"] == service and c["result"] == "error"]
    missing = [
        op
        for op in public
        if not any(c["method"] == op["method"] and c["route"] == op["path"] for c in successful)
    ]
    coverage[service] = {
        "public_endpoints": len(public),
        "success_captures": len(successful),
        "error_captures": len(errors),
        "missing": missing,
        "internal_excluded": [op for op in operations if op["internal"]],
    }
    rows.append(f"<h2>{html.escape(service)}</h2><p>{len(successful)}/{len(public)} operaciones exitosas; {len(errors)} captura de error.</p><table><thead><tr><th>Método</th><th>Endpoint</th><th>HTTP</th><th>Captura real</th></tr></thead><tbody>")
    error_operations = {(c["method"], c["route"]) for c in errors}
    service_captures = [c for c in captures if c["service"] == service]
    service_captures.sort(key=lambda c: (0 if (c["method"], c["route"]) in error_operations else 1, c["route"], c["method"], 0 if c["result"] == "error" else 1))
    for item in service_captures:
        label = "Error de autorización" if item["result"] == "error" else "Resultado exitoso"
        rows.append(
            f'<tr><td>{item["method"]}</td><td><code>{html.escape(item["route"])}</code><br>{html.escape(item["label"])}</td>'
            f'<td>{item["status"]}</td><td><a href="{html.escape(item["capture"])}">{label}</a></td></tr>'
        )
    rows.append("</tbody></table>")
    if missing:
        rows.append("<p>Pendientes: " + ", ".join(html.escape(op["method"] + " " + op["path"]) for op in missing) + "</p>")

total = sum(v["public_endpoints"] for v in coverage.values())
successes = sum(v["success_captures"] for v in coverage.values())
errors = sum(v["error_captures"] for v in coverage.values())
coverage["summary"] = {"public_endpoints": total, "success_captures": successes, "error_captures": errors, "screenshots": len(captures), "complete": successes == total and errors == len(inventory)}
(OUTPUT / "coverage.json").write_text(json.dumps(coverage, ensure_ascii=False, indent=2) + "\n")
body = """<!doctype html><html lang="es"><meta charset="utf-8"><title>Capturas reales de Swagger · Red House</title>
<style>body{font:16px system-ui;max-width:1200px;margin:40px auto;padding:0 20px;background:#f7f8fa;color:#17243a}table{border-collapse:collapse;width:100%;background:white}td,th{border:1px solid #d6dce4;padding:12px;text-align:left}code{overflow-wrap:anywhere}h2{margin-top:40px}a{color:#174c85}</style>
<h1>Capturas reales de Swagger</h1>
<p>Operaciones ejecutadas desde Swagger UI contra https://34.18.186.116. Las imágenes son capturas nativas de Chromium, sin generación mediante IA.</p>
<p>Las credenciales, los tokens y las URLs firmadas se ocultan. Se conserva el resultado HTTP real. Se ocultan los ejemplos estáticos de respuestas para distinguirlos de la respuesta ejecutada.</p>
<p>Alcance: endpoints públicos de los once microservicios. Las rutas internas entre servicios quedan excluidas por indicación del usuario; no requieren abrir SSH para este recorrido.</p>
""" + f"<p>{successes}/{total} operaciones con éxito; {errors} errores; {len(captures)} capturas.</p>" + "".join(rows) + "</html>"
(OUTPUT / "index.html").write_text(body)
lines = [
    "# Capturas reales de Swagger",
    "",
    "[Abrir índice visual](index.html). Las imágenes son capturas nativas de Chrome de peticiones ejecutadas en Swagger UI contra el despliegue público GCP. No se generaron imágenes con IA ni se fabricaron respuestas.",
    "",
    f"Cobertura: **{successes}/{total} endpoints públicos con éxito**, **{errors} errores de autorización** y **{len(captures)} PNG**. [Detalle verificable](coverage.json).",
    "",
    "Por cada servicio se captura un endpoint protegido sin JWT y después con autorización. Los demás endpoints públicos se capturan únicamente con resultado exitoso. Método y ruta identifican cada operación; GET y POST de una misma ruta cuentan por separado.",
    "",
    "Se ocultan credenciales, tokens y URLs firmadas. También se ocultan los ejemplos estáticos y el bloque Curl con credenciales; se conserva visible el código HTTP real. Los cuerpos de emisión/renovación de tokens y entrega de URLs firmadas se enmascaran para no publicar secretos.",
    "",
    "Las rutas `/internal/v1/` están excluidas por la aclaración del usuario: este recorrido usa únicamente Swagger público, sin SSH. Los documentos Swagger se inventariaron en `inventory.json`; las capturas y sus fechas constan en `manifest.json`.",
    "",
    "Las escrituras utilizan datos ficticios propios de esta ejecución, identificados como Swagger o por folios SW-. La preparación de relaciones y las transiciones adicionales también utiliza peticiones reales. Los checkpoints y las credenciales se conservan únicamente en `.local/swagger-capture`, fuera del expediente público.",
    "",
    "Reproducción desde la raíz: instalar Playwright en un entorno privado, indicar `REDHOUSE_PLAYWRIGHT` si corresponde y ejecutar `node scripts/capture_swagger_endpoints.cjs`. Requiere Chrome, acceso HTTPS y la configuración privada de cuentas de demostración. El script reanuda usando su checkpoint; no es un comando de solo lectura. Reconstruir el índice con `python3 scripts/build_swagger_capture_index.py`.",
    "",
    "| Servicio | Endpoints públicos | Éxitos | Errores |",
    "| --- | ---: | ---: | ---: |",
]
for service in inventory:
    c = coverage[service]
    lines.append(f'| {service} | {c["public_endpoints"]} | {c["success_captures"]} | {c["error_captures"]} |')
(OUTPUT / "README.md").write_text("\n".join(lines) + "\n")
print(json.dumps(coverage["summary"]))
