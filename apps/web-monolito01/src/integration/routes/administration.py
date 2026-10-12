"""Rutas web: administration. Las reglas residen en las API propietarias."""

from .common import (
    BusinessError,
    call,
    detail,
    COMPONENTS,
    GROUPS,
    ROLES,
    admin,
    field,
    g,
    render_template,
    request,
    require,
    submit,
    table,
    url_for,
)


@admin.get("/administracion/<entity>", endpoint="index")
def admin_index(entity):
    require(g.principal, "administration")
    if entity == "institutions":
        return table(
            "Instituciones",
            "institutions",
            "identidad_acceso",
            "/api/v1/institutions",
            [("name", "Institución"), ("active", "Participación activa")],
            new=url_for("admin.new", entity=entity),
            links=lambda r: url_for("admin.institution_detail", identifier=r["id"]),
            actions=lambda r: (
                [
                    (
                        "Editar institución",
                        url_for("maintenance.institution_edit", identifier=r["id"]),
                        "pencil",
                    )
                ]
                if r["id"] == str(g.principal.institution_id)
                else []
            ),
        )
    if entity == "users":
        return table(
            "Usuarios",
            "users",
            "identidad_acceso",
            "/api/v1/users",
            [
                ("username", "Cuenta"),
                ("role", "Perfil"),
                ("active", "Activo"),
            ],
            filters=("q", "role"),
            new=url_for("admin.new", entity=entity),
            actions=lambda row: (
                [
                    (
                        "Desactivar" if row["active"] else "Activar",
                        url_for(
                            "admin.user_state",
                            identifier=row["id"],
                            version=row["version"],
                            active="false" if row["active"] else "true",
                        ),
                        "state",
                    )
                ]
                if row["id"] != str(g.principal.account_id)
                else []
            ),
        )
    if entity == "components":
        return render_template(
            "integration/catalogue.html",
            title="Catálogos",
            active="components",
            components=COMPONENTS,
            groups=GROUPS,
        )
    raise BusinessError("Catálogo no disponible.", 404)


@admin.route("/administracion/<entity>/nuevo", methods=["GET", "POST"], endpoint="new")
def admin_new(entity):
    require(g.principal, "administration")
    if entity == "institutions":
        fields = [field("name", "Nombre de la institución y municipio")]
    elif entity == "users":
        fields = [
            field("username", "Cuenta institucional"),
            field("password", "Contraseña (mínimo 12 caracteres)", "password"),
            field(
                "tenant_id",
                "Institución",
                "hidden",
                default=str(g.principal.institution_id),
            ),
            field("role", "Perfil", "select", list(ROLES.items())),
        ]
    else:
        raise BusinessError("Catálogo no disponible.", 404)
    return submit(
        "identidad_acceso",
        "/api/v1/" + entity,
        fields,
        title="Registrar institución"
        if entity == "institutions"
        else "Registrar usuario",
        active=entity,
        back=url_for("admin.index", entity=entity),
        success=(
            lambda r: url_for(
                "maintenance.institution_administrator", identifier=r["id"]
            )
        )
        if entity == "institutions"
        else None,
    )


@admin.route(
    "/administracion/usuarios/<uuid:identifier>/estado", methods=["GET", "POST"]
)
def user_state(identifier):
    require(g.principal, "administration")
    return submit(
        "identidad_acceso",
        "/api/v1/users/" + str(identifier),
        [
            field(
                "active",
                "Mantener la cuenta activa",
                "checkbox",
                default=request.args.get("active") == "true",
            ),
            field(
                "version", "Versión", "number", default=request.args.get("version", 1)
            ),
        ],
        method="PATCH",
        title="Cambiar estado de la cuenta",
        active="users",
        back=url_for("admin.index", entity="users"),
        note="Desactivar revoca sus sesiones. Reactivar no recupera tokens anteriores.",
    )


@admin.get("/configuracion")
def settings():
    require(g.principal, "administration")
    return render_template(
        "integration/settings.html",
        title="Roles y parámetros",
        active="settings",
        roles=ROLES,
    )


@admin.get("/instituciones/<uuid:identifier>")
def institution_detail(identifier):
    require(g.principal, "administration")
    row = call("identidad_acceso", "/api/v1/institutions/" + str(identifier))
    actions = []
    if str(identifier) == str(g.principal.institution_id):
        actions.append(
            (
                "Editar institución",
                url_for("maintenance.institution_edit", identifier=identifier),
            )
        )
    elif row.get("created_by") == str(g.principal.account_id):
        actions.append(
            (
                "Configurar primer administrador",
                url_for("maintenance.institution_administrator", identifier=identifier),
            )
        )
    return detail(row["name"], "institutions", row, actions)
