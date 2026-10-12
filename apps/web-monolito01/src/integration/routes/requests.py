from ..selectors import selection

"""Rutas web: requests. Las reglas residen en las API propietarias."""
from .common import (
    COMPONENTS,
    call,
    choices,
    confirmations,
    detail,
    display,
    field,
    g,
    regional,
    render_template,
    rows,
    submit,
    table,
    url_for,
)


@regional.get("/solicitudes", endpoint="requests")
def requests_list():
    return table(
        "Solicitudes y compatibilidad",
        "solicitudes",
        "receptores",
        "/api/v1/requests",
        [
            ("reference", "Solicitud"),
            ("kind", "Recurso"),
            ("component", "Componente"),
            ("quantity", "Cantidad"),
            ("urgency", "Urgencia · 1–3"),
            ("status", "Estado"),
            ("created_at", "Registro"),
        ],
        filters=("kind", "status"),
        links=lambda row: url_for("regional.request_detail", identifier=row["id"]),
        new=url_for("regional.request_new")
        if g.principal.role_code == "MEDICAL"
        else None,
    )


@regional.route("/solicitudes/nueva", methods=["GET", "POST"])
def request_new():
    return submit(
        "receptores",
        "/api/v1/requests",
        [
            selection("recipient_id", "Receptor", "recipients"),
            field("component", "Componente requerido", "select", COMPONENTS),
            field("quantity", "Cantidad", "number", default=1),
            field("urgency", "Urgencia capturada", "number", default=2),
        ],
        title="Registrar solicitud",
        active="solicitudes",
        back=url_for("regional.requests"),
        success=lambda row: url_for("regional.request_detail", identifier=row["id"]),
    )


@regional.get("/solicitudes/<uuid:identifier>")
def request_detail(identifier):
    row = call("receptores", "/api/v1/requests/" + str(identifier))
    actions, sections = [], [("Cobertura de la solicitud", row["coverage"])]
    if g.principal.role_code == "MEDICAL":
        evaluations = rows(
            "compatibilidad", "/api/v1/evaluations", request_id=str(identifier)
        )
        for evaluation in evaluations:
            evaluation["_href"] = url_for(
                "regional.evaluation_detail", identifier=evaluation["id"]
            )
        sections.append(("Historial de evaluaciones", evaluations))
        if row["status"] in ("OPEN", "IN_PROGRESS"):
            actions = [
                (
                    "Evaluar candidatos",
                    url_for("regional.evaluate", identifier=identifier),
                ),
                (
                    "Cancelar solicitud",
                    url_for("regional.request_cancel", identifier=identifier),
                ),
            ]
    if row.get("can_edit") and g.principal.role_code == "MEDICAL":
        actions.append(
            (
                "Editar solicitud",
                url_for("maintenance.edit", entity="requests", identifier=identifier),
            )
        )
    sections.append(("Decisiones registradas", row.get("decisions", [])))
    return detail(
        "Solicitud " + str(identifier)[:8].upper(),
        "solicitudes",
        row,
        actions,
        sections,
        note="La recepción logística completa cierra la solicitud; no registra una transfusión o trasplante.",
    )


@regional.route("/solicitudes/<uuid:identifier>/evaluar", methods=["GET", "POST"])
def evaluate(identifier):
    return submit(
        "compatibilidad",
        "/api/v1/evaluations",
        [field("request_id", "Solicitud", "hidden", default=str(identifier))],
        title="Evaluar candidatos",
        active="solicitudes",
        back=url_for("regional.request_detail", identifier=identifier),
        success=lambda row: url_for("regional.evaluation_detail", identifier=row["id"]),
        note="Preselección demostrativa explicable. Se requiere dictamen humano antes de reservar; no interpreta HLA.",
    )


@regional.route("/solicitudes/<uuid:identifier>/cancelar", methods=["GET", "POST"])
def request_cancel(identifier):
    row = call("receptores", "/api/v1/requests/" + str(identifier))
    return submit(
        "receptores",
        "/api/v1/requests/" + str(identifier) + "/cancel",
        [field("version", "Versión", "hidden", default=row["version"])]
        + confirmations(),
        title="Cancelar solicitud",
        active="solicitudes",
        back=url_for("regional.request_detail", identifier=identifier),
    )


@regional.get("/evaluaciones/<uuid:identifier>")
def evaluation_detail(identifier):
    row = call("compatibilidad", "/api/v1/evaluations/" + str(identifier))
    reviews = {r["resource_id"]: r for r in row["reviews"]}
    candidates = []
    for candidate in row["candidates"]:
        review = reviews.get(candidate["resource_id"])
        candidates.append(
            dict(
                candidate,
                review=review,
                review_url=url_for(
                    "regional.candidate_review",
                    identifier=identifier,
                    resource_id=candidate["resource_id"],
                ),
                reserve_url=url_for(
                    "regional.reserve",
                    identifier=identifier,
                    resource_id=candidate["resource_id"],
                ),
            )
        )
    rankings = rows(
        "priorizacion_geografia", "/api/v1/rankings", evaluation_id=str(identifier)
    )
    return render_template(
        "integration/evaluation.html",
        title="Compatibilidad y candidatos",
        active="solicitudes",
        evaluation=row,
        candidates=candidates,
        rankings=rankings,
        ranking_url=url_for("regional.rank", identifier=identifier),
        back=url_for("regional.request_detail", identifier=row["request_id"]),
    )


@regional.route(
    "/evaluaciones/<uuid:identifier>/dictamen/<uuid:resource_id>",
    methods=["GET", "POST"],
)
def candidate_review(identifier, resource_id):
    return submit(
        "compatibilidad",
        "/api/v1/evaluations/" + str(identifier) + "/reviews",
        [
            field("resource_id", "Recurso", "hidden", default=str(resource_id)),
            field(
                "decision",
                "Dictamen",
                "select",
                [("FAVORABLE", "Favorable"), ("UNFAVORABLE", "No favorable")],
            ),
        ]
        + confirmations(),
        title="Dictamen del candidato",
        active="solicitudes",
        back=url_for("regional.evaluation_detail", identifier=identifier),
    )


@regional.route(
    "/evaluaciones/<uuid:identifier>/reservar/<uuid:resource_id>",
    methods=["GET", "POST"],
)
def reserve(identifier, resource_id):
    return submit(
        "inventario",
        "/api/v1/reservations",
        [
            field("evaluation_id", "Evaluación", "hidden", default=str(identifier)),
            field("resource_id", "Recurso", "hidden", default=str(resource_id)),
        ]
        + confirmations(),
        title="Autorizar reserva",
        active="solicitudes",
        back=url_for("regional.evaluation_detail", identifier=identifier),
        success=lambda row: url_for(
            "regional.operation", identifier=row["operation_id"]
        ),
        note="La reserva vuelve a comprobar versiones, disponibilidad y capacidad. Ante una respuesta pendiente, consulta su seguimiento.",
    )


@regional.get("/operaciones/<uuid:identifier>")
def operation(identifier):
    row = call("inventario", "/api/v1/operations/" + str(identifier))
    actions = (
        [
            (
                "Reanudar operación",
                url_for("regional.operation_resume", identifier=identifier),
            )
        ]
        if row["status"] in ("PENDING", "ROLLBACK_PENDING")
        else []
    )
    if row.get("reservation"):
        actions.append(
            (
                "Ver reserva",
                url_for("regional.reservation", identifier=row["reservation"]["id"]),
            )
        )
    return detail(
        "Seguimiento de reserva",
        "solicitudes",
        row,
        actions,
        note="Pendiente no significa fallida. Conserva este enlace para consultar el resultado.",
    )


@regional.route("/operaciones/<uuid:identifier>/reanudar", methods=["GET", "POST"])
def operation_resume(identifier):
    return submit(
        "inventario",
        "/api/v1/operations/" + str(identifier) + "/resume",
        [],
        title="Reanudar operación",
        active="solicitudes",
        back=url_for("regional.operation", identifier=identifier),
    )


@regional.get("/reservas")
def reservations():
    return table(
        "Reservas y asignaciones",
        "traslados",
        "inventario",
        "/api/v1/reservations",
        [
            ("reference", "Reserva"),
            ("origin_id", "Origen"),
            ("destination_id", "Destino"),
            ("status", "Estado"),
            ("created_at", "Fecha"),
        ],
        links=lambda row: url_for("regional.reservation", identifier=row["id"]),
    )


@regional.get("/reservas/<uuid:identifier>")
def reservation(identifier):
    row = call("inventario", "/api/v1/reservations/" + str(identifier))
    actions = []
    if row["status"] == "RESERVED" and not row["shipment_id"]:
        if g.principal.role_code == "COORDINATOR":
            actions.append(
                (
                    "Planear traslado",
                    url_for("regional.shipment_new", reservation_id=identifier),
                )
            )
        elif g.principal.role_code == "MEDICAL":
            actions.append(
                (
                    "Cancelar reserva",
                    url_for("regional.reservation_cancel", identifier=identifier),
                )
            )
    if row["shipment_id"]:
        actions.append(
            (
                "Ver traslado y custodia",
                url_for("regional.shipment_detail", identifier=row["shipment_id"]),
            )
        )
    return detail("Reserva " + str(identifier)[:8].upper(), "traslados", row, actions)


@regional.route("/reservas/<uuid:identifier>/cancelar", methods=["GET", "POST"])
def reservation_cancel(identifier):
    return submit(
        "inventario",
        "/api/v1/reservations/" + str(identifier) + "/cancel",
        confirmations(),
        title="Cancelar reserva",
        active="traslados",
        back=url_for("regional.reservation", identifier=identifier),
    )


@regional.route("/evaluaciones/<uuid:identifier>/ordenar", methods=["GET", "POST"])
def rank(identifier):
    return submit(
        "priorizacion_geografia",
        "/api/v1/rankings",
        [field("evaluation_id", "Evaluación", "hidden", default=str(identifier))],
        title="Generar ranking operativo",
        active="solicitudes",
        back=url_for("regional.evaluation_detail", identifier=identifier),
    )


@regional.get("/propuestas")
def proposals():
    return table(
        "Propuestas de cobertura",
        "propuestas",
        "priorizacion_geografia",
        "/api/v1/allocation-proposals",
        [
            ("reference", "Propuesta"),
            ("slot_count", "Cupos considerados"),
            ("matched_count", "Cobertura propuesta"),
            ("elapsed_ms", "Procesamiento · ms"),
            ("created_at", "Registro"),
        ],
        new=url_for("regional.proposal_new"),
        links=lambda row: url_for("regional.proposal_detail", identifier=row["id"]),
        note="Matching máximo sobre evaluaciones con dictamen favorable. Las propuestas no reservan recursos ni sustituyen la autorización médica.",
    )


@regional.route("/propuestas/nueva", methods=["GET", "POST"])
def proposal_new():
    evaluations = rows("compatibilidad", "/api/v1/evaluations")
    return submit(
        "priorizacion_geografia",
        "/api/v1/allocation-proposals",
        [
            field(
                "evaluation_ids",
                "Evaluaciones revisadas (selecciona una por solicitud)",
                "multiselect",
                [
                    (
                        r["id"],
                        "Solicitud "
                        + r["request_id"][:8].upper()
                        + " · "
                        + display(r["kind"])
                        + " · "
                        + display(r["created_at"]),
                    )
                    for r in evaluations
                ],
            )
        ],
        title="Proponer cobertura regional",
        active="propuestas",
        back=url_for("regional.proposals"),
        success=lambda row: url_for("regional.proposal_detail", identifier=row["id"]),
        note="Selecciona evaluaciones con dictámenes favorables. Se conserva la versión de cada instantánea; toda reserva posterior vuelve a validar disponibilidad y capacidad.",
    )


@regional.get("/propuestas/<uuid:identifier>")
def proposal_detail(identifier):
    row = call(
        "priorizacion_geografia", "/api/v1/allocation-proposals/" + str(identifier)
    )
    sections = [
        (
            "Cobertura propuesta",
            [
                {
                    "Solicitud": "SOL-" + r["request_id"][:8].upper(),
                    "Recurso": "REC-" + r["resource_id"][:8].upper(),
                    "Explicación": r["explanation"],
                }
                for r in row["result"]
            ],
        )
    ]
    row["quantity"] = row["matched_count"]
    return detail(
        "Propuesta de cobertura",
        "propuestas",
        row,
        sections=sections,
        note="La propuesta se basa en instantáneas y no modifica inventario ni solicitudes. Reservar requiere revalidación y autorización humana.",
    )
