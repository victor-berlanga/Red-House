package org.redhouse.mobile

import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.liveRegion
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import io.ktor.client.plugins.onUpload
import io.ktor.client.request.header
import io.ktor.client.request.put
import io.ktor.client.request.setBody
import io.ktor.http.HttpMethod
import io.ktor.http.Url
import io.ktor.http.isSuccess
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.launch
import kotlinx.datetime.Instant
import kotlinx.serialization.json.*

/*
 * Huecos H1 y H2 del donante en el móvil (Android e iOS comparten este archivo).
 *
 * H1. «Evaluaciones humanas»: salen de GET /api/v1/donors/{id} (ms_donantes, campo `reviews`). El servidor
 *     devuelve el expediente solo si pertenece al donante autenticado (donor_access: tenant + user_id).
 * H2. Consentimiento firmado: flujo de ms_documentos igual al del portal — POST /api/v1/documents (metadatos y
 *     URL firmada), PUT al almacenamiento privado, POST /api/v1/files/{id}/verify (tamaño, MIME, firma y
 *     antivirus). El estado sale de GET /api/v1/documents/{id}/status. Sujeto DONOR, categoría CONSENT.
 *     Desde el móvil solo se envía JPEG tomado con la cámara (misma ruta que la evidencia de traslados);
 *     el servidor además acepta PNG y PDF, hasta 10 MiB.
 */

// ---------------------------------------------------------------- H1: evaluaciones humanas

/** Una evaluación humana del expediente: fecha, resultado y nota visible para el donante. */
data class DonorReview(val id: String, val decision: String, val note: String, val createdAt: String)

/**
 * Evaluaciones del campo `reviews` de GET /api/v1/donors/{id}, la más reciente primero.
 * Devuelve null si el campo no es una lista (respuesta fuera de contrato: se muestra como error, no como vacío).
 * `actor_id` (quién evaluó) no se muestra: el portal tampoco lo mostraba al donante en la nota.
 */
fun parseDonorReviews(donor: JsonObject): List<DonorReview>? {
    val rows = donor["reviews"] as? JsonArray ?: return null
    fun millis(value: String) = runCatching { Instant.parse(value).toEpochMilliseconds() }.getOrNull() ?: Long.MIN_VALUE
    return rows.mapNotNull { it as? JsonObject }
        .filter { it.text("decision").isNotBlank() }
        .map { DonorReview(it.text("id"), it.text("decision"), it.text("reason"), it.text("created_at")) }
        .sortedByDescending { millis(it.createdAt) }
}

/** Estados de la sección de evaluaciones: cargando, error, vacío o con datos. */
sealed interface ReviewsUi {
    data object Loading : ReviewsUi
    data class Error(val message: String) : ReviewsUi
    data object Empty : ReviewsUi
    data class Loaded(val rows: List<DonorReview>) : ReviewsUi
}

fun reviewsUi(loading: Boolean, error: String?, rows: List<DonorReview>?): ReviewsUi = when {
    loading -> ReviewsUi.Loading
    error != null -> ReviewsUi.Error(error)
    rows == null -> ReviewsUi.Error("No se pudieron consultar tus evaluaciones.")
    rows.isEmpty() -> ReviewsUi.Empty
    else -> ReviewsUi.Loaded(rows)
}

private val uuidPattern = Regex("[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")

/** Expediente propio con sus evaluaciones. Si el expediente no es del donante, el servidor responde 403. */
suspend fun MobileRepository.loadDonorReviews(donorId: String): List<DonorReview> {
    require(donorId.matches(uuidPattern)) { "Expediente no válido." }
    return parseDonorReviews(session.request("donantes", "/api/v1/donors/$donorId"))
        ?: throw ApiFailure(502, "response_contract")
}

// ---------------------------------------------------------------- H2: consentimiento firmado

/** Estado del documento de consentimiento tal como lo ve el donante. */
enum class ConsentDocStatus { Unknown, Missing, InReview, Verified, Rejected, Failed }

data class ConsentDoc(val status: ConsentDocStatus, val id: String = "", val version: Int = 0, val createdAt: String = "")

/** Tamaño máximo y tipo que valida el servidor (Upload en document_contracts.py); desde el móvil solo JPEG. */
const val CONSENT_MAX_BYTES = 10_485_760
const val CONSENT_MIME = "image/jpeg"

/** La versión vigente es la de mayor `version` entre los documentos CONSENT del donante. */
fun latestConsentDocument(items: List<JsonObject>): JsonObject? =
    items.filter { it.text("category") == "CONSENT" && it.text("subject_kind") == "DONOR" }
        .maxByOrNull { (it["version"] as? JsonPrimitive)?.intOrNull ?: 0 }

/**
 * Estado a partir de `file_status` (PENDING, VERIFIED, REJECTED, ERROR, MISSING) y `analysis`
 * (PENDING, CLEAN, INFECTED, ERROR) de GET /api/v1/documents/{id}/status. Lo que no se reconoce queda
 * como Unknown: no se adivina un estado.
 */
fun consentDocFromStatus(meta: JsonObject, status: JsonObject): ConsentDoc {
    val file = status.text("file_status")
    val analysis = status.text("analysis")
    val state = when {
        file == "REJECTED" || analysis == "INFECTED" -> ConsentDocStatus.Rejected
        file == "ERROR" || file == "MISSING" || analysis == "ERROR" -> ConsentDocStatus.Failed
        file == "VERIFIED" && analysis == "CLEAN" -> ConsentDocStatus.Verified
        file == "PENDING" || (file == "VERIFIED" && analysis == "PENDING") -> ConsentDocStatus.InReview
        else -> ConsentDocStatus.Unknown
    }
    return ConsentDoc(state, meta.text("id"), (meta["version"] as? JsonPrimitive)?.intOrNull ?: 0, meta.text("created_at"))
}

/** Falta cargar (o volver a cargar) el consentimiento: sin documento, rechazado o con fallo de verificación. */
fun consentNeedsUpload(doc: ConsentDoc) = doc.status in setOf(ConsentDocStatus.Missing, ConsentDocStatus.Rejected, ConsentDocStatus.Failed)

/**
 * Paso de Inicio. Solo se evalúa con expediente propio ya cargado. Sustituye a «Buscar horarios» (la cita
 * próxima, el registro pendiente y los errores de consulta conservan su lugar); con cita próxima, Inicio
 * muestra además un acceso secundario (ver [consentReminder]).
 */
fun donorNextStepWithConsent(base: DonorStep, hasRecord: Boolean, doc: ConsentDoc): DonorStep =
    if (hasRecord && base.kind == DonorStepKind.Book && consentNeedsUpload(doc))
        DonorStep(DonorStepKind.Consent, consentStepTitle(doc), "Cargar documento")
    else base

/** Recordatorio secundario cuando la acción principal es otra (por ejemplo, la cita próxima). */
fun consentReminder(base: DonorStep, hasRecord: Boolean, doc: ConsentDoc): String? =
    if (hasRecord && base.kind == DonorStepKind.Appointment && consentNeedsUpload(doc)) consentStepTitle(doc) else null

private fun consentStepTitle(doc: ConsentDoc) =
    if (doc.status == ConsentDocStatus.Missing) "Falta tu consentimiento firmado" else "Vuelve a cargar tu consentimiento"

fun consentStatusLabel(status: ConsentDocStatus) = when (status) {
    ConsentDocStatus.Unknown -> "Sin comprobar"
    ConsentDocStatus.Missing -> "Sin documento"
    ConsentDocStatus.InReview -> "En revisión"
    ConsentDocStatus.Verified -> "Verificado"
    ConsentDocStatus.Rejected -> "Rechazado"
    ConsentDocStatus.Failed -> "Sin verificar"
}

/** Texto que ayuda a decidir el siguiente paso; solo cuando el estado lo necesita. */
fun consentStatusHelp(status: ConsentDocStatus) = when (status) {
    ConsentDocStatus.Unknown -> "No fue posible confirmar el estado. Actualiza antes de cargar otro documento."
    ConsentDocStatus.Missing -> "Fotografía tu consentimiento firmado y cárgalo. Tu institución lo revisará."
    ConsentDocStatus.InReview -> "Se está analizando. Vuelve a consultar en unos minutos."
    ConsentDocStatus.Verified -> "Tu institución ya cuenta con tu consentimiento firmado."
    ConsentDocStatus.Rejected -> "El archivo no pasó la revisión. Toma otra fotografía clara y vuelve a cargarla."
    ConsentDocStatus.Failed -> "No se pudo verificar el archivo. Vuelve a cargarlo."
}

/** Mensaje de error de la carga: lo que la persona puede hacer, sin detalles internos. */
fun consentUploadError(e: Exception): String = when {
    e is ApiFailure && e.status == 412 -> "Tu documento cambió mientras lo cargabas. Actualiza e inténtalo de nuevo."
    e is ApiFailure && e.status == 422 -> "El servidor no aceptó el archivo. Toma otra fotografía (JPEG de hasta 10 MiB)."
    e is ApiFailure && e.status == 403 -> "No tienes permiso para cargar documentos en este expediente."
    e is ApiFailure && e.status == 409 -> "El documento aún no se puede verificar. Inténtalo de nuevo en unos minutos."
    e is ApiFailure -> e.message.orEmpty()
    e is IllegalArgumentException -> e.message.orEmpty()
    else -> "Sin confirmación de la carga. Pulsa de nuevo «Cargar documento»; no se duplicará."
}

/** Etapas visibles de la carga. */
enum class ConsentUploadStage(val label: String) {
    Preparing("Preparando carga…"), Uploading("Subiendo archivo…"), Verifying("Verificando y analizando…")
}

/** Texto de progreso: etapa X de 3 y, al subir, el porcentaje real de bytes enviados. */
fun consentProgressText(stage: ConsentUploadStage, fraction: Float?): String {
    val percent = if (stage == ConsentUploadStage.Uploading && fraction != null) " ${(fraction.coerceIn(0f, 1f) * 100).toInt()} %" else ""
    return "Paso ${stage.ordinal + 1} de ${ConsentUploadStage.entries.size} · ${stage.label}$percent"
}

/**
 * Lista el documento CONSENT vigente del donante y consulta su estado. `Missing` solo si el servidor
 * confirma que no hay documentos; si falla la consulta se propaga el error (nunca se devuelve Missing).
 */
suspend fun MobileRepository.loadConsentDocument(donorId: String): ConsentDoc {
    require(donorId.matches(uuidPattern)) { "Expediente no válido." }
    val page = checkedPage(listPage("documentos", "/api/v1/documents?subject_kind=DONOR&subject_id=$donorId&category=CONSENT", 1), 1)
    val latest = latestConsentDocument((page["items"] as JsonArray).map { it.jsonObject }) ?: return ConsentDoc(ConsentDocStatus.Missing)
    require(latest.text("id").matches(uuidPattern)) { "Documento no válido." }
    return consentDocFromStatus(latest, session.request("documentos", "/api/v1/documents/${latest.text("id")}/status"))
}

/**
 * Prepara, sube y verifica un consentimiento (JPEG). La clave de idempotencia se guarda en el diario
 * cifrado por donante y huella del archivo: tras perder la respuesta, repetir la carga no duplica el
 * documento ni vuelve a subir un archivo ya verificado. La clave se libera con una respuesta terminal.
 * [supersedes] es el documento vigente cuando se reemplaza uno rechazado o fallido.
 */
suspend fun MobileRepository.uploadConsentDocument(
    donorId: String, bytes: ByteArray, supersedes: String? = null,
    onStage: (ConsentUploadStage, Float?) -> Unit = { _, _ -> }
): JsonObject {
    require(donorId.matches(uuidPattern)) { "Expediente no válido." }
    require(bytes.size in 1..CONSENT_MAX_BYTES) { "El archivo debe pesar entre 1 byte y 10 MiB." }
    val digest = sha256(bytes)
    val name = "consent:$donorId:$digest"
    val key = journal.value(name)?.jsonPrimitive?.content ?: newId().also { journal.put(name, JsonPrimitive(it)) }
    try {
        onStage(ConsentUploadStage.Preparing, null)
        val prepared = session.request("documentos", "/api/v1/documents", HttpMethod.Post, buildJsonObject {
            put("subject_kind", "DONOR");put("subject_id", donorId);put("category", "CONSENT")
            if (supersedes != null) put("supersedes", supersedes)
            put("policy_reference", "Consentimiento firmado cargado desde la app móvil")
            put("mime_type", CONSENT_MIME);put("size", bytes.size);put("sha256", digest)
        }, key)
        val id = prepared.text("id")
        require(id.matches(uuidPattern)) { "Respuesta de preparación no válida." }
        val local = storageTarget(prepared.text("upload_url"), session.api.bases.getValue("documentos"))
        val headers = storageHeaders(prepared.getValue("upload_headers").jsonObject, local)
        onStage(ConsentUploadStage.Uploading, 0f)
        val result = session.api.client.put(Url(prepared.text("upload_url"))) {
            headers.forEach { (k, v) -> header(k, v) }
            setBody(bytes)
            onUpload { sent, total -> if (total > 0) onStage(ConsentUploadStage.Uploading, sent.toFloat() / total) }
        }
        // 412: la carga anterior sí llegó y solo se perdió la respuesta.
        if (!result.status.isSuccess() && result.status.value != 412) throw ApiFailure(503, "upload")
        onStage(ConsentUploadStage.Verifying, null)
        // Preparar y verificar son operaciones distintas del servidor: cada una con su clave estable.
        val verified = session.request("documentos", "/api/v1/files/$id/verify", HttpMethod.Post, key = "$key-verify")
        journal.remove(name)
        return verified
    } catch (e: ApiFailure) {
        // Una respuesta terminal (rechazo, conflicto, sin permiso) no se reintenta con la misma clave.
        if (e.status in setOf(400, 403, 409, 412, 422)) journal.remove(name)
        throw e
    }
}

// ---------------------------------------------------------------- Pantallas

/** Evaluaciones humanas del expediente: fecha, resultado y nota del personal. Lectura propia; no se edita aquí. */
@Composable fun DonorReviewsSection(repository: MobileRepository, donorId: String) {
    var loading by remember(donorId) { mutableStateOf(true) }
    var error by remember(donorId) { mutableStateOf<String?>(null) }
    var rows by remember(donorId) { mutableStateOf<List<DonorReview>?>(null) }
    var attempt by remember(donorId) { mutableIntStateOf(0) }
    LaunchedEffect(donorId, attempt) {
        loading = true;error = null
        try { rows = repository.loadDonorReviews(donorId) }
        catch (e: CancellationException) { throw e }
        catch (e: Exception) { error = if (e is ApiFailure) e.message.orEmpty() else "No se pudieron consultar tus evaluaciones." }
        finally { loading = false }
    }
    Spacer(Modifier.height(12.dp))
    Text("Evaluaciones del personal médico", style = MaterialTheme.typography.titleMedium)
    when (val ui = reviewsUi(loading, error, rows)) {
        ReviewsUi.Loading -> { LinearProgressIndicator(modifier = Modifier.fillMaxWidth()); Text("Consultando tus evaluaciones…", style = MaterialTheme.typography.bodyMedium) }
        is ReviewsUi.Error -> {
            Text(ui.message, color = MaterialTheme.colorScheme.error, modifier = Modifier.semantics { liveRegion = LiveRegionMode.Polite })
            OutlinedButton(onClick = { attempt++ }, modifier = Modifier.heightIn(min = 48.dp)) { Text("Reintentar") }
        }
        ReviewsUi.Empty -> Text("Aún no tienes evaluaciones registradas. Aparecerán aquí cuando el personal médico las registre.", style = MaterialTheme.typography.bodyMedium)
        is ReviewsUi.Loaded -> ui.rows.forEach { review ->
            Column(Modifier.fillMaxWidth().padding(vertical = 6.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    Text(displayBriefDate(review.createdAt), style = MaterialTheme.typography.bodyMedium)
                    StatusChip(review.decision)
                }
                if (review.note.isNotBlank()) Text(review.note, style = MaterialTheme.typography.bodyMedium)
            }
            HorizontalDivider()
        }
    }
    Text("La información registrada requiere evaluación humana autorizada.", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
}

/**
 * Consentimiento firmado: estado vigente, captura con la cámara, vista previa, progreso y resultado.
 * [doc] lo carga DonorScreen (también alimenta el paso de Inicio); [onChanged] pide recargarlo tras cargar.
 */
@Composable fun ConsentDocumentSection(repository: MobileRepository, devices: DeviceAccess, donorId: String, doc: ConsentDoc, onChanged: () -> Unit) {
    val scope = rememberCoroutineScope()
    var photo by remember(donorId) { mutableStateOf<ByteArray?>(null) }
    var stage by remember(donorId) { mutableStateOf<ConsentUploadStage?>(null) }
    var fraction by remember(donorId) { mutableStateOf<Float?>(null) }
    var message by remember(donorId) { mutableStateOf("") }
    val uploading = stage != null
    Spacer(Modifier.height(12.dp))
    Text("Consentimiento firmado", style = MaterialTheme.typography.titleMedium)
    Row(verticalAlignment = androidx.compose.ui.Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        Text("Documento")
        ConsentChip(doc.status)
    }
    if (doc.createdAt.isNotBlank()) Text("Cargado: ${displayBriefDate(doc.createdAt)} · versión ${doc.version}", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
    Text(consentStatusHelp(doc.status), style = MaterialTheme.typography.bodyMedium)
    if (message.isNotBlank()) Text(message, modifier = Modifier.semantics { liveRegion = LiveRegionMode.Polite })
    stage?.let { current ->
        val sent = fraction
        if (current == ConsentUploadStage.Uploading && sent != null) LinearProgressIndicator(progress = { sent.coerceIn(0f, 1f) }, modifier = Modifier.fillMaxWidth())
        else LinearProgressIndicator(modifier = Modifier.fillMaxWidth())
        Text(consentProgressText(current, fraction), style = MaterialTheme.typography.bodyMedium, modifier = Modifier.semantics { liveRegion = LiveRegionMode.Polite })
    }
    val canReplace = doc.status != ConsentDocStatus.Verified && doc.status != ConsentDocStatus.InReview && doc.status != ConsentDocStatus.Unknown
    val label = when {
        doc.status == ConsentDocStatus.Missing -> "Fotografiar consentimiento"
        canReplace -> "Fotografiar de nuevo"
        else -> "Cargar una versión nueva"
    }
    if (photo == null) {
        OutlinedButton(enabled = !uploading, modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp), onClick = {
            devices.photograph { bytes, failure -> photo = bytes; message = failure.orEmpty() }
        }) { Text(label) }
        if (doc.status == ConsentDocStatus.Verified || doc.status == ConsentDocStatus.InReview)
            Text("Solo cárgalo de nuevo si tu institución te lo pide.", style = MaterialTheme.typography.bodySmall)
    }
    photo?.let { bytes ->
        Image(remember(bytes) { imageBitmap(bytes) }, "Vista previa del consentimiento", Modifier.fillMaxWidth().height(180.dp))
        Text("Revisa que el documento se lea completo (${bytes.size / 1024} KB).", style = MaterialTheme.typography.bodySmall)
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Button(enabled = !uploading, onClick = {
                message = "";stage = ConsentUploadStage.Preparing;fraction = null
                scope.launch {
                    try {
                        // Reemplaza solo el documento vigente que ya existe en el servidor.
                        val previous = doc.id.takeIf { it.isNotBlank() }
                        repository.uploadConsentDocument(donorId, bytes, previous) { s, f -> stage = s;fraction = f }
                        photo = null;message = "Documento cargado. Quedó en revisión."
                    } catch (e: CancellationException) { throw e }
                    catch (e: Exception) { message = consentUploadError(e) }
                    finally { stage = null;fraction = null;onChanged() }
                }
            }) { Text("Cargar documento") }
            TextButton(enabled = !uploading, onClick = { photo = null }) { Text("Eliminar foto") }
        }
    }
    if (doc.status == ConsentDocStatus.Unknown || doc.status == ConsentDocStatus.InReview)
        TextButton(enabled = !uploading, onClick = onChanged) { Text("Actualizar estado") }
}

@Composable private fun ConsentChip(status: ConsentDocStatus) {
    val tone = when (status) {
        ConsentDocStatus.Verified -> StatusTone.Done
        ConsentDocStatus.InReview -> StatusTone.Active
        ConsentDocStatus.Missing -> StatusTone.Waiting
        ConsentDocStatus.Rejected, ConsentDocStatus.Failed -> StatusTone.Alert
        ConsentDocStatus.Unknown -> StatusTone.Neutral
    }
    val (container, content) = when (tone) {
        StatusTone.Done -> androidx.compose.ui.graphics.Color(0xFFDCFCE7) to androidx.compose.ui.graphics.Color(0xFF14532D)
        StatusTone.Active -> MaterialTheme.colorScheme.secondaryContainer to MaterialTheme.colorScheme.onSecondaryContainer
        StatusTone.Waiting -> MaterialTheme.colorScheme.tertiaryContainer to MaterialTheme.colorScheme.onTertiaryContainer
        StatusTone.Alert -> MaterialTheme.colorScheme.errorContainer to MaterialTheme.colorScheme.onErrorContainer
        StatusTone.Neutral -> MaterialTheme.colorScheme.surfaceVariant to MaterialTheme.colorScheme.onSurfaceVariant
    }
    Surface(color = container, contentColor = content, shape = androidx.compose.foundation.shape.RoundedCornerShape(50)) {
        Text(consentStatusLabel(status), style = MaterialTheme.typography.labelMedium, modifier = Modifier.padding(horizontal = 10.dp, vertical = 4.dp))
    }
}
