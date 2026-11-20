package org.redhouse.mobile

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import io.ktor.client.call.body
import io.ktor.client.request.*
import io.ktor.client.statement.*
import io.ktor.http.*
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.launch
import kotlinx.datetime.Instant
import kotlinx.serialization.json.*
import kotlin.time.Duration.Companion.days

/*
 * Hueco H3: resumen de tareas, indicadores y reportes de traslados del perfil TRANSPORT.
 *
 * Antes vivían en la consola de escritorio (`/api/v1/summary`, `/api/v1/portal-metrics` y trabajos de
 * exportación `SHIPMENTS`). Aquí se consumen los mismos endpoints sin cambiar contratos: el servidor ya
 * acota los tres a los traslados asignados a la cuenta (ver apps/services/tests/test_transporte_resumen.py).
 * Los reportes se piden en CSV, se verifican contra el hash que publica Documentos y se muestran en pantalla;
 * «Compartir» entrega el mismo CSV al selector del sistema (Android: Intent; iOS: UIActivityViewController).
 */

// ---------------------------------------------------------------- lógica pura (probada en commonTest)

/**
 * Contadores del resumen. Los estados se agrupan igual que las etapas del recorrido de la app.
 * No hay contador de incidencias: en el servidor una incidencia es una transición que NO cambia el estado del
 * traslado (ms_transporte/routes.py: `status = row["status"] if state == "INCIDENT"`), así que `/summary` nunca
 * devuelve el estado INCIDENT. Por si algún día lo hiciera, se cuenta como «En curso» para que no se pierda.
 */
internal data class SummaryCounts(val pending: Int, val inProgress: Int, val delivered: Int, val closed: Int, val total: Int)

internal fun summaryCounts(data: JsonObject): SummaryCounts {
    val statuses = data["statuses"] as? JsonArray ?: throw ApiFailure(502, "response_contract")
    val byStatus = HashMap<String, Int>()
    statuses.forEach {
        val row = it as? JsonObject ?: throw ApiFailure(502, "response_contract")
        val value = (row["value"] as? JsonPrimitive)?.intOrNull ?: throw ApiFailure(502, "response_contract")
        if (value < 0) throw ApiFailure(502, "response_contract")
        byStatus[row.text("status")] = (byStatus[row.text("status")] ?: 0) + value
    }
    fun sum(vararg names: String) = names.sumOf { byStatus[it] ?: 0 }
    val total = (data["total"] as? JsonPrimitive)?.intOrNull ?: byStatus.values.sum()
    return SummaryCounts(sum("PLANNED", "PREPARED"), sum("COLLECTED", "IN_TRANSIT", "INCIDENT"), sum("DELIVERED", "ACCEPTED"), sum("CANCELLED", "REJECTED"), total)
}

internal data class MetricPoint(val label: String, val value: Double?)
internal data class MetricSeries(val title: String, val denominator: Int, val unit: String, val points: List<MetricPoint>)

/** Indicadores que daba el escritorio. La cobertura por destino llega con identificadores internos: se resume en un conteo. */
internal fun metricSeries(data: JsonObject): List<MetricSeries> {
    val series = data["series"] as? JsonArray ?: throw ApiFailure(502, "response_contract")
    return series.map { element ->
        val row = element as? JsonObject ?: throw ApiFailure(502, "response_contract")
        val title = row.text("title")
        val denominator = (row["denominator"] as? JsonPrimitive)?.intOrNull ?: 0
        val unit = row.text("unit").ifBlank { "registros" }
        val raw = (row["values"] as? JsonArray).orEmpty().map {
            val point = it as? JsonObject ?: throw ApiFailure(502, "response_contract")
            MetricPoint(point.text("label"), (point["value"] as? JsonPrimitive)?.doubleOrNull)
        }
        if (title == "Cobertura por destino") MetricSeries(title, denominator, "destinos", listOf(MetricPoint("Destinos distintos", raw.size.toDouble())))
        else MetricSeries(title, denominator, unit, raw.map { it.copy(label = displayValue("status", it.label)) })
    }
}

internal fun metricValueText(value: Double?, unit: String): String {
    if (value == null) return "Sin datos"
    val number = if (value == value.toLong().toDouble()) value.toLong().toString() else ((value * 10).toLong() / 10.0).toString()
    return if (unit == "registros" || unit == "destinos") number else "$number $unit"
}

/** Cuerpo para pedir el reporte de traslados propios: 30 días atrás y 30 adelante (salidas programadas), máximo permitido 366. */
internal fun shipmentReportBody(now: Instant): JsonObject = buildJsonObject {
    put("report", "SHIPMENTS"); put("format", "CSV")
    put("from_at", (now - 30.days).toString()); put("until_at", (now + 30.days).toString())
    put("timezone", "America/Monterrey")
}

/** CSV según RFC 4180 (comillas, comas y saltos dentro de comillas); descarta la marca BOM que antepone el servidor. */
internal fun parseCsv(text: String): List<List<String>> {
    val rows = ArrayList<List<String>>(); var row = ArrayList<String>(); val cell = StringBuilder(); var quoted = false; var i = 0
    val input = text.removePrefix("\uFEFF")
    fun endCell() { row.add(cell.toString()); cell.clear() }
    fun endRow() { endCell(); if (!(row.size == 1 && row[0].isEmpty())) rows.add(row); row = ArrayList() }
    while (i < input.length) {
        val c = input[i]
        when {
            quoted && c == '"' && input.getOrNull(i + 1) == '"' -> { cell.append('"'); i++ }
            c == '"' -> quoted = !quoted
            quoted -> cell.append(c)
            c == ',' -> endCell()
            c == '\r' -> {}
            c == '\n' -> endRow()
            else -> cell.append(c)
        }
        i++
    }
    if (cell.isNotEmpty() || row.isNotEmpty()) endRow()
    return rows
}

internal data class ReportLine(val title: String, val status: String, val departure: String, val eta: String)

/** Filas del reporte SHIPMENTS por nombre de columna (el servidor ordena las columnas alfabéticamente). */
internal fun shipmentReportLines(csv: String): List<ReportLine> {
    val table = parseCsv(csv)
    val header = table.firstOrNull() ?: return emptyList()
    if ("sin_resultados" in header) return emptyList()
    fun column(name: String) = header.indexOf(name)
    val id = column("id"); val status = column("status")
    if (id < 0 || status < 0) return emptyList()
    fun List<String>.at(index: Int) = if (index >= 0) getOrNull(index).orEmpty().takeIf { it != "Sin dato" }.orEmpty() else ""
    return table.drop(1).map { row ->
        val folio = row.at(column("folio"))
        ReportLine(folio.ifBlank { "Traslado ${row.at(id).take(8)}" }, row.at(status), row.at(column("departure_at")), row.at(column("eta")))
    }
}

internal fun reportStatusText(status: String) = when (status) {
    "PENDING" -> "En preparación"
    "COMPLETE" -> "Listo"
    "RETRYABLE", "FAILED" -> "No se pudo generar; solicita otro"
    else -> status
}

// ---------------------------------------------------------------- acceso al servidor (extensiones del repositorio)

private const val MAX_REPORT_BYTES = 2_000_000
/** Tope de texto que se entrega al selector del sistema: un Intent grande (>~1 MB) lanza TransactionTooLargeException en Android. */
internal const val MAX_SHARE_CHARS = 400_000

internal suspend fun MobileRepository.transportSummary(): JsonObject = session.request("transporte", "/api/v1/summary")
internal suspend fun MobileRepository.transportMetrics(): JsonObject = session.request("transporte", "/api/v1/portal-metrics")
internal suspend fun MobileRepository.shipmentReportJobs(): List<JsonObject> =
    (listPage("documentos", "/api/v1/export-jobs?report=SHIPMENTS&format=CSV", 1)["items"] as? JsonArray).orEmpty().map { it.jsonObject }
/** Cada pulsación es una solicitud nueva con su propia llave; un reporte duplicado es inofensivo (solo lectura). */
internal suspend fun MobileRepository.requestShipmentReport(now: Instant): JsonObject =
    session.request("documentos", "/api/v1/export-jobs", HttpMethod.Post, shipmentReportBody(now), newId())

/**
 * Descarga el CSV de un reporte listo. Repite la cadena del escritorio: el trabajo debe estar COMPLETE, el
 * documento VERIFIED y sin amenazas, la URL firmada debe ser de este gateway o del bucket fijado y el SHA-256
 * de los bytes debe coincidir con el publicado. Máximo 2 MB.
 */
internal suspend fun MobileRepository.downloadReportCsv(jobId: String): String {
    val job = session.request("documentos", "/api/v1/export-jobs/$jobId")
    val fileId = job.text("file_id")
    if (job.text("status") != "COMPLETE" || fileId.isBlank() || job.text("format") != "CSV") throw ApiFailure(409, "report_not_ready")
    val meta = session.request("documentos", "/api/v1/documents/$fileId/verified")
    if (meta.text("analysis") != "CLEAN" || meta.text("file_status") != "VERIFIED" || meta.text("sha256").isBlank()) throw ApiFailure(409, "report_not_verified")
    val url = session.request("documentos", "/api/v1/files/$fileId/download").text("download_url")
    storageTarget(url, session.api.bases.getValue("documentos"))
    val response = session.api.client.get(url)
    if (!response.status.isSuccess()) throw ApiFailure(503, "download")
    // Se rechaza por la cabecera antes de leer el cuerpo; la comprobación de abajo cubre respuestas sin longitud.
    if ((response.contentLength() ?: 0L) > MAX_REPORT_BYTES) throw ApiFailure(502, "report_integrity")
    val bytes = response.body<ByteArray>()
    if (bytes.size > MAX_REPORT_BYTES || sha256(bytes) != meta.text("sha256")) throw ApiFailure(502, "report_integrity")
    return bytes.decodeToString()
}

/** Entrega el texto al selector del sistema para compartir o abrir con otra app. */
@Composable expect fun rememberReportShare(): (String) -> Unit

// ---------------------------------------------------------------- pantallas

private fun failureText(e: Exception, fallback: String) = if (e is ApiFailure) e.message.orEmpty() else fallback

@Composable private fun Counter(label: String, value: Int, modifier: Modifier = Modifier) {
    Column(modifier.semantics(mergeDescendants = true) { contentDescription = "$label: $value" }) {
        Text(value.toString(), style = MaterialTheme.typography.headlineSmall)
        Text(label, style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
    }
}

@Composable private fun CountersRow(counts: SummaryCounts) {
    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        Counter("Pendientes", counts.pending, Modifier.weight(1f))
        Counter("En curso", counts.inProgress, Modifier.weight(1f))
        Counter("Entregadas", counts.delivered, Modifier.weight(1f))
        Counter("Canceladas", counts.closed, Modifier.weight(1f))
    }
}

/** Tarjeta compacta del Inicio: contadores y enlace a la sección completa. Un fallo aquí no estorba al resto del Inicio. */
@Composable fun TransportSummaryCard(repository: MobileRepository, onOpen: () -> Unit) {
    var counts by remember { mutableStateOf<SummaryCounts?>(null) }
    var error by remember { mutableStateOf("") }
    var busy by remember { mutableStateOf(true) }
    val scope = rememberCoroutineScope()
    fun load() {
        busy = true; error = ""
        scope.launch {
            try { counts = summaryCounts(repository.transportSummary()) }
            catch (e: CancellationException) { throw e }
            catch (e: Exception) { error = failureText(e, "No se pudo consultar el resumen.") }
            finally { busy = false }
        }
    }
    LaunchedEffect(Unit) { load() }
    Card(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text("Resumen de tus traslados", style = MaterialTheme.typography.titleMedium)
            val current = counts
            when {
                busy && current == null -> { Text("Cargando resumen…"); LinearProgressIndicator(Modifier.fillMaxWidth()) }
                error.isNotBlank() -> { Text(error); TextButton(onClick = { load() }, modifier = Modifier.heightIn(min = 48.dp)) { Text("Reintentar") } }
                current != null && current.total == 0 -> Text("Aún no tienes traslados asignados.")
                current != null -> CountersRow(current)
            }
            TextButton(onClick = onOpen, modifier = Modifier.heightIn(min = 48.dp)) { Text("Ver resumen") }
        }
    }
}

/** Sección «Resumen»: tareas, indicadores y reportes de traslados propios. */
@Composable fun TransportSummaryScreen(repository: MobileRepository) {
    val scope = rememberCoroutineScope()
    val share = rememberReportShare()
    var counts by remember { mutableStateOf<SummaryCounts?>(null) }
    var metrics by remember { mutableStateOf<List<MetricSeries>?>(null) }
    var jobs by remember { mutableStateOf<List<JsonObject>?>(null) }
    var summaryError by remember { mutableStateOf("") }
    var metricsError by remember { mutableStateOf("") }
    var jobsError by remember { mutableStateOf("") }
    var busy by remember { mutableStateOf(true) }
    var message by remember { mutableStateOf("") }
    var opened by remember { mutableStateOf<Pair<String, String>?>(null) } // id del trabajo, CSV
    fun load() {
        busy = true; summaryError = ""; metricsError = ""; jobsError = ""
        scope.launch {
            try {
                try { counts = summaryCounts(repository.transportSummary()) } catch (e: CancellationException) { throw e } catch (e: Exception) { summaryError = failureText(e, "No se pudo consultar el resumen.") }
                try { metrics = metricSeries(repository.transportMetrics()) } catch (e: CancellationException) { throw e } catch (e: Exception) { metricsError = failureText(e, "No se pudieron consultar los indicadores.") }
                try { jobs = repository.shipmentReportJobs() } catch (e: CancellationException) { throw e } catch (e: Exception) { jobsError = failureText(e, "No se pudieron consultar los reportes.") }
            } finally { busy = false }
        }
    }
    LaunchedEffect(Unit) { load() }
    if (busy) LinearProgressIndicator(Modifier.fillMaxWidth())
    if (message.isNotBlank()) Text(message)

    Text("Tareas", style = MaterialTheme.typography.titleMedium)
    val c = counts
    when {
        summaryError.isNotBlank() -> Text(summaryError)
        c == null -> if (busy) Text("Cargando…")
        c.total == 0 -> Text("Aún no tienes traslados asignados.")
        else -> Card(Modifier.fillMaxWidth()) { Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            CountersRow(c)
            Text("Total asignado: ${c.total}", style = MaterialTheme.typography.bodyMedium)
        } }
    }

    Text("Indicadores", style = MaterialTheme.typography.titleMedium)
    val m = metrics
    when {
        metricsError.isNotBlank() -> Text(metricsError)
        m == null -> if (busy) Text("Cargando…")
        m.isEmpty() -> Text("Sin indicadores para el periodo.")
        else -> {
            Text("Últimos 30 días, solo tus traslados.", style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
            m.forEach { series ->
                Card(Modifier.fillMaxWidth()) { Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    Text(series.title, style = MaterialTheme.typography.titleSmall)
                    if (series.points.isEmpty() || series.denominator == 0) Text("Sin datos en el periodo.")
                    else series.points.forEach { Text("${it.label}: ${metricValueText(it.value, series.unit)}") }
                } }
            }
        }
    }

    Text("Reportes", style = MaterialTheme.typography.titleMedium)
    Text("Reporte de tus traslados en formato CSV.", style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
    Button(enabled = !busy, modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp), onClick = {
        busy = true; message = ""
        scope.launch {
            try { repository.requestShipmentReport(kotlinx.datetime.Clock.System.now()); message = "Reporte solicitado. Actualiza en unos momentos para verlo."; jobs = repository.shipmentReportJobs() }
            catch (e: CancellationException) { throw e }
            catch (e: Exception) { message = failureText(e, "No se pudo solicitar el reporte.") }
            finally { busy = false }
        }
    }) { Text("Solicitar reporte de traslados") }
    val list = jobs
    when {
        jobsError.isNotBlank() -> Text(jobsError)
        list == null -> if (busy) Text("Cargando…")
        list.isEmpty() -> Text("Aún no has solicitado reportes.")
        else -> list.forEach { job ->
            Card(Modifier.fillMaxWidth()) { Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                Text("Reporte de traslados", style = MaterialTheme.typography.titleSmall)
                Text("Solicitado: ${displayBriefDate(job.text("created_at"))}")
                Text(reportStatusText(job.text("status")))
                if (job.text("status") == "COMPLETE") TextButton(enabled = !busy, modifier = Modifier.heightIn(min = 48.dp), onClick = {
                    busy = true; message = ""
                    scope.launch {
                        try { opened = job.text("id") to repository.downloadReportCsv(job.text("id")) }
                        catch (e: CancellationException) { throw e }
                        catch (e: Exception) { message = failureText(e, "No se pudo abrir el reporte.") }
                        finally { busy = false }
                    }
                }) { Text("Abrir reporte") }
            } }
        }
    }
    opened?.let { (_, csv) ->
        val lines = remember(csv) { shipmentReportLines(csv) }
        Text("Reporte abierto", style = MaterialTheme.typography.titleMedium)
        if (lines.isEmpty()) Text("El reporte no tiene traslados en el periodo.")
        lines.take(100).forEach { line ->
            Card(Modifier.fillMaxWidth()) { Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(2.dp)) {
                Text(line.title, style = MaterialTheme.typography.titleSmall)
                Text("Estado: ${displayValue("status", line.status)}")
                if (line.departure.isNotBlank()) Text("Salida: ${displayBriefDate(line.departure)}")
                if (line.eta.isNotBlank()) Text("Llegada prevista: ${displayBriefDate(line.eta)}")
            } }
        }
        if (lines.size > 100) Text("Se muestran 100 de ${lines.size}; comparte el CSV para verlos todos.")
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            OutlinedButton(modifier = Modifier.heightIn(min = 48.dp), onClick = {
                if (csv.length > MAX_SHARE_CHARS) message = "El reporte es demasiado grande para compartirlo. Solicita uno nuevo."
                else share(csv.removePrefix("\uFEFF"))
            }) { Text("Compartir CSV") }
            TextButton(modifier = Modifier.heightIn(min = 48.dp), onClick = { opened = null }) { Text("Cerrar reporte") }
        }
    }
    TextButton(enabled = !busy, onClick = { load() }, modifier = Modifier.heightIn(min = 48.dp)) { Text("Actualizar") }
}
