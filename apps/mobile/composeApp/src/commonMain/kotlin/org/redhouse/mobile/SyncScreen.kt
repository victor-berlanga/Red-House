package org.redhouse.mobile

import androidx.compose.runtime.*
import androidx.compose.material3.*
import kotlinx.coroutines.*
import kotlinx.serialization.json.*

@Composable fun SyncScreen(queue:ObservationQueue){
    var rows by remember{mutableStateOf(queue.entries())};var busy by remember{mutableStateOf(false)};var status by remember{mutableStateOf("")}
    val scope=rememberCoroutineScope()
    LaunchedEffect(queue){while(isActive){rows=queue.entries();delay(2000)}}
    Text("Observaciones de esta identidad e institución",style=MaterialTheme.typography.titleMedium)
    Text("No incluye transferencias de custodia ni decisiones clínicas. Tras cinco intentos automáticos se requiere recuperación manual.")
    Text(status)
    rows.forEach{row->val command=row["command"]!!.jsonObject;Text("${command.text("id").take(8)} · captura ${displayDate(command.text("captured_at"))} · ${displayValue("state", row.text("state"))} · intentos ${row.text("attempts").ifBlank{"0"}}")}
    if(rows.isEmpty())Text("Sin observaciones guardadas")
    Button(enabled=!busy,onClick={busy=true;scope.launch{try{queue.synchronize(manual=true);rows=queue.entries();status="Resultados consultados; revisa conflictos y rechazos"}catch(e:CancellationException){throw e}catch(e:Exception){status=e.message?:"Sin confirmación"}finally{busy=false}}}){Text("Recuperar y sincronizar")}
    TextButton(enabled=!busy,onClick={scope.launch{queue.dismissCompleted();rows=queue.entries()}}){Text("Limpiar confirmadas, rechazadas y vencidas")}
}
