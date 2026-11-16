package org.redhouse.mobile

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.liveRegion
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.*
import kotlinx.serialization.json.*

internal fun isAppointmentCommand(command:JsonObject):Boolean = command.text("service")=="donantes" &&
    (command.text("path")=="/api/v1/appointments" || command.text("path").startsWith("/api/v1/appointments/"))

internal fun appointmentFailureMessage(error:Exception):String = when((error as? ApiFailure)?.code) {
    "pending_operation" -> "Hay un intento anterior sin confirmar. Recupera la operación pendiente antes de reservar otro horario."
    "pending_operation_changed" -> "La operación pendiente cambió. Actualiza la información antes de recuperarla."
    "slot_full" -> "Este horario ya no tiene cupo. Elige otro horario."
    "campaign_full" -> "La campaña está cerrada o sin cupo. Consulta otra campaña."
    "active_appointment" -> "Ya tienes una cita activa en esta campaña. Consulta Mis citas."
    else -> if(error is ApiFailure) error.message.orEmpty() else "No recibimos confirmación. Conservamos el intento para que puedas recuperarlo."
}

/** Displays the stored attempt's own server context; never fills a new form from it. */
@Composable internal fun AppointmentRecoveryCard(
    repository:MobileRepository,command:JsonObject,busy:Boolean,actionScope:CoroutineScope,
    onBusyChange:(Boolean)->Unit,onResult:suspend (String,String)->Unit
) {
    var originalSlot by remember(command) {mutableStateOf<JsonObject?>(null)}
    var contextLoaded by remember(command) {mutableStateOf(false)}
    var contextAttempt by remember(command) {mutableIntStateOf(0)}
    var message by remember(command) {mutableStateOf("")}
    var working by remember(command) {mutableStateOf(false)}
    val body=command["body"]?.jsonObject
    LaunchedEffect(command,contextAttempt) {
        contextLoaded=false
        try {
            val slotId=body?.text("slot_id").orEmpty().ifBlank {
                val appointment=command.text("path").removePrefix("/api/v1/appointments/").substringBefore('/')
                if(command.text("path")=="/api/v1/appointments") ""
                else repository.session.request("donantes","/api/v1/appointments/$appointment/schedule").text("slot_id")
            }
            if(slotId.isNotBlank())originalSlot=repository.session.request("donantes","/api/v1/campaign-slots/$slotId")
        } catch(cancelled:CancellationException){throw cancelled}
        catch(_:Exception){originalSlot=null}
        finally{contextLoaded=true}
    }
    Card(Modifier.fillMaxWidth().padding(vertical=6.dp)) { Column(Modifier.padding(16.dp),verticalArrangement=Arrangement.spacedBy(8.dp)) {
        Text("Intento anterior sin confirmar",style=MaterialTheme.typography.titleMedium)
        originalSlot?.let {slot->
            Text(slot.text("campaign_title"));Text("Sede: ${slot.text("site_name")}")
            Text(displayBriefDate(slot.text("starts_at")))
        } ?: Text(if(contextLoaded) "No pudimos consultar el horario de este intento." else "Consultando el horario del intento anterior…")
        Text(if(command.text("captured_at").isBlank()) "Intento guardado en este teléfono." else "Guardado: ${displayBriefDate(command.text("captured_at"))}")
        Text("Recupera este intento para conocer su resultado. Se conservarán los datos que guardaste.")
        if(message.isNotBlank())Text(message,Modifier.semantics{liveRegion=LiveRegionMode.Polite})
        Button(enabled=!busy && !working,onClick={
            working=true;onBusyChange(true)
            actionScope.launch {
                try {
                    message=try {repository.recover(command);"Operación recuperada. Consulta tus citas."}
                    catch(cancelled:CancellationException){throw cancelled}
                    catch(error:Exception){appointmentFailureMessage(error)}
                    onResult(message,body?.text("slot_id").orEmpty())
                } finally {working=false;onBusyChange(false)}
            }
        }){Text("Recuperar intento anterior")}
        if(contextLoaded && originalSlot==null)TextButton(enabled=!busy && !working,onClick={contextAttempt++}){Text("Consultar horario del intento")}
    } }
}
