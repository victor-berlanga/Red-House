from ..selectors import selection

"""Rutas web: people. Las reglas residen en las API propietarias."""
from .common import (
    person_extra,
    BusinessError,
    COMPONENTS,
    GROUPS,
    call,
    choices,
    confirmations,
    detail,
    field,
    g,
    regional,
    request,
    rows,
    soon,
    submit,
    table,
    url_for,
)


@regional.get("/donantes/<kind>")
def people(kind):
    if kind not in ("donor", "recipient"):
        raise BusinessError("Vista no disponible.", 404)
    service, path = (
        ("donantes", "donors") if kind == "donor" else ("receptores", "recipients")
    )
    return table(
        "Donantes" if kind == "donor" else "Receptores",
        "donantes" if kind == "donor" else "receptores",
        service,
        "/api/v1/" + path,
        [
            ("folio", "Folio"),
            ("display_name", "Nombre"),
            ("blood_group", "ABO / Rh"),
            ("kind", "Recurso"),
            ("status", "Estado"),
        ],
        filters=("q",) if kind == "donor" else ("q", "kind"),
        links=lambda row: (
            url_for("regional.person_detail", kind=kind, identifier=row["id"])
            if kind == "donor" or g.principal.role_code == "MEDICAL"
            else None
        ),
        new=url_for("regional.person_new", kind=kind)
        if kind == "donor" or g.principal.role_code == "MEDICAL"
        else None,
    )


@regional.route("/donantes/<kind>/nuevo", methods=["GET", "POST"])
def person_new(kind):
    fields = [
        field("folio", "Folio del expediente"),
        field("display_name", "Nombre completo"),
        field("blood_group", "ABO / Rh", "select", [(s, s) for s in GROUPS]),
    ]
    if kind == "donor":
        fields.append(
            field("consent", "Se registró el consentimiento del donante", "checkbox")
        )
        service, path = "donantes", "donors"
    elif kind == "recipient":
        fields += [
            field(
                "kind",
                "Tipo de recurso",
                "select",
                [("BLOOD", "Sangre"), ("ORGAN", "Órgano")],
            ),
            field(
                "organ_type",
                "Órgano requerido (solo para órganos)",
                "select",
                COMPONENTS[1:],
                required=False,
            ),
            field("studies", "Estudios y antecedentes documentales", "textarea"),
        ]
        service, path = "receptores", "recipients"
    else:
        raise BusinessError("Vista no disponible.", 404)
    fields += person_extra(kind)
    return submit(
        service,
        "/api/v1/" + path,
        fields,
        title="Registrar " + ("donante" if kind == "donor" else "receptor"),
        active="donantes" if kind == "donor" else "receptores",
        back=url_for("regional.people", kind=kind),
        success=lambda row: url_for(
            "regional.person_detail", kind=kind, identifier=row["id"]
        ),
    )


@regional.get("/donantes/<kind>/<uuid:identifier>")
def person_detail(kind, identifier):
    if kind not in ("donor", "recipient"):
        raise BusinessError("Vista no disponible.", 404)
    row = call(
        "donantes" if kind == "donor" else "receptores",
        "/api/v1/"
        + ("donors" if kind == "donor" else "recipients")
        + "/"
        + str(identifier),
    )
    actions = []
    if kind == "donor" and g.principal.role_code == "MEDICAL":
        actions = [
            (
                "Registrar dictamen",
                url_for("regional.donor_review", identifier=identifier),
            ),
            (
                "Registrar donación",
                url_for("regional.donation_new", donor_id=identifier),
            ),
        ]
    if (kind == "donor" and g.principal.role_code in ("OPERATOR", "MEDICAL")) or (
        kind == "recipient" and g.principal.role_code == "MEDICAL"
    ):
        actions.append(
            (
                "Editar expediente",
                url_for(
                    "maintenance.edit",
                    entity="donors" if kind == "donor" else "recipients",
                    identifier=identifier,
                ),
            )
        )
    return detail(
        row["folio"],
        "donantes" if kind == "donor" else "receptores",
        row,
        actions,
        sections=[("Evaluaciones humanas", row.get("reviews", []))]
        if kind == "donor"
        else [],
        note="La información registrada requiere evaluación humana autorizada.",
    )


@regional.route("/donantes/evaluacion/<uuid:identifier>", methods=["GET", "POST"])
def donor_review(identifier):
    row = call("donantes", "/api/v1/donors/" + str(identifier))
    return submit(
        "donantes",
        "/api/v1/donors/" + str(identifier) + "/reviews",
        [
            field(
                "decision",
                "Dictamen",
                "select",
                [("ELIGIBLE", "Elegible"), ("DEFERRED", "Diferido")],
            ),
            field("version", "Versión", "hidden", default=row["version"]),
        ]
        + confirmations(),
        title="Evaluación de " + row["folio"],
        active="donantes",
        back=url_for("regional.person_detail", kind="donor", identifier=identifier),
    )


@regional.get("/donaciones")
def donations():
    return table(
        "Donaciones y procesamiento",
        "donaciones",
        "donantes",
        "/api/v1/donations",
        [
            ("reference", "Referencia"),
            ("kind", "Recurso"),
            ("component", "Componente"),
            ("blood_group", "ABO / Rh"),
            ("collected_at", "Recolección"),
            ("status", "Estado"),
        ],
        links=lambda row: url_for("regional.donation_detail", identifier=row["id"]),
        new=url_for("regional.donation_new")
        if g.principal.role_code == "MEDICAL"
        else None,
    )


@regional.route("/donaciones/nueva", methods=["GET", "POST"])
def donation_new():
    return submit(
        "donantes",
        "/api/v1/donations",
        [
            selection(
                "donor_id",
                "Donante con dictamen elegible",
                "eligible-donors",
                default=request.args.get("donor_id", ""),
            ),
            field(
                "kind",
                "Tipo de donación",
                "select",
                [("BLOOD", "Sangre"), ("ORGAN", "Órgano")],
            ),
            field("component", "Componente", "select", COMPONENTS),
            field(
                "collected_at", "Fecha de recolección", "datetime-local", default=soon()
            ),
        ]
        + confirmations(),
        title="Registrar donación",
        active="donaciones",
        back=url_for("regional.donations"),
        success=lambda row: url_for("regional.donation_detail", identifier=row["id"]),
    )


@regional.get("/donaciones/<uuid:identifier>")
def donation_detail(identifier):
    row = call("donantes", "/api/v1/donations/" + str(identifier))
    return detail(
        "Donación " + str(identifier)[:8].upper(),
        "donaciones",
        row,
        (
            [
                (
                    "Documentar procesamiento",
                    url_for("regional.donation_step", identifier=identifier),
                )
            ]
            + (
                [
                    (
                        "Editar recolección",
                        url_for(
                            "maintenance.edit",
                            entity="donations",
                            identifier=identifier,
                        ),
                    )
                ]
                if g.principal.role_code == "MEDICAL"
                else []
            )
        )
        if row["status"] == "COLLECTED"
        else [],
        sections=[("Procesamiento", row["steps"])],
    )


@regional.route("/donaciones/<uuid:identifier>/procesar", methods=["GET", "POST"])
def donation_step(identifier):
    row = call("donantes", "/api/v1/donations/" + str(identifier))
    return submit(
        "donantes",
        "/api/v1/donations/" + str(identifier) + "/steps",
        [
            field(
                "state",
                "Resultado",
                "select",
                [("PROCESSED", "Procesado"), ("REJECTED", "Rechazado")],
            ),
            field("version", "Versión", "hidden", default=row["version"]),
        ]
        + confirmations(),
        title="Documentar procesamiento",
        active="donaciones",
        back=url_for("regional.donation_detail", identifier=identifier),
    )


@regional.get("/campanas")
def campaigns():
    return table(
        "Campañas de donación",
        "campanas",
        "donantes",
        "/api/v1/campaigns",
        [
            ("title", "Campaña"),
            ("starts_at", "Inicio"),
            ("ends_at", "Fin"),
            ("capacity", "Cupo"),
            ("status", "Estado"),
        ],
        new=url_for("regional.campaign_new")
        if g.principal.role_code == "OPERATOR"
        else None,
        links=(
            lambda r: url_for(
                "maintenance.edit", entity="campaigns", identifier=r["id"]
            )
        )
        if g.principal.role_code == "OPERATOR"
        else None,
    )


@regional.route("/campanas/nueva", methods=["GET", "POST"])
def campaign_new():
    return submit(
        "donantes",
        "/api/v1/campaigns",
        [
            field("title", "Nombre de la campaña"),
            field("starts_at", "Inicio", "datetime-local", default=soon()),
            field("ends_at", "Fin", "datetime-local", default=soon(48)),
            field("capacity", "Cupo de citas", "number", default=25),
        ],
        title="Registrar campaña",
        active="campanas",
        back=url_for("regional.campaigns"),
    )


@regional.get("/citas")
def appointments():
    return table(
        "Citas de donación",
        "citas",
        "donantes",
        "/api/v1/appointments",
        [("reference", "Cita"), ("status", "Estado"), ("created_at", "Registro")],
        new=url_for("regional.appointment_new"),
        links=lambda row: (
            url_for("regional.appointment_cancel", identifier=row["id"])
            if row["status"] == "BOOKED"
            else None
        ),
    )


@regional.route("/citas/nueva", methods=["GET", "POST"])
def appointment_new():
    return submit(
        "donantes",
        "/api/v1/appointments",
        [
            selection("donor_id", "Donante", "donors"),
            selection("campaign_id", "Campaña", "campaigns"),
        ],
        title="Agendar cita",
        active="citas",
        back=url_for("regional.appointments"),
    )


@regional.route("/citas/<uuid:identifier>/cancelar", methods=["GET", "POST"])
def appointment_cancel(identifier):
    return submit(
        "donantes",
        "/api/v1/appointments/" + str(identifier) + "/cancel",
        [],
        title="Cancelar cita",
        active="citas",
        back=url_for("regional.appointments"),
    )
