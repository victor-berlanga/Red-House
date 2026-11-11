package org.redhouse.mobile

import androidx.compose.runtime.*
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.*
import kotlinx.datetime.Clock
import kotlinx.datetime.Instant
import kotlinx.serialization.json.*

@Composable
fun TransportScreen(id:String,repository:MobileRepository,queue:ObservationQueue,devices:DeviceAccess) {
    val session=repository.session
    val scope=rememberCoroutineScope()
    var row by remember(id) {mutableStateOf<JsonObject?>(null)}
    var error by remember {mutableStateOf("")}
    var busy by remember {mutableStateOf(false)}
    var scan by remember {mutableStateOf<JsonObject?>(null)}
    var seal by remember {mutableStateOf("")}
    var counterpart by remember {mutableStateOf("")}
    var reason by remember {mutableStateOf("")}
    var destination by remember {mutableStateOf("")}
    var photograph by remember {mutableStateOf<ByteArray?>(null)}
    var evidence by remember {mutableStateOf<JsonObject?>(null)}
    var trackingEnabled by remember {mutableStateOf(session.user?.text("role")!="TRANSPORT")}
    var automaticLocation by remember {mutableStateOf(false)}
    var pendingAction by remember {mutableStateOf<String?>(null)}
    var discardPosition by remember {mutableStateOf(false)}
    var entries by remember {mutableStateOf(queue.entries())}
    var operational by remember(id) {mutableStateOf<JsonObject?>(null)}
    val foreground by MobileLifecycle.foreground.collectAsState()
    val tracking=remember(id) {Tracking(session.api.client,session,session.api.bases.getValue("transporte"),repository.journal)}
    val live by tracking.state.collectAsState()
    fun run(action:suspend ()->Unit) {if(busy)return;busy=true;scope.launch {try{action()} catch(e:CancellationException){throw e} catch(e:Exception){error=if(e is ApiFailure || e is IllegalArgumentException)e.message.orEmpty() else "Sin confirmación. Revisa pendientes antes de repetir."}finally{busy=false}}}
    LaunchedEffect(id) {try{row=repository.shipment(id)}catch(e:Exception){error=e.message.orEmpty()}}
    LaunchedEffect(trackingEnabled,foreground) {if(trackingEnabled && foreground) tracking.follow(id)}
    LaunchedEffect(foreground) {if(foreground) {while(isActive) {try{queue.synchronize();entries=queue.entries()}catch(_:Exception){};delay(30000)}}}
    LaunchedEffect(automaticLocation,trackingEnabled,foreground,live.connected) {
        if(automaticLocation && trackingEnabled && foreground && live.connected)while(isActive){
            try {
                val point=suspendCancellableCoroutine<PhonePosition>{continuation->
                    devices.locate {position,failure->if(continuation.isActive){if(position!=null)continuation.resumeWith(Result.success(position)) else continuation.resumeWith(Result.failure(IllegalArgumentException(failure)))}}
                    continuation.invokeOnCancellation {devices.cancel()}
                }
                tracking.publish(buildJsonObject{put("event_id",newId());put("shipment_id",id);put("device_id",repository.journal.deviceId());put("source",devices.source);put("sequence",repository.journal.sequence());put("captured_at",point.capturedAt);put("simulated",point.simulated);put("fix_valid",true);put("latitude",point.latitude);put("longitude",point.longitude);put("accuracy_m",point.accuracy)})
                error="Ubicación periódica confirmada por Transporte"
            }catch(e:CancellationException){throw e}catch(e:Exception){error=e.message?:"Ubicación sin confirmación"}
            delay(15000)
        }
    }
    DisposableEffect(id) {onDispose{devices.cancel()}}
    var referencesView by remember(id) {mutableStateOf(false)}
    var contactsView by remember(id) {mutableStateOf(false)}
    var evidenceView by remember(id) {mutableStateOf(false)}
    var historyView by remember(id) {mutableStateOf(false)}
    var locationView by remember(id) {mutableStateOf(false)}
    var observationsView by remember(id) {mutableStateOf(false)}
    Text("Traslado ${id.take(8)}",style=MaterialTheme.typography.titleLarge)
    if(error.isNotBlank())Text(error)
    if(busy) LinearProgressIndicator(Modifier.fillMaxWidth())
    row?.let {task ->
        Text("Estado: ${displayValue("status", task.text("status"))}")
        SettingRow("Referencias del traslado") {referencesView=!referencesView}
        if(referencesView) {
            Text("Traslado: $id · versión ${task.text("version")}")
            Text("Origen: ${task.text("origin_id")}\nDestino: ${task.text("destination_id")}")
        }
        Text("Salida: ${displayDate(task.text("departure_at"))} · Llegada planificada: ${displayDate(task.text("eta"))}")
        SettingRow("Contactos y ruta") {contactsView=!contactsView}
        if(contactsView) {
        OutlinedButton(enabled=!busy,onClick={run {
            operational=session.request("transporte","/api/v1/shipments/$id/operational-context")
        }}){Text("Consultar contactos y ruta de esta tarea")}
        operational?.let {context ->
            OperationalDetails(context)
            val side=if(task.text("status")=="PREPARED")"origin" else "destination"
            if(session.user?.text("role")=="TRANSPORT") {
                context.getValue(side).jsonObject.getValue("operators").jsonArray.forEach {item->
                    val person=item.jsonObject
                    TextButton(enabled=!busy,onClick={counterpart=person.text("id")}){Text("Contraparte: ${person.text("name")}")}
                }
            } else if(session.user?.text("role")=="OPERATOR") {
                TextButton(enabled=!busy,onClick={counterpart=context.text("transport_user_id")}){Text("Seleccionar transportista asignado")}
            }
        }
        }
        OutlinedButton(enabled=!busy,onClick={run{row=repository.shipment(id);scan=null;error="Estado actualizado"}}){Text("Actualizar estado")}
        val transport=session.user?.text("role")=="TRANSPORT"
        val operator=session.user?.text("role")=="OPERATOR"
        val final=task.text("status") in setOf("ACCEPTED","CANCELLED","REJECTED")
        if(!final && (transport||operator)) {
            Button(enabled=!busy,onClick={devices.scan {code,failure->if(code!=null)run{scan=repository.scan(id,code);error="Código verificado por Transporte"}else error=failure.orEmpty()}}){Text("Escanear unidad")}
            scan?.let {Text("Unidad verificada: ${it.text("resource_id")} · ${it.text("status")}")}
            OutlinedTextField(seal,{seal=it},label={Text("Sello verificado")})
            OutlinedTextField(counterpart,{counterpart=it},label={Text("Referencia de la contraparte autorizada")})
            OutlinedTextField(reason,{reason=it},label={Text("Observación / motivo (mínimo 6 caracteres)")})
            if(operator && session.user?.text("tenant_id")==task.text("destination_id") && task.text("status")=="DELIVERED") OutlinedTextField(destination,{destination=it},label={Text("UUID ubicación receptora (opcional)")})
            SettingRow("Evidencia",if(photograph!=null) "Fotografía pendiente de cargar" else evidence?.text("status")) {evidenceView=!evidenceView}
            if(evidenceView) {
            Button(enabled=!busy,onClick={devices.photograph {bytes,failure->photograph=bytes;evidence=null;error=failure.orEmpty()}}){Text("Capturar evidencia")}
            photograph?.let {bytes ->
                Image(imageBitmap(bytes),"Vista previa de evidencia",Modifier.fillMaxWidth().height(180.dp))
                Row {
                    Button(enabled=!busy,onClick={run{evidence=repository.uploadPhoto(id,bytes);photograph=null;error="Archivo: ${evidence?.text("status")}"}}){Text("Cargar y verificar")}
                    TextButton(onClick={photograph=null}){Text("Eliminar foto")}
                }
            }
            evidence?.let{Text("Evidencia ${it.text("id")} · ${it.text("status")}")}
            }
            val action=when {
                transport && task.text("status")=="PREPARED" -> "COLLECTED"
                transport && task.text("status")=="COLLECTED" -> "IN_TRANSIT"
                transport && task.text("status")=="IN_TRANSIT" -> "DELIVERED"
                operator && session.user?.text("tenant_id")==task.text("origin_id") && task.text("status")=="PLANNED" -> "PREPARED"
                operator && session.user?.text("tenant_id")==task.text("destination_id") && task.text("status")=="DELIVERED" -> "ACCEPTED"
                else -> null
            }
            action?.let {Button(enabled=!busy && reason.length>=6,onClick={pendingAction=it}){Text(when(it){"COLLECTED"->"Confirmar recolección";"IN_TRANSIT"->"Iniciar traslado";"DELIVERED"->"Confirmar entrega física";"ACCEPTED"->"Aceptar recepción logística";else->"Preparar unidad"})}}
            OutlinedButton(enabled=!busy && reason.length>=6,onClick={pendingAction="INCIDENT"}){Text("Registrar incidencia")}
            if(transport) {
                Button(enabled=!busy && reason.length>=6,onClick={run{queue.enqueue(id,repository.journal.deviceId(),task.getValue("version").jsonPrimitive.int,reason);entries=queue.entries();devices.scheduleSync();error="Observación pendiente; no confirma custodia."}}){Text("Guardar observación para sincronizar")}
                SettingRow("Ubicación",if(trackingEnabled) "Autorizada durante esta tarea" else "Sin captura autorizada") {locationView=!locationView}
                if(locationView || trackingEnabled || automaticLocation) {
                Button(enabled=!busy,onClick={run{
                    if(trackingEnabled){devices.cancel();trackingEnabled=false;repository.stopTracking(task)}else{repository.startTracking(task);trackingEnabled=true}
                }}){Text(if(trackingEnabled)"Detener ubicación" else "Autorizar ubicación durante esta tarea")}
                Row {Checkbox(automaticLocation,{automaticLocation=it},enabled=trackingEnabled,modifier=Modifier.semantics{contentDescription="Enviar GPS cada 15 segundos mientras la tarea esté visible"});Text("Enviar GPS cada 15 segundos mientras la tarea esté visible")}
                Button(enabled=trackingEnabled && live.connected && !automaticLocation && !busy,onClick={devices.locate {point,failure->
                    if(point==null)error=failure.orEmpty() else run {
                        tracking.publish(buildJsonObject {
                            put("event_id",newId());put("shipment_id",id);put("device_id",repository.journal.deviceId());put("source",devices.source)
                            put("sequence",repository.journal.sequence());put("captured_at",point.capturedAt);put("simulated",point.simulated)
                            put("fix_valid",true);put("latitude",point.latitude);put("longitude",point.longitude);put("accuracy_m",point.accuracy)
                        });error="Ubicación confirmada por Transporte (PERSISTED_SQL)"
                    }
                }}){Text("Capturar y publicar ubicación")}
                }
            }
        }
        if(session.user?.text("role")=="COORDINATOR" && task.text("status") in setOf("PLANNED","PREPARED")) {
            OutlinedTextField(reason,{reason=it},label={Text("Motivo de cancelación (mínimo 6 caracteres)")})
            Button(enabled=!busy && reason.length>=6,onClick={pendingAction="CANCELLED"}){Text("Cancelar antes de recolección")}
        }
        SettingRow("Historial") {historyView=!historyView}
        if(historyView) (task["transitions"] as? JsonArray)?.forEach {val event=it.jsonObject;Text("${event.text("sequence")} · ${event.text("state")} · ${event.text("created_at")}")}
        if(repository.journal.value("transition:$id")!=null) Button(enabled=!busy,onClick={run{row=repository.recoverTransition(id);error="Resultado recuperado sin cambiar la clave"}}){Text("Recuperar operación incierta")}
        pendingAction?.let {state ->
            AlertDialog(onDismissRequest={pendingAction=null},title={Text("Confirmación humana")},text={Text("Registrar $state. La entrega física no equivale a aceptación clínica. El servidor comprobará versión, permisos y secuencia.")},
                confirmButton={Button(onClick={pendingAction=null;run{
                    val body=buildJsonObject {
                        put("state",state);put("version",task.getValue("version"));put("reason",reason);put("human_confirmation",true)
                        if(state in setOf("COLLECTED","DELIVERED","ACCEPTED")) {
                            val verified=scan?:throw IllegalArgumentException("Escanea y verifica la unidad antes de transferir.")
                            require(verified["version"]==task["version"]){"El escaneo corresponde a otra versión; vuelve a escanear."}
                            put("custody",buildJsonObject {put("scanned_resource_id",verified.text("resource_id"));put("seal",seal);put("captured_at",Clock.System.now().toString());put("reported_handover_user_id",counterpart);put("electronic_acceptance",true)})
                        }
                        evidence?.let{put("evidence",obj("object_id" to it.text("id")))}
                        if(state=="ACCEPTED" && destination.isNotBlank()) put("destination_location_id",destination)
                    }
                    row=repository.transition(id,body);scan=null;reason="";error="Paso confirmado"
                    if(state in setOf("DELIVERED","ACCEPTED","CANCELLED")){devices.cancel();trackingEnabled=false;runCatching{repository.stopTracking(row!!)}}
                }}){Text("Confirmar")}},dismissButton={TextButton(onClick={pendingAction=null}){Text("Cancelar")}})
        }
    }
    Text("Seguimiento: ${live.status} · ${if(live.connected)"WSS conectado" else "WSS desconectado"}")
    if(repository.journal.value("position:$id")!=null) {
        Text("Lectura conservada sin confirmación. Reintentar conserva su identificador y hora originales.")
        TextButton(enabled=!busy,onClick={discardPosition=true}){Text("Descartar lectura sin confirmar")}
    }
    if(discardPosition)AlertDialog(onDismissRequest={discardPosition=false},
        title={Text("Descartar lectura local")},
        text={Text("No confirma ni borra una recepción remota. Se detendrá la captura; vuelve a autorizar ubicación para enviar una lectura nueva. La custodia no cambia.")},
        confirmButton={Button(onClick={discardPosition=false;automaticLocation=false;trackingEnabled=false;devices.cancel();run{tracking.discardPending(id);error="Lectura descartada localmente; recepción remota no confirmada"}}){Text("Descartar")}},
        dismissButton={TextButton(onClick={discardPosition=false}){Text("Conservar")}})
    val point=live.position
    point?.let {
        var age by remember {mutableStateOf(0L)}
        LaunchedEffect(it.text("event_id")){while(isActive){age=(Clock.System.now()-Instant.parse(it.text("captured_at"))).inWholeSeconds;delay(1000)}}
        Text("Fuente: ${it.text("source")} ${if(it["simulated"]?.jsonPrimitive?.booleanOrNull==true)"SIMULADA / INYECTADA" else ""}\nCaptura: ${it.text("captured_at")} · antigüedad ${age}s · precisión ${it.text("accuracy_m")} m")
        Text("Última coordenada recibida: latitud ${it.text("latitude")}, longitud ${it.text("longitude")}")
        if(age>30 || !live.connected)Text("Última observación; no se considera ubicación actual.")
    }
    RegionalMap(point?.get("latitude")?.jsonPrimitive?.doubleOrNull,point?.get("longitude")?.jsonPrimitive?.doubleOrNull,point?.text("source").orEmpty())
    SettingRow("Observaciones por sincronizar (${entries.size})") {observationsView=!observationsView}
    if(observationsView) {
    Text("Sincronización: solo observaciones; nunca custodia ni decisiones clínicas")
    entries.forEach {Text("${it.getValue("command").jsonObject.text("id").take(8)} · ${it.text("state")}")}
    OutlinedButton(enabled=!busy,onClick={run{queue.synchronize(manual=true);entries=queue.entries()}}){Text("Sincronizar y consultar resultados")}
    }
}
