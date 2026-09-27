"""Metadatos de presentación; ningún permiso se decide solo por el menú."""
from datetime import datetime, timezone

REGIONAL_LABELS = {
    'COORDINATION': 'Coordinación', 'destination':'Recepción en mi ámbito',
    'HOSPITAL': 'Hospital', 'BLOOD_BANK': 'Banco de sangre', 'TRANSPLANT_CENTER': 'Centro de trasplantes',
    'AVAILABLE': 'Disponible', 'QUARANTINED': 'Cuarentena', 'WITHDRAWN': 'Baja',
    'PENDING': 'Pendiente de evaluación', 'ELIGIBLE': 'Elegible', 'DEFERRED': 'Diferido',
    'ACTIVE': 'Activo', 'INACTIVE': 'Inactivo', 'REGISTERED': 'Registrada',
    'COLLECTED': 'Recolectado', 'PROCESSED': 'Procesado', 'CANCELLED': 'Cancelado',
    'OPEN': 'Abierta', 'IN_PROGRESS': 'En atención', 'CLOSED': 'Cerrada',
    'URGENT': 'Urgente', 'PRIORITY': 'Prioritaria', 'ROUTINE': 'Ordinaria',
    'RESERVED': 'Reservada', 'ASSIGNED': 'Asignada', 'RECEIVED': 'Recibida',
    'SCHEDULED': 'Programado', 'PREPARED': 'Preparado', 'IN_TRANSIT': 'En tránsito',
    'DELIVERED': 'Entregado', 'ACCEPTED': 'Aceptado', 'INCIDENT': 'Incidencia',
}


def regional_value(value, field):
    """Traduce estados tipados; preserva folios, nombres y texto registrado."""
    if value is None:
        return '—'
    if isinstance(value, datetime):
        from .timezones import datefmt
        return datefmt(value)
    if field in ('current_status', 'shipment_status', 'status', 'decision', 'urgency',
                 'institution_type', 'participation_status', 'new_status',
                 'Estado', 'Asignación', 'Traslado', 'Urgencia'):
        return REGIONAL_LABELS.get(value, value)
    return value

TITLES = {"institutions": "Instituciones", "sites": "Sedes", "locations": "Ubicaciones",
          "components": "Componentes sanguíneos", "users": "Usuarios"}

FUTURE = {
    "organos": {"title": "Órganos y HLA", "subtitle": "Gestión de donación y trasplante de órganos.",
                "action": "Registrar disponibilidad"},
}

NAV = [
    ("GENERAL", "dashboard", "Panel principal", "layout-grid", "portal.dashboard", {}, "dashboard", False),
    ("BANCO DE SANGRE", "regional", "Panel regional", "building-2", "regional.dashboard", {}, "regional.read", False),
    ("BANCO DE SANGRE", "donantes", "Donantes", "droplet", "regional.people", {"kind": "donor"}, "donor.write", False),
    ("BANCO DE SANGRE", "donaciones", "Donaciones y procesamiento", "layers", "regional.donations", {}, "donor.write", False),
    ("BANCO DE SANGRE", "receptores", "Receptores", "users", "regional.people", {"kind": "recipient"}, "recipient.write", False),
    ("BANCO DE SANGRE", "inventory", "Inventario sanguíneo", "package", "inventory.index", {}, "inventory.read", False),
    ("BANCO DE SANGRE", "solicitudes", "Solicitudes y compatibilidad", "triangle-alert", "regional.requests", {}, "regional.read", False),
    ("BANCO DE SANGRE", "rutas", "Rutas y estimaciones", "map-pin", "regional.routes", {}, "route.write", False),
    ("LOGÍSTICA", "traslados", "Traslados y custodia", "truck", "regional.allocations", {}, "logistics", False),
    ("LOGÍSTICA", "trazabilidad", "Trazabilidad regional", "file-clock", "regional.allocations", {}, "trace.read", False),
    ("DONACIÓN / TRASPLANTE DE ÓRGANOS", "organos", "Órganos y HLA", "heart-pulse", "organs.index", {}, "organ.read", False),
    ("DONACIÓN / TRASPLANTE DE ÓRGANOS", "organos-logistica", "Traslados de órganos", "truck", "organs.allocations", {}, "organ.logistics", False),
    ("AUDITORÍA", "audit", "Bitácora de auditoría", "scroll-text", "portal.audit", {}, "audit.read", False),
    ("ADMINISTRACIÓN", "institutions", "Instituciones", "building-2", "admin.index", {"entity": "institutions"}, "administration", False),
    ("ADMINISTRACIÓN", "users", "Usuarios", "user-round-cog", "admin.index", {"entity": "users"}, "administration", False),
    ("ADMINISTRACIÓN", "components", "Catálogos", "settings-2", "admin.index", {"entity": "components"}, "administration", False),
    ("ADMINISTRACIÓN", "settings", "Roles y parámetros", "sliders-horizontal", "admin.settings", {}, "administration", False),
]


AUDIT_LABELS = {
    'ORGAN_DONOR':'Donante de órganos', 'ORGAN_RECIPIENT':'Receptor de órgano',
    'ORGAN_OFFER':'Disponibilidad de órgano', 'ORGAN_CANDIDATE':'Candidato de órgano',
    'ORGAN_REVIEW':'Dictamen de órgano', 'ORGAN_ALLOCATION':'Asignación de órgano',
    'LIST':'Consulta de listado', 'SUMMARY':'Consulta de resumen/panel',
    'READ':'Consulta', 'SENSITIVE_READ':'Consulta de información restringida',
    'CREATE':'Alta', 'UPDATE':'Modificación', 'DELETE':'Baja', 'LOGIN':'Inicio de sesión',
    'LOGOUT':'Cierre de sesión', 'RENEW':'Continuación de sesión', 'ACCESS':'Acceso',
    'AUTHORIZE':'Autorización', 'EVALUATE':'Evaluación de alternativas', 'RESERVE':'Reserva',
    'ASSIGN':'Asignación', 'CANCEL':'Cancelación', 'CLOSED':'Solicitud completada',
    'BLOOD_UNIT':'Unidad sanguínea', 'BLOOD_REQUEST':'Solicitud', 'DONOR':'Donante',
    'RECIPIENT':'Receptor', 'DONATION':'Donación', 'DONOR_REVIEW':'Evaluación del donante',
    'SHIPMENT':'Traslado', 'BLOOD_ALLOCATION':'Asignación', 'AUDIT_EVENT':'Evento de auditoría',
    'USER_ACCOUNT':'Cuenta de usuario', 'WEB_SESSION':'Sesión', 'REGIONAL_ROUTE':'Ruta regional',
    'REGIONAL_DASHBOARD':'Panel regional', 'DASHBOARD':'Panel principal', 'ENDPOINT':'Operación del portal',
    'INSTITUTION':'Institución', 'SITE':'Sede', 'STORAGE_LOCATION':'Ubicación', 'BLOOD_COMPONENT':'Componente',
    'record_code':'Folio del expediente','display_name':'Nombre','blood_group':'ABO/Rh',
    'restrictions':'Restricciones','background':'Antecedentes','studies':'Estudios',
    'current_status':'Estado','requirement':'Requerimiento','source_reference':'Procedencia de estimación',
}

def audit_label(value):
    return AUDIT_LABELS.get(value, REGIONAL_LABELS.get(value,value))
