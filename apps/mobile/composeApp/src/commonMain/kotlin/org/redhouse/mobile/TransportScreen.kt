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
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.LocalWindowInfo

@Composable
/** [startStage] 0 abre el detalle; 1 y 2 abren directo el paso de transferencia (atajos del inicio: acción principal e incidencia). */
fun TransportScreen(id:String,repository:MobileRepository,queue:ObservationQueue,devices:DeviceAccess,startStage:Int=0) {
    key(id) { TransportTask(id,repository,queue,devices,startStage) }
}

@Composable
private fun TransportTask(id:String,repository:MobileRepository,queue:ObservationQueue,devices:DeviceAccess,startStage:Int) {
    val openInMaps=rememberOpenInMaps()
    val session=repository.session
    val scope=rememberCoroutineScope()
    var row by remember(id) {mutableStateOf<JsonObject?>(null)}
    var error by remember {mutableStateOf("")}
    var busy by remember {mutableStateOf(false)}
    var scan by remember {mutableStateOf<JsonObject?>(null)}
    var seal by remember {mutableStateOf("")}
    var counterpart by remember {mutableStateOf("")}
    var reason by remember {mutableStateOf("")}
    var photograph by remember {mutableStateOf<ByteArray?>(null)}
    var evidence by remember {mutableStateOf<JsonObject?>(null)}
    var trackingEnabled by remember {mutableStateOf(session.user?.text("role")!="TRANSPORT")}
    var automaticLocation by remember {mutableStateOf(false)}
    var pendingAction by remember {mutableStateOf<String?>(null)}
    var discardPosition by remember {mutableStateOf(false)}
    var entries by remember(queue) {mutableStateOf(queue.entries())}
    val queueRevision by queue.changes.collectAsState()
    var operational by remember(id) {mutableStateOf<JsonObject?>(null)}
    var operationalLoading by remember(id) {mutableStateOf(true)}
    var operationalError by remember(id) {mutableStateOf(false)}
    var operationalDenied by remember(id) {mutableStateOf(false)}
    val foreground by MobileLifecycle.foreground.collectAsState()
    val tracking=remember(id) {Tracking(session.api.client,session,session.api.bases.getValue("transporte"),repository.journal)}
    val live by tracking.state.collectAsState()
    fun run(action:suspend ()->Unit) {if(busy)return;busy=true;scope.launch {try{action()} catch(e:CancellationException){throw e} catch(e:Exception){error=if(e is ApiFailure || e is IllegalArgumentException)e.message.orEmpty() else "Sin confirmación. Revisa pendientes antes de repetir."}finally{busy=false}}}
    suspend fun loadOperational() {
        operationalLoading=true;operationalError=false;operationalDenied=false
        try {operational=session.request("transporte","/api/v1/shipments/$id/operational-context")}
        catch(e:CancellationException){throw e}
        catch(e:Exception){operational=null;operationalDenied=e is ApiFailure && e.status in setOf(401,403);operationalError=!operationalDenied}
        finally {operationalLoading=false}
    }
    LaunchedEffect(id) {
        try {row=repository.shipment(id)} catch(e:CancellationException){throw e} catch(e:Exception){error=if(e is ApiFailure)e.message.orEmpty() else "No se pudo consultar el traslado."}
        loadOperational()
    }
    LaunchedEffect(tracking,trackingEnabled,foreground) {if(trackingEnabled && foreground) tracking.follow(id)}
    LaunchedEffect(queue,queueRevision,foreground) {entries=queue.entries()}
    LaunchedEffect(automaticLocation,trackingEnabled,foreground,live.connected) {
        if(automaticLocation && trackingEnabled && foreground && live.connected)while(isActive){
            try {
                val point=suspendCancellableCoroutine<PhonePosition>{continuation->
                    devices.locate {position,failure->if(continuation.isActive){if(position!=null)continuation.resumeWith(Result.success(position)) else continuation.resumeWith(Result.failure(IllegalArgumentException(failure)))}}
                    continuation.invokeOnCancellation {devices.cancel()}
                }
                tracking.publish(buildJsonObject{put("event_id",newId());put("shipment_id",id);put("device_id",repository.journal.deviceId());put("source",devices.source);put("sequence",repository.journal.sequence());put("captured_at",point.capturedAt);put("simulated",point.simulated);put("fix_valid",true);put("latitude",point.latitude);put("longitude",point.longitude);put("accuracy_m",point.accuracy)})
                error="Ubicación periódica confirmada por Transporte"
            }catch(e:CancellationException){throw e}catch(e:Exception){error=if(e is ApiFailure)e.message.orEmpty() else "No se pudo confirmar la ubicación."}
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
    var observationDialog by remember(id) {mutableStateOf(false)}
    var observationDraft by remember(id) {mutableStateOf("")}
    fun saveObservation(task:JsonObject,value:String) = run {
        val note=value.trim()
        require(note.length in 6..1000) {"Escribe una observación de entre 6 y 1000 caracteres."}
        queue.enqueue(id,repository.journal.deviceId(),task.getValue("version").jsonPrimitive.int,note)
        entries=queue.entries();devices.scheduleSync();observationsView=true
        observationDialog=false;observationDraft="";error="Observación guardada en Pendientes."
    }
    var transferView by remember(id) {mutableStateOf(startStage>0)}
    var transferStage by remember(id) {mutableIntStateOf(startStage.coerceIn(1,2))}
    if(error.isNotBlank())Text(error)
    if(busy) LinearProgressIndicator(Modifier.fillMaxWidth())
    val point=live.position?.takeIf {candidate->candidate.values.all {it is JsonPrimitive}}
    if(!transferView) {
        val density=LocalDensity.current
        val windowHeight=with(density) {LocalWindowInfo.current.containerSize.height.toDp()}
        val mapHeight=if(windowHeight<720.dp || density.fontScale>=1.2f) 200.dp else 280.dp
        val coordinates=validMapPosition(point)
        val simulated=isSimulatedPosition(point)
        RegionalMap(coordinates?.first,coordinates?.second,if(simulated) "Ubicación simulada" else "Última ubicación",mapHeight)
    }
    row?.let {task ->
        val transport=session.user?.text("role")=="TRANSPORT"
        val final=task.text("status") in setOf("ACCEPTED","CANCELLED","REJECTED")
        val action=transportAction(session.user?.text("role").orEmpty(),task.text("status"))
        val nextStep=when(action){"COLLECTED"->"Confirmar recolección";"IN_TRANSIT"->"Iniciar traslado";"DELIVERED"->"Confirmar entrega física";else->transportWaitingText(task.text("status"))}
        LaunchedEffect(action) {if(action==null) {transferView=false;transferStage=1}}
        if(transferView) Row(verticalAlignment=androidx.compose.ui.Alignment.CenterVertically) {
            TextButton(onClick={transferView=false}) {Text("Volver al mapa")}
            Text("Traslado · ${displayValue("status",task.text("status"))}",style=MaterialTheme.typography.titleMedium)
        } else Card(Modifier.fillMaxWidth()) { Column(Modifier.padding(horizontal=16.dp,vertical=8.dp),verticalArrangement=Arrangement.spacedBy(6.dp)) {
            Text("Traslado · ${displayValue("status",task.text("status"))}",style=MaterialTheme.typography.titleMedium)
            StageTracker(task.text("status"))
            Text(transportLocationSummary(point,live.connected),style=MaterialTheme.typography.bodySmall)
            operational?.let {context ->
                val origin=context["origin"]?.jsonObject?.text("name").orEmpty()
                val destinationName=context["destination"]?.jsonObject?.text("name").orEmpty()
                if(origin.isNotBlank() && destinationName.isNotBlank()) Text("$origin → $destinationName",style=MaterialTheme.typography.bodyMedium)
            }
            if(operational==null) {
                Text(if(operationalLoading) "Consultando origen y destino…" else if(operationalDenied) "No se pudo confirmar tu acceso al origen y destino." else "Origen y destino temporalmente no disponibles.",style=MaterialTheme.typography.bodySmall)
                if(operationalError) TextButton(enabled=!busy,onClick={run{loadOperational()}}) {Text("Volver a consultar")}
            }
            // La API no publica coordenadas ni dirección de las sedes: se busca por nombre (origen antes de recolectar, destino después); sin nombre, la última posición válida.
            val place=mapsPlaceName(task.text("status"),operational?.get("origin")?.jsonObject?.text("name").orEmpty(),operational?.get("destination")?.jsonObject?.text("name").orEmpty())
            val coordinates=validMapPosition(point)
            val mapTarget=if(place.isNotBlank()) MapTarget(null,null,place) else if(coordinates!=null) MapTarget(coordinates.first,coordinates.second) else null
            if(mapTarget!=null) OutlinedButton(onClick={if(!openInMaps(mapTarget)) error="No hay una app de mapas disponible en este teléfono."},modifier=Modifier.fillMaxWidth().heightIn(min=48.dp)) {Text("Abrir en mapas")}
            if(!final && transport) {
                if(action!=null) SettingRow("Siguiente paso: $nextStep") {transferView=true}
                else Text(nextStep,style=MaterialTheme.typography.bodyMedium)
            }
        } }
        if(!final && transport) {
            if(transferView && action!=null) {
                val handover=action in setOf("COLLECTED","DELIVERED")
                Text("Paso $transferStage de 3",style=MaterialTheme.typography.titleMedium)
                if(transferStage==1) {
                    Text(if(handover) "Verifica la unidad y el sello." else "Revisa la tarea antes de continuar.")
                    if(handover) {
                        Button(enabled=!busy,onClick={devices.scan {code,failure->if(code!=null)run{scan=repository.scan(id,code);error="Código verificado"}else error=failure.orEmpty()}}){Text("Escanear unidad")}
                        scan?.let {Text("Unidad verificada")}
                        OutlinedTextField(seal,{seal=it},label={Text("Sello verificado")})
                    }
                    Button(enabled=!busy && (!handover || (scan!=null && seal.isNotBlank())),onClick={transferStage=2}) {Text("Continuar")}
                }
                if(transferStage==2) {
                    if(handover) {
                        Text("Selecciona la persona que participa en la entrega.")
                        val context=operational
                        if(context==null) {
                            Text(if(operationalDenied) "No se pudo confirmar tu acceso a las personas autorizadas." else "No se pudieron cargar las personas autorizadas.")
                            if(!operationalDenied) OutlinedButton(enabled=!busy,onClick={run{loadOperational()}}){Text("Volver a consultar")}
                        } else {
                            val side=if(task.text("status")=="PREPARED") "origin" else "destination"
                            val operators=context.getValue(side).jsonObject.getValue("operators").jsonArray
                            if(operators.isEmpty()) Text("No hay personas disponibles para esta entrega.")
                            operators.forEach {item->val person=item.jsonObject
                                Row {RadioButton(selected=counterpart==person.text("id"),onClick={counterpart=person.text("id")});TextButton(onClick={counterpart=person.text("id")}){Text(person.text("name"))}}
                            }
                        }
                    }
                    OutlinedTextField(reason,{reason=it},label={Text("Observación / motivo (mínimo 6 caracteres)")})
                    Row {TextButton(onClick={transferStage=1}){Text("Atrás")}
                        Button(enabled=!busy && reason.length>=6 && (!handover || counterpart.isNotBlank()),onClick={transferStage=3}){Text("Revisar")}}
                    OutlinedButton(enabled=!busy && reason.length>=6,onClick={pendingAction="INCIDENT"}){Text("Registrar incidencia")}
                    if(transport) TextButton(enabled=!busy && reason.trim().length in 6..1000,onClick={saveObservation(task,reason)}){Text("Guardar observación para sincronizar")}
                }
                if(transferStage==3) {
                    Text("Revisa los datos antes de confirmar. La entrega física no equivale a aceptación clínica.")
                    Text("Observación: $reason")
                    SettingRow("Evidencia",if(photograph!=null) "Fotografía pendiente de cargar" else evidence?.let { if(it.text("status")=="VERIFIED") "Foto verificada" else "No se confirmó la verificación" }) {evidenceView=!evidenceView}
                    if(evidenceView) {
                        Button(enabled=!busy,onClick={devices.photograph {bytes,failure->photograph=bytes;evidence=null;error=failure.orEmpty()}}){Text("Capturar evidencia")}
                        photograph?.let {bytes ->
                            Image(remember(bytes) { imageBitmap(bytes) },"Vista previa de evidencia",Modifier.fillMaxWidth().height(180.dp))
                            Row {
                                Button(enabled=!busy,onClick={run{evidence=repository.uploadPhoto(id,bytes);photograph=null;error=""}}){Text("Cargar y verificar")}
                                TextButton(onClick={photograph=null}){Text("Eliminar foto")}
                            }
                        }
                    }
                    Row {TextButton(onClick={transferStage=2}){Text("Atrás")}
                        action?.let {Button(enabled=!busy,onClick={pendingAction=it}){Text(when(it){"COLLECTED"->"Confirmar recolección";"IN_TRANSIT"->"Iniciar traslado";else->"Confirmar entrega física"})}}}
                }
            }
            if(transport) {
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
                        });error="Ubicación guardada para este traslado"
                    }
                }}){Text("Capturar y publicar ubicación")}
                }
            }
        }
        OutlinedButton(enabled=!busy,onClick={run{row=repository.shipment(id);scan=null;error="Estado actualizado"}}){Text("Actualizar estado")}
        SettingRow("Referencias del traslado") {referencesView=!referencesView}
        if(referencesView) {
            Text("Traslado: $id · versión ${task.text("version")}")
            Text("Origen: ${task.text("origin_id")}\nDestino: ${task.text("destination_id")}")
        }
        Text("Salida: ${displayBriefDate(task.text("departure_at"))} · Llegada planificada: ${displayBriefDate(task.text("eta"))}")
        SettingRow("Contactos y ruta") {contactsView=!contactsView}
        if(contactsView) {
        OutlinedButton(enabled=!busy && !operationalDenied,onClick={run {
            loadOperational()
        }}){Text("Consultar contactos y ruta de esta tarea")}
        operational?.let {context ->
            OperationalDetails(context)
            val side=if(task.text("status")=="PREPARED")"origin" else "destination"
            context.getValue(side).jsonObject.getValue("operators").jsonArray.forEach {item->
                val person=item.jsonObject
                TextButton(enabled=!busy,onClick={counterpart=person.text("id")}){Text("Contraparte: ${person.text("name")}")}
            }
        }
        }
        SettingRow("Historial") {historyView=!historyView}
        if(historyView) (task["transitions"] as? JsonArray)?.forEach {val event=it.jsonObject;Text("${displayValue("state",event.text("state"))} · ${displayBriefDate(event.text("created_at"))}")}
        if(repository.journal.value("transition:$id")!=null) Button(enabled=!busy,onClick={run{row=repository.recoverTransition(id);photograph=null;evidence=null;error="Resultado recuperado"}}){Text("Recuperar operación incierta")}
        pendingAction?.let {state ->
            AlertDialog(onDismissRequest={pendingAction=null},title={Text("Confirmación humana")},text={Text("Registrar ${displayValue("state",state)}. La entrega física no equivale a aceptación clínica. Se comprobarán los permisos y el estado de la tarea.")},
                confirmButton={Button(onClick={pendingAction=null;run{
                    val body=buildJsonObject {
                        put("state",state);put("version",task.getValue("version"));put("reason",reason);put("human_confirmation",true)
                        if(state in setOf("COLLECTED","DELIVERED")) {
                            val verified=scan?:throw IllegalArgumentException("Escanea y verifica la unidad antes de transferir.")
                            require(verified["version"]==task["version"]){"El escaneo corresponde a otra versión; vuelve a escanear."}
                            put("custody",buildJsonObject {put("scanned_resource_id",verified.text("resource_id"));put("seal",seal);put("captured_at",Clock.System.now().toString());put("reported_handover_user_id",counterpart);put("electronic_acceptance",true)})
                        }
                        evidence?.let{put("evidence",obj("object_id" to it.text("id")))}
                    }
                    row=repository.transition(id,body);scan=null;seal="";counterpart="";reason="";photograph=null;evidence=null;transferView=false;transferStage=1;error="Paso confirmado"
                    if(state=="DELIVERED"){devices.cancel();trackingEnabled=false;runCatching{repository.stopTracking(row!!)}}
                }}){Text("Confirmar")}},dismissButton={TextButton(onClick={pendingAction=null}){Text("Cancelar")}})
        }
    }
    Text("Seguimiento: ${if(live.connected)"conectado" else "sin conexión"}")
    if(live.status.startsWith("Sin permiso") || live.status.startsWith("Sesión vencida")) Text(live.status)
    if(repository.journal.value("position:$id")!=null) {
        Text("Lectura conservada sin confirmación. Reintentar conserva su identificador y hora originales.")
        TextButton(enabled=!busy,onClick={discardPosition=true}){Text("Descartar lectura sin confirmar")}
    }
    if(discardPosition)AlertDialog(onDismissRequest={discardPosition=false},
        title={Text("Descartar lectura local")},
        text={Text("No confirma ni borra una recepción remota. Se detendrá la captura; vuelve a autorizar ubicación para enviar una lectura nueva. La custodia no cambia.")},
        confirmButton={Button(onClick={discardPosition=false;automaticLocation=false;trackingEnabled=false;devices.cancel();run{tracking.discardPending(id);error="Lectura descartada localmente; recepción remota no confirmada"}}){Text("Descartar")}},
        dismissButton={TextButton(onClick={discardPosition=false}){Text("Conservar")}})
    point?.let {
        var age by remember {mutableStateOf(0L)}
        LaunchedEffect(it.text("event_id")){while(isActive){age=runCatching {(Clock.System.now()-Instant.parse(it.text("captured_at"))).inWholeSeconds}.getOrDefault(0L);delay(1000)}}
        if(validMapPosition(it)==null) {
            Text(transportLocationSummary(it,live.connected))
        } else {
            val simulated=isSimulatedPosition(it)
            Text("${if(simulated) "Ubicación simulada" else "Ubicación recibida"}\n${displayBriefDate(it.text("captured_at"))} · hace ${age}s · precisión ${it.text("accuracy_m")} m")
            Text("Última coordenada recibida: latitud ${it.text("latitude")}, longitud ${it.text("longitude")}")
            if(age>30 || !live.connected)Text("Última observación; no se considera ubicación actual.")
        }
    }
    val pendingObservations=entries.count {it.text("state") in setOf("PENDING","SENDING","UNCERTAIN")}
    val recordedObservations=entries.count {it.text("state")=="RECORDED"}
    val reviewObservations=entries.size-pendingObservations-recordedObservations
    val observationSummary="$pendingObservations pendientes · $recordedObservations enviadas · $reviewObservations para revisar"
    SettingRow("Observaciones",observationSummary) {observationsView=!observationsView}
    row?.let {task ->
        val transport=session.user?.text("role")=="TRANSPORT"
        val action=transportAction(session.user?.text("role").orEmpty(),task.text("status"))
        if(transport && action!=null) {
            OutlinedButton(enabled=!busy,onClick={error="";observationDialog=true}) {Text("Añadir observación")}
            if(observationDialog) AlertDialog(
                onDismissRequest={if(!busy)observationDialog=false},
                title={Text("Añadir observación")},
                text={Column(verticalArrangement=Arrangement.spacedBy(8.dp)) {
                    Text("La observación no cambia el estado del traslado. Se guardará en Pendientes para enviarla después.")
                    OutlinedTextField(observationDraft,{observationDraft=it},label={Text("Observación")},
                        supportingText={Text("${observationDraft.trim().length} / 1000 caracteres · mínimo 6")},minLines=3,maxLines=6)
                    if(error.isNotBlank()) Text(error)
                }},
                confirmButton={Button(enabled=!busy && observationDraft.trim().length in 6..1000,onClick={saveObservation(task,observationDraft)}) {Text("Guardar observación")}},
                dismissButton={TextButton(enabled=!busy,onClick={observationDialog=false}) {Text("Cancelar")}})
        }
    }
    if(observationsView) {
    Text("Sincroniza tus observaciones cuando tengas conexión. Las enviadas permanecen en el historial.")
    entries.forEach {Text("${displayBriefDate(it.getValue("command").jsonObject.text("captured_at"))} · ${displayValue("state",it.text("state"))}")}
    OutlinedButton(enabled=!busy,onClick={run{queue.synchronize(manual=true);entries=queue.entries()}}){Text("Sincronizar y consultar resultados")}
    }
}
