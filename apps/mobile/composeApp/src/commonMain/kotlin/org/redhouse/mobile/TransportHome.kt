package org.redhouse.mobile

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.launch
import kotlinx.serialization.json.*

/**
 * Órdenes asignadas al transportista.
 *
 * `home=true` es el Inicio: la orden activa arriba con su acción principal (Recolectar, Iniciar traslado o
 * Entregar), atajos de escaneo, incidencia y mapas, y debajo las demás órdenes. `home=false` es la pestaña
 * «Traslados»: la lista completa con estado visible y paginación. [onOpen] recibe el id y el paso con el que
 * se abre la tarea (0 detalle, 1 transferencia, 2 incidencia; ver [TransportScreen]).
 */
@Composable fun TransportOrders(repository: MobileRepository, queue: ObservationQueue, home: Boolean, onOpen: (String, Int) -> Unit, onPending: () -> Unit, onSummary: () -> Unit = {}) {
    val scope = rememberCoroutineScope()
    val openInMaps = rememberOpenInMaps()
    var rows by remember { mutableStateOf<List<JsonObject>>(emptyList()) }
    var page by remember { mutableIntStateOf(1) }
    var loaded by remember { mutableStateOf(false) }
    var busy by remember { mutableStateOf(true) }
    var message by remember { mutableStateOf("") }
    val revision by queue.changes.collectAsState()
    val saved = remember(revision) { queue.entries() }
    val waiting = saved.count { it.text("state") in setOf("PENDING", "SENDING", "UNCERTAIN") }
    fun load(number: Int) {
        busy = true; message = ""
        scope.launch {
            try {
                val data = repository.listPage("transporte", "/api/v1/shipments", number)
                rows = (data["items"] as? JsonArray)?.map { it.jsonObject } ?: emptyList()
                page = number; loaded = true
            } catch (e: CancellationException) { throw e }
            catch (e: Exception) { loaded = false; message = if (e is ApiFailure) e.message.orEmpty() else "No se pudieron consultar tus traslados." }
            finally { busy = false }
        }
    }
    LaunchedEffect(Unit) { load(1) }
    val ordered = orderedShipments(rows)
    val active = if (home) activeShipment(rows) else null
    val rest = if (active == null) ordered else ordered.filter { it !== active }

    if (message.isNotBlank()) Text(message)
    if (busy) LinearProgressIndicator(Modifier.fillMaxWidth())
    if (home) {
        if (active != null) ActiveOrderCard(active, onOpen, openInMaps) { message = it }
        else if (loaded) Card(Modifier.fillMaxWidth()) { Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            Text("Sin traslado activo", style = MaterialTheme.typography.titleMedium)
            Text(ordered.firstOrNull { it.text("status") == "PLANNED" }?.let { "Próximo: ${shipmentTitle(it)} · ${transportWaitingText("PLANNED")}" } ?: "Cuando te asignen una orden aparecerá aquí.")
        } }
        // Pendientes ya no es una pestaña: mientras haya observaciones guardadas (también las que dieron conflicto o fueron rechazadas) queda esta entrada.
        if (saved.isNotEmpty()) Card(Modifier.fillMaxWidth()) { Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            Text(if (waiting > 0) "$waiting por sincronizar" else "Observaciones guardadas", style = MaterialTheme.typography.titleMedium)
            OutlinedButton(onClick = onPending, modifier = Modifier.heightIn(min = 48.dp)) { Text("Ver pendientes") }
        } }
        // Después de la acción principal y de los pendientes: la tarjeta de resumen nunca desplaza el traslado activo.
        TransportSummaryCard(repository, onSummary)
        if (rest.isNotEmpty()) Text("Otras órdenes", style = MaterialTheme.typography.titleMedium)
    }
    if (!home && loaded && rows.isEmpty() && !busy) Text("No tienes traslados asignados.")
    (if (home) rest.take(5) else rest).forEach { OrderCard(it, onOpen) }
    if (!home) Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        OutlinedButton(enabled = !busy && page > 1, onClick = { load(page - 1) }) { Text("Anterior") }
        OutlinedButton(enabled = !busy && rows.size == 20, onClick = { load(page + 1) }) { Text("Siguiente") }
    }
    TextButton(enabled = !busy, onClick = { load(page) }, modifier = Modifier.heightIn(min = 48.dp)) { Text("Actualizar") }
}

private fun shipmentTitle(row: JsonObject) = row.text("reference").ifBlank { row.text("folio") }.ifBlank { "Traslado ${row.text("id").take(8)}" }
private fun shipmentRoute(row: JsonObject): String {
    val origin = row.text("origin_name"); val destination = row.text("destination_name")
    return if (origin.isNotBlank() && destination.isNotBlank()) "$origin → $destination" else ""
}

@Composable private fun ActiveOrderCard(row: JsonObject, onOpen: (String, Int) -> Unit, openInMaps: (MapTarget) -> Boolean, onMessage: (String) -> Unit) {
    val status = row.text("status")
    val step = transportStep(status) ?: return
    val id = row.text("id")
    val place = mapsPlaceName(status, row.text("origin_name"), row.text("destination_name"))
    Card(Modifier.fillMaxWidth(), colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer, contentColor = MaterialTheme.colorScheme.onPrimaryContainer)) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Text("Traslado activo", style = MaterialTheme.typography.labelLarge)
                StatusChip(status)
            }
            Text(shipmentTitle(row), style = MaterialTheme.typography.titleLarge)
            shipmentRoute(row).takeIf { it.isNotBlank() }?.let { Text(it) }
            StageTracker(status)
            Button(onClick = { onOpen(id, 1) }, modifier = Modifier.fillMaxWidth().heightIn(min = 56.dp)) { Text(step.label, style = MaterialTheme.typography.titleMedium) }
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                if (step.verifiesUnit) OutlinedButton(onClick = { onOpen(id, 1) }, modifier = Modifier.weight(1f).heightIn(min = 48.dp)) { Text("Escanear") }
                OutlinedButton(onClick = { onOpen(id, 2) }, modifier = Modifier.weight(1f).heightIn(min = 48.dp)) { Text("Incidencia") }
                if (place.isNotBlank()) OutlinedButton(onClick = { if (!openInMaps(MapTarget(null, null, place))) onMessage("No hay una app de mapas disponible en este teléfono.") }, modifier = Modifier.weight(1f).heightIn(min = 48.dp)) { Text("Mapas") }
            }
            TextButton(onClick = { onOpen(id, 0) }, modifier = Modifier.heightIn(min = 48.dp)) { Text("Ver detalle del traslado") }
        }
    }
}

@Composable private fun OrderCard(row: JsonObject, onOpen: (String, Int) -> Unit) {
    val status = row.text("status")
    Card(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Text(shipmentTitle(row), style = MaterialTheme.typography.titleMedium, modifier = Modifier.weight(1f))
                StatusChip(status)
            }
            shipmentRoute(row).takeIf { it.isNotBlank() }?.let { Text(it) }
            row.text("departure_at").takeIf { it.isNotBlank() }?.let { Text("Salida: ${displayBriefDate(it)}", style = MaterialTheme.typography.bodyMedium) }
            if (transportStep(status) == null) Text(transportWaitingText(status), style = MaterialTheme.typography.bodyMedium)
            TextButton(onClick = { onOpen(row.text("id"), 0) }, modifier = Modifier.heightIn(min = 48.dp)) { Text("Abrir traslado") }
        }
    }
}
