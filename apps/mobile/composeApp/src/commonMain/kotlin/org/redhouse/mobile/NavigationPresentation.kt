package org.redhouse.mobile

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.drawscope.scale
import androidx.compose.ui.graphics.vector.PathParser
import androidx.compose.ui.unit.dp
import kotlinx.serialization.json.*

fun primaryDestinations(role: String): List<String> = when(role) {
    "DONOR" -> listOf("Inicio", "Campañas", "Avisos", "Cuenta")
    "TRANSPORT" -> listOf("Traslados", "Pendientes", "Avisos", "Cuenta")
    "OPERATOR" -> listOf("Inventario", "Traslados", "Avisos", "Cuenta")
    "COORDINATOR" -> listOf("Traslados", "Región", "Avisos", "Cuenta")
    "MEDICAL" -> listOf("Solicitudes", "Laboratorio", "Avisos", "Cuenta")
    else -> listOf("Perfil", "Avisos")
}

@Composable expect fun PresentationBackHandler(enabled: Boolean, onBack: () -> Unit)

@Composable fun DestinationIcon(destination: String) {
    // Same 24-unit linear icon family as the portal; the native item supplies its label.
    val data = when(destination) {
        "Inicio" -> "M3 11L12 3L21 11V21H15V15H9V21H3Z"
        "Campañas", "Citas" -> "M4 5H20V21H4ZM8 2V8M16 2V8M4 11H20M8 15H10M14 15H16"
        "Avisos" -> "M3 5H21V19H3ZM3 5L12 12L21 5"
        "Cuenta", "Perfil" -> "M8 6A4 4 0 1 0 16 6A4 4 0 1 0 8 6M4 22V19A8 8 0 0 1 20 19V22"
        "Traslados" -> "M2 4H14V17H2ZM14 8H18L22 13V17H14M5 17A2 2 0 1 0 9 17A2 2 0 1 0 5 17M16 17A2 2 0 1 0 20 17A2 2 0 1 0 16 17"
        "Región" -> "M3 5L9 2L15 5L21 2V19L15 22L9 19L3 22ZM9 2V19M15 5V22"
        "Laboratorio" -> "M8 2H16M10 2V10L4 20V22H20V20L14 10V2M7 16H17"
        else -> "M5 3H19V21H5ZM9 8H15M9 12H15M9 16H13"
    }
    val path = remember(data) { PathParser().parsePathString(data).toPath() }
    val color = LocalContentColor.current
    Canvas(Modifier.size(24.dp)) { scale(size.width / 24f, size.height / 24f, pivot=androidx.compose.ui.geometry.Offset.Zero) { drawPath(path, color, style=Stroke(width=1.7f)) } }
}

@Composable fun SettingRow(label: String, description: String? = null, onClick: () -> Unit) {
    Column(Modifier.fillMaxWidth().clickable(onClick=onClick).padding(vertical=16.dp)) {
        Row(Modifier.fillMaxWidth(), horizontalArrangement=Arrangement.SpaceBetween) {
            Text(label, Modifier.weight(1f), style=MaterialTheme.typography.bodyLarge)
            Text("›", Modifier.padding(start=12.dp), style=MaterialTheme.typography.titleMedium)
        }
        description?.let { Text(it, style=MaterialTheme.typography.bodyMedium, color=MaterialTheme.colorScheme.onSurfaceVariant) }
    }
    HorizontalDivider()
}

@Composable fun ResourceSummary(screen: Screen, row: JsonObject): Boolean {
    if(screen.path.endsWith("/summary")) return false // The parent renders the authorized aggregate counts.
    var expanded by remember(row.text("id"), screen.title) { mutableStateOf(false) }
    fun first(vararg fields: String) = fields.firstNotNullOfOrNull { field -> row[field]?.jsonPrimitive?.contentOrNull?.takeIf { it.isNotBlank() } }
    val heading = when(screen.title) {
        "Mis citas", "Horarios" -> first("scheduled_at", "starts_at")?.let(::displayDate) ?: first("campaign_title") ?: "Inscripción ${row.text("id").take(8)}"
        "Campañas" -> first("title") ?: "Campaña"
        "Avisos" -> first("message", "title", "message_code") ?: "Aviso"
        "Inventario" -> first("folio", "identifier") ?: "Unidad"
        "Traslados" -> first("reference", "folio") ?: "Traslado ${row.text("id").take(8)}"
        "Solicitudes" -> first("reference", "folio") ?: "Solicitud ${row.text("id").take(8)}"
        "Muestras autorizadas" -> first("identifier", "test_code") ?: "Muestra ${row.text("id").take(8)}"
        "Resultados autorizados" -> first("test_code", "identifier") ?: "Resultado ${row.text("id").take(8)}"
        "Reservas regionales" -> first("reference", "folio") ?: "Reserva ${row.text("id").take(8)}"
        else -> first("folio", "test_code", "display_name", "username", "title") ?: screen.title
    }
    Text(heading, style=MaterialTheme.typography.titleMedium)
    val fields = when(screen.title) {
        "Mis citas", "Horarios" -> listOf("campaign_title", "campaign_start", "site_name", "status", "available")
        "Campañas" -> listOf("starts_at", "ends_at", "venue", "status")
        "Traslados" -> listOf("origin_name", "destination_name", "status", "departure_at")
        "Inventario" -> listOf("component", "blood_group", "status", "location_name")
        "Avisos" -> listOf("created_at", "status", "severity")
        else -> listOf("status", "state", "measured_at", "created_at")
    }
    fields.forEach { field -> row[field]?.jsonPrimitive?.contentOrNull?.takeIf { it.isNotBlank() }?.let { Text("${fieldLabel(field)}: ${displayValue(field,it)}", style=MaterialTheme.typography.bodyMedium) } }
    TextButton(onClick={expanded=!expanded}) { Text(if(expanded) "Ocultar información" else if(screen.title=="Mis citas") "Consultar cita" else "Más información") }
    if(expanded) {
        // Explicit field allowlist: never render arbitrary clinical payloads or tokens.
        (listOf("id", "title", "folio", "identifier", "test_code", "measured_at", "display_name", "username", "role", "status", "state", "starts_at", "ends_at", "scheduled_at", "available", "severity", "message", "origin_id", "destination_id") - fields.toSet()).forEach { field ->
            row[field]?.jsonPrimitive?.contentOrNull?.let { Text("${fieldLabel(field)}: ${displayValue(field,it)}", style=MaterialTheme.typography.bodyMedium) }
        }
    }
    return expanded
}
