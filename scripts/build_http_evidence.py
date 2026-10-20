"""Publica un visor local de ejecuciones redactadas; no fabrica solicitudes."""

import argparse
import hashlib
import html
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps/services"))
from redhouse.evidence import redact

STYLE = """body{font:15px system-ui;margin:32px;background:#f4f5f7;color:#202631}main{max-width:1250px;margin:auto}h1{color:#8e2434;font-size:26px}small{color:#556}a{color:#8e2434}table{border-collapse:collapse;width:100%;background:white}td,th{padding:9px;border:1px solid #ccd;vertical-align:top;text-align:left}pre{white-space:pre-wrap;word-break:break-word;background:#fff;border:1px solid #ccd;padding:12px;font:12px monospace;max-height:300px;overflow:auto}section{margin:20px 0}.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}.tag{padding:4px 9px;background:#e5ece7}.error{background:#f8e5e6}input{padding:12px;width:70%;margin:15px 0}details{margin:12px 0}nav{margin-bottom:20px}"""


def page(title, body):
    return (
        '<!doctype html><html lang="es"><meta charset="utf-8"><title>'
        + html.escape(title)
        + "</title><style>"
        + STYLE
        + "</style><main>"
        + body
        + "</main></html>"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "documentation/evidencias/segundo-parcial/http",
    )
    args = parser.parse_args()
    out = args.output
    (out / "records").mkdir(parents=True, exist_ok=True)
    (out / "endpoints").mkdir(exist_ok=True)
    inventory, grouped = {}, defaultdict(list)
    for folder in args.inputs:
        for source in sorted(folder.glob("*/*.json")):
            service = source.parent.name
            value = json.loads(source.read_text())
            if source.name == "inventory.json":
                for item in value:
                    inventory[(service, item["method"], item["route"])] = item
                continue
            key = (service, value["method"], value["route"])
            record = redact(value)
            raw = json.dumps(record, ensure_ascii=False, indent=2) + "\n"
            digest = hashlib.sha256(raw.encode()).hexdigest()[:24]
            target = out / "records" / (digest + ".json")
            target.write_text(raw)
            grouped[key].append((digest, record))
    coverage, links = [], []
    for key, contract in sorted(inventory.items()):
        service, method, route = key
        records = grouped[key]
        http = [(n, r) for n, r in records if r["transport"] == "http"]
        successful = [(n, r) for n, r in http if r["status"] < 300]
        errors = [(n, r) for n, r in http if r["status"] >= 400]
        fixed_document = method == "GET" and route in (
            "/docs",
            "/docs/",
            "/docs/swagger.json",
            "/openapi.json",
        )
        identifier = hashlib.sha256("|".join(key).encode()).hexdigest()[:16]
        row = dict(
            service=service,
            **contract,
            http_records=len(http),
            successes=len(successful),
            errors=len(errors),
            error_applicability=(
                "Documento fijo, sin parámetros de entrada ni operación de negocio; "
                "no se fabrica un error de dominio. Los contratos y archivos "
                "dinámicos tienen sus rutas y errores propios."
                if fixed_document and not errors
                else "Error HTTP ejecutado"
                if errors
                else "Pendiente de evidencia aplicable"
            ),
            formats=sorted(
                {
                    r["response_headers"].get("Content-Type", "").split(";")[0]
                    for _, r in http
                }
            ),
            success_formats=sorted(
                {
                    r["response_headers"].get("Content-Type", "").split(";")[0]
                    for _, r in successful
                }
            ),
            persistence_effects=sorted(
                {
                    r.get("persistence", {}).get("effect", "missing")
                    for _, r in successful
                    if r["method"] != "GET"
                }
            ),
            page="endpoints/" + identifier + ".html",
            screenshot="captures/" + identifier + ".png",
        )
        coverage.append(row)
        text = (
            '<nav><a href="../index.html">Inventario completo</a></nav><h1>'
            + html.escape(service + " · " + method + " " + route)
            + "</h1>"
        )
        text += (
            "<p>"
            + html.escape(contract["objective"])
            + "</p><p>Registro de ejecución real. Credenciales y firmas redactadas. Los cuerpos completos están en el JSON enlazado.</p>"
        )
        if not errors:
            text += "<p>Errores: " + html.escape(row["error_applicability"]) + "</p>"
        candidates = successful[:1] + errors[:1]
        if not candidates:
            text += '<p class="error">Sin ejecución HTTP registrada. No se presenta un ejemplo generado como prueba.</p>'
        for digest, record in candidates:
            text += (
                "<section><h2>HTTP "
                + str(record["status"])
                + "</h2><p><b>"
                + html.escape(record["captured_at"])
                + "</b> · versión "
                + html.escape(record["version"])
                + "</p>"
            )
            text += (
                "<p>Correlación: "
                + html.escape(record["correlation_id"])
                + "<br>URL: "
                + html.escape(record["url"])
                + "</p>"
            )
            text += (
                '<p><a href="../records/'
                + digest
                + '.json">Petición, respuesta, headers y persistencia completos</a></p><div class="grid">'
            )
            for label, value in [
                (
                    "Petición",
                    {
                        "headers": record["request_headers"],
                        "parameters": record["parameters"],
                        "body": record["request_body"],
                    },
                ),
                (
                    "Respuesta",
                    {
                        "headers": record["response_headers"],
                        "body": record["response_body"],
                    },
                ),
            ]:
                text += (
                    "<div><h3>"
                    + label
                    + "</h3><pre>"
                    + html.escape(json.dumps(value, ensure_ascii=False, indent=2))
                    + "</pre></div>"
                )
            text += (
                "</div><details><summary>Persistencia y versión de implementación</summary><pre>"
                + html.escape(
                    json.dumps(record["persistence"], ensure_ascii=False, indent=2)
                )
                + "</pre><p>SHA-256: "
                + record["implementation_sha256"]
                + "</p></details></section>"
            )
        text += "<h2>Todas las variantes ejecutadas</h2><ul>"
        for digest, record in records:
            label = (
                str(record["status"])
                + " · "
                + record["transport"]
                + " · "
                + record["response_headers"].get("Content-Type", "")
                + " · "
                + record["captured_at"]
            )
            text += (
                '<li><a href="../records/'
                + digest
                + '.json">'
                + html.escape(label)
                + "</a></li>"
            )
        text += "</ul>"
        (out / row["page"]).write_text(page(service + " " + route, text))
        links.append(
            "<tr><td>"
            + html.escape(service)
            + '</td><td><a href="'
            + row["page"]
            + '">'
            + html.escape(method + " " + route)
            + "</a></td><td>"
            + str(len(successful))
            + "</td><td>"
            + str(len(errors))
            + "</td><td>"
            + html.escape(", ".join(row["formats"]))
            + "</td></tr>"
        )
    summary = {
        "endpoints": len(coverage),
        "with_http": sum(bool(r["http_records"]) for r in coverage),
        "with_success": sum(bool(r["successes"]) for r in coverage),
        "with_error": sum(bool(r["errors"]) for r in coverage),
    }
    (out / "coverage.json").write_text(
        json.dumps(
            {"summary": summary, "endpoints": coverage}, indent=2, ensure_ascii=False
        )
        + "\n"
    )
    body = (
        "<h1>Red House · Expediente HTTP ejecutado</h1><p>Inventario dinámico, datos ficticios y secretos redactados. HTTP, WSGI y backend embebido se identifican por separado. Fecha y hash en cada registro.</p><p>"
        + html.escape(json.dumps(summary))
        + '</p><input aria-label="Filtrar endpoints" placeholder="Filtrar por servicio, método o ruta" oninput="for(const r of document.querySelectorAll(\'tbody tr\'))r.hidden=!r.textContent.toLowerCase().includes(this.value.toLowerCase())"><table><thead><tr><th>Servicio</th><th>Método y ruta</th><th>Éxitos</th><th>Errores</th><th>Formatos HTTP</th></tr></thead><tbody>'
        + "".join(links)
        + "</tbody></table>"
    )
    (out / "index.html").write_text(page("Expediente HTTP Red House", body))
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
