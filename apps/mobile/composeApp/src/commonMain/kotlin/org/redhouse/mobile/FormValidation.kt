package org.redhouse.mobile

import kotlinx.datetime.Instant

/** Client syntax checks only. The owning service remains responsible for business authorization. */
internal fun planningError(reservation:String,responsible:String,departure:String,eta:String,reason:String):String? {
    val uuid=Regex("[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")
    if(!uuid.matches(reservation.trim()))return "Selecciona una reserva válida."
    if(!uuid.matches(responsible.trim()))return "Selecciona un transportista válido."
    val start=runCatching{Instant.parse(departure.trim())}.getOrNull()?:return "Selecciona la fecha y hora de salida."
    val end=runCatching{Instant.parse(eta.trim())}.getOrNull()?:return "Selecciona la fecha y hora de llegada."
    if(end<=start)return "La llegada debe ser posterior a la salida."
    if(reason.trim().length<6)return "Describe el motivo con al menos 6 caracteres."
    return null
}

internal fun finiteTemperature(value:String):Double?=value.trim().toDoubleOrNull()?.takeIf{it.isFinite()}
