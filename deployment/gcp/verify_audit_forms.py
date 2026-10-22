"""Comprueba el despliegue académico sin registrar operaciones de negocio nuevas.

Ejecutar en la VM después del recorrido del navegador, indicando su hallazgo cerrado.
Lee credenciales existentes sin incluirlas en el informe; los POST de prueba son inválidos.
"""

import argparse
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from uuid import uuid4


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--finding", required=True)
    parser.add_argument("--resource", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    directory = Path("/opt/redhouse/.local/compose")
    assert (directory / "installation.json").is_file()
    state = json.loads((directory / "state.json").read_text())
    services = (
        "identidad_acceso",
        "donantes",
        "receptores",
        "inventario",
        "compatibilidad",
        "priorizacion_geografia",
        "transporte",
        "custodia",
        "alertas",
        "auditoria",
        "monitoreo",
    )
    tokens = {}
    report = {"checks": [], "resource_id": args.resource, "finding_id": args.finding}

    def request(service, method, path, user=None, data=None, mime="application/json"):
        headers = {"Accept": mime}
        if user:
            headers["Authorization"] = "Bearer " + tokens[user]
        if data is not None:
            headers.update(
                {"Content-Type": "application/json", "Idempotency-Key": str(uuid4())}
            )
        url = f"http://127.0.0.1:{6101 + services.index(service)}{path}"
        req = urllib.request.Request(
            url,
            json.dumps(data).encode() if data is not None else None,
            headers,
            method=method,
        )
        try:
            response = urllib.request.urlopen(req, timeout=30)
        except urllib.error.HTTPError as exc:
            response = exc
        raw = response.read()
        return response.status, ET.fromstring(raw) if mime.endswith(
            "xml"
        ) else json.loads(raw)

    def ok(name, service, path, user, mime="application/json"):
        status, body = request(service, "GET", path, user, mime=mime)
        assert status == 200, (name, status)
        report["checks"].append({"name": name, "status": status, "mime": mime})
        return body if mime.endswith("xml") else body["data"]

    try:
        for user in (
            "admin1",
            "operator1",
            "medical1",
            "medical2",
            "coordinator1",
            "coordinator2",
            "transport1",
            "auditor1",
        ):
            status, body = request(
                "identidad_acceso",
                "POST",
                "/api/v1/auth/login",
                data={"username": user, "password": state["password"]},
            )
            assert status == 200, ("login", user, status)
            tokens[user] = body["data"]["access_token"]
        paths = {
            "identidad_acceso": ("/api/v1/users", "admin1"),
            "donantes": ("/api/v1/campaigns", "operator1"),
            "receptores": ("/api/v1/requests", "medical2"),
            "inventario": ("/api/v1/resources", "operator1"),
            "compatibilidad": ("/api/v1/evaluations", "medical2"),
            "priorizacion_geografia": ("/api/v1/routes", "coordinator1"),
            "transporte": ("/api/v1/shipments", "coordinator1"),
            "alertas": ("/api/v1/alerts", "operator1"),
            "auditoria": ("/api/v1/events", "auditor1"),
            "monitoreo": ("/api/v1/status", "admin1"),
        }
        shipments = ok(
            "Traslados del transportista",
            "transporte",
            "/api/v1/shipments",
            "transport1",
        )
        assert shipments["items"]
        paths["custodia"] = (
            "/api/v1/chains/" + shipments["items"][0]["id"],
            "transport1",
        )
        for service, (path, user) in paths.items():
            for mime in ("application/json", "application/xml"):
                ok(service + " " + mime, service, path, user, mime)

        options = ok(
            "Catálogo de auditoría", "auditoria", "/api/v1/event-options", "auditor1"
        )
        assert options["export_limit"] == 5000
        suffix = "?" + urllib.parse.urlencode({"resource": args.resource})
        rows = ok(
            "Filtro por recurso", "auditoria", "/api/v1/events" + suffix, "auditor1"
        )
        exported = ok(
            "Exportación filtrada completa",
            "auditoria",
            "/api/v1/events/export" + suffix,
            "auditor1",
        )
        assert rows["total"] == exported["total"] == len(exported["items"])
        assert rows["total"] > 0
        report["filtered_total"] = rows["total"]
        report["filtered_ids"] = [row["id"] for row in exported["items"]]
        event_id = rows["items"][0]["id"]
        ok("Detalle histórico", "auditoria", "/api/v1/events/" + event_id, "auditor1")
        ok(
            "Secuencia relacionada",
            "auditoria",
            "/api/v1/events/" + event_id + "/related",
            "auditor1",
        )
        for user, path, expected in (
            ("medical1", "/api/v1/events", 403),
            ("operator1", "/api/v1/findings", 403),
            ("coordinator2", "/api/v1/findings/" + args.finding, 404),
            (None, "/api/v1/events", 401),
        ):
            status, _ = request("auditoria", "GET", path, user)
            assert status == expected, (user, path, status)
            report["checks"].append(
                {"name": "Acceso rechazado " + str(user), "status": status}
            )
        for mime in ("application/json", "application/xml"):
            ok(
                "Hallazgo cerrado " + mime,
                "auditoria",
                "/api/v1/findings/" + args.finding,
                "auditor1",
                mime,
            )
        finding = ok(
            "Historial del hallazgo",
            "auditoria",
            "/api/v1/findings/" + args.finding,
            "coordinator1",
        )
        assert (
            finding["status"] == "CLOSED"
            and finding["version"] == 4
            and len(finding["history"]) == 4
        )
        assert [row["status"] for row in finding["history"]] == [
            "OPEN",
            "IN_PROGRESS",
            "PENDING_VERIFICATION",
            "CLOSED",
        ]
        report["finding"] = {
            "status": finding["status"],
            "version": finding["version"],
            "history_count": len(finding["history"]),
            "links": len(finding["events"]),
        }

        invalid = {
            "folio": "INVALID-" + uuid4().hex[:8],
            "display_name": "Validación ficticia sin persistencia",
            "blood_group": "O+",
            "consent": True,
            "restrictions": "abc",
        }
        for mime in ("application/json", "application/xml"):
            status, body = request(
                "donantes", "POST", "/api/v1/donors", "medical1", invalid, mime
            )
            assert status == 422, status
            if mime.endswith("json"):
                details = body["error"]["details"]
                assert any(
                    row["field"] == "restrictions" and row["message"] for row in details
                )
                assert all("input" not in row for row in details)
            else:
                assert "restrictions" in ET.tostring(body, encoding="unicode")
            report["checks"].append(
                {"name": "Detalles seguros de validación " + mime, "status": status}
            )

        deadline = time.monotonic() + 60
        while True:
            seen = {}
            for user in ("coordinator1", "auditor1"):
                status, data = request(
                    "alertas", "GET", "/api/v1/alerts?page_size=100", user
                )
                assert status == 200
                seen[user] = any(
                    args.finding in json.dumps(row) for row in data["data"]["items"]
                )
            if all(seen.values()):
                break
            assert time.monotonic() < deadline, "Notificaciones del hallazgo pendientes"
            time.sleep(2)
        report["checks"].append(
            {"name": "Notificación dirigida a coordinación y auditoría", "passed": True}
        )
        report["result"] = "passed"
    except Exception as exc:
        report.update(result="failed", failure=str(exc))
        raise
    finally:
        for user in tokens:
            # Cerrar únicamente las sesiones abiertas por esta verificación.
            request("identidad_acceso", "POST", "/api/v1/auth/logout", user, {})
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"result": report["result"], "checks": len(report["checks"])}))


if __name__ == "__main__":
    os.umask(0o077)
    main()
