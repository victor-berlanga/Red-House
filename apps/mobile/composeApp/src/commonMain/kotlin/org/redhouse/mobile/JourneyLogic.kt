package org.redhouse.mobile

import io.ktor.http.encodeURLParameter
import kotlinx.serialization.json.JsonObject

/*
 * Lógica pura de los recorridos de DONOR y TRANSPORT (sin Compose): qué es "el siguiente paso",
 * en qué orden se muestran las órdenes y qué tono de color lleva cada estado. Vive aparte para
 * probarla en commonTest. La app móvil es solo para estos dos perfiles.
 */

/** Perfiles que pueden usar la app móvil. El servidor es quien impone el bloqueo; aquí solo se decide la navegación. */
internal val mobileRoles = setOf("DONOR", "TRANSPORT")

/** Tono visual de un estado: la UI lo traduce a color, el texto siempre acompaña (no se depende solo del color). */
enum class StatusTone { Done, Active, Waiting, Alert, Neutral }

fun statusTone(status: String): StatusTone = when (status) {
    "CONFIRMED", "ACCEPTED", "DELIVERED", "RECORDED", "ATTENDED", "ACKNOWLEDGED", "ACTIVE", "ELIGIBLE" -> StatusTone.Done
    "COLLECTED", "IN_TRANSIT", "PREPARED", "BOOKED", "OPEN", "SENDING" -> StatusTone.Active
    "PLANNED", "PENDING", "QUEUED", "PRELIMINARY", "DRAFT", "DEFERRED" -> StatusTone.Waiting
    "CANCELLED", "REJECTED", "UNCERTAIN", "CONFLICT", "EXPIRED", "WITHDRAWN" -> StatusTone.Alert
    else -> StatusTone.Neutral
}

// ---------------------------------------------------------------- Transporte

/** Etapas visibles del seguimiento, en orden. PLANNED todavía no ha completado ninguna. */
internal val transportStages = listOf("PREPARED", "COLLECTED", "IN_TRANSIT", "DELIVERED")

/** Índice de la última etapa cumplida (-1 si ninguna). ACCEPTED cuenta como entregada. */
internal fun transportStageIndex(status: String): Int = when (status) {
    "PREPARED" -> 0
    "COLLECTED" -> 1
    "IN_TRANSIT" -> 2
    "DELIVERED", "ACCEPTED" -> 3
    else -> -1
}

/** Acción principal del transportista: etiqueta corta, transición que solicita y si exige escanear unidad y sello. */
internal class TransportStep(val action: String, val label: String, val verifiesUnit: Boolean)

internal fun transportStep(status: String): TransportStep? = when (status) {
    "PREPARED" -> TransportStep("COLLECTED", "Recolectar", true)
    "COLLECTED" -> TransportStep("IN_TRANSIT", "Iniciar traslado", false)
    "IN_TRANSIT" -> TransportStep("DELIVERED", "Entregar", true)
    else -> null
}

/** Texto del estado cuando el transportista no tiene acción disponible. */
internal fun transportWaitingText(status: String): String = when (status) {
    "PLANNED" -> "La institución prepara la unidad"
    "DELIVERED" -> "Entregado; la institución confirma la recepción"
    "ACCEPTED" -> "Recepción aceptada"
    "CANCELLED", "REJECTED" -> "Traslado cerrado"
    else -> "Esperando la siguiente etapa"
}

private fun shipmentPriority(status: String): Int = when (status) {
    "IN_TRANSIT" -> 0
    "COLLECTED" -> 1
    "PREPARED" -> 2
    "PLANNED" -> 3
    "DELIVERED" -> 4
    else -> 5
}

/** Órdenes asignadas: primero las que ya están en marcha, luego las próximas, al final las cerradas. Estable entre iguales. */
internal fun orderedShipments(rows: List<JsonObject>): List<JsonObject> =
    rows.withIndex().sortedWith(compareBy({ shipmentPriority(it.value.text("status")) }, { it.index })).map { it.value }

/** La orden activa es la primera con una acción propia del transportista (recolectar, iniciar o entregar). */
internal fun activeShipment(rows: List<JsonObject>): JsonObject? =
    orderedShipments(rows).firstOrNull { transportStep(it.text("status")) != null }

/**
 * Punto al que conviene llegar: antes de recolectar es el origen; después, el destino.
 * Devuelve vacío si el nombre no está disponible.
 */
internal fun mapsPlaceName(status: String, originName: String, destinationName: String): String =
    (if (status in setOf("PLANNED", "PREPARED")) originName else destinationName).trim()

// ---------------------------------------------------------------- Mapas del sistema

/** Lugar a abrir en la app de mapas del sistema: coordenadas confirmadas, un nombre o ambos. */
class MapTarget(val latitude: Double?, val longitude: Double?, val query: String = "") {
    val hasCoordinates get() = latitude != null && longitude != null
    val isEmpty get() = !hasCoordinates && query.isBlank()
}

/** URI `geo:` de Android. Con coordenadas fija el punto y usa el nombre como etiqueta; sin ellas busca por nombre. */
fun geoUri(target: MapTarget): String = when {
    target.hasCoordinates -> "geo:${target.latitude},${target.longitude}?q=${target.latitude},${target.longitude}" +
        (if (target.query.isNotBlank()) "(${target.query.encodeURLParameter()})" else "")
    else -> "geo:0,0?q=${target.query.encodeURLParameter()}"
}

/** URL de Apple Maps para iOS. */
fun appleMapsUrl(target: MapTarget): String = when {
    target.hasCoordinates -> "https://maps.apple.com/?ll=${target.latitude},${target.longitude}" +
        (if (target.query.isNotBlank()) "&q=${target.query.encodeURLParameter()}" else "")
    else -> "https://maps.apple.com/?q=${target.query.encodeURLParameter()}"
}

// ---------------------------------------------------------------- Donante

enum class DonorStepKind { Loading, Error, Register, Appointment, Book, Consent }

/** Siguiente paso del donante en Inicio: título, y etiqueta del botón principal. */
class DonorStep(val kind: DonorStepKind, val title: String, val action: String)

/**
 * Prioridad: sin expediente se completa el registro preliminar; con cita próxima se muestra la cita;
 * si no, se reserva horario. Mientras carga o si falla la consulta no se adivina nada.
 */
fun donorNextStep(donorLoaded: Boolean, hasRecord: Boolean, nextLoaded: Boolean, next: JsonObject?, busy: Boolean): DonorStep = when {
    donorLoaded && !hasRecord -> DonorStep(DonorStepKind.Register, "Completa tu registro preliminar", "Registrarme")
    !nextLoaded && busy -> DonorStep(DonorStepKind.Loading, "Consultando tus citas…", "")
    !nextLoaded -> DonorStep(DonorStepKind.Error, "No fue posible consultar tu próxima cita.", "Actualizar")
    next != null -> DonorStep(DonorStepKind.Appointment, next.text("title").ifBlank { "Tu próxima cita" }, "Ver mi cita")
    else -> DonorStep(DonorStepKind.Book, "Aún no tienes cita", "Buscar horarios")
}

/** Avisos sin leer: todo lo que no esté reconocido ni descartado. */
fun unreadNotices(rows: List<JsonObject>): Int = rows.count { it.text("status") !in setOf("ACKNOWLEDGED", "DISMISSED") }
