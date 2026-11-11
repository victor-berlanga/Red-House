"""Operación administrativa por institución, sin facultades clínicas implícitas."""

from .common import (
    admin,
    regional,
    call,
    choices,
    confirmations,
    detail,
    field,
    g,
    render_template,
    rows,
    soon,
    submit,
    table,
    url_for,
    uuid4,
)
from .conservation import permit


@admin.route("/configuracion/politica", methods=["GET", "POST"])
def policy_edit():
    permit("ADMIN")
    row = call("identidad_acceso", "/api/v1/portal-policy")
    return submit(
        "identidad_acceso",
        "/api/v1/portal-policy",
        [
            field("version", "Versión", "hidden", default=row["version"]),
            field(
                "timezone",
                "Zona horaria institucional",
                "select",
                [
                    (v, v)
                    for v in (
                        "America/Monterrey",
                        "America/Mexico_City",
                        "America/Tijuana",
                        "UTC",
                    )
                ],
                default=row["timezone"],
            ),
            field(
                "tracking_interval_seconds",
                "Frecuencia esperada de ubicación (segundos)",
                "number",
                default=row["tracking_interval_seconds"],
            ),
            field(
                "tracking_stale_seconds",
                "Antigüedad para indicar retraso (segundos)",
                "number",
                default=row["tracking_stale_seconds"],
            ),
            field(
                "reference",
                "Justificación operativa",
                "textarea",
                default=row["reference"],
            ),
        ]
        + confirmations(),
        title="Actualizar política operativa",
        active="users",
        back=url_for("admin.settings"),
        note="Se conserva cada versión en la auditoría institucional. Estos parámetros no conceden autorización clínica ni cambian permisos o MFA.",
    )


@admin.route("/configuracion/institucion", methods=["GET", "POST"])
def institution_presentation_edit():
    permit("ADMIN")
    identifier = str(g.principal.institution_id)
    row = call("identidad_acceso", f"/api/v1/institutions/{identifier}/presentation")
    return submit(
        "identidad_acceso",
        f"/api/v1/institutions/{identifier}/presentation",
        [
            field("version", "Versión", "hidden", default=row["version"]),
            field(
                "published",
                "Autorizar publicación del nombre y descripción institucional",
                "checkbox",
                default=row["published"],
                required=False,
            ),
            field(
                "description",
                "Descripción pública",
                "textarea",
                default=row["description"],
                required=False,
            ),
            field(
                "latitude",
                "Latitud WGS84",
                "decimal",
                default=row["latitude"] if row["latitude"] is not None else "",
                required=False,
            ),
            field(
                "longitude",
                "Longitud WGS84",
                "decimal",
                default=row["longitude"] if row["longitude"] is not None else "",
                required=False,
            ),
            field(
                "coordinate_source",
                "Fuente de las coordenadas",
                default=row["coordinate_source"] or "",
                required=False,
            ),
            field(
                "coordinate_recorded_at",
                "Fecha de consulta de coordenadas",
                "datetime-local",
                required=False,
            ),
            field(
                "synthetic",
                "Coordenadas ficticias para pruebas",
                "checkbox",
                default=row["synthetic"],
                required=False,
            ),
        ]
        + confirmations(),
        transform=lambda d: dict(
            d, published=d.get("published", False), synthetic=d.get("synthetic", False)
        ),
        title="Actualizar presentación institucional",
        active="institutions",
        back=url_for("admin.settings"),
        note="Sin coordenadas verificadas deja ambos campos pendientes. El sitio público solo muestra nombre y descripción expresamente autorizados.",
    )


@admin.get("/administracion/dispositivos")
def devices():
    permit("ADMIN")
    return table(
        "Dispositivos de traslado",
        "users",
        "identidad_acceso",
        "/api/v1/devices",
        [
            ("label", "Dispositivo"),
            ("source", "Fuente"),
            ("active", "Activo"),
            ("expires_at", "Vigencia"),
        ],
        filters=("q",),
        new=url_for("admin.device_new"),
        links=lambda r: url_for("admin.device_detail", identifier=r["id"]),
    )


@admin.route("/administracion/dispositivos/nuevo", methods=["GET", "POST"])
def device_new():
    permit("ADMIN")
    return submit(
        "identidad_acceso",
        "/api/v1/devices",
        [
            field("id", "Dispositivo", "hidden", default=str(uuid4())),
            field(
                "user_id",
                "Transportista responsable",
                "select",
                choices(
                    rows("identidad_acceso", "/api/v1/users", role="TRANSPORT"),
                    "username",
                ),
            ),
            field(
                "source",
                "Fuente",
                "select",
                [
                    ("SIMULATOR", "Simulador identificado"),
                    ("ANDROID", "Teléfono Android"),
                    ("IOS", "Teléfono iOS (verificación de plataforma pendiente)"),
                    ("GPS_BRIDGE", "Puente GPS externo opcional"),
                ],
            ),
            field("label", "Nombre del dispositivo"),
            field(
                "expires_at",
                "Vigencia (hasta 30 días)",
                "datetime-local",
                default=soon(24),
            ),
        ],
        title="Registrar dispositivo",
        active="users",
        back=url_for("admin.devices"),
        success=lambda r: url_for("admin.device_detail", identifier=r["id"]),
    )


@admin.get("/administracion/dispositivos/<uuid:identifier>")
def device_detail(identifier):
    permit("ADMIN")
    row = call("identidad_acceso", f"/api/v1/devices/{identifier}")
    actions = (
        [
            (
                "Rotar credencial",
                url_for("admin.device_credential", identifier=identifier),
            ),
            (
                "Revocar dispositivo",
                url_for("admin.device_revoke", identifier=identifier),
            ),
        ]
        if row["active"]
        else []
    )
    return detail(
        row["label"],
        "users",
        row,
        actions,
        note="Registrar un dispositivo no lo asigna a una orden. Transporte conserva esa autorización.",
    )


@admin.route(
    "/administracion/dispositivos/<uuid:identifier>/credencial", methods=["GET", "POST"]
)
def device_credential(identifier):
    permit("ADMIN")
    row = call("identidad_acceso", f"/api/v1/devices/{identifier}")
    return submit(
        "identidad_acceso",
        f"/api/v1/devices/{identifier}/credentials",
        [field("version", "Versión", "hidden", default=row["version"])]
        + confirmations(),
        title="Rotar credencial de dispositivo",
        active="users",
        back=url_for("admin.device_detail", identifier=identifier),
        note="La anterior deja de funcionar. La nueva se muestra una vez; si se pierde la respuesta, consulta la versión y rota de nuevo.",
        result_view=lambda r: render_template(
            "integration/device_credential.html",
            title="Credencial emitida",
            active="users",
            credential=r["credential"],
            identifier=identifier,
        ),
    )


@admin.route(
    "/administracion/dispositivos/<uuid:identifier>/revocar", methods=["GET", "POST"]
)
def device_revoke(identifier):
    permit("ADMIN")
    row = call("identidad_acceso", f"/api/v1/devices/{identifier}")
    return submit(
        "identidad_acceso",
        f"/api/v1/devices/{identifier}/revoke",
        [field("version", "Versión", "hidden", default=row["version"])]
        + confirmations(),
        title="Revocar dispositivo",
        active="users",
        back=url_for("admin.device_detail", identifier=identifier),
    )


@regional.route("/campanas/<uuid:identifier>/publicacion", methods=["GET", "POST"])
def campaign_publication(identifier):
    permit("OPERATOR")
    row = call("donantes", f"/api/v1/campaigns/{identifier}/publication")
    return submit(
        "donantes",
        f"/api/v1/campaigns/{identifier}/publication",
        [
            field("version", "Versión", "hidden", default=row["version"]),
            field(
                "published",
                "Autorizar publicación",
                "checkbox",
                default=row["published"],
                required=False,
            ),
            field("venue", "Lugar público de atención", default=row["venue"]),
            field(
                "information",
                "Información pública revisada",
                "textarea",
                default=row["information"],
            ),
        ]
        + confirmations(),
        transform=lambda d: dict(d, published=d.get("published", False)),
        title="Actualizar publicación de campaña",
        active="campanas",
        back=url_for("regional.campaign_detail", identifier=identifier),
        note="Solo campañas abiertas y vigentes aparecen públicamente. No incluyas nombres de donantes, expedientes ni requisitos médicos sin revisión.",
    )
