package org.redhouse.mobile

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp

/** Abre el lugar en la app de mapas del sistema (Android: geo:; iOS: Apple Maps). Devuelve false si no hay app que lo atienda. */
@Composable expect fun rememberOpenInMaps(): (MapTarget) -> Boolean

/** Etiqueta de estado con color por tono; el texto siempre dice el estado, el color solo refuerza. */
@Composable fun StatusChip(status: String, modifier: Modifier = Modifier) {
    val (container, content) = when (statusTone(status)) {
        StatusTone.Done -> Color(0xFFDCFCE7) to Color(0xFF14532D)
        StatusTone.Active -> MaterialTheme.colorScheme.secondaryContainer to MaterialTheme.colorScheme.onSecondaryContainer
        StatusTone.Waiting -> MaterialTheme.colorScheme.tertiaryContainer to MaterialTheme.colorScheme.onTertiaryContainer
        StatusTone.Alert -> MaterialTheme.colorScheme.errorContainer to MaterialTheme.colorScheme.onErrorContainer
        StatusTone.Neutral -> MaterialTheme.colorScheme.surfaceVariant to MaterialTheme.colorScheme.onSurfaceVariant
    }
    Surface(color = container, contentColor = content, shape = RoundedCornerShape(50), modifier = modifier) {
        Text(displayValue("status", status), style = MaterialTheme.typography.labelMedium, modifier = Modifier.padding(horizontal = 10.dp, vertical = 4.dp))
    }
}

/** Seguimiento por etapas: Preparado, Recolectado, En tránsito, Entregado. Las cumplidas llevan ✓; la actual va resaltada. */
@Composable fun StageTracker(status: String, modifier: Modifier = Modifier) {
    val reached = transportStageIndex(status)
    val summary = if (reached < 0) "Traslado sin etapas cumplidas" else "Etapa ${reached + 1} de ${transportStages.size}: ${displayValue("status", transportStages[reached])}"
    Row(modifier.fillMaxWidth().semantics(mergeDescendants = true) { contentDescription = summary }, horizontalArrangement = Arrangement.SpaceBetween) {
        transportStages.forEachIndexed { index, stage ->
            val done = index <= reached
            val current = index == reached
            Column(Modifier.weight(1f), horizontalAlignment = Alignment.CenterHorizontally) {
                Box(Modifier.size(28.dp).background(if (done) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.surfaceVariant, CircleShape), contentAlignment = Alignment.Center) {
                    Text(if (done) "✓" else "${index + 1}", color = if (done) MaterialTheme.colorScheme.onPrimary else MaterialTheme.colorScheme.onSurfaceVariant, style = MaterialTheme.typography.labelMedium)
                }
                Text(displayValue("status", stage), style = if (current) MaterialTheme.typography.labelMedium else MaterialTheme.typography.labelSmall,
                    color = if (current) MaterialTheme.colorScheme.onSurface else MaterialTheme.colorScheme.onSurfaceVariant, textAlign = TextAlign.Center)
            }
        }
    }
}
