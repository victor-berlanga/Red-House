"""Formularios administrativos y correcciones; toda decisión se valida por API."""

from datetime import datetime
from zoneinfo import ZoneInfo
from flask import Blueprint, g, request, url_for
from ..access import BusinessError, require
from ..presentation.timezones import selected_zone
from .client import call
from .presentation import edit_action
from .routes.common import (
    field,
    submit,
    table,
    detail,
    rows,
    choices,
    confirmations,
    GROUPS,
    COMPONENTS,
    person_extra,
    location_field,
)

bp = Blueprint("maintenance", __name__)
CATALOGUES = {
    "sites": "Sedes",
    "contacts": "Contactos",
    "schedules": "Horarios",
    "capacities": "Capacidades",
    "locations": "Ubicaciones",
}


def defaults(fields, row):
    for item in fields:
        value = row.get(item["name"], "")
        if value is None:
            value = ""
        if value and item["type"] == "datetime-local":
            value = (
                datetime.fromisoformat(value.replace("Z", "+00:00"))
                .astimezone(ZoneInfo(selected_zone()))
                .strftime("%Y-%m-%dT%H:%M")
            )
        item["default"] = value
    return fields


def catalogue_fields(kind):
    fields = [field("name", "Nombre")]
    if kind == "sites":
        fields += [field("municipality", "Municipio"), field("address", "Dirección")]
    elif kind == "contacts":
        fields += [field("value", "Teléfono o correo institucional")]
    else:
        sites = [
            r
            for r in rows("identidad_acceso", "/api/v1/catalogues/sites")
            if r["active"]
        ]
        fields += [field("parent_id", "Sede", "select", choices(sites, "name"))]
        if kind == "schedules":
            fields += [
                field(
                    "weekday",
                    "Día de la semana",
                    "integer-select",
                    list(
                        enumerate(
                            [
                                "Lunes",
                                "Martes",
                                "Miércoles",
                                "Jueves",
                                "Viernes",
                                "Sábado",
                                "Domingo",
                            ]
                        )
                    ),
                ),
                field("opens_at", "Apertura", "time"),
                field("closes_at", "Cierre", "time"),
            ]
        elif kind == "capacities":
            fields += [
                field("component", "Componente", "select", COMPONENTS),
                field("quantity", "Capacidad registrada", "number"),
            ]
        elif kind == "locations":
            fields += [field("description", "Descripción de la ubicación")]
    return fields


@bp.get("/catalogos/<kind>")
def catalogue_list(kind):
    require(g.principal, "administration")
    if kind not in CATALOGUES:
        raise BusinessError("Catálogo no disponible.", 404)
    return table(
        CATALOGUES[kind],
        "components",
        "identidad_acceso",
        "/api/v1/catalogues/" + kind,
        [("name", "Nombre"), ("active", "Activo")],
        filters=("q", "active"),
        new=url_for("maintenance.catalogue_new", kind=kind),
        links=lambda r: url_for(
            "maintenance.catalogue_detail", kind=kind, identifier=r["id"]
        ),
        actions=lambda r: [
            (
                "Editar",
                url_for("maintenance.catalogue_edit", kind=kind, identifier=r["id"]),
                "pencil",
            )
        ],
    )


@bp.route("/catalogos/<kind>/nuevo", methods=["GET", "POST"])
def catalogue_new(kind):
    require(g.principal, "administration")
    if kind not in CATALOGUES:
        raise BusinessError("Catálogo no disponible.", 404)
    return submit(
        "identidad_acceso",
        "/api/v1/catalogues/" + kind,
        catalogue_fields(kind),
        title="Registrar " + CATALOGUES[kind].lower(),
        active="components",
        back=url_for("maintenance.catalogue_list", kind=kind),
    )


@bp.route("/catalogos/<kind>/<uuid:identifier>/editar", methods=["GET", "POST"])
def catalogue_edit(kind, identifier):
    require(g.principal, "administration")
    if kind not in CATALOGUES:
        raise BusinessError("Catálogo no disponible.", 404)
    path = "/api/v1/catalogues/" + kind + "/" + str(identifier)
    row = call("identidad_acceso", path)
    fields = (
        defaults(catalogue_fields(kind), row)
        + [
            field("active", "Activo", "checkbox", default=row["active"]),
            field("version", "Versión", "hidden", default=row["version"]),
        ]
        + confirmations()
    )
    return submit(
        "identidad_acceso",
        path,
        fields,
        method="PATCH",
        title="Editar " + row["name"],
        active="components",
        back=url_for("maintenance.catalogue_list", kind=kind),
    )


@bp.route("/instituciones/<uuid:identifier>/responsable", methods=["GET", "POST"])
def institution_administrator(identifier):
    require(g.principal, "administration")
    row = call("identidad_acceso", "/api/v1/institutions/" + str(identifier))
    fields = [
        field("username", "Cuenta del primer administrador"),
        field("password", "Contraseña (mínimo 12 caracteres)", "password"),
    ] + confirmations()
    return submit(
        "identidad_acceso",
        "/api/v1/institutions/" + str(identifier) + "/administrator",
        fields,
        title="Completar alta de " + row["name"],
        active="institutions",
        back=url_for("admin.index", entity="institutions"),
    )


@bp.route("/instituciones/<uuid:identifier>/editar", methods=["GET", "POST"])
def institution_edit(identifier):
    require(g.principal, "administration")
    path = "/api/v1/institutions/" + str(identifier)
    row = call("identidad_acceso", path)
    if str(identifier) != str(g.principal.institution_id):
        return detail(
            row["name"],
            "institutions",
            row,
            [
                (
                    "Configurar primer administrador",
                    url_for(
                        "maintenance.institution_administrator", identifier=identifier
                    ),
                )
            ]
            if row.get("created_by") == str(g.principal.account_id)
            else [],
        )
    return submit(
        "identidad_acceso",
        path,
        [
            field("name", "Nombre", default=row["name"]),
            field("version", "Versión", "hidden", default=row["version"]),
        ]
        + confirmations(),
        method="PATCH",
        title="Editar institución",
        active="institutions",
        back=url_for("admin.index", entity="institutions"),
    )


@bp.route("/registros/<entity>/<uuid:identifier>/editar", methods=["GET", "POST"])
def edit(entity, identifier):
    owners = {
        "donors": "donantes",
        "recipients": "receptores",
        "resources": "inventario",
        "requests": "receptores",
        "donations": "donantes",
        "campaigns": "donantes",
    }
    if entity not in owners:
        raise BusinessError("Registro no disponible.", 404)
    path = "/api/v1/" + entity + "/" + str(identifier)
    allowed_roles = {
        "donors": ("OPERATOR", "MEDICAL"),
        "recipients": ("MEDICAL",),
        "resources": ("OPERATOR",),
        "requests": ("MEDICAL",),
        "donations": ("MEDICAL",),
        "campaigns": ("OPERATOR",),
    }
    if g.principal.role_code not in allowed_roles[entity]:
        raise BusinessError("Tu perfil no permite editar este registro.", 403)
    row = call(owners[entity], path)
    if not edit_action(entity, row):
        raise BusinessError(
            "El estado o historial de este registro ya no permite corregirlo.", 409
        )
    if entity in ("donors", "recipients"):
        fields = [
            field("folio", "Folio"),
            field("display_name", "Nombre completo"),
            field("blood_group", "ABO / Rh", "select", [(s, s) for s in GROUPS]),
        ]
        if entity == "donors":
            fields += [field("consent", "Consentimiento registrado", "checkbox")]
        else:
            fields += [
                field(
                    "kind",
                    "Recurso",
                    "select",
                    [("BLOOD", "Sangre"), ("ORGAN", "Órgano")],
                ),
                field("organ_type", "Órgano", "select", COMPONENTS[1:], required=False),
                field("studies", "Estudios documentales", "textarea"),
            ]
        fields += person_extra("donor" if entity == "donors" else "recipient")
        active = "donantes" if entity == "donors" else "receptores"
        back = url_for(
            "regional.person_detail",
            kind="donor" if entity == "donors" else "recipient",
            identifier=identifier,
        )
    elif entity == "resources":
        fields = [
            location_field(),
            field(
                "collected_at", "Fecha de recolección", "datetime-local", required=False
            ),
            field("folio", "Folio"),
            field("kind", "Recurso", "hidden"),
            field("component", "Componente", "select", COMPONENTS),
            field("blood_group", "ABO / Rh", "select", [(s, s) for s in GROUPS]),
            field("expires_at", "Caducidad capturada", "datetime-local"),
            field("donation_id", "Procedencia", "hidden", required=False),
        ]
        active = "inventory"
        back = url_for("inventory.detail", identifier=identifier)
    elif entity == "requests":
        fields = [
            field("component", "Componente", "select", COMPONENTS),
            field("quantity", "Cantidad", "number"),
            field("urgency", "Urgencia capturada (1–3)", "number"),
        ]
        active = "solicitudes"
        back = url_for("regional.request_detail", identifier=identifier)
    elif entity == "donations":
        fields = [field("collected_at", "Recolección", "datetime-local")]
        active = "donaciones"
        back = url_for("regional.donation_detail", identifier=identifier)
    else:
        fields = [
            field("title", "Título"),
            field("starts_at", "Inicio", "datetime-local"),
            field("ends_at", "Fin", "datetime-local"),
            field("capacity", "Cupo", "number"),
        ]
        active = "campanas"
        back = url_for("regional.campaigns")
    fields = (
        defaults(fields, row)
        + [field("version", "Versión", "hidden", default=row["version"])]
        + confirmations()
    )
    return submit(
        owners[entity],
        path,
        fields,
        method="PATCH",
        title="Editar registro",
        active=active,
        back=back,
        note=None,
    )


@bp.route("/inventario/<uuid:identifier>/retirar", methods=["GET", "POST"])
def withdraw(identifier):
    row = call("inventario", "/api/v1/resources/" + str(identifier))
    return submit(
        "inventario",
        "/api/v1/resources/" + str(identifier) + "/withdraw",
        [field("version", "Versión", "hidden", default=row["version"])]
        + confirmations(),
        title="Retirar " + row["folio"],
        active="inventory",
        back=url_for("inventory.detail", identifier=identifier),
    )


@bp.get("/catalogos/<kind>/<uuid:identifier>")
def catalogue_detail(kind, identifier):
    require(g.principal, "administration")
    if kind not in CATALOGUES:
        raise BusinessError("Catálogo no disponible.", 404)
    row = call("identidad_acceso", "/api/v1/catalogues/" + kind + "/" + str(identifier))
    return detail(
        row["name"],
        "components",
        row,
        [
            (
                "Editar",
                url_for("maintenance.catalogue_edit", kind=kind, identifier=identifier),
            )
        ],
    )
