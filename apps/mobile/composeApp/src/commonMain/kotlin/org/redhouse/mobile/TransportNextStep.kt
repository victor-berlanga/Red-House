package org.redhouse.mobile

import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.booleanOrNull
import kotlinx.serialization.json.contentOrNull
import kotlinx.serialization.json.doubleOrNull

/** Transición que puede solicitar la persona con este perfil. La app móvil solo ejecuta traslados como TRANSPORT. */
internal fun transportAction(role: String, status: String): String? =
    if (role == "TRANSPORT") transportStep(status)?.action else null

internal fun transportLocationSummary(point:JsonObject?,connected:Boolean):String {
    if(point==null) return "Ubicación no disponible en esta vista; el mapa muestra la región."
    val captured=(point["captured_at"] as? JsonPrimitive)?.contentOrNull.orEmpty()
    val whenReceived=if(captured.isBlank()) "hora no disponible" else displayBriefDate(captured)
    val simulated=if(isSimulatedPosition(point)) " · simulada" else ""
    val connection=if(connected) "" else " · sin conexión"
    val label=if(validMapPosition(point)==null) "Sin señal GPS" else "Última ubicación"
    return "$label: $whenReceived$simulated$connection"
}

internal fun isSimulatedPosition(point:JsonObject?):Boolean =
    (point?.get("simulated") as? JsonPrimitive)?.booleanOrNull==true ||
        (point?.get("source") as? JsonPrimitive)?.contentOrNull=="SIMULATOR"

internal fun validMapPosition(point:JsonObject?):Pair<Double,Double>? {
    val fix=point?.get("fix_valid") as? JsonPrimitive ?: return null
    if(fix.isString || fix.booleanOrNull!=true) return null
    val latValue=point["latitude"] as? JsonPrimitive ?: return null
    val lonValue=point["longitude"] as? JsonPrimitive ?: return null
    if(latValue.isString || lonValue.isString) return null
    val latitude=latValue.doubleOrNull ?: return null
    val longitude=lonValue.doubleOrNull ?: return null
    if(!latitude.isFinite() || !longitude.isFinite() || latitude !in -90.0..90.0 || longitude !in -180.0..180.0) return null
    return latitude to longitude
}
