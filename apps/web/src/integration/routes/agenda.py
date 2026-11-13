"""Consentimiento y horarios: formularios sobre el propietario Donantes."""

from .common import (
    call,
    confirmations,
    field,
    g,
    regional,
    soon,
    submit,
    table,
    url_for,
    rows,
    display,
)


def schedule_options(campaign_id):
    sites = {
        r["id"]: r["name"]
        for r in rows("identidad_acceso", "/api/v1/appointment-sites")
    }
    return [
        (
            r["id"],
            f"{sites.get(r['site_id'], 'Sede pendiente')} · {display(r['starts_at'])} · {r['available']} lugares disponibles",
        )
        for r in rows(
            "donantes", "/api/v1/campaign-slots", campaign_id=campaign_id, active="true"
        )
    ]


@regional.get("/donantes/donor/<uuid:identifier>/consentimientos")
def consents(identifier):
    return table(
        "Historial de consentimiento",
        "donantes",
        "donantes",
        f"/api/v1/donors/{identifier}/consents",
        [
            ("version", "Versión"),
            ("policy_version", "Política"),
            ("granted", "Otorgado"),
            ("effective_at", "Fecha efectiva"),
        ],
        new=url_for("regional.consent_new", identifier=identifier),
    )


@regional.route(
    "/donantes/donor/<uuid:identifier>/consentimientos/nuevo", methods=["GET", "POST"]
)
def consent_new(identifier):
    donor = call("donantes", f"/api/v1/donors/{identifier}")
    return submit(
        "donantes",
        f"/api/v1/donors/{identifier}/consents",
        [
            field("version", "Versión", "hidden", default=donor["version"]),
            field("policy_version", "Versión de la política informada"),
            field("reference", "Referencia del consentimiento"),
            field("effective_at", "Fecha efectiva", "datetime-local", default=soon(-1)),
            field("granted", "Consentimiento otorgado", "checkbox", required=False),
        ]
        + confirmations(),
        transform=lambda data: dict(data, granted=data.get("granted", False)),
        title="Registrar consentimiento",
        active="donantes",
        back=url_for("regional.consents", identifier=identifier),
        note="Registra la decisión informada. Retirar consentimiento impide nuevas operaciones; no borra el historial.",
    )


@regional.get("/campanas/<uuid:identifier>/horarios")
def slots(identifier):
    sites = {
        r["id"]: r["name"]
        for r in rows("identidad_acceso", "/api/v1/appointment-sites")
    }

    def prepare(items):
        for item in items:
            item["site_name"] = sites.get(item["site_id"], "Sede pendiente")

    return table(
        "Horarios por sede",
        "campanas",
        "donantes",
        "/api/v1/campaign-slots",
        [
            ("site_name", "Sede"),
            ("starts_at", "Inicio"),
            ("ends_at", "Fin"),
            ("capacity", "Cupo"),
            ("occupied", "Ocupación"),
            ("available", "Disponibles"),
            ("attended", "Asistencias"),
        ],
        prepare=prepare,
        params={"campaign_id": str(identifier)},
        actions=lambda row: [
            (
                "Reservar horario",
                url_for(
                    "regional.appointment_new",
                    campaign_id=identifier,
                    slot_id=row["id"],
                ),
                "",
            )
        ],
        new=url_for("regional.slot_new", identifier=identifier)
        if g.principal.role_code == "OPERATOR"
        else None,
    )


@regional.route("/campanas/<uuid:identifier>/horarios/nuevo", methods=["GET", "POST"])
def slot_new(identifier):
    call("donantes", f"/api/v1/campaigns/{identifier}")
    sites = rows("identidad_acceso", "/api/v1/catalogues/sites")
    return submit(
        "donantes",
        "/api/v1/campaign-slots",
        [
            field("campaign_id", "Campaña", "hidden", default=str(identifier)),
            field("site_id", "Sede", "select", [(r["id"], r["name"]) for r in sites]),
            field("starts_at", "Inicio", "datetime-local", default=soon(24)),
            field("ends_at", "Fin", "datetime-local", default=soon(25)),
            field("capacity", "Cupo", "number"),
        ],
        title="Crear horario",
        active="campanas",
        back=url_for("regional.slots", identifier=identifier),
    )


@regional.route("/citas/<uuid:identifier>/horario", methods=["GET", "POST"])
def appointment_schedule(identifier):
    row = call("donantes", f"/api/v1/appointments/{identifier}/schedule")
    slot = call("donantes", "/api/v1/campaign-slots/" + row["slot_id"])
    actions = [
        ("CONFIRM", "Confirmar"),
        ("RESCHEDULE", "Reprogramar"),
        ("CANCEL", "Cancelar"),
    ]
    if g.principal.role_code == "OPERATOR":
        actions.append(("ATTEND", "Registrar asistencia"))
    return submit(
        "donantes",
        f"/api/v1/appointments/{identifier}/commands",
        [
            field("version", "Versión", "hidden", default=row["version"]),
            field("action", "Operación", "select", actions),
            field(
                "slot_id",
                "Nuevo horario (solo al reprogramar)",
                "select",
                schedule_options(slot["campaign_id"]),
                required=False,
            ),
        ]
        + confirmations(),
        title="Gestionar horario de cita",
        active="citas",
        back=url_for("regional.appointment_detail", identifier=identifier),
    )
