from ..selectors import selection

"""Rutas web: logistics. Las reglas residen en las API propietarias."""
from .common import (
    location_field,
    BusinessError,
    call,
    choices,
    confirmations,
    detail,
    display,
    field,
    g,
    organs,
    regional,
    request,
    rows,
    soon,
    submit,
    table,
    url_for,
)


@regional.get("/rutas", endpoint="routes")
def routes_list():
    return table(
        "Rutas y estimaciones",
        "rutas",
        "priorizacion_geografia",
        "/api/v1/routes",
        [
            ("origin_id", "Origen"),
            ("destination_id", "Destino"),
            ("distance_km", "Distancia · km"),
            ("travel_minutes", "Tiempo · min"),
        ],
        actions=lambda row: (
            [
                (
                    "Editar ruta",
                    url_for("regional.route_edit", identifier=row["id"]),
                    "pencil",
                )
            ]
            if g.principal.role_code == "COORDINATOR"
            else []
        ),
        new=url_for("regional.route_new")
        if g.principal.role_code == "COORDINATOR"
        else None,
        links=lambda row: (
            url_for("regional.route_detail", identifier=row["id"])
            if g.principal.role_code in ("COORDINATOR", "MEDICAL")
            else None
        ),
    )


@regional.route("/rutas/nueva", methods=["GET", "POST"])
def route_new():
    options = list(g.institutions.items())
    return submit(
        "priorizacion_geografia",
        "/api/v1/routes",
        [
            field("origin_id", "Institución de origen", "select", options),
            field("destination_id", "Institución de destino", "select", options),
            field("distance_km", "Distancia estimada (km)", "decimal"),
            field("travel_minutes", "Tiempo estimado (min)", "number"),
            field("source", "Fuente de la estimación", "textarea"),
        ],
        title="Registrar ruta",
        active="rutas",
        back=url_for("regional.routes"),
    )


@regional.route("/rutas/<uuid:identifier>/editar", methods=["GET", "POST"])
def route_edit(identifier):
    match = call("priorizacion_geografia", "/api/v1/routes/" + str(identifier))
    return submit(
        "priorizacion_geografia",
        "/api/v1/routes/" + str(identifier),
        [
            field(
                "distance_km",
                "Distancia estimada (km)",
                "decimal",
                default=match["distance_km"],
            ),
            field(
                "travel_minutes",
                "Tiempo estimado (min)",
                "number",
                default=match["travel_minutes"],
            ),
            field(
                "source", "Fuente de la estimación", "textarea", default=match["source"]
            ),
            field("version", "Versión", "hidden", default=match["version"]),
        ],
        method="PATCH",
        title="Actualizar estimación",
        active="rutas",
        back=url_for("regional.routes"),
    )


@regional.get("/traslados")
@organs.get("/organos/traslados")
def allocations():
    return table(
        "Traslados y custodia",
        "traslados",
        "transporte",
        "/api/v1/shipments",
        [
            ("reference", "Traslado"),
            ("origin_id", "Origen"),
            ("destination_id", "Destino"),
            ("departure_at", "Salida prevista"),
            ("eta", "Llegada prevista"),
            ("status", "Estado"),
        ],
        links=lambda row: url_for("regional.shipment_detail", identifier=row["id"]),
        new=url_for("regional.shipment_new")
        if g.principal.role_code == "COORDINATOR"
        else None,
        note="Reservas listas para programar: consulta la sección de reservas."
        if g.principal.role_code != "TRANSPORT"
        else "Se muestran únicamente los traslados que tienes asignados.",
    )


@regional.route("/traslados/nuevo", methods=["GET", "POST"])
def shipment_new():
    return submit(
        "transporte",
        "/api/v1/shipments",
        [
            selection(
                "reservation_id",
                "Reserva confirmada",
                "reservations",
                default=request.args.get("reservation_id", ""),
            ),
            selection("transport_user_id", "Responsable de traslado", "transport"),
            field("departure_at", "Salida prevista", "datetime-local", default=soon()),
            field("eta", "Llegada prevista", "datetime-local", default=soon(1)),
        ]
        + confirmations(),
        title="Planear traslado",
        active="traslados",
        back=url_for("regional.allocations"),
        success=lambda row: url_for("regional.shipment_detail", identifier=row["id"]),
    )


@regional.get("/traslados/<uuid:identifier>")
def shipment_detail(identifier):
    row = call("transporte", "/api/v1/shipments/" + str(identifier))
    sections = [
        ("Eventos de traslado", row["transitions"]),
        ("Planificación", row.get("decisions", [])),
    ]
    try:
        custody = call("custodia", "/api/v1/chains/" + str(identifier))
        sections.append(
            (
                "Cadena de custodia",
                [
                    dict(
                        state=e["event"]["metadata"]["state"],
                        sequence=e["sequence"],
                        created_at=e["event"]["occurred_at"],
                        hash=e["hash"],
                    )
                    for e in custody["events"]
                ],
            )
        )
    except BusinessError as exc:
        if exc.status not in (404, 503):
            raise
        sections.append(
            (
                "Cadena de custodia",
                [
                    {
                        "message": "Historial pendiente de sincronización. Los eventos del traslado se conservan."
                    }
                ],
            )
        )
    actions = []
    role = g.principal.role_code
    next_state = {
        "PLANNED": "PREPARED",
        "PREPARED": "COLLECTED",
        "COLLECTED": "IN_TRANSIT",
        "IN_TRANSIT": "DELIVERED",
        "DELIVERED": "ACCEPTED",
    }.get(row["status"])
    tenant = str(g.principal.institution_id)
    authorized = (
        (next_state == "PREPARED" and role == "OPERATOR" and tenant == row["origin_id"])
        or (
            next_state == "ACCEPTED"
            and role == "OPERATOR"
            and tenant == row["destination_id"]
        )
        or (
            next_state in ("COLLECTED", "IN_TRANSIT", "DELIVERED")
            and role == "TRANSPORT"
        )
    )
    if next_state and authorized and not row["inventory_pending"]:
        actions.append(
            (
                display(next_state),
                url_for(
                    "regional.shipment_transition",
                    identifier=identifier,
                    state=next_state,
                ),
            )
        )
    if row["status"] not in ("ACCEPTED", "CANCELLED", "REJECTED") and role in (
        "OPERATOR",
        "COORDINATOR",
        "TRANSPORT",
    ):
        actions.append(
            (
                "Registrar incidencia",
                url_for(
                    "regional.shipment_transition",
                    identifier=identifier,
                    state="INCIDENT",
                ),
            )
        )
    if role == "COORDINATOR" and row["status"] in ("PLANNED", "PREPARED"):
        actions.append(
            (
                "Cancelar antes de recolección",
                url_for(
                    "regional.shipment_transition",
                    identifier=identifier,
                    state="CANCELLED",
                ),
            )
        )
    if role == "TRANSPORT" and row["status"] in ("COLLECTED", "IN_TRANSIT"):
        actions.append(
            (
                "Registrar ubicación autorizada",
                url_for("regional.telemetry", identifier=identifier),
            )
        )
    return detail(
        "Traslado " + str(identifier)[:8].upper(),
        "traslados",
        row,
        actions,
        sections,
        note="Recepción logística y cadena de custodia. No equivale a transfusión ni trasplante realizado.",
    )


@regional.route("/traslados/<uuid:identifier>/paso/<state>", methods=["GET", "POST"])
def shipment_transition(identifier, state):
    if state not in (
        "PREPARED",
        "COLLECTED",
        "IN_TRANSIT",
        "DELIVERED",
        "ACCEPTED",
        "INCIDENT",
        "CANCELLED",
    ):
        raise BusinessError("Paso inválido.", 422)
    row = call("transporte", "/api/v1/shipments/" + str(identifier))
    return submit(
        "transporte",
        "/api/v1/shipments/" + str(identifier) + "/transitions",
        [
            field("state", "Paso", "hidden", default=state),
            field("version", "Versión", "hidden", default=row["version"]),
        ]
        + ([location_field("destination_location_id")] if state == "ACCEPTED" else [])
        + confirmations(),
        title="Documentar: " + display(state),
        active="traslados",
        back=url_for("regional.shipment_detail", identifier=identifier),
    )


@regional.route("/traslados/<uuid:identifier>/ubicacion", methods=["GET", "POST"])
def telemetry(identifier):
    row = call("transporte", "/api/v1/shipments/" + str(identifier))
    if g.principal.role_code != "TRANSPORT" or row["status"] not in (
        "COLLECTED",
        "IN_TRANSIT",
    ):
        raise BusinessError(
            "La ubicación solo se registra durante un traslado activo asignado a tu cuenta.",
            403,
        )
    g.location_capture = True
    return submit(
        "transporte",
        "/api/v1/shipments/" + str(identifier) + "/telemetry",
        [
            field("latitude", "Latitud capturada", "decimal"),
            field("longitude", "Longitud capturada", "decimal"),
            field("captured_at", "Fecha de captura", "datetime-local", default=soon()),
        ],
        title="Registrar ubicación",
        active="traslados",
        back=url_for("regional.shipment_detail", identifier=identifier),
        note="Captura únicamente la ubicación autorizada del proceso. La muestra debe corresponder a los últimos cinco minutos.",
        location_capture=True,
    )


@regional.get("/rutas/<uuid:identifier>")
def route_detail(identifier):
    row = call("priorizacion_geografia", "/api/v1/routes/" + str(identifier))
    actions = (
        [("Editar ruta", url_for("regional.route_edit", identifier=identifier))]
        if g.principal.role_code == "COORDINATOR"
        else []
    )
    return detail("Ruta entre instituciones", "rutas", row, actions)
