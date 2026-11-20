"""Sección activa de la barra lateral, derivada de la petición.

Antes cada ruta pasaba ``active="..."`` a mano y varias eligieron un id que no
era el de su entrada de ``NAV`` (por ejemplo Apoyo a decisiones resaltaba
«Rutas»). Ahora el servidor calcula ``nav_active`` para cada página con esta
precedencia, y ``base.html`` solo lee ese valor:

1. ``g.nav_section``: lo fija ``mark()`` cuando la sección depende del dato
   (una unidad de inventario es sangre u órgano).
2. ``ENDPOINT_SECTIONS``: mapa explícito endpoint -> id de ``NAV``. Un valor
   ``None`` significa «ninguna entrada» a propósito. Una prueba exige que todo
   endpoint del portal esté aquí.
3. ``PATH_PREFIXES``: respaldo por prefijo de ruta (el más largo gana), para
   páginas de error 404 o rutas nuevas aún sin registrar.

``active=`` en ``render_template``/``table()``/``submit()`` sigue existiendo,
pero solo como clave de listado (``LISTS``, ``return_to``, filtros); ya no
decide el resaltado. La URL determina la sección, así que enlace directo,
recarga y Atrás/Adelante coinciden (las respuestas llevan ``no-store`` y ningún
script modifica la barra).
"""

from flask import g, request


def _people(args):
    return "receptores" if args.get("kind") == "recipient" else "donantes"


def _admin_entity(args):
    return (
        args.get("entity") if args.get("entity") in ("institutions", "users") else None
    )


_EDIT_ENTITIES = {
    "donors": "donantes",
    "recipients": "receptores",
    "resources": "inventory",
    "requests": "solicitudes",
    "donations": "donaciones",
    "campaigns": "campanas",
}


def _edit_record(args):
    return _EDIT_ENTITIES.get(args.get("entity"))


def _catalogue(args):
    return "components"


ENDPOINT_SECTIONS = {
    # GENERAL
    "portal.dashboard": "dashboard",
    "regional.dashboard": "dashboard",
    "regional.reports": "reportes",
    "regional.report_new": "reportes",
    "regional.report_detail": "reportes",
    "regional.report_retry": "reportes",
    "regional.document_center": "documentos",
    "regional.document_new": "documentos",
    "regional.document_detail": "documentos",
    "regional.document_verify": "documentos",
    "regional.document_conservation": "documentos",
    "regional.download_file": "traslados",
    "regional.verify_file": "traslados",
    # Preferencia de horario: redirige a la página de origen, sin entrada propia.
    "portal.timezone_preference": None,
    "selectors.options": None,
    # LOGÍSTICA · Apoyo a decisiones (incluye simulaciones, fuentes y anomalías)
    "regional.decision_support": "algoritmos",
    "regional.decision_history": "algoritmos",
    "regional.decision_detail": "algoritmos",
    "regional.decision_new": "algoritmos",
    "regional.public_reference_sources": "algoritmos",
    "regional.import_reference_roads": "algoritmos",
    "regional.algorithm_runs": "algoritmos",
    "regional.algorithm_run": "algoritmos",
    "regional.demand_simulation": "algoritmos",
    "regional.anomaly_reviews": "algoritmos",
    "regional.anomaly_review": "algoritmos",
    "regional.anomaly_resolve": "algoritmos",
    # LOGÍSTICA · Rutas
    "regional.routes": "rutas",
    "regional.route_new": "rutas",
    "regional.route_detail": "rutas",
    "regional.route_edit": "rutas",
    # LOGÍSTICA · Traslados y custodia (incluye reservas, archivos y rastreo)
    "regional.allocations": "traslados",
    "organs.allocations": "traslados",
    "regional.shipment_new": "traslados",
    "regional.shipment_detail": "traslados",
    "regional.shipment_transition": "traslados",
    "regional.shipment_files": "traslados",
    "regional.shipment_tracking": "traslados",
    "regional.tracking_access": "traslados",
    "regional.tracking_assignments": "traslados",
    "regional.tracking_assign": "traslados",
    "regional.tracking_revoke": "traslados",
    "regional.telemetry": "traslados",
    "regional.reservations": "traslados",
    "regional.reservation": "traslados",
    "regional.reservation_cancel": "traslados",
    # BANCO DE SANGRE · Laboratorio y Muestras
    "regional.laboratory": "laboratorio",
    "regional.lab_result": "laboratorio",
    "regional.lab_correct": "laboratorio",
    "regional.lab_review": "laboratorio",
    "regional.rule_profiles": "laboratorio",
    "regional.rule_detail": "laboratorio",
    "regional.rule_new": "laboratorio",
    "regional.rule_action": "laboratorio",
    "regional.samples": "muestras",
    "regional.sample_new": "muestras",
    "regional.sample_detail": "muestras",
    "regional.sample_completeness": "muestras",
    "regional.sample_receive": "muestras",
    "regional.result_new": "muestras",
    # BANCO DE SANGRE · Donantes y receptores (según ``kind`` de la URL)
    "regional.people": _people,
    "regional.person_new": _people,
    "regional.person_detail": _people,
    "regional.consents": "donantes",
    "regional.consent_new": "donantes",
    "regional.donor_personal": "donantes",
    "regional.donor_review": "donantes",
    "regional.donor_withdraw": "donantes",
    # BANCO DE SANGRE · Donaciones, campañas e inscripciones
    "regional.donations": "donaciones",
    "regional.donation_new": "donaciones",
    "regional.donation_detail": "donaciones",
    "regional.donation_step": "donaciones",
    "regional.campaigns": "campanas",
    "regional.campaign_new": "campanas",
    "regional.campaign_detail": "campanas",
    "regional.campaign_publication": "campanas",
    "regional.slots": "campanas",
    "regional.slot_new": "campanas",
    "regional.appointments": "citas",
    "regional.appointment_new": "citas",
    "regional.appointment_detail": "citas",
    "regional.appointment_schedule": "citas",
    "regional.appointment_cancel": "citas",
    # BANCO DE SANGRE · Inventario, disponibilidad y conservación
    "inventory.index": "inventory",
    "inventory.new": "inventory",
    "inventory.detail": "inventory",
    "inventory.destination": "inventory",
    "inventory.release": "inventory",
    "inventory.fractionate": "inventory",
    "inventory.lineage": "inventory",
    "inventory.label": "inventory",
    "inventory.controls_new": "inventory",
    "inventory.cold_reading_new": "inventory",
    "inventory.quality_review": "inventory",
    "inventory.resource_conservation": "inventory",
    "maintenance.edit": _edit_record,
    "maintenance.withdraw": "inventory",
    "inventory.availability": "disponibilidad",
    "regional.conservation": "conservacion",
    "regional.cold_equipment": "conservacion",
    "regional.cold_equipment_new": "conservacion",
    "regional.cold_profiles": "conservacion",
    "regional.cold_profile_new": "conservacion",
    "regional.cold_profile_detail": "conservacion",
    # BANCO DE SANGRE · Solicitudes, evaluaciones y propuestas
    "regional.requests": "solicitudes",
    "regional.request_new": "solicitudes",
    "regional.request_detail": "solicitudes",
    "regional.request_cancel": "solicitudes",
    "regional.evaluate": "solicitudes",
    "regional.evaluation_detail": "solicitudes",
    "regional.candidate_review": "solicitudes",
    "regional.reserve": "solicitudes",
    "regional.rank": "solicitudes",
    "regional.operation": "solicitudes",
    "regional.operation_resume": "solicitudes",
    "regional.external_authorizations": "solicitudes",
    "regional.external_authorization_new": "solicitudes",
    "regional.proposals": "propuestas",
    "regional.proposal_new": "propuestas",
    "regional.proposal_detail": "propuestas",
    # DONACIÓN / TRASPLANTE DE ÓRGANOS
    "organs.index": "organos",
    # SEGUIMIENTO
    "portal.alerts": "alertas",
    "portal.alert_ack": "alertas",
    "portal.audit": "audit",
    "portal.audit_detail": "audit",
    "portal.findings": "findings",
    "portal.finding_new": "findings",
    "portal.finding_detail": "findings",
    "portal.finding_action": "findings",
    "portal.monitor": "monitoreo",
    # ADMINISTRACIÓN
    "admin.index": _admin_entity,
    "admin.new": _admin_entity,
    "admin.user_detail": "users",
    "admin.user_role": "users",
    "admin.user_state": "users",
    "admin.institution_detail": "institutions",
    "maintenance.institution_edit": "institutions",
    "maintenance.institution_administrator": "institutions",
    "maintenance.catalogue_list": _catalogue,
    "maintenance.catalogue_new": _catalogue,
    "maintenance.catalogue_detail": _catalogue,
    "maintenance.catalogue_edit": _catalogue,
    # Configuración y seguridad (política, presentación y dispositivos)
    "admin.settings": "configuracion",
    "admin.policy_edit": "configuracion",
    "admin.institution_presentation_edit": "configuracion",
    "admin.devices": "configuracion",
    "admin.device_new": "configuracion",
    "admin.device_detail": "configuracion",
    "admin.device_credential": "configuracion",
    "admin.device_revoke": "configuracion",
}

# Endpoints sin barra lateral (sitio público, sesión, recursos estáticos).
EXCLUDED_BLUEPRINTS = {"public", "static"}

# Respaldo por prefijo para páginas sin endpoint (404) o rutas aún no mapeadas.
PATH_PREFIXES = [
    ("/laboratorio/muestras", "muestras"),
    ("/laboratorio", "laboratorio"),
    ("/apoyo-decisiones", "algoritmos"),
    ("/algoritmos", "algoritmos"),
    ("/revision-anomalias", "algoritmos"),
    ("/rutas", "rutas"),
    ("/traslados", "traslados"),
    ("/reservas", "traslados"),
    ("/archivos", "traslados"),
    ("/organos/traslados", "traslados"),
    ("/organos", "organos"),
    ("/inventario", "inventory"),
    ("/disponibilidad", "disponibilidad"),
    ("/conservacion", "conservacion"),
    ("/donantes/recipient", "receptores"),
    ("/donantes", "donantes"),
    ("/donaciones", "donaciones"),
    ("/solicitudes", "solicitudes"),
    ("/evaluaciones", "solicitudes"),
    ("/operaciones", "solicitudes"),
    ("/propuestas", "propuestas"),
    ("/campanas", "campanas"),
    ("/citas", "citas"),
    ("/reportes", "reportes"),
    ("/documentos", "documentos"),
    ("/notificaciones", "alertas"),
    ("/auditoria", "audit"),
    ("/hallazgos", "findings"),
    ("/monitoreo", "monitoreo"),
    ("/administracion/dispositivos", "configuracion"),
    ("/administracion/usuarios", "users"),
    ("/administracion/users", "users"),
    ("/administracion/institutions", "institutions"),
    ("/instituciones", "institutions"),
    ("/catalogos", "components"),
    ("/configuracion", "configuracion"),
    ("/panel", "dashboard"),
    ("/regional", "dashboard"),
]


def mark(section):
    """Fija la sección cuando depende del dato (p. ej. órgano o sangre)."""
    g.nav_section = section


def resolve(endpoint, path, view_args, forced=None):
    """Id de ``NAV`` que debe resaltarse, o ``None`` si ninguno."""
    if forced:
        return forced
    if endpoint in ENDPOINT_SECTIONS:
        value = ENDPOINT_SECTIONS[endpoint]
        return value(view_args or {}) if callable(value) else value
    for prefix, section in PATH_PREFIXES:
        if path == prefix or path.startswith(prefix + "/"):
            return section
    return None


def register(blueprint):
    """Publica ``nav_active`` en todas las plantillas (también las de error)."""

    @blueprint.app_context_processor
    def navigation_context():
        return {
            "nav_active": resolve(
                request.endpoint, request.path, request.view_args, g.get("nav_section")
            )
        }
