"""Recorridos de revisión y corrección; reglas y permisos permanecen en sus propietarios."""

from .common import (
    BusinessError,
    ZoneInfo,
    call,
    confirmations,
    datetime,
    detail,
    field,
    g,
    inventory,
    regional,
    selected_zone,
    soon,
    submit,
    table,
    url_for,
)


@regional.get("/laboratorio")
def laboratory():
    return table(
        "Resultados de laboratorio",
        "laboratorio",
        "compatibilidad",
        "/api/v1/laboratory/results",
        [
            ("test_code", "Prueba"),
            ("status", "Estado"),
            ("measured_at", "Medición"),
            ("version", "Versión"),
        ],
        filters=(
            "sample_id",
            "status",
            "q",
            "from_at",
            "until_at",
            "date_field",
            "sort",
        ),
        links=lambda row: url_for("regional.lab_result", identifier=row["id"]),
    )


@regional.get("/laboratorio/resultados/<uuid:identifier>")
def lab_result(identifier):
    row = call("compatibilidad", "/api/v1/laboratory/results/" + str(identifier))
    actions = [
        (
            "Registrar corrección",
            url_for("regional.lab_correct", identifier=identifier),
        ),
        (
            "Documentos privados",
            url_for(
                "regional.document_center", subject_kind="RESULT", subject_id=identifier
            ),
        ),
        (
            "Historia de la muestra",
            url_for("regional.laboratory", sample_id=row["sample_id"]),
        ),
    ]
    if g.principal.role_code == "MEDICAL" and row["status"] == "CAPTURED":
        actions.append(
            ("Revisar resultado", url_for("regional.lab_review", identifier=identifier))
        )
    return detail("Resultado de " + row["test_code"], "laboratorio", row, actions)


@regional.route(
    "/laboratorio/resultados/<uuid:identifier>/corregir", methods=["GET", "POST"]
)
def lab_correct(identifier):
    row = call("compatibilidad", "/api/v1/laboratory/results/" + str(identifier))
    return submit(
        "compatibilidad",
        "/api/v1/laboratory/results",
        [
            field("sample_id", "Muestra", "hidden", default=row["sample_id"]),
            field("test_code", "Prueba", "hidden", default=row["test_code"]),
            field(
                "supersedes", "Resultado anterior", "hidden", default=str(identifier)
            ),
            field(
                "value",
                "Valor corregido",
                "textarea",
                default=row["value"] or "",
                required=False,
            ),
            field(
                "result_state",
                "Estado informado",
                "select",
                [
                    (v, v)
                    for v in (
                        "NOT_PERFORMED",
                        "PENDING",
                        "INDETERMINATE",
                        "REPORTED",
                        "CORRECTED",
                    )
                ],
                default="CORRECTED",
            ),
            field(
                "hla_loci",
                "Loci y alelos declarados (una línea por locus: A=A*01:01,A*02:01; ? indica ambigüedad)",
                "textarea",
                required=False,
                default="\n".join(
                    x["locus"]
                    + ("?" if x["ambiguous"] else "")
                    + "="
                    + ",".join([*x["alleles"], *x.get("groups", [])])
                    for x in (row.get("hla") or {}).get("loci", [])
                ),
            ),
            field(
                "catalogue_version",
                "Edición de catálogo HLA",
                "select",
                [
                    (r["version"], r["version"])
                    for r in call(
                        "compatibilidad", "/api/v1/laboratory/reference-sources"
                    )["catalogues"]
                ],
                required=False,
                default=(row.get("hla") or {}).get("catalogue_version", ""),
            ),
            field(
                "nomenclature_version",
                "Versión de nomenclatura declarada",
                required=False,
                default=(row.get("hla") or {}).get(
                    "nomenclature_version", "2010:syntax-2"
                ),
            ),
            field(
                "resolution",
                "Resolución declarada",
                required=False,
                default=(row.get("hla") or {}).get("resolution", ""),
            ),
            field(
                "issued_at",
                "Fecha de emisión",
                "datetime-local",
                required=False,
                default=soon(),
            ),
            field(
                "document_id",
                "Documento privado de la muestra",
                required=False,
                default=row.get("document_id") or "",
            ),
            field("unit", "Unidad", default=row.get("unit") or "", required=False),
            field("method", "Método", default=row["method"]),
            field("laboratory", "Laboratorio", default=row["laboratory"]),
            field(
                "reference",
                "Referencia documental de la corrección",
                default=row["reference"],
            ),
            field("measured_at", "Fecha de medición", "datetime-local", default=soon()),
        ]
        + crossmatch_fields(row.get("crossmatch")),
        transform=hla_form,
        title="Registrar corrección",
        active="laboratorio",
        back=url_for("regional.lab_result", identifier=identifier),
        success=lambda result: url_for("regional.lab_result", identifier=result["id"]),
        note="Se conserva el resultado anterior. La corrección requiere revisión médica y una nueva evaluación antes de reservar.",
    )


@regional.route(
    "/laboratorio/resultados/<uuid:identifier>/revisar", methods=["GET", "POST"]
)
def lab_review(identifier):
    row = call("compatibilidad", "/api/v1/laboratory/results/" + str(identifier))
    return submit(
        "compatibilidad",
        f"/api/v1/laboratory/results/{identifier}/review",
        [
            field("version", "Versión", "hidden", default=row["version"]),
            field(
                "decision",
                "Decisión",
                "select",
                [
                    ("AUTHORIZED", "Autorizar resultado registrado"),
                    ("REJECTED", "Rechazar resultado"),
                ],
            ),
        ]
        + confirmations(),
        title="Revisar resultado",
        active="laboratorio",
        back=url_for("regional.lab_result", identifier=identifier),
    )


@inventory.route("/inventario/<uuid:identifier>/destino", methods=["GET", "POST"])
def destination(identifier):
    row = call("inventario", "/api/v1/resources/" + str(identifier))
    if g.principal.role_code != "MEDICAL":
        raise BusinessError("Requiere personal médico autorizado.", 403)
    history = call(
        "inventario",
        "/api/v1/resource-destinations",
        params={"resource_id": str(identifier), "page_size": 100},
    )["items"]
    old = max(history, key=lambda r: r["version"]) if history else None
    fields = [
        field("version", "Versión", "hidden", default=row["version"]),
        field(
            "destination",
            "Destino registrado",
            "select",
            [
                (k, v)
                for k, v in [
                    ("TRANSFUSED", "Transfundido"),
                    ("TRANSPLANTED", "Trasplantado"),
                    ("DISCARDED", "Descartado"),
                    ("RETURNED", "Devuelto"),
                    ("RESEARCH", "Investigación"),
                ]
            ],
            default=old["destination"] if old else "",
        ),
        field(
            "occurred_at",
            "Fecha del hecho",
            "datetime-local",
            default=datetime.fromisoformat(old["occurred_at"].replace("Z", "+00:00"))
            .astimezone(ZoneInfo(selected_zone()))
            .replace(tzinfo=None)
            .isoformat()
            if old
            else soon(),
        ),
        field("reference", "Referencia autorizada"),
    ]
    if old:
        fields.append(
            field("supersedes", "Destino anterior", "hidden", default=old["id"])
        )
    return submit(
        "inventario",
        f"/api/v1/resources/{identifier}/destination",
        fields + confirmations(),
        title="Corregir destino" if old else "Registrar destino",
        active="inventory",
        back=url_for("inventory.detail", identifier=identifier),
        note="La recepción logística y el uso clínico son hechos distintos. Una corrección conserva toda la historia.",
    )


REPORTS = {
    "INVENTORY": "Inventario",
    "EXPIRY": "Caducidades",
    "REQUESTS": "Solicitudes",
    "SHIPMENTS": "Tiempos de traslado",
    "ACTIVITY": "Actividad",
    "CUSTODY": "Custodia",
    "TRACEABILITY": "Trazabilidad",
}


@regional.get("/reportes")
def reports():
    return table(
        "Reportes privados",
        "reportes",
        "documentos",
        "/api/v1/export-jobs",
        [
            ("report", "Reporte"),
            ("format", "Formato"),
            ("status", "Estado"),
            ("created_at", "Solicitado"),
        ],
        new=url_for("regional.report_new"),
        links=lambda row: url_for("regional.report_detail", identifier=row["id"]),
    )


@regional.route("/reportes/nuevo", methods=["GET", "POST"])
def report_new():
    def report_filters(data):
        data["filters"] = {
            key: data.pop("filter_" + key)
            for key in ("q", "status", "kind", "component", "source", "action")
            if data.get("filter_" + key)
        }
        for key in ("q", "status", "kind", "component", "source", "action"):
            data.pop("filter_" + key, None)
        return data

    return submit(
        "documentos",
        "/api/v1/export-jobs",
        [
            field("report", "Contenido", "select", list(REPORTS.items())),
            field(
                "format", "Formato", "select", [(v, v) for v in ("PDF", "CSV", "XLSX")]
            ),
            field("subject_id", "Identificador del traslado o recurso", required=False),
            field("from_at", "Desde", "datetime-local", default=soon(-24)),
            field("until_at", "Hasta, sin incluir", "datetime-local", default=soon(1)),
            field(
                "timezone", "Zona de presentación", "hidden", default=selected_zone()
            ),
            *[
                field("filter_" + key, label, required=False)
                for key, label in (
                    ("q", "Búsqueda"),
                    ("status", "Estado"),
                    ("kind", "Tipo"),
                    ("component", "Componente"),
                    ("source", "Fuente de auditoría"),
                    ("action", "Acción de auditoría"),
                )
            ],
            field(
                "order",
                "Orden",
                "select",
                [
                    ("DATE_DESC", "Más reciente primero"),
                    ("ID_ASC", "Identificador ascendente"),
                ],
            ),
        ],
        title="Solicitar reporte",
        transform=report_filters,
        active="reportes",
        back=url_for("regional.reports"),
        success=lambda row: url_for("regional.report_detail", identifier=row["id"]),
        note="Custodia y trazabilidad requieren identificador. La descarga permanece privada y requiere análisis del archivo.",
    )


@regional.get("/reportes/<uuid:identifier>")
def report_detail(identifier):
    row = call("documentos", "/api/v1/export-jobs/" + str(identifier))
    actions = []
    if row["status"] == "RETRYABLE":
        actions.append(
            (
                "Reintentar con permisos vigentes",
                url_for("regional.report_retry", identifier=identifier),
            )
        )
    if row["status"] == "COMPLETE":
        actions.append(
            (
                "Descargar reporte",
                url_for("regional.download_file", identifier=row["file_id"]),
            )
        )
    return detail(
        "Reporte " + REPORTS.get(row["report"], row["report"]), "reportes", row, actions
    )


@regional.route("/reportes/<uuid:identifier>/reintentar", methods=["GET", "POST"])
def report_retry(identifier):
    call("documentos", "/api/v1/export-jobs/" + str(identifier))
    return submit(
        "documentos",
        f"/api/v1/export-jobs/{identifier}/retry",
        confirmations(),
        title="Reintentar reporte",
        active="reportes",
        back=url_for("regional.report_detail", identifier=identifier),
        note="Se verifica tu autorización actual. Una sesión vencida durante la extracción exige un nuevo intento autorizado.",
    )


def hla_form(data):
    lines = data.pop("hla_loci", "")
    release = data.pop("nomenclature_version", "")
    resolution = data.pop("resolution", "")
    catalogue = data.pop("catalogue_version", None)
    if lines:
        loci = []
        for line in lines.splitlines():
            if not line.strip():
                continue
            if "=" not in line:
                raise BusinessError(
                    "Declara cada locus como A=A*01:01; usa ? para ambigüedad.", 422
                )
            name, alleles = line.split("=", 1)
            name = name.strip()
            loci.append(
                {
                    "locus": name.rstrip("?"),
                    "ambiguous": name.endswith("?"),
                    "alleles": [x.strip() for x in alleles.split(",") if ":" in x],
                    "groups": [x.strip() for x in alleles.split(",") if ":" not in x],
                    "partial": any(":" not in x for x in alleles.split(",")),
                }
            )
        data["hla"] = {
            "nomenclature": "HLA-colon-2010",
            "nomenclature_version": release,
            "resolution": resolution,
            "catalogue_version": catalogue,
            "loci": loci,
        }
    cross = {
        key: data.pop("cross_" + key, None)
        for key in (
            "donor_sample_id",
            "recipient_sample_id",
            "request_id",
            "technique",
            "reported_interpretation",
        )
    }
    if any(cross.values()):
        if not all(cross.values()):
            raise BusinessError(
                "Prueba cruzada requiere ambas muestras, solicitud, técnica e interpretación declarada.",
                422,
            )
        data["crossmatch"] = cross
    return data


def crossmatch_fields(value=None):
    value = value or {}
    return [
        field("cross_" + key, label, required=False, default=value.get(key, ""))
        for key, label in (
            ("donor_sample_id", "Prueba cruzada: muestra del donante"),
            ("recipient_sample_id", "Prueba cruzada: muestra del receptor"),
            ("request_id", "Prueba cruzada: solicitud"),
            ("technique", "Prueba cruzada: técnica declarada"),
        )
    ] + [
        field(
            "cross_reported_interpretation",
            "Prueba cruzada: interpretación del laboratorio",
            "select",
            [(x, x) for x in ("PENDING", "POSITIVE", "NEGATIVE", "INDETERMINATE")],
            required=False,
            default=value.get("reported_interpretation", ""),
        )
    ]


@regional.get("/algoritmos")
def algorithm_runs():
    return table(
        "Simulaciones académicas",
        "rutas",
        "priorizacion_geografia",
        "/api/v1/algorithm-runs",
        [
            ("algorithm_version", "Algoritmo"),
            ("source", "Fuente"),
            ("created_at", "Fecha"),
        ],
        new=url_for("regional.demand_simulation"),
        links=lambda row: url_for("regional.algorithm_run", identifier=row["id"]),
    )


@regional.get("/algoritmos/<uuid:identifier>")
def algorithm_run(identifier):
    row = call("priorizacion_geografia", "/api/v1/algorithm-runs/" + str(identifier))
    return detail(
        "Simulación académica",
        "rutas",
        row,
        note="Información registrada y completitud técnica no equivalen a compatibilidad. Esta simulación no emite dictamen ni crea reservas.",
    )


@regional.route("/algoritmos/demanda", methods=["GET", "POST"])
def demand_simulation():
    def transform(data):
        data["history"] = [float(v.strip()) for v in data["history"].split(",")]
        return dict(
            data,
            algorithm_version="DEMAND-SES-1.0",
            synthetic=True,
            profile_version="SYNTHETIC-1",
        )

    return submit(
        "priorizacion_geografia",
        "/api/v1/algorithm-runs",
        [
            field("component", "Componente"),
            field("source", "Procedencia del consumo sintético"),
            field("as_of", "Corte del historial", "datetime-local", default=soon()),
            field(
                "history",
                "Consumo por ventanas consecutivas, separado por comas",
                "textarea",
            ),
            field("window_days", "Días por ventana", "number", default=1),
            field("stock", "Existencias", "decimal", default=0),
        ],
        transform=transform,
        title="Estimar demanda sintética",
        active="rutas",
        back=url_for("regional.algorithm_runs"),
        success=lambda row: url_for("regional.algorithm_run", identifier=row["id"]),
        note="Use datos ficticios del mismo componente e institución. No modifica caducidades ni ejecuta transferencias.",
    )
