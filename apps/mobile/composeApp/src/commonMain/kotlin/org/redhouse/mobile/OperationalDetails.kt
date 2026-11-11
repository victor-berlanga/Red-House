package org.redhouse.mobile

import androidx.compose.runtime.Composable
import androidx.compose.material3.Text
import kotlinx.serialization.json.*

/** Owner-projected operational data only; no client-selected institution or route. */
@Composable fun OperationalDetails(context:JsonObject) {
    for((key,title) in listOf("origin" to "Origen","destination" to "Destino")) {
        val institution=context.getValue(key).jsonObject
        Text("$title: ${institution.text("name")}")
        val contacts=institution.getValue("contacts").jsonArray
        if(contacts.isEmpty())Text("Sin contactos publicados para operaciones; solicita apoyo institucional.")
        contacts.forEach {val contact=it.jsonObject;Text("${contact.text("name")}: ${contact.text("value")} · versión ${contact.text("version")}")}
    }
    val route=context.getValue("route").jsonObject
    Text("Ruta vinculada a la reserva: ${route.text("id").take(8)}")
    Text("${route.text("distance_km")} km · ${route.text("travel_minutes")} minutos estimados\nFuente: ${route.text("source")}\nActualización: ${displayDate(route.text("updated_at"))}")
    Text("Versión reservada: ${route.text("reserved_version")} · actual: ${route.text("current_version")}")
    if(route.getValue("changed").jsonPrimitive.boolean)Text("La referencia cambió desde la reserva. Solicita revisión al coordinador; estos valores no sustituyen el plan autorizado.")
    Text("Estimación logística; no geometría vial ni tiempo medido. Consulta: ${displayDate(context.text("consulted_at"))}")
}
