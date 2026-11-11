"""Conservación y componentes; Inventario conserva todas las decisiones de negocio."""

import base64
from .common import (
    BusinessError,
    call,
    choices,
    confirmations,
    detail,
    field,
    g,
    inventory,
    regional,
    render_template,
    request,
    rows,
    soon,
    submit,
    table,
    url_for,
)


def permit(*roles):
    if g.principal.role_code not in roles:
        raise BusinessError("Tu perfil no tiene facultades para esta operación.", 403)


@regional.get("/conservacion")
def conservation():
    permit("OPERATOR", "MEDICAL")
    return render_template(
        "integration/workspace.html",
        title="Conservación",
        active="inventory",
        note="Los límites térmicos provienen de perfiles documentados. Los perfiles académicos se identifican como sintéticos.",
        links=[
            ("Equipos y calibración", url_for("regional.cold_equipment")),
            ("Perfiles térmicos versionados", url_for("regional.cold_profiles")),
            ("Cuarentena", url_for("inventory.index", status="QUARANTINE")),
            ("Próximos a vencer", url_for("inventory.index", expiry="soon")),
            ("Vencidos", url_for("inventory.index", expiry="expired")),
        ],
    )


@regional.get("/conservacion/equipos")
def cold_equipment():
    return table(
        "Equipos de conservación",
        "inventory",
        "inventario",
        "/api/v1/cold/equipment",
        [
            ("label", "Equipo"),
            ("location", "Ubicación"),
            ("calibration_reference", "Calibración"),
            ("active", "Activo"),
        ],
        filters=("q", "active"),
        new=url_for("regional.cold_equipment_new")
        if g.principal.role_code == "OPERATOR"
        else None,
    )


@regional.route("/conservacion/equipos/nuevo", methods=["GET", "POST"])
def cold_equipment_new():
    permit("OPERATOR")
    return submit(
        "inventario",
        "/api/v1/cold/equipment",
        [
            field("label", "Nombre del equipo"),
            field("location", "Ubicación"),
            field("calibration_reference", "Referencia de calibración", required=False),
        ],
        title="Registrar equipo",
        active="inventory",
        back=url_for("regional.cold_equipment"),
    )


@regional.get("/conservacion/perfiles")
def cold_profiles():
    return table(
        "Perfiles térmicos",
        "inventory",
        "inventario",
        "/api/v1/cold/profiles",
        [
            ("component", "Producto"),
            ("minimum_c", "Mínimo °C"),
            ("maximum_c", "Máximo °C"),
            ("max_gap_seconds", "Intervalo máximo (s)"),
            ("source", "Fuente"),
            ("synthetic", "Sintético"),
            ("version", "Versión"),
        ],
        filters=("q", "component"),
        links=lambda r: url_for("regional.cold_profile_detail", identifier=r["id"]),
        new=url_for("regional.cold_profile_new")
        if g.principal.role_code == "MEDICAL"
        else None,
    )


@regional.get("/conservacion/perfiles/<uuid:identifier>")
def cold_profile_detail(identifier):
    row = call("inventario", f"/api/v1/cold/profiles/{identifier}")
    return detail(
        "Perfil térmico",
        "inventory",
        row,
        [
            (
                "Registrar nueva versión",
                url_for("regional.cold_profile_new", supersedes=identifier),
            )
        ]
        if g.principal.role_code == "MEDICAL"
        else [],
        note="Perfil sintético para pruebas académicas. No constituye autorización clínica.",
    )


@regional.route("/conservacion/perfiles/nuevo", methods=["GET", "POST"])
def cold_profile_new():
    permit("MEDICAL")
    previous = request.values.get("supersedes")
    old = call("inventario", "/api/v1/cold/profiles/" + previous) if previous else {}
    return submit(
        "inventario",
        "/api/v1/cold/profiles",
        [
            field(
                "kind",
                "Tipo",
                "select",
                [("BLOOD", "Sangre"), ("ORGAN", "Órgano")],
                default=old.get("kind", ""),
            ),
            field("component", "Producto", default=old.get("component", "")),
            field(
                "minimum_c",
                "Temperatura mínima °C",
                "decimal",
                default=old.get("minimum_c", ""),
            ),
            field(
                "maximum_c",
                "Temperatura máxima °C",
                "decimal",
                default=old.get("maximum_c", ""),
            ),
            field(
                "max_gap_seconds",
                "Intervalo máximo sin lectura (segundos)",
                "number",
                default=old.get("max_gap_seconds", ""),
            ),
            field("source", "Fuente y justificación de parámetros sintéticos"),
            field("effective_at", "Fecha efectiva", "datetime-local", default=soon(-1)),
            field("version", "Versión", "hidden", default=old.get("version", 0) + 1),
            field(
                "supersedes",
                "Sustituye",
                "hidden",
                default=previous or "",
                required=False,
            ),
        ],
        transform=lambda d: dict(d, synthetic=True),
        title="Registrar perfil térmico sintético",
        active="inventory",
        back=url_for("regional.cold_profiles"),
        note="No se proponen temperaturas clínicas. Registra únicamente parámetros sintéticos documentados.",
    )


@inventory.get("/inventario/<uuid:identifier>/conservacion")
def resource_conservation(identifier):
    permit("OPERATOR", "MEDICAL")
    unit = call("inventario", f"/api/v1/resources/{identifier}")
    try:
        control = call("inventario", f"/api/v1/resources/{identifier}/controls")
    except BusinessError as exc:
        if exc.status != 404:
            raise
        control = None
    readings = rows("inventario", f"/api/v1/resources/{identifier}/cold-readings")
    actions = (
        [
            (
                "Registrar lectura",
                url_for("inventory.cold_reading_new", identifier=identifier),
            )
        ]
        if g.principal.role_code == "OPERATOR"
        else [
            (
                "Configurar controles",
                url_for("inventory.controls_new", identifier=identifier),
            )
        ]
    )
    if control and control["blocked"] and g.principal.role_code == "MEDICAL":
        actions.append(
            (
                "Documentar revisión de incidencia",
                url_for("inventory.quality_review", identifier=identifier),
            )
        )
    return render_template(
        "integration/conservation.html",
        title="Conservación · " + unit["folio"],
        active="inventory",
        unit=unit,
        control=control,
        readings=readings,
        actions=actions,
    )


@inventory.route("/inventario/<uuid:identifier>/controles", methods=["GET", "POST"])
def controls_new(identifier):
    permit("MEDICAL")
    unit = call("inventario", f"/api/v1/resources/{identifier}")
    return submit(
        "inventario",
        f"/api/v1/resources/{identifier}/controls",
        [
            field("version", "Versión", "hidden", default=unit["version"]),
            field(
                "lab_profile_id",
                "Perfil de laboratorio",
                "select",
                choices(rows("compatibilidad", "/api/v1/laboratory/profiles"), "name"),
            ),
            field(
                "cold_equipment_id",
                "Equipo",
                "select",
                choices(rows("inventario", "/api/v1/cold/equipment"), "label"),
                required=False,
            ),
            field(
                "cold_profile_id",
                "Perfil térmico",
                "select",
                [
                    (
                        r["id"],
                        f"{r['component']} · {r['source']} · versión {r['version']}",
                    )
                    for r in rows("inventario", "/api/v1/cold/profiles")
                ],
                required=False,
            ),
        ]
        + confirmations(),
        title="Configurar controles de conservación",
        active="inventory",
        back=url_for("inventory.resource_conservation", identifier=identifier),
    )


@inventory.route("/inventario/<uuid:identifier>/lectura", methods=["GET", "POST"])
def cold_reading_new(identifier):
    permit("OPERATOR")
    call("inventario", f"/api/v1/resources/{identifier}")
    return submit(
        "inventario",
        f"/api/v1/resources/{identifier}/cold-readings",
        [
            field("temperature_c", "Temperatura observada °C", "decimal"),
            field(
                "captured_at", "Fecha de lectura", "datetime-local", default=soon(-1)
            ),
            field("source", "Fuente de la lectura"),
            field("calibration_reference", "Calibración", required=False),
        ],
        title="Registrar lectura térmica",
        active="inventory",
        back=url_for("inventory.resource_conservation", identifier=identifier),
    )


@inventory.route(
    "/inventario/<uuid:identifier>/revision-calidad", methods=["GET", "POST"]
)
def quality_review(identifier):
    permit("MEDICAL")
    control = call("inventario", f"/api/v1/resources/{identifier}/controls")
    return submit(
        "inventario",
        f"/api/v1/resources/{identifier}/quality-review",
        [field("version", "Versión", "hidden", default=control["version"])]
        + confirmations(),
        title="Documentar revisión de calidad",
        active="inventory",
        back=url_for("inventory.resource_conservation", identifier=identifier),
        note="La revisión no libera el recurso. Conserva el dictamen y los controles de liberación médica.",
    )


@inventory.route("/inventario/<uuid:identifier>/componentes", methods=["GET", "POST"])
def fractionate(identifier):
    permit("OPERATOR")
    unit = call("inventario", f"/api/v1/resources/{identifier}")
    fields = [field("version", "Versión", "hidden", default=unit["version"])]
    for n in range(1, 9):
        fields += [
            field(f"folio_{n}", f"Componente {n}: folio", required=n == 1),
            field(
                f"component_{n}",
                f"Componente {n}: producto",
                "select",
                [(v, v) for v in ("RBC", "PLASMA", "PLATELETS")],
                required=n == 1,
            ),
            field(
                f"expires_at_{n}",
                f"Componente {n}: caducidad documentada",
                "datetime-local",
                required=n == 1,
            ),
        ]

    def transform(data):
        children = []
        for n in range(1, 9):
            child = {
                k: data.pop(f"{k}_{n}", None)
                for k in ("folio", "component", "expires_at")
            }
            if any(child.values()):
                if not all(child.values()):
                    raise BusinessError(
                        f"Completa folio, producto y caducidad del componente {n}.", 422
                    )
                children.append(child)
        return dict(data, children=children)

    return submit(
        "inventario",
        f"/api/v1/resources/{identifier}/components",
        fields + confirmations(),
        transform=transform,
        title="Registrar fraccionamiento",
        active="inventory",
        back=url_for("inventory.lineage", identifier=identifier),
        note="Cada componente queda en cuarentena y conserva la donación de origen. El backend impide fraccionar un recurso sin origen procesado.",
    )


@inventory.get("/inventario/<uuid:identifier>/linaje")
def lineage(identifier):
    permit("OPERATOR", "MEDICAL")
    unit = call("inventario", f"/api/v1/resources/{identifier}")
    links = call("inventario", f"/api/v1/resources/{identifier}/lineage")
    children = [call("inventario", "/api/v1/resources/" + r["child_id"]) for r in links]
    return render_template(
        "integration/lineage.html",
        title="Linaje · " + unit["folio"],
        active="inventory",
        unit=unit,
        children=children,
    )


@inventory.get("/inventario/<uuid:identifier>/etiqueta")
def label(identifier):
    permit("OPERATOR", "MEDICAL")
    from reportlab.graphics.barcode import createBarcodeDrawing

    unit = call("inventario", f"/api/v1/resources/{identifier}")
    drawing = createBarcodeDrawing(
        "Code128", value=str(identifier), barHeight=45, humanReadable=False
    )
    barcode = base64.b64encode(drawing.asString("svg").encode("utf-8")).decode()
    return render_template(
        "integration/label.html",
        title="Etiqueta · " + unit["folio"],
        active="inventory",
        unit=unit,
        barcode=barcode,
    )
