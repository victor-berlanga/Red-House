"""Vocabulario y composición visual. Las API conservan toda autorización."""

from urllib.parse import urlsplit, parse_qsl, urlencode
from flask import g, request, url_for


def institution_label(value):
    return value


LISTS = {
    "inventory": ("Inventario sanguíneo", "/inventario", "Registrar unidad"),
    "organos": ("Órganos y HLA", "/organos", "Registrar órgano"),
    "donantes": ("Donantes", "/donantes/donor", "Registrar donante"),
    "receptores": ("Receptores", "/donantes/recipient", "Registrar receptor"),
    "donaciones": ("Donaciones", "/donaciones", "Registrar donación"),
    "solicitudes": ("Solicitudes", "/solicitudes", "Crear solicitud"),
    "campanas": ("Campañas", "/campanas", "Crear campaña"),
    "citas": ("Inscripciones", "/citas", "Reservar cupo"),
    "rutas": ("Rutas", "/rutas", "Registrar ruta"),
    "traslados": ("Traslados", "/traslados", "Planear traslado"),
    "institutions": (
        "Instituciones",
        "/administracion/institutions",
        "Registrar institución",
    ),
    "users": ("Usuarios", "/administracion/users", "Crear usuario"),
    "components": ("Catálogos", "/administracion/components", "Registrar entrada"),
    "alertas": ("Notificaciones", "/notificaciones", "Registrar aviso"),
    "audit": ("Bitácora", "/auditoria", "Registrar evento"),
    "propuestas": ("Propuestas", "/propuestas", "Crear propuesta"),
    "disponibilidad": ("Disponibilidad", "/disponibilidad", "Registrar recurso"),
}


def return_to(active, fallback=None):
    """Solo listados GET de la aplicación, nunca una URL externa ni un POST."""
    default = fallback or LISTS.get(active, ("", "/panel", ""))[1]
    candidate = request.values.get("return_to", "")
    try:
        part = urlsplit(candidate)
    except ValueError:
        return default
    allowed = {v[1] for v in LISTS.values()} | {"/reservas", "/panel", "/regional"}
    allowed |= {
        "/catalogos/" + k
        for k in ("sites", "contacts", "schedules", "capacities", "locations")
    }
    if (
        part.scheme
        or part.netloc
        or part.fragment
        or part.path not in allowed
        or "\\" in candidate
    ):
        return default
    if any(ord(c) < 32 for c in candidate):
        return default
    params = [
        (k, v) for k, v in parse_qsl(part.query) if k not in ("format", "return_to")
    ]
    return part.path + ("?" + urlencode(params) if params else "")


def contextual(link, target):
    if not link:
        return link
    part = urlsplit(link)
    params = [(k, v) for k, v in parse_qsl(part.query) if k != "return_to"]
    return part.path + "?" + urlencode(params + [("return_to", target)])


def edit_action(entity, row):
    role = g.principal.role_code
    state = row.get("status")
    permitted = {
        "resources": role == "OPERATOR" and state == "QUARANTINE",
        "donors": role in ("OPERATOR", "MEDICAL") and state == "PRELIMINARY",
        "recipients": role == "MEDICAL" and row.get("can_edit", False),
        "requests": role == "MEDICAL"
        and state == "OPEN"
        and row.get("can_edit", False),
        "donations": role == "MEDICAL" and state == "COLLECTED",
        "campaigns": role == "OPERATOR",
    }.get(entity, False)
    return (
        [
            (
                "Editar",
                url_for("maintenance.edit", entity=entity, identifier=row["id"]),
                "pencil",
            )
        ]
        if permitted
        else []
    )


FIELD_LABELS = {
    "name": "Nombre",
    "title": "Campaña",
    "municipality": "Municipio",
    "address": "Dirección",
    "value": "Contacto",
    "description": "Descripción",
    "parent_id": "Sede (referencia)",
    "weekday": "Día de la semana",
    "opens_at": "Apertura",
    "closes_at": "Cierre",
    "capacity": "Cupo",
    "starts_at": "Inicio",
    "ends_at": "Fin",
    "active": "Activo",
    "status": "Estado",
    "state": "Paso",
    "quantity": "Cantidad",
    "received": "Recibido",
    "remaining": "Pendiente",
    "reserved": "Reservado",
    "held": "Retenido",
    "decision": "Dictamen",
    "reason": "Motivo",
    "message": "Seguimiento",
    "action": "Movimiento",
    "created_at": "Fecha",
    "occurred_at": "Fecha",
    "actor_id": "Responsable",
    "evidence": "Evidencia",
    "changes": "Cambios registrados",
    "sequence": "Secuencia",
    "folio": "Folio",
    "component": "Componente",
    "blood_group": "Grupo sanguíneo",
    "kind": "Recurso",
    "collected_at": "Recolección",
    "expires_at": "Caducidad",
    "background": "Antecedentes",
    "restrictions": "Restricciones",
    "requirement": "Requerimiento",
    "studies": "Estudios",
    "source": "Procedencia",
    "distance_km": "Distancia (km)",
    "travel_minutes": "Tiempo (min)",
    "display_name": "Nombre",
    "version": "Versión",
    "human_confirmation": "Confirmación humana",
    "consent": "Consentimiento registrado",
    "consent_reference": "Referencia del consentimiento",
    "consent_at": "Fecha del consentimiento",
    "donation_kind": "Tipo de donación",
    "organ_type": "Órgano",
    "urgency": "Nivel de urgencia",
    "username": "Cuenta",
    "role": "Perfil",
    "message_code": "Evento",
    "departure_at": "Salida prevista",
    "eta": "Llegada prevista",
    "origin_id": "Origen",
    "destination_id": "Destino",
    "current_institution_id": "Institución",
    "location_id": "Ubicación (referencia)",
    "tenant_id": "Institución",
    "request_id": "Solicitud",
    "resource_id": "Recurso",
    "user_id": "Cuenta",
    "donor_id": "Donante",
    "recipient_id": "Receptor",
    "campaign_title": "Campaña",
    "campaign_start": "Inicio de la campaña",
    "campaign_end": "Fin de la campaña",
    "donor_name": "Donante",
    "Solicitud": "Solicitud",
    "Recurso": "Recurso",
    "Explicación": "Motivo de la propuesta",
}

TECHNICAL = {
    "id",
    "hash",
    "previous_hash",
    "correlation_id",
    "version",
    "algorithm_version",
    "elapsed_ms",
    "tenant_id",
    "region_id",
}


def grouped_facts(row, facts):
    clinical = {
        "Antecedentes",
        "Restricciones",
        "Estudios documentales",
        "Requerimiento",
        "Referencia del consentimiento",
        "Fecha del consentimiento",
        "Tipo de donación",
    }
    technical = {"Versión", "Versión de la regla", "Procesamiento (ms)"}
    if row.get("tenant_id") == row.get("current_institution_id") and row.get(
        "tenant_id"
    ):
        facts = [(k, v) for k, v in facts if k != "Institución"]
    return [
        ("Resumen", [(k, v) for k, v in facts if k not in clinical | technical]),
        ("Información del expediente", [(k, v) for k, v in facts if k in clinical]),
        ("Datos de trazabilidad", [(k, v) for k, v in facts if k in technical]),
    ]


TASKS = {
    "OPERATOR": [
        ("Registrar unidad", "/inventario/nuevo", "Captura y ubicación del inventario"),
        (
            "Inventario en cuarentena",
            "/inventario?status=QUARANTINE",
            "Revisar registros pendientes",
        ),
        ("Traslados", "/traslados", "Preparar salidas y aceptar recepciones"),
    ],
    "MEDICAL": [
        (
            "Solicitudes abiertas",
            "/solicitudes?status=OPEN",
            "Evaluar candidatos y cobertura",
        ),
        (
            "Liberaciones pendientes",
            "/inventario?status=QUARANTINE",
            "Revisar unidades antes de liberarlas",
        ),
        ("Donantes", "/donantes/donor", "Consultar expedientes y emitir dictámenes"),
    ],
    "COORDINATOR": [
        (
            "Reservas y asignaciones",
            "/reservas",
            "Consultar recursos para planear traslados",
        ),
        ("Traslados", "/traslados", "Coordinar origen, destino y responsable"),
        ("Disponibilidad regional", "/disponibilidad", "Consultar recursos de la red"),
    ],
    "TRANSPORT": [
        ("Mis traslados", "/traslados", "Recolección, tránsito y entrega"),
        ("Notificaciones", "/notificaciones", "Avisos de las órdenes asignadas"),
    ],
    "ADMIN": [
        ("Usuarios", "/administracion/users", "Administrar accesos institucionales"),
        ("Catálogos", "/catalogos/sites", "Sedes, contactos y ubicaciones"),
        (
            "Estado de la plataforma",
            "/monitoreo",
            "Consultar disponibilidad de servicios",
        ),
    ],
    "AUDITOR": [
        ("Bitácora", "/auditoria", "Consultar eventos de la región"),
        (
            "Estado de la plataforma",
            "/monitoreo",
            "Disponibilidad y fallas de dependencias",
        ),
    ],
    "DONOR": [
        ("Mi expediente", "/donantes/donor", "Consultar registro y evaluaciones"),
        ("Campañas", "/campanas", "Consultar jornadas de donación"),
        ("Mis inscripciones", "/citas", "Reservar cupo en una campaña"),
    ],
}


EVENT_LABELS = {
    "ALERT_ACKNOWLEDGED": "Notificación leída",
    "ALLOCATION_PROPOSAL_CREATED": "Propuesta de cobertura generada",
    "APPOINTMENT_BOOKED": "Inscripción en campaña confirmada",
    "APPOINTMENT_CANCELLED": "Inscripción en campaña cancelada",
    "CAMPAIGN_CREATED": "Campaña registrada",
    "CAMPAIGN_UPDATED": "Campaña actualizada",
    "CATALOGUE_CREATED": "Entrada de catálogo registrada",
    "CATALOGUE_UPDATED": "Catálogo actualizado",
    "DONATION_COLLECTED": "Donación recolectada",
    "DONATION_PROCESSED": "Donación procesada",
    "DONATION_REJECTED": "Donación rechazada",
    "DONATION_UPDATED": "Donación actualizada",
    "DONOR_REGISTERED": "Donante registrado",
    "DONOR_REVIEWED": "Evaluación del donante registrada",
    "DONOR_UPDATED": "Expediente del donante actualizado",
    "EVALUATION_CREATED": "Evaluación de candidatos generada",
    "EVALUATION_REVIEWED": "Dictamen de candidato registrado",
    "FILE_PREPARED": "Archivo preparado",
    "FILE_VERIFIED": "Archivo verificado",
    "INSTITUTION_CREATED": "Institución registrada",
    "INSTITUTION_PROVISIONED": "Acceso institucional habilitado",
    "INSTITUTION_UPDATED": "Institución actualizada",
    "INVENTORY_SHIPMENT_EVENT": "Inventario actualizado por traslado",
    "LOGIN": "Inicio de sesión",
    "LOGIN_FAILED": "Intento de acceso fallido",
    "LOGOUT": "Cierre de sesión",
    "REFRESH_ATTEMPT": "Renovación de sesión solicitada",
    "RANKING_CREATED": "Orden de candidatos generado",
    "RECIPIENT_CREATED": "Receptor registrado",
    "RECIPIENT_UPDATED": "Expediente del receptor actualizado",
    "REQUEST_CREATED": "Solicitud registrada",
    "REQUEST_UPDATED": "Solicitud actualizada",
    "REQUEST_CANCELLED": "Solicitud cancelada",
    "REQUEST_CLOSED": "Solicitud atendida",
    "REQUEST_IN_PROGRESS": "Solicitud en atención",
    "REQUEST_OPEN": "Solicitud abierta",
    "RESERVATION_CANCELLED": "Reserva cancelada",
    "RESERVATION_RECEIVED": "Recurso reservado recibido",
    "RESOURCE_CREATED": "Recurso registrado",
    "RESOURCE_RELEASED": "Recurso liberado",
    "RESOURCE_RESERVED": "Reserva de recurso confirmada",
    "RESOURCE_UPDATED": "Recurso actualizado",
    "RESOURCE_WITHDRAWN": "Recurso retirado",
    "ROUTE_CREATED": "Ruta registrada",
    "ROUTE_UPDATED": "Ruta actualizada",
    "SHIPMENT_PLAN_PENDING": "Planeación de traslado en confirmación",
    "SHIPMENT_PLAN_REJECTED": "Planeación de traslado rechazada",
    "SHIPMENT_PLANNED": "Traslado programado",
    "SHIPMENT_PREPARED": "Traslado preparado",
    "SHIPMENT_COLLECTED": "Recolección confirmada",
    "SHIPMENT_IN_TRANSIT": "Traslado en tránsito",
    "SHIPMENT_DELIVERED": "Entrega de traslado registrada",
    "SHIPMENT_ACCEPTED": "Recepción de traslado aceptada",
    "SHIPMENT_CANCELLED": "Traslado cancelado",
    "SHIPMENT_INCIDENT": "Incidencia de traslado registrada",
    "TELEMETRY_RECORDED": "Ubicación de traslado registrada",
    "USER_CREATED": "Cuenta creada",
    "USER_STATE_CHANGED": "Acceso de cuenta actualizado",
    "CAPACITY_HELD": "Cupo de solicitud retenido",
    "CAPACITY_CONFIRMED": "Cupo de solicitud confirmado",
    "CAPACITY_RELEASED": "Cupo de solicitud liberado",
    "CAPACITY_RECEIVED": "Recepción aplicada a la solicitud",
}

SERVICE_LABELS = {
    "identidad_acceso": "Acceso y cuentas",
    "donantes": "Donantes y campañas",
    "receptores": "Receptores y solicitudes",
    "inventario": "Inventario y reservas",
    "compatibilidad": "Evaluación de candidatos",
    "priorizacion_geografia": "Cobertura y rutas",
    "transporte": "Traslados",
    "custodia": "Cadena de custodia",
    "alertas": "Notificaciones",
    "auditoria": "Auditoría",
    "monitoreo": "Supervisión de disponibilidad",
}


def event_label(code):
    return EVENT_LABELS.get(code, "Actividad registrada")


def service_label(code):
    return SERVICE_LABELS.get(code, "Servicio de la plataforma")


def related_alert(row):
    """Enlaces de consulta por perfil; el propietario valida el recurso al abrirlo."""
    from uuid import UUID

    code, identifier, role = (
        row.get("message_code", ""),
        row.get("resource_id"),
        g.principal.role_code,
    )
    try:
        identifier = UUID(str(identifier))
    except ValueError:
        return None
    if code.startswith("APPOINTMENT_") and role in ("DONOR", "OPERATOR"):
        return url_for("regional.appointment_detail", identifier=identifier)
    if code.startswith("DONOR_") and role in ("DONOR", "OPERATOR", "MEDICAL"):
        return url_for("regional.person_detail", kind="donor", identifier=identifier)
    if code.startswith("CAMPAIGN_") and role in ("DONOR", "OPERATOR", "MEDICAL"):
        return url_for("regional.campaign_detail", identifier=identifier)
    if code.startswith("REQUEST_") and role in ("OPERATOR", "MEDICAL"):
        return url_for("regional.request_detail", identifier=identifier)
    if code.startswith("SHIPMENT_") and role in (
        "OPERATOR",
        "MEDICAL",
        "COORDINATOR",
        "TRANSPORT",
    ):
        return url_for("regional.shipment_detail", identifier=identifier)
    if (code == "RESOURCE_RESERVED" or code.startswith("RESERVATION_")) and role in (
        "OPERATOR",
        "MEDICAL",
        "COORDINATOR",
    ):
        return url_for("regional.reservation", identifier=identifier)
    if code.startswith("RESOURCE_") and role in ("OPERATOR", "MEDICAL", "COORDINATOR"):
        return url_for("inventory.detail", identifier=identifier)
    if code.startswith("DONATION_") and role in ("OPERATOR", "MEDICAL"):
        return url_for("regional.donation_detail", identifier=identifier)
    return None
