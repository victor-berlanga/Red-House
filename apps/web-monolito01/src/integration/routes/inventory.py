from ..selectors import selection

"""Rutas web: inventory. Las reglas residen en las API propietarias."""
from .common import (
    location_field,
    BusinessError,
    COMPONENTS,
    GROUPS,
    call,
    confirmations,
    detail,
    field,
    g,
    inventory,
    organs,
    request,
    require,
    rows,
    submit,
    table,
    url_for,
)


@inventory.get("/disponibilidad")
def availability():
    require(g.principal, "inventory.read")
    return table(
        "Disponibilidad regional",
        "disponibilidad",
        "inventario",
        "/api/v1/availability",
        [
            ("reference", "Referencia"),
            ("tenant_id", "Institución"),
            ("kind", "Recurso"),
            ("component", "Componente"),
            ("blood_group", "ABO / Rh"),
            ("expires_at", "Caducidad capturada"),
        ],
        note="Consulta orientativa de recursos disponibles, con caché breve. La evaluación y la reserva verifican nuevamente los datos actuales y requieren revisión humana.",
    )


@inventory.get("/inventario", endpoint="index")
def inventory_index():
    return stock("BLOOD")


@organs.get("/organos", endpoint="index")
def organs_index():
    return stock("ORGAN")


def stock(kind):
    return table(
        "Inventario sanguíneo" if kind == "BLOOD" else "Órganos y HLA",
        "inventory" if kind == "BLOOD" else "organos",
        "inventario",
        "/api/v1/resources",
        [
            ("folio", "Folio"),
            ("component", "Componente"),
            ("blood_group", "ABO / Rh"),
            ("current_institution_id", "Institución"),
            ("expires_at", "Caducidad"),
            ("status", "Estado"),
        ],
        params={"kind": kind},
        filters=("q", "status"),
        links=lambda row: url_for("inventory.detail", identifier=row["id"]),
        new=url_for("inventory.new", kind=kind)
        if g.principal.role_code == "OPERATOR"
        else None,
        note="Cada órgano conserva un flujo separado. HLA se documenta en el expediente; su interpretación corresponde al especialista."
        if kind == "ORGAN"
        else None,
    )


@inventory.route("/inventario/nuevo", methods=["GET", "POST"], endpoint="new")
def resource_new():
    kind = request.args.get("kind", "BLOOD")
    if kind not in ("BLOOD", "ORGAN"):
        raise BusinessError("Tipo de recurso inválido.", 422)
    return submit(
        "inventario",
        "/api/v1/resources",
        [
            location_field(),
            field(
                "collected_at", "Fecha de recolección", "datetime-local", required=False
            ),
            field("folio", "Folio de trazabilidad"),
            field("kind", "Tipo de recurso", "hidden", default=kind),
            field(
                "component",
                "Componente",
                "select",
                COMPONENTS[:1] if kind == "BLOOD" else COMPONENTS[1:],
            ),
            field("blood_group", "ABO / Rh", "select", [(s, s) for s in GROUPS]),
            field("expires_at", "Límite de conservación capturado", "datetime-local"),
            selection(
                "donation_id",
                "Donación local procesada",
                "donations-blood" if kind == "BLOOD" else "donations-organ",
                required=False,
            ),
        ],
        title="Registrar unidad" if kind == "BLOOD" else "Registrar órgano",
        active="inventory" if kind == "BLOOD" else "organos",
        back=url_for("inventory.index" if kind == "BLOOD" else "organs.index"),
        success=lambda row: url_for("inventory.detail", identifier=row["id"]),
        note="El recurso ingresa en cuarentena. La fecha debe provenir de una fuente autorizada; el sistema no calcula un límite clínico.",
    )


@inventory.get("/inventario/<uuid:identifier>", endpoint="detail")
def resource_detail(identifier):
    row = call("inventario", "/api/v1/resources/" + str(identifier))
    actions = []
    if g.principal.role_code == "OPERATOR":
        if row["status"] == "QUARANTINE":
            actions.append(
                (
                    "Editar registro",
                    url_for(
                        "maintenance.edit", entity="resources", identifier=identifier
                    ),
                )
            )
        if row["status"] in ("QUARANTINE", "AVAILABLE"):
            actions.append(
                (
                    "Retirar recurso",
                    url_for("maintenance.withdraw", identifier=identifier),
                )
            )
    if row["status"] == "QUARANTINE" and g.principal.role_code == "MEDICAL":
        actions.append(
            ("Liberación médica", url_for("inventory.release", identifier=identifier))
        )
    return detail(
        row["folio"],
        "inventory" if row["kind"] == "BLOOD" else "organos",
        row,
        actions,
        sections=[
            ("Movimientos", row.get("movements", [])),
            ("Dictámenes", row.get("reviews", [])),
        ],
    )


@inventory.route("/inventario/<uuid:identifier>/liberar", methods=["GET", "POST"])
def release(identifier):
    row = call("inventario", "/api/v1/resources/" + str(identifier))
    return submit(
        "inventario",
        "/api/v1/resources/" + str(identifier) + "/release",
        [field("version", "Versión", "hidden", default=row["version"])]
        + confirmations(),
        title="Liberar " + row["folio"],
        active="inventory",
        back=url_for("inventory.detail", identifier=identifier),
    )
