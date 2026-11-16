package org.redhouse.mobile

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.size
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.drawscope.scale
import androidx.compose.ui.graphics.drawscope.translate
import androidx.compose.ui.graphics.vector.PathParser
import androidx.compose.ui.unit.dp
import androidx.compose.material3.lightColorScheme
import androidx.compose.ui.graphics.Color
import kotlinx.datetime.toLocalDateTime

/** Presentation only. Values sent to services are never transformed here. */
val redHouseColors = lightColorScheme(
    primary = Color(0xFFC8102E), onPrimary = Color.White,
    primaryContainer = Color(0xFFFFE8EC), onPrimaryContainer = Color(0xFF760019),
    secondary = Color(0xFF1E3A5F), onSecondary = Color.White,
    secondaryContainer = Color(0xFFDCE8F5), onSecondaryContainer = Color(0xFF0F1B2D),
    tertiary = Color(0xFF754B00), onTertiary = Color.White,
    tertiaryContainer = Color(0xFFFFF8E6), onTertiaryContainer = Color(0xFF754B00),
    background = Color(0xFFF0F4F8), onBackground = Color(0xFF0F172A),
    surface = Color.White, onSurface = Color(0xFF0F172A),
    surfaceVariant = Color(0xFFE8EDF3), onSurfaceVariant = Color(0xFF475569),
    surfaceContainerLowest = Color.White, surfaceContainerLow = Color(0xFFF7F9FC),
    surfaceContainer = Color(0xFFF0F4F8), surfaceContainerHigh = Color(0xFFE8EDF3), surfaceContainerHighest = Color(0xFFDFE7F0),
    surfaceTint = Color(0xFF1E3A5F),
    outline = Color(0xFF64748B), outlineVariant = Color(0xFFCBD5E1),
    error = Color(0xFF991B1B), onError = Color.White,
    errorContainer = Color(0xFFFFE8E8), onErrorContainer = Color(0xFF7F1D1D)
)

fun fieldLabel(field: String): String = mapOf(
    "id" to "Referencia", "origin_id" to "Referencia de origen", "destination_id" to "Referencia de destino",
    "campaign_title" to "Campaña", "campaign_start" to "Inicio de campaña", "site_name" to "Sede", "venue" to "Sede", "origin_name" to "Origen", "destination_name" to "Destino", "departure_at" to "Salida", "location_name" to "Ubicación",
    "kind" to "Recurso", "component" to "Componente", "quantity" to "Cantidad",
    "urgency" to "Urgencia", "expires_at" to "Caducidad", "version" to "Versión",
    "created_at" to "Fecha de registro", "message_code" to "Aviso", "result_state" to "Estado del resultado",
    "value" to "Valor", "unit" to "Unidad", "method" to "Método", "laboratory" to "Laboratorio", "reference" to "Referencia",
    "title" to "Título", "folio" to "Folio", "identifier" to "Identificador",
    "test_code" to "Prueba", "measured_at" to "Fecha de medición", "display_name" to "Nombre",
    "username" to "Cuenta", "role" to "Perfil", "status" to "Estado", "state" to "Estado",
    "starts_at" to "Inicio", "ends_at" to "Fin", "scheduled_at" to "Fecha programada",
    "available" to "Cupos disponibles", "severity" to "Severidad del aviso", "message" to "Mensaje"
)[field] ?: field.replace('_', ' ')

fun displayValue(field: String, value: String): String {
    if (field == "message_code") return mapOf(
        "APPOINTMENT_BOOKED" to "Inscripción en campaña confirmada",
        "APPOINTMENT_CANCELLED" to "Inscripción en campaña cancelada",
        "APPOINTMENT_CONFIRM" to "Cita confirmada",
        "APPOINTMENT_RESCHEDULE" to "Cita reprogramada",
        "APPOINTMENT_ATTEND" to "Asistencia a cita registrada",
        "APPOINTMENT_CANCEL" to "Cita cancelada",
        "APPOINTMENT_REMINDER" to "Recordatorio de tu cita",
        "CAMPAIGN_CREATED" to "Campaña registrada",
        "CAMPAIGN_UPDATED" to "Campaña actualizada",
        "CAMPAIGN_SLOT_CREATED" to "Cupo de campaña creado",
        "CAMPAIGN_PUBLICATION_CHANGED" to "Publicación de campaña actualizada",
        "DONOR_REVIEWED" to "Evaluación del donante registrada"
    )[value] ?: value
    if (field == "role") return mapOf("DONOR" to "Donante", "TRANSPORT" to "Transporte",
        "OPERATOR" to "Operador", "MEDICAL" to "Médico", "COORDINATOR" to "Coordinador",
        "ADMIN" to "Administración", "AUDITOR" to "Auditoría")[value] ?: value
    if (field in setOf("status", "state", "result_state")) return mapOf(
        "AUTHORIZED" to "Autorizado documentalmente", "CORRECTED" to "Corregido",
        "NOT_CHECKED" to "Sin comprobar", "SENDING" to "Enviando; sin confirmación", "RECORDED" to "Registrado", "QUEUED" to "Pendiente local", "PENDING" to "Pendiente", "CONFIRMED" to "Confirmado",
        "BOOKED" to "Reservada", "PLANNED" to "Planificado", "OPEN" to "Abierta", "CLOSED" to "Cerrada", "QUARANTINE" to "En cuarentena",
        "CANCELLED" to "Cancelado", "PREPARED" to "Preparado", "COLLECTED" to "Recolectado",
        "IN_TRANSIT" to "En tránsito", "DELIVERED" to "Entregado", "ACCEPTED" to "Aceptado",
        "RECEIVED" to "Recibido", "WITHDRAWN" to "Retirado",
        "ACTIVE" to "Activo", "INACTIVE" to "Inactivo", "DRAFT" to "Borrador", "DEFERRED" to "Aplazado", "PRELIMINARY" to "Registro preliminar",
        "AVAILABLE" to "Disponible", "RESERVED" to "Reservado", "EXPIRED" to "Vencido",
        "REJECTED" to "Rechazado", "UNCERTAIN" to "Sin confirmación", "CONFLICT" to "Conflicto"
    )[value] ?: value
    return if ((field.endsWith("_at") || field=="campaign_start")) displayBriefDate(value) else value
}

/** Keeps the original offset, precision and instant; only rearranges visible text. */
fun displayDate(value: String): String {
    val match = Regex("^(\\d{4})-(\\d{2})-(\\d{2})T(.+?)(Z|[+-]\\d{2}:\\d{2})$").matchEntire(value) ?: return value
    val (year, month, day, time, zone) = match.destructured
    return "$day/$month/$year · $time ${if (zone == "Z") "UTC" else "UTC$zone"}"
}

/** Present the actual instant in the device time zone without changing the stored timestamp. */
fun displayBriefDate(value:String):String = try {
    val date=kotlinx.datetime.Instant.parse(value).toLocalDateTime(kotlinx.datetime.TimeZone.currentSystemDefault())
    val months=listOf("ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic")
    "${date.dayOfMonth} ${months[date.monthNumber-1]} ${date.year} · ${date.hour.toString().padStart(2,'0')}:${date.minute.toString().padStart(2,'0')}"
} catch(_:Exception) {value}

/** Existing Lucide droplet, lucide-static v1.41.0, ISC; same path as web branding. */
@Composable fun RedHouseMark() {
    val path = remember { PathParser().parsePathString("M12 22a7 7 0 0 0 7-7c0-2-1-3.9-3-5.5s-3.5-4-4-6.5c-.5 2.5-2 4.9-4 6.5C6 11.1 5 13 5 15a7 7 0 0 0 7 7z").toPath() }
    Canvas(Modifier.size(40.dp)) {
        drawRoundRect(Color(0xFFC8102E), cornerRadius = CornerRadius(8.dp.toPx()))
        translate(size.width * .2f, size.height * .2f) {
            scale(size.width * .6f / 24f, size.height * .6f / 24f, pivot = androidx.compose.ui.geometry.Offset.Zero) {
                drawPath(path, Color.White, style = Stroke(width = 2f))
            }
        }
    }
}
