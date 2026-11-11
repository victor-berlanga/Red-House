"""Minimal complete workbench; algorithms and approvals execute only in owners."""

from .common import (
    call,
    choices,
    confirmations,
    detail,
    field,
    regional,
    render_template,
    rows,
    soon,
    submit,
    table,
    url_for,
)

PRODUCTS = [
    ("RBC", "Eritrocitos"),
    ("PLASMA", "Plasma"),
    ("PLATELETS", "Plaquetas"),
    ("KIDNEY", "Riñón"),
    ("LIVER", "Hígado"),
    ("HEART", "Corazón"),
]


@regional.get("/apoyo-decisiones")
def decision_support():
    return render_template(
        "integration/decision_support.html", title="Apoyo a decisiones", active="rutas"
    )


@regional.get("/apoyo-decisiones/historial")
def decision_history():
    return table(
        "Análisis registrados",
        "rutas",
        "priorizacion_geografia",
        "/api/v1/decision-runs",
        [
            ("algorithm_version", "Algoritmo"),
            ("created_at", "Fecha"),
            ("source", "Fuente"),
        ],
        new=url_for("regional.decision_new"),
        links=lambda row: url_for("regional.decision_detail", identifier=row["id"]),
    )


@regional.get("/apoyo-decisiones/<uuid:identifier>")
def decision_detail(identifier):
    row = call("priorizacion_geografia", "/api/v1/decision-runs/" + str(identifier))
    reproduction = call(
        "priorizacion_geografia",
        "/api/v1/decision-runs/" + str(identifier) + "/reproduce",
    )
    return render_template(
        "integration/decision_detail.html",
        title="Análisis y explicación",
        active="rutas",
        record=row,
        reproduction=reproduction,
        note="Registro, completitud, preselección y dictamen son niveles distintos. Una simulación no autoriza usos clínicos. GPS observado, recorrido, ruta y ETA conservan fuentes separadas.",
    )


@regional.route("/apoyo-decisiones/nuevo", methods=["GET", "POST"])
def decision_new():
    def transform(data):
        value = data.pop("evaluation_id", None)
        data["evaluation_ids"] = [value] if value else []
        return data

    return submit(
        "priorizacion_geografia",
        "/api/v1/decision-runs",
        [
            field(
                "branch",
                "Análisis",
                "select",
                [
                    (x, y)
                    for x, y in [
                        ("ALG-01", "Evaluación explicable"),
                        ("ALG-02", "Comparación logística sintética"),
                        ("ALG-02-GEO", "Ruta regional estimada"),
                        ("ALG-03", "Propuesta de cobertura"),
                        ("ALG-04", "Demanda y caducidad"),
                        ("ALG-05", "Revisión de inconsistencias"),
                    ]
                ],
            ),
            field(
                "evaluation_id",
                "Evaluación registrada",
                "select",
                choices(rows("compatibilidad", "/api/v1/evaluations"), "created_at"),
                required=False,
            ),
            field(
                "policy_id",
                "Política operativa sintética",
                "select",
                choices(rows("compatibilidad", "/api/v1/laboratory/profiles"), "name"),
                required=False,
            ),
            field(
                "graph_id",
                "Grafo regional",
                "select",
                choices(
                    rows("priorizacion_geografia", "/api/v1/regional-graphs"), "name"
                ),
                required=False,
            ),
            field("origin", "Nodo de origen", required=False),
            field("destination", "Nodo de destino", required=False),
            field(
                "shipment_id",
                "Traslado para consultar observaciones autorizadas",
                required=False,
            ),
            field("component", "Producto", "select", PRODUCTS),
            field("days", "Ventana histórica en días", "number", default=30),
        ],
        transform=transform,
        title="Crear análisis",
        active="rutas",
        back=url_for("regional.decision_support"),
        success=lambda row: url_for("regional.decision_detail", identifier=row["id"]),
        note="Evaluación requerida para los tres primeros análisis de candidatos. Ruta requiere grafo y nodos registrados. Consumo e inconsistencias se obtienen de sus propietarios. No se ejecutan reservas ni transferencias.",
    )


@regional.get("/laboratorio/perfiles")
def rule_profiles():
    return table(
        "Perfiles de datos exigidos",
        "laboratorio",
        "compatibilidad",
        "/api/v1/laboratory/profiles",
        [
            ("name", "Perfil"),
            ("component", "Producto"),
            ("version", "Versión"),
            ("synthetic", "Académico"),
        ],
        new=url_for("regional.rule_new"),
        links=lambda row: url_for("regional.rule_detail", identifier=row["id"]),
    )


@regional.get("/laboratorio/perfiles/<uuid:identifier>")
def rule_detail(identifier):
    row = call("compatibilidad", "/api/v1/laboratory/profiles/" + str(identifier))
    gov = call(
        "compatibilidad",
        "/api/v1/laboratory/profiles/" + str(identifier) + "/governance",
    )
    return render_template(
        "integration/rule_detail.html",
        title="Perfil y gobierno",
        active="laboratorio",
        record=row,
        governance=gov,
        note="La fuente normativa y la cuenta de prueba no acreditan aprobación profesional. El estado del perfil no es dictamen de un paciente.",
    )


@regional.route("/laboratorio/perfiles/nuevo", methods=["GET", "POST"])
def rule_new():
    def transform(data):
        data["required_tests"] = [
            x.strip() for x in data["required_tests"].split(",") if x.strip()
        ]
        data["required_loci"] = [
            x.strip() for x in data.pop("loci", "").split(",") if x.strip()
        ]
        reference = data.pop("evidence_rule", None)
        data["evidence_rules"] = [reference] if reference else []
        ranking = data.pop("ranking_policy", None)
        age = data.pop("max_age_seconds", None)
        data["policy"] = {
            "version": "COMPLETENESS-2.0",
            "max_age_seconds": int(age) if age else None,
            "contradictions": "REVIEW",
            "require_document": True,
            "require_hla_catalogue": data.pop("check_catalogue", "NO") == "YES",
        }
        if ranking == "SYNTHETIC":
            data["policy"].update(
                ranking_order="URGENCY_WAIT_EXPIRY_TIME_DISTANCE_ID",
                urgency_scale="CAPTURED_1_3_SYNTHETIC",
            )
        return dict(data, synthetic=True, version=1)

    return submit(
        "compatibilidad",
        "/api/v1/laboratory/profiles",
        [
            field("name", "Nombre"),
            field("kind", "Tipo", "select", [("BLOOD", "Sangre"), ("ORGAN", "Órgano")]),
            field("component", "Producto", "select", PRODUCTS),
            field("purpose", "Propósito"),
            field(
                "ranking_policy",
                "Comparación logística",
                "select",
                [
                    ("NONE", "Sin política de orden"),
                    (
                        "SYNTHETIC",
                        "Sintética: urgencia, espera, vencimiento, minutos, distancia",
                    ),
                ],
            ),
            field("source", "Fuente y alcance"),
            field(
                "evidence_rule",
                "Referencia documental (no aprobación)",
                "select",
                [
                    (r["id"], r["id"] + " · " + r["section"])
                    for r in call(
                        "compatibilidad", "/api/v1/laboratory/reference-sources"
                    )["rules"]
                ],
                required=False,
            ),
            field(
                "check_catalogue",
                "Exigir reconocimiento en catálogo HLA",
                "select",
                [
                    ("NO", "No exigido por este perfil"),
                    ("YES", "Sí, comprobación técnica de referencia"),
                ],
            ),
            field("required_tests", "Pruebas exigidas, separadas por comas"),
            field("loci", "Loci exigidos por este perfil", required=False),
            field(
                "max_age_seconds",
                "Antigüedad máxima sintética, segundos",
                "number",
                required=False,
            ),
            field(
                "effective_at", "Inicio de vigencia", "datetime-local", default=soon()
            ),
            field("valid_until", "Fin de vigencia", "datetime-local"),
        ],
        transform=transform,
        title="Registrar perfil académico",
        active="laboratorio",
        back=url_for("regional.rule_profiles"),
        success=lambda row: url_for("regional.rule_detail", identifier=row["id"]),
        note="Parámetros sintéticos. La vigencia se aplica como intervalo cerrado al inicio y abierto al final; no son umbrales clínicos aprobados.",
    )


@regional.route(
    "/laboratorio/perfiles/<uuid:identifier>/acciones", methods=["GET", "POST"]
)
def rule_action(identifier):
    gov = call(
        "compatibilidad",
        "/api/v1/laboratory/profiles/" + str(identifier) + "/governance",
    )
    return submit(
        "compatibilidad",
        "/api/v1/laboratory/profiles/" + str(identifier) + "/actions",
        [
            field("sequence", "Secuencia", "hidden", default=len(gov["actions"]) + 1),
            field(
                "state",
                "Transición",
                "select",
                [(x, x) for x in ("IN_REVIEW", "APPROVED", "RETIRED")],
            ),
            field(
                "competency_reference",
                "Referencia de competencia acreditada",
                required=False,
            ),
            field("document_id", "Documento privado de aprobación", required=False),
        ]
        + confirmations(),
        title="Registrar decisión sobre perfil",
        active="laboratorio",
        back=url_for("regional.rule_detail", identifier=identifier),
        note="Aprobación requiere competencia configurada, segregación, evidencia verificada y perfil no sintético. Retirar revoca usos posteriores.",
    )


@regional.get("/laboratorio/muestras")
def samples():
    return table("Muestras de laboratorio", "laboratorio", "compatibilidad", "/api/v1/laboratory/samples",
        [("identifier", "Muestra"), ("status", "Estado"), ("collected_at", "Toma"), ("received_at", "Recepción")],
        filters=("q", "status", "from_at", "until_at", "sort"), new=url_for("regional.sample_new"),
        links=lambda row: url_for("regional.sample_detail", identifier=row["id"]))


@regional.route("/laboratorio/muestras/nueva", methods=["GET", "POST"])
def sample_new():
    def transform(data):
        kind = data.pop("subject_kind")
        identifier = data.pop("subject_id")
        data[kind] = identifier
        return data

    return submit(
        "compatibilidad",
        "/api/v1/laboratory/samples",
        [
            field(
                "subject_kind",
                "Sujeto de muestra",
                "select",
                [
                    (x, y)
                    for x, y in [
                        ("resource_id", "Unidad u órgano"),
                        ("recipient_id", "Receptor"),
                        ("donation_id", "Donación"),
                    ]
                ],
            ),
            field("subject_id", "Referencia de sujeto autorizado"),
            field("request_id", "Solicitud relacionada", required=False),
            field(
                "profile_id",
                "Perfil",
                "select",
                choices(rows("compatibilidad", "/api/v1/laboratory/profiles"), "name"),
            ),
            field("identifier", "Identificador de muestra"),
            field("collected_at", "Fecha de toma", "datetime-local", default=soon()),
        ],
        transform=transform,
        title="Registrar muestra",
        active="laboratorio",
        back=url_for("regional.laboratory"),
        success=lambda row: url_for("regional.sample_detail", identifier=row["id"]),
    )


@regional.get("/laboratorio/muestras/<uuid:identifier>")
def sample_detail(identifier):
    row = call("compatibilidad", "/api/v1/laboratory/samples/" + str(identifier))
    return detail(
        "Muestra registrada",
        "laboratorio",
        row,
        actions=[
            ("Resultados e historia", url_for("regional.laboratory", sample_id=identifier)),
            (
                "Consultar completitud",
                url_for("regional.sample_completeness", identifier=identifier),
            ),
            (
                "Recibir muestra",
                url_for("regional.sample_receive", identifier=identifier),
            ),
            (
                "Registrar resultado",
                url_for("regional.result_new", identifier=identifier),
            ),
        ],
    )


@regional.get("/laboratorio/muestras/<uuid:identifier>/completitud")
def sample_completeness(identifier):
    result = call(
        "compatibilidad",
        "/api/v1/laboratory/samples/" + str(identifier) + "/completeness",
    )
    return render_template(
        "integration/laboratory_completeness.html",
        title="Completitud según perfil",
        active="laboratorio",
        result=result,
        identifier=identifier,
    )


@regional.route(
    "/laboratorio/muestras/<uuid:identifier>/recibir", methods=["GET", "POST"]
)
def sample_receive(identifier):
    row = call("compatibilidad", "/api/v1/laboratory/samples/" + str(identifier))
    return submit(
        "compatibilidad",
        "/api/v1/laboratory/samples/" + str(identifier) + "/receive",
        [
            field("version", "Versión", "hidden", default=row["version"]),
            field(
                "decision",
                "Recepción",
                "select",
                [("RECEIVED", "Recibida"), ("REJECTED", "Rechazada")],
            ),
        ]
        + confirmations(),
        title="Recibir muestra",
        active="laboratorio",
        back=url_for("regional.sample_detail", identifier=identifier),
    )


@regional.route(
    "/laboratorio/muestras/<uuid:identifier>/resultado", methods=["GET", "POST"]
)
def result_new(identifier):
    from .quality import crossmatch_fields, hla_form

    return submit(
        "compatibilidad",
        "/api/v1/laboratory/results",
        [
            field("sample_id", "Muestra", "hidden", default=str(identifier)),
            field("test_code", "Código de prueba"),
            field(
                "result_state",
                "Estado registrado",
                "select",
                [
                    (x, x)
                    for x in ("PENDING", "NOT_PERFORMED", "INDETERMINATE", "REPORTED")
                ],
            ),
            field("value", "Valor documentado", required=False),
            field("method", "Método"),
            field("laboratory", "Laboratorio"),
            field("reference", "Procedencia documental"),
            field("measured_at", "Fecha de medición", "datetime-local", default=soon()),
            field("issued_at", "Fecha de emisión", "datetime-local", required=False),
            field(
                "document_id", "Documento verificado de esta muestra", required=False
            ),
            field(
                "hla_loci",
                "HLA declarado: A=A*01:01; grupo parcial A=A*01; ? para ambigüedad",
                "textarea",
                required=False,
            ),
            field(
                "nomenclature_version",
                "Versión de nomenclatura",
                required=False,
                default="2010:syntax-2",
            ),
            field("resolution", "Resolución declarada", required=False),
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
            ),
        ]
        + crossmatch_fields(),
        transform=hla_form,
        title="Registrar resultado",
        active="laboratorio",
        back=url_for("regional.sample_detail", identifier=identifier),
        success=lambda row: url_for("regional.lab_result", identifier=row["id"]),
        note="Para adjuntar un documento, registre primero el resultado pendiente y prepare el archivo privado sobre ese resultado. Después registre su corrección informada.",
    )


@regional.get("/revision-anomalias")
def anomaly_reviews():
    return table(
        "Anomalías pendientes de revisión",
        "auditoria",
        "auditoria",
        "/api/v1/anomaly-reviews",
        [("state", "Estado"), ("created_at", "Fecha"), ("source", "Fuente")],
        links=lambda row: url_for("regional.anomaly_review", identifier=row["id"]),
    )


@regional.get("/revision-anomalias/<uuid:identifier>")
def anomaly_review(identifier):
    row = call("auditoria", "/api/v1/anomaly-reviews/" + str(identifier))
    return detail(
        "Revisión de anomalía potencial",
        "auditoria",
        row,
        actions=[
            (
                "Resolver revisión",
                url_for("regional.anomaly_resolve", identifier=identifier),
            )
        ],
        note="La detección no confirma incidente. La resolución no cambia los hechos originales.",
    )


@regional.route(
    "/revision-anomalias/<uuid:identifier>/resolver", methods=["GET", "POST"]
)
def anomaly_resolve(identifier):
    row = call("auditoria", "/api/v1/anomaly-reviews/" + str(identifier))
    return submit(
        "auditoria",
        "/api/v1/anomaly-reviews/" + str(identifier) + "/resolve",
        [
            field("version", "Versión", "hidden", default=row["version"]),
            field(
                "state",
                "Resolución",
                "select",
                [
                    ("CONFIRMED", "Confirmada tras revisión"),
                    ("DISMISSED", "Descartada tras revisión"),
                ],
            ),
        ]
        + confirmations(),
        title="Resolver revisión",
        active="auditoria",
        back=url_for("regional.anomaly_review", identifier=identifier),
    )


@regional.get("/apoyo-decisiones/fuentes")
def public_reference_sources():
    return render_template(
        "integration/public_sources.html",
        title="Fuentes y límites de aplicación",
        active="rutas",
        sources=call("compatibilidad", "/api/v1/laboratory/reference-sources"),
        roads=call("priorizacion_geografia", "/api/v1/regional-graph-sources"),
    )


@regional.route("/apoyo-decisiones/importar-rutas", methods=["GET", "POST"])
def import_reference_roads():
    refs = call("priorizacion_geografia", "/api/v1/regional-graph-sources")["items"]
    return submit(
        "priorizacion_geografia",
        "/api/v1/regional-graphs/from-reference",
        [
            field(
                "reference_id",
                "Fuente vial conservada",
                "select",
                [(r["id"], r["name"]) for r in refs],
            ),
            field(
                "supersedes",
                "Grafo anterior que sustituye, si corresponde",
                required=False,
            ),
        ],
        title="Registrar rutas de fuente pública",
        active="rutas",
        back=url_for("regional.public_reference_sources"),
        success=lambda row: url_for("regional.decision_new"),
        note="Rutas de OpenStreetMap/OSRM; duración modelada, sin tráfico medido. Cobertura y fecha de los datos se muestran en Fuentes. No interviene GPS físico.",
    )
