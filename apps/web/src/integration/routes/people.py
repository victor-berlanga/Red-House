from ..selectors import selection
from ..appointments import enrich_appointments

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
    edit_action,
    field,
    find_record,
    g,
    regional,
    request,
    rows,
    soon,
    submit,
    table,
    url_for,
)


def withdrawal_action(row):
    if g.principal.role_code != "MEDICAL" or row["status"] == "INACTIVE":
        return []
    return [
        (
            "Retirar donante",
            url_for("regional.donor_withdraw", identifier=row["id"]),
            "trash",
        )
    ]


@regional.get("/donantes/<kind>")
def people(kind):
    if kind not in ("donor", "recipient"):
        raise BusinessError("Vista no disponible.", 404)
    service, path = (
        ("donantes", "donors") if kind == "donor" else ("receptores", "recipients")
    )
    return table(
        ("Mi expediente" if g.principal.role_code == "DONOR" else "Donantes")
        if kind == "donor"
        else "Receptores",
        "donantes" if kind == "donor" else "receptores",
        service,
        "/api/v1/" + path,
        [
            ("folio", "Folio"),
            *(
                [("display_name", "Nombre"), ("blood_group", "ABO / Rh")]
                if kind == "donor" or g.principal.role_code == "MEDICAL"
                else []
            ),
            *([("kind", "Recurso")] if kind == "recipient" else []),
            ("status", "Estado"),
        ],
        filters=("q", "status") if kind == "donor" else ("q", "kind"),
        links=lambda row: (
            url_for("regional.person_detail", kind=kind, identifier=row["id"])
            if kind == "donor" or g.principal.role_code == "MEDICAL"
            else None
        ),
        new=url_for("regional.person_new", kind=kind)
        if kind == "donor" or g.principal.role_code == "MEDICAL"
        else None,
        actions=(lambda row: edit_action("donors", row) + withdrawal_action(row))
        if kind == "donor"
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
    if (
        kind == "donor"
        and g.principal.role_code == "MEDICAL"
        and row["status"] != "INACTIVE"
    ):
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
    actions.extend(
        ("Editar expediente", link)
        for _, link, _ in edit_action(
            "donors" if kind == "donor" else "recipients", row
        )
    )
    if kind == "donor":
        actions.extend(withdrawal_action(row))
    return detail(
        row["folio"],
        "donantes" if kind == "donor" else "receptores",
        row,
        actions,
        sections=[("Evaluaciones humanas", row.get("reviews", []))]
        if kind == "donor"
        else [],
        note=(
            "Este donante ya no está activo. Puedes consultar sus antecedentes."
            if kind == "donor" and row["status"] == "INACTIVE"
            else "La información registrada requiere evaluación humana autorizada."
        ),
    )


@regional.route("/donantes/donor/<uuid:identifier>/baja", methods=["GET", "POST"])
def donor_withdraw(identifier):
    if g.principal.role_code != "MEDICAL":
        raise BusinessError("Solo el personal médico puede retirar donantes.", 403)
    version = 0
    subject = ""
    if request.method == "GET":
        row = call("donantes", "/api/v1/donors/" + str(identifier))
        if row["status"] == "INACTIVE":
            raise BusinessError("Este donante ya no está activo.", 409)
        version = row["version"]
        subject = f"{row['display_name']} · Folio: {row['folio']}. "
    return submit(
        "donantes",
        "/api/v1/donors/" + str(identifier) + "/withdraw",
        [
            field("version", "Versión", "hidden", default=version),
            field("reason", "Motivo", "textarea"),
            field(
                "human_confirmation",
                "Confirmo que quiero retirar a este donante",
                "checkbox",
            ),
        ],
        title="Retirar donante",
        active="donantes",
        back=url_for("regional.people", kind="donor"),
        note=(
            subject + "Dejará de aparecer en la lista de donantes. "
            "Sus citas pendientes se cancelarán."
        ),
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
        links=lambda row: url_for("regional.campaign_detail", identifier=row["id"]),
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
        "Mis inscripciones"
        if g.principal.role_code == "DONOR"
        else "Inscripciones a campañas",
        "citas",
        "donantes",
        "/api/v1/appointments",
        [
            ("campaign_title", "Campaña"),
            *(
                [("donor_name", "Donante")]
                if g.principal.role_code == "OPERATOR"
                else []
            ),
            ("campaign_start", "Inicio de campaña"),
            ("campaign_end", "Fin de campaña"),
            ("status", "Estado"),
        ],
        prepare=enrich_appointments,
        links=lambda row: url_for("regional.appointment_detail", identifier=row["id"]),
        note="La inscripción reserva un cupo en la campaña. Confirma con tu institución el lugar y la hora de atención.",
        new=url_for("regional.appointment_new"),
        actions=lambda row: (
            [
                (
                    "Cancelar inscripción",
                    url_for("regional.appointment_cancel", identifier=row["id"]),
                    "cancel",
                )
            ]
            if row["status"] == "BOOKED"
            else []
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
        title="Reservar cupo en campaña",
        active="citas",
        back=url_for("regional.appointments"),
        note="Reserva un cupo; la institución confirmará el lugar y la hora de atención.",
    )


@regional.route("/citas/<uuid:identifier>/cancelar", methods=["GET", "POST"])
def appointment_cancel(identifier):
    row = find_record("donantes", "/api/v1/appointments", identifier)
    enrich_appointments([row])
    return submit(
        "donantes",
        "/api/v1/appointments/" + str(identifier) + "/cancel",
        [],
        title="Cancelar inscripción",
        prompt=(
            "¿Cancelar tu inscripción a «"
            if g.principal.role_code == "DONOR"
            else "¿Cancelar la inscripción de " + row["donor_name"] + " a «"
        )
        + row["campaign_title"]
        + "»? Se liberará el cupo reservado.",
        active="citas",
        back=url_for("regional.appointments"),
    )


@regional.get("/citas/<uuid:identifier>")
def appointment_detail(identifier):
    row = find_record("donantes", "/api/v1/appointments", identifier)
    enrich_appointments([row])
    actions = [
        (
            "Consultar campaña",
            url_for("regional.campaign_detail", identifier=row["campaign_id"]),
        )
    ]
    if row["status"] == "BOOKED":
        actions.append(
            (
                "Cancelar inscripción",
                url_for("regional.appointment_cancel", identifier=identifier),
            )
        )
    return detail(
        "Inscripción a campaña",
        "citas",
        row,
        actions,
        note="El periodo corresponde a la campaña. Confirma el lugar y la hora de atención con tu institución.",
    )


@regional.get("/campanas/<uuid:identifier>")
def campaign_detail(identifier):
    row = call("donantes", "/api/v1/campaigns/" + str(identifier))
    actions = (
        [
            (
                "Editar campaña",
                url_for("maintenance.edit", entity="campaigns", identifier=identifier),
            )
        ]
        if g.principal.role_code == "OPERATOR"
        else []
    )
    return detail(row["title"], "campanas", row, actions)
