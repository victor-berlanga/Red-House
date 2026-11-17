"""Genera anexos técnicos desde metadatos SQL y contratos versionados."""

import json
import re
import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps/services"))
from redhouse.config import SERVICES
from scripts.document import DESCRIPTIONS


def cell(value):
    return str(value or "—").replace("|", "\\|").replace("\n", " ")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--final", action="store_true")
    parser.add_argument("--metadata", type=Path)
    args = parser.parse_args()
    if args.final and not args.metadata:
        parser.error(
            "--final requiere --metadata del esquema instalado; no reutiliza el corte histórico"
        )
    output = ROOT / (
        "documentation/entrega-final/modelos"
        if args.final
        else "documentation/segundo-parcial"
    )
    output.mkdir(parents=True, exist_ok=True)
    (output / "diagramas").mkdir(exist_ok=True)
    metadata_path = (
        args.metadata
        or ROOT / "documentation/evidencias/segundo-parcial/postgresql-physical.json"
    )
    metadata = json.loads(metadata_path.read_text())
    if args.final and (
        metadata.get("schema_version") != 21
        or metadata.get("transaction_read_only") is not True
        or set(metadata.get("service_names", [])) != set(SERVICES)
    ):
        parser.error(
            "Metadatos finales requieren esquema 21, READ ONLY y propietarios coincidentes"
        )
    metadata_link = os.path.relpath(metadata_path.resolve(), output)
    repository_link = "../../.." if args.final else "../.."
    lines = [
        "# Modelo físico PostgreSQL instalado",
        "",
        (
            "Base `red_house`, esquemas `red_house` y `web_runtime`, versión 21. Catálogo extraído en una transacción READ ONLY del laboratorio privado; no contiene filas de negocio ni credenciales. No acredita instalación GCP, validación clínica ni normalización lógica por sí solo."
            if args.final
            else "Base `red_house`, esquema `red_house`. Metadatos exportados de la instancia Docker aislada. No contiene filas de negocio ni credenciales."
        ),
        "",
        f"{len(metadata['tables'])} tablas físicas y {len(metadata['indexes'])} índices. Las vistas `access_*` adaptan los contratos sin duplicar estas tablas. La correspondencia por propietario está en las fichas de servicios; una vista no constituye otra tabla física.",
        "",
        f"[Metadatos verificables]({metadata_link}) · [SQL de instalación]({repository_link}/data/database/schema.sql) · [Diagrama editable](diagramas/postgresql-completo.mmd) · [SVG físico ampliable](diagramas/postgresql-completo.svg). La generación e inspección se identifican por separado en el registro editorial.",
        "",
    ]
    for table in metadata["tables"]:
        name = table["name"]
        lines += [
            "## "
            + ((table.get("schema", "red_house") + ".") if args.final else "")
            + name,
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
            and (not args.final or x.get("schemaname") == table["schema"])
        ]
        if args.final:
            lines += ["", "Disparadores no internos:", ""]
            lines += [
                "- `" + t["name"] + "`: `" + t["definition"] + "`."
                for t in table["triggers"]
            ]
        lines += [""]
    if not args.final:
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

    def entity(table):
        return table["schema"] + "__" + table["name"] if args.final else table["name"]

    for table in metadata["tables"]:
        er += ["  " + entity(table) + " {"]
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
                if args.final:
                    target = constraint["target"].replace(".", "__")
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
                    f"  {target} {parent}..{child} {entity(table)} : {constraint['name']}"
                )
    (output / "diagramas/postgresql-completo.mmd").write_text("\n".join(er) + "\n")
    if args.final:
        blocks = {
            name: block
            for block, name in re.findall(
                r"(  (\w+) \{\n.*?^  \})", "\n".join(er), re.M | re.S
            )
        }
        relations = [line for line in er if " : " in line]
        table_index = {entity(table): table for table in metadata["tables"]}

        def key_block(name):
            table = table_index[name]
            keys = set()
            for constraint in table["constraints"]:
                if constraint["type"] in ("p", "u", "f"):
                    keys.update(
                        x.strip().strip('"')
                        for x in re.search(r"\(([^)]+)\)", constraint["definition"])[
                            1
                        ].split(",")
                    )
            selected = [
                line
                for line in blocks[name].splitlines()[1:-1]
                if line.split()[-1] in keys
            ]
            return "\n".join(["  " + name + " {", *selected, "  }"])

        def projection(selected, key_only=False):
            edges = [line for line in relations if line.split()[2] in selected]
            visible = selected | {line.split()[0] for line in edges}
            if not visible <= set(table_index):
                raise ValueError(
                    "Una FK referencia una tabla fuera del catálogo capturado"
                )
            return (
                "\n".join(
                    [
                        *er[:2],
                        *(
                            key_block(name)
                            if key_only or name not in selected
                            else blocks[name]
                            for name in sorted(visible)
                        ),
                        *edges,
                    ]
                )
                + "\n"
            )

        (output / "diagramas/modelo-relacional.mmd").write_text(
            projection(set(table_index), key_only=True)
        )
        (output / "Modelo_relacional.md").write_text(
            "# Vista relacional final derivada del esquema instalado\n\n"
            "Esquema 21. Se proyectan los atributos de PK, UNIQUE y FK y sus relaciones reales, "
            "sin inventar cardinalidades clínicas ni presentar el ejercicio 0FN–4FN como instalado. "
            "Los atributos restantes, CHECK, índices parciales, disparadores y valores predeterminados "
            "se conservan en [el catálogo físico](Modelo_fisico.md).\n\n"
            "Fuente editable: [modelo-relacional.mmd](diagramas/modelo-relacional.mmd). "
            "[SVG relacional ampliable](diagramas/modelo-relacional.svg). "
            "La generación e inspección se identifican por separado en el registro editorial.\n"
        )
        for owner in SERVICES:
            selected = {
                table.replace(".", "__")
                for view in metadata["views"]
                if view["owner"] == owner
                for table in view["tables"]
            }
            (output / ("diagramas/postgresql-" + owner + ".mmd")).write_text(
                projection(selected)
            )
    # Cardinalities follow FK nullability and declared UNIQUE/PRIMARY KEYs.
    # Conditional/partial indexes and clinical constraints remain in the catalogue.
    lines = [
        "# Fichas individuales de microservicios",
        "",
        (
            "Corte final: doce servicios independientes; esquema 21. Las versiones contractuales se leen de sus OpenAPI actuales. El catálogo documenta contratos, no ejecución ni aceptación de todas sus operaciones."
            if args.final
            else "Edición 0.3.0. Los contratos enlazados contienen campos, tipos, obligatoriedad, ejemplos JSON/XML, XSD, errores y paginación. El expediente HTTP distingue ejemplos de ejecuciones."
        ),
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
    if args.final:
        access_views = [
            (
                view["owner"],
                view["name"],
                " ".join("FROM " + name for name in view["tables"]),
            )
            for view in metadata["views"]
        ]
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
            f"**Ámbito SQL:** `access_{name}`. La correspondencia siguiente procede "
            + ("del catálogo capturado." if args.final else "del SQL de instalación.")
            + " Las tablas técnicas `service_*` filtran el propietario; las claves y relaciones completas constan en el [catálogo físico](Modelo_fisico.md).",
            "",
            "| Vista autorizada | Tabla física compartida |",
            "| --- | --- |",
        ]
        for owner, view, definition in access_views:
            if owner != name:
                continue
            physical = re.findall(r"FROM red_house\.([a-z_]+)", definition)
            if not args.final:
                assert physical, (owner, view)
            lines.append(
                f"| `{view}` | "
                + (
                    ", ".join(f"`red_house.{table}`" for table in physical)
                    or "Sin dependencia física directa declarada en pg_depend"
                )
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
        if args.final:
            lines += [
                "",
                "**Corte final de esta ficha:** versión OpenAPI `"
                + str(contract["info"]["version"])
                + "`. Documentos es propietario de archivos/reportes. LOCAL es el proveedor operativo principal; GCS es opcional y su evidencia académica se conserva separada. Las relaciones de vistas proceden del catálogo instalado, no del SQL base anterior a las migraciones.",
                "",
            ]
        lines += [
            "",
            "**Entradas y salidas:** encabezados `Authorization`, `Accept`, `Content-Type`, `X-Correlation-ID` y `Idempotency-Key` según operación. Parámetros de ruta UUID y consulta/paginación constan en OpenAPI. Respuesta `{data,meta}` o `{error,meta}`, con representación XML equivalente. El contrato interno añade encabezados de firma del servicio; los valores secretos están redactados en evidencia.",
            "",
            "**Pruebas:** suite de `apps/services/tests`, expediente dinámico por método/ruta y pruebas Docker de negocio. Consultar `RESULTADOS.md` para resultados reales y limitaciones; no se considera probado un endpoint solo por aparecer en esta tabla.",
            "",
        ]
    content = "\n".join(lines) + "\n"
    if args.final:
        content = content.replace("../../apps/services/", "../../../apps/services/")
        content = content.replace(
            "../evidencias/segundo-parcial/http/index.html",
            "../../evidencias/segundo-parcial/http/index.html",
        )
        content = content.replace(
            "Transporte añade configuración GCS;",
            "Documentos añade configuración LOCAL/GCS y antivirus;",
        )
    (output / "Fichas_microservicios.md").write_text(content)
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
