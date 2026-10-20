"""Genera anexos técnicos desde metadatos SQL y contratos versionados."""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps/services"))
from redhouse.config import SERVICES
from scripts.document import DESCRIPTIONS


def cell(value):
    return str(value or "—").replace("|", "\\|").replace("\n", " ")


def main():
    output = ROOT / "documentation/segundo-parcial"
    output.mkdir(parents=True, exist_ok=True)
    metadata = json.loads(
        (
            ROOT / "documentation/evidencias/segundo-parcial/postgresql-physical.json"
        ).read_text()
    )
    lines = [
        "# Modelo físico PostgreSQL instalado",
        "",
        "Base `red_house`, esquema `red_house`. Metadatos exportados de la instancia Docker aislada. No contiene filas de negocio ni credenciales.",
        "",
        f"{len(metadata['tables'])} tablas físicas y {len(metadata['indexes'])} índices. Las vistas `access_*` adaptan los contratos sin duplicar estas tablas. Algunas tablas conservadas de main no son escritas por los servicios actuales; consultar la correspondencia en `Esquema_compartido.md`.",
        "",
        "[Metadatos verificables](../evidencias/segundo-parcial/postgresql-physical.json) · [SQL de instalación](../../data/database/schema.sql) · [Diagrama físico completo, ampliable](diagramas/postgresql-completo.svg)",
        "",
    ]
    for table in metadata["tables"]:
        name = table["name"]
        lines += [
            "## " + name,
            "",
            "| Columna | Tipo físico | NULL | Predeterminado |",
            "| --- | --- | --- | --- |",
        ]
        for col in table["columns"]:
            type_name = col["data_type"]
            if col["character_maximum_length"]:
                type_name += "(" + str(col["character_maximum_length"]) + ")"
            lines.append(
                "| "
                + " | ".join(
                    map(
                        cell,
                        [
                            col["column_name"],
                            type_name,
                            col["is_nullable"],
                            col["column_default"],
                        ],
                    )
                )
                + " |"
            )
        lines += ["", "Restricciones:", ""]
        lines += [
            "- `" + c["name"] + "`: `" + c["definition"] + "`."
            for c in table["constraints"] or []
        ]
        lines += ["", "Índices:", ""]
        lines += [
            "- `" + x["indexname"] + "`: `" + x["indexdef"] + "`."
            for x in metadata["indexes"]
            if x["tablename"] == name
        ]
        lines += [""]
    lines += [
        "## Almacenamiento técnico del portal: web_runtime.session_revocations",
        "",
        "Además de las 71 tablas anteriores, el portal utiliza una tabla técnica en el esquema `web_runtime` de la misma base PostgreSQL. El instalador aplica [web_sessions.sql](../../data/database/web_sessions.sql) con permisos exclusivos para `rh_web_sessions`; los servicios de dominio no tienen acceso. Total instalado tras esta actualización: 72 tablas entre ambos esquemas.",
        "",
        "| Columna | Tipo | Regla |",
        "| --- | --- | --- |",
        "| id | text | PK; SHA-256 de la cookie opaca, 64 caracteres hexadecimales |",
        "| payload | bytea, admite NULL | Credenciales cifradas pendientes de revocar; se elimina al confirmar |",
        "| expires | timestamptz | NOT NULL; marca de cierre conservada hasta 24 horas |",
        "| confirmed | boolean | NOT NULL, false inicial; true después de confirmar revocación |",
        "",
        "Índices: clave primaria sobre `id`; `session_revocations_pending` sobre `expires` para filas sin confirmar; `session_revocations_expiry` para limpiar vencidas. Sin claves foráneas al dominio: identifica la sesión técnica del navegador, no un expediente clínico. El worker reintenta cierres pendientes; una marca confirmada impide reactivar la cookie desde una copia antigua de Redis. El respaldo PostgreSQL incluye este esquema.",
        "",
        "Las sesiones activas y concesiones de renovación residen en Redis con TTL. La credencial Redis del portal solo accede al prefijo `web:*`; la credencial SQL solo accede a esta tabla.",
        "",
    ]
    (output / "Modelo_fisico.md").write_text("\n".join(lines) + "\n")
    # Actual FK graph, distinct from the conceptual relationship summary.
    er = ["erDiagram", "  direction LR"]
    for table in metadata["tables"]:
        er += ["  " + table["name"] + " {"]
        for column in table["columns"]:
            er.append(
                "    "
                + re.sub(r"[^a-zA-Z0-9_]", "_", column["udt_name"])
                + " "
                + column["column_name"]
            )
        er.append("  }")
    for table in metadata["tables"]:
        for constraint in table["constraints"] or []:
            if constraint["type"] == "f":
                target = constraint["target"].rsplit(".", 1)[-1]
                fields = {
                    x.strip().strip('"')
                    for x in re.search(
                        r"FOREIGN KEY \(([^)]+)\)", constraint["definition"]
                    )[1].split(",")
                }
                required = all(
                    c["is_nullable"] == "NO"
                    for c in table["columns"]
                    if c["column_name"] in fields
                )
                unique = any(
                    {
                        x.strip().strip('"')
                        for x in re.search(r"\(([^)]+)\)", c["definition"])[1].split(
                            ","
                        )
                    }
                    <= fields
                    for c in table["constraints"] or []
                    if c["type"] in ("u", "p")
                )
                parent, child = ("||" if required else "|o"), ("o|" if unique else "o{")
                er.append(
                    f"  {target} {parent}..{child} {table['name']} : {constraint['name']}"
                )
    (output / "diagramas/postgresql-completo.mmd").write_text("\n".join(er) + "\n")
    # Cardinalities follow FK nullability and declared UNIQUE/PRIMARY KEYs.
    # Conditional/partial indexes and clinical constraints remain in the catalogue.
    lines = [
        "# Fichas individuales de microservicios",
        "",
        "Edición 0.3.0. Los contratos enlazados contienen campos, tipos, obligatoriedad, ejemplos JSON/XML, XSD, errores y paginación. El expediente HTTP distingue ejemplos de ejecuciones.",
        "",
        "Cada servicio tiene API Flask/REST y worker supervisado, módulos de rutas/modelos, biblioteca común de autorización/contratos y persistencia propia mediante vistas limitadas. Puerto interno 8080; el gateway publica un puerto por propietario. Versiones exactas de dependencias en `requirements-verified.txt`; Docker usa Python 3.13 y las pruebas locales Python 3.12.",
        "",
    ]
    installation_sql = (ROOT / "data/database/schema.sql").read_text()
    access_views = re.findall(
        r"CREATE VIEW access_([a-z_]+)\.([a-z_]+) AS(.*?);",
        installation_sql,
        re.S,
    )
    assert {service for service, _, _ in access_views} == set(SERVICES)
    contracts, consumers = {}, {name: set() for name in SERVICES}
    for name in SERVICES:
        module = "servicio_monitoreo" if name == "monitoreo" else "ms_" + name
        contracts[name] = json.loads(
            (ROOT / "apps/services" / module / "contracts/openapi.json").read_text()
        )
        for route, methods in contracts[name]["paths"].items():
            if not route.startswith("/internal/"):
                continue
            for operation in methods.values():
                description = operation.get("description", "")
                marker = "Contrato interno firmado; consumidores: "
                if marker in description:
                    consumers[name].update(description.split(marker)[1].split(", "))
    for name, port in SERVICES.items():
        module = "servicio_monitoreo" if name == "monitoreo" else "ms_" + name
        contract = contracts[name]
        destinations = sorted(
            owner for owner, callers in consumers.items() if name in callers
        )
        title, purpose, persistence, scenario, _ = DESCRIPTIONS[name]
        lines += [
            "## " + title,
            "",
            purpose,
            "",
            "**Justificación y proceso:** " + scenario,
            "",
            "**Integración declarada:** puede invocar contratos internos de "
            + (", ".join(destinations) or "ningún otro propietario")
            + (
                "; acepta llamadas firmadas de " + ", ".join(sorted(consumers[name]))
                if consumers[name]
                else "; no ofrece contratos internos firmados"
            )
            + ". Estas relaciones incluyen entrega de eventos. Monitoreo consulta además la salud pública de todos los componentes. Cada ruta conserva su lista específica de consumidores y delegación en OpenAPI.",
            "",
            "**Persistencia y relaciones:** " + persistence,
            "",
            f"**Ámbito SQL:** `access_{name}`. La correspondencia siguiente procede del SQL de instalación. Las tablas técnicas `service_*` filtran el propietario; las claves y relaciones completas constan en el [catálogo físico](Modelo_fisico.md).",
            "",
            "| Vista autorizada | Tabla física compartida |",
            "| --- | --- |",
        ]
        for owner, view, definition in access_views:
            if owner != name:
                continue
            physical = re.findall(r"FROM red_house\.([a-z_]+)", definition)
            assert physical, (owner, view)
            lines.append(
                f"| `{view}` | "
                + ", ".join(f"`red_house.{table}`" for table in physical)
                + " |"
            )
        lines += [
            "",
            f"**Despliegue:** [Dockerfile](../../apps/services/{module}/Dockerfile), dos instancias `{name.replace('_', '-')}-a/b`, gateway `http://127.0.0.1:{port + 1000}` y Swagger `/docs/`. Configuración privada propia: `DATABASE_URL`, `REDIS_URL`, claves públicas JWT y de servicios, clave privada de firma interna y URLs del gateway. Solo Identidad conserva la clave privada JWT. Transporte añade configuración GCS; los cuatro propietarios documentales añaden MongoDB.",
            "",
            "**Seguridad:** JWT RS256 con Redis en cada operación protegida; rol y recurso según contrato. Rutas internas exigen firma, nonce y autoridad llamante. POST/PATCH de negocio conservan Idempotency-Key donde está declarado, versión y motivo cuando corresponde. GET autorizado genera auditoría; las transacciones publican eventos por outbox.",
            "",
            f"**Contratos:** [OpenAPI completo](../../apps/services/{module}/contracts/openapi.json) · [Directorio JSON/XML/XSD](../../apps/services/{module}/contracts/) · [Ejecuciones HTTP](../evidencias/segundo-parcial/http/index.html).",
            "",
            "| Método | Ruta | Objetivo | Códigos declarados |",
            "| --- | --- | --- | --- |",
        ]
        for route, methods in contract["paths"].items():
            for method, operation in methods.items():
                if method not in ("get", "post", "patch", "put", "delete"):
                    continue
                lines.append(
                    "| "
                    + " | ".join(
                        map(
                            cell,
                            [
                                method.upper(),
                                "`" + route + "`",
                                operation.get("summary"),
                                ", ".join(operation["responses"]),
                            ],
                        )
                    )
                    + " |"
                )
        lines += [
            "",
            "**Entradas y salidas:** encabezados `Authorization`, `Accept`, `Content-Type`, `X-Correlation-ID` y `Idempotency-Key` según operación. Parámetros de ruta UUID y consulta/paginación constan en OpenAPI. Respuesta `{data,meta}` o `{error,meta}`, con representación XML equivalente. El contrato interno añade encabezados de firma del servicio; los valores secretos están redactados en evidencia.",
            "",
            "**Pruebas:** suite de `apps/services/tests`, expediente dinámico por método/ruta y pruebas Docker de negocio. Consultar `RESULTADOS.md` para resultados reales y limitaciones; no se considera probado un endpoint solo por aparecer en esta tabla.",
            "",
        ]
    (output / "Fichas_microservicios.md").write_text("\n".join(lines) + "\n")
    print(
        json.dumps(
            {
                "tables": len(metadata["tables"]),
                "indexes": len(metadata["indexes"]),
                "services": len(SERVICES),
            }
        )
    )


if __name__ == "__main__":
    main()
