package org.redhouse.mobile

import androidx.compose.runtime.*
import androidx.compose.foundation.layout.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.material3.*
import kotlinx.coroutines.*
import kotlinx.serialization.json.*
import kotlinx.datetime.Clock

/** The shell bar already offers «Volver» and the destination title; the detail only adds a subtitle when it differs. */
@Composable fun OperationalDetail(screen:Screen,id:String,repository:MobileRepository,devices:DeviceAccess,shellTitle:String){
    var row by remember {mutableStateOf<JsonObject?>(null)};var status by remember{mutableStateOf("")}
    var temperature by remember{mutableStateOf("")};var reference by remember{mutableStateOf("")};var confirmed by remember{mutableStateOf(false)}
    var busy by remember{mutableStateOf(false)};val scope=rememberCoroutineScope()
    fun run(action:suspend ()->Unit){if(busy)return;busy=true;scope.launch{try{action()}catch(e:CancellationException){throw e}catch(e:Exception){status=if(e is ApiFailure || e is IllegalArgumentException)e.message.orEmpty() else "Sin confirmación; consulta resultados pendientes."}finally{busy=false}}}
    LaunchedEffect(id){try{row=repository.session.request(screen.service,screen.path+"/"+id)}catch(e:CancellationException){throw e}catch(e:Exception){status=if(e is ApiFailure)e.message.orEmpty() else "No se pudo consultar la información."}}
    detailSubtitle(screen.title,shellTitle)?.let{Text(it,style=MaterialTheme.typography.titleMedium)}
    if(status.isNotBlank())Text(status)
    row?.let{value->
        listOf("folio","identifier","kind","component","status","quantity","urgency","expires_at","version","created_at","severity","message_code","test_code","result_state","value","unit","method","laboratory","reference","measured_at").forEach{key->(value[key] as? JsonPrimitive)?.contentOrNull?.let{Text("${fieldLabel(key)}: ${displayValue(key, it)}")}}
        if(screen.service=="inventario" && repository.session.user?.text("role")=="OPERATOR"){
            Button(enabled=!busy,onClick={devices.scan{code,error->if(code!=null)run{require(code==id){"El código no pertenece a la unidad abierta."};row=repository.session.request("inventario","/api/v1/resources/$id");status="Unidad consultada y autorizada por Inventario"}else status=error.orEmpty()}}){Text("Escanear y consultar unidad")}
            OutlinedTextField(temperature,{temperature=it},label={Text("Lectura manual en °C")})
            OutlinedTextField(reference,{reference=it},label={Text("Referencia de calibración del instrumento")})
            Button(enabled=!busy && finiteTemperature(temperature)!=null && reference.isNotBlank(),onClick={confirmed=true}){Text("Registrar lectura manual")}
            if(confirmed)AlertDialog(onDismissRequest={confirmed=false},title={Text("Confirmar lectura observada")},text={Text("El servidor comprobará equipo, perfil térmico y restricciones. Esta captura no libera la unidad.")},confirmButton={Button(onClick={confirmed=false;run{
                val result=repository.execute("inventario","/api/v1/resources/$id/cold-readings",buildJsonObject{put("temperature_c",temperature.toDouble());put("captured_at",Clock.System.now().toString());put("source","MANUAL_MOVIL");put("calibration_reference",reference)})
                status="Lectura registrada. Excursión: ${result.text("excursion")}; intervalo: ${result.text("gap")}";temperature=""
            }}){Text("Confirmar")}},dismissButton={TextButton(onClick={confirmed=false}){Text("Cancelar")}})
        }
        (value["coverage"] as? JsonArray)?.forEach{val row=it.jsonObject;Text("Cobertura ${row.text("status")}: ${row.text("quantity")}")}
        (value["movements"] as? JsonArray)?.forEach{val row=it.jsonObject;Text("${row.text("action")} · ${row.text("created_at")}")}
        if(screen.service=="compatibilidad") {
            Text("Resultados institucionales autorizados. La completitud no constituye aprobación ni elegibilidad clínica.")
            if(screen.path.endsWith("/samples"))Button(enabled=!busy,onClick={run{
                val result=repository.session.request("compatibilidad","/api/v1/laboratory/samples/$id/completeness")
                status="Completitud: ${result.text("complete")} · perfil ${result.text("profile_version")} · sintético ${result.text("synthetic")} · faltantes: "+(result["missing"] as? JsonArray)?.joinToString{it.jsonPrimitive.content}.orEmpty()
            }}){Text("Consultar completitud registrada")}
        }
        if(screen.service=="receptores")Text("Consulta operativa. Evaluación y autorizaciones clínicas se realizan en los flujos institucionales habilitados.")
        if(screen.service=="alertas")Button(enabled=!busy,onClick={run{repository.execute("alertas","/api/v1/alerts/$id/acknowledge");status="Aviso reconocido"}}){Text("Marcar leído")}
    }
}

@Composable fun CoordinatorPlanning(repository:MobileRepository){
    var reservation by remember{mutableStateOf("")};var responsible by remember{mutableStateOf("")}
    var chosenReservation by remember{mutableStateOf<JsonObject?>(null)};var responsibleName by remember{mutableStateOf("")}
    var reservations by remember{mutableStateOf<List<JsonObject>>(emptyList())};var transporters by remember{mutableStateOf<List<JsonObject>>(emptyList())}
    var reservationPage by remember{mutableIntStateOf(1)};var transporterPage by remember{mutableIntStateOf(1)}
    var reservationTotal by remember{mutableIntStateOf(0)};var transporterTotal by remember{mutableIntStateOf(0)}
    var choosingReservation by remember{mutableStateOf(false)};var choosingTransporter by remember{mutableStateOf(false)}
    var reservationLoading by remember{mutableStateOf(true)};var transporterLoading by remember{mutableStateOf(true)}
    var reservationError by remember{mutableStateOf(false)};var transporterError by remember{mutableStateOf(false)}
    var reservationRetry by remember{mutableIntStateOf(0)};var transporterRetry by remember{mutableIntStateOf(0)}
    var departure by remember{mutableStateOf("")};var eta by remember{mutableStateOf("")};var reason by remember{mutableStateOf("")}
    var status by remember{mutableStateOf("")};var busy by remember{mutableStateOf(false)};var confirm by remember{mutableStateOf(false)}
    val scope=rememberCoroutineScope()
    LaunchedEffect(reservationPage,reservationRetry) {reservationLoading=true;reservationError=false;try {
        val page=repository.listPage("inventario","/api/v1/reservations?status=RESERVED&unplanned=true",reservationPage)
        reservations=page.getValue("items").jsonArray.map{it.jsonObject};reservationTotal=page.getValue("total").jsonPrimitive.int
    } catch(e:CancellationException){throw e} catch(_:Exception){reservationError=true} finally {reservationLoading=false}}
    LaunchedEffect(transporterPage,transporterRetry) {transporterLoading=true;transporterError=false;try {
        val page=repository.listPage("identidad","/api/v1/users?role=TRANSPORT",transporterPage)
        transporters=page.getValue("items").jsonArray.map{it.jsonObject};transporterTotal=page.getValue("total").jsonPrimitive.int
    } catch(e:CancellationException){throw e} catch(_:Exception){transporterError=true} finally {transporterLoading=false}}
    Text("Programar traslado sobre reserva autorizada",style=MaterialTheme.typography.titleMedium);if(status.isNotBlank())Text(status)
    SettingRow("Reserva",chosenReservation?.let {"Registrada: ${displayBriefDate(it.text("created_at"))}"} ?: "Selecciona una reserva") {choosingReservation=!choosingReservation}
    if(choosingReservation) {
        if(reservationLoading) Text("Consultando reservas…")
        else if(reservationError) TextButton(onClick={reservationRetry++}) {Text("No se pudieron consultar las reservas. Reintentar")}
        else if(reservations.isEmpty()) Text("No hay reservas disponibles en esta página.")
        if(!reservationLoading && !reservationError) reservations.forEach {item ->
            Column {
                TextButton(modifier=Modifier.testTag("reservation:"+item.text("id")),onClick={chosenReservation=item;reservation=item.text("id");responsible="";responsibleName="";choosingReservation=false}) {
                    Text("Reserva del ${displayBriefDate(item.text("created_at"))}")
                }
                Text("Referencia: ${item.text("id").take(8)}",style=MaterialTheme.typography.labelSmall)
            }
        }
        if(reservationTotal>20) Row {
            TextButton(enabled=reservationPage>1,onClick={reservationPage--}){Text("Anterior")}
            TextButton(enabled=reservationPage*20<reservationTotal,onClick={reservationPage++}){Text("Siguiente")}
        }
    }
    SettingRow("Transportista",responsibleName.ifBlank {"Selecciona una persona de la institución de origen"}) {choosingTransporter=!choosingTransporter}
    if(choosingTransporter) {
        if(chosenReservation==null) Text("Selecciona primero una reserva.")
        else {
            val candidates=transporters.filter {it.text("tenant_id")==chosenReservation?.text("origin_id")}
            if(transporterLoading) Text("Consultando personal de traslado…")
            else if(transporterError) TextButton(onClick={transporterRetry++}) {Text("No se pudo consultar el personal. Reintentar")}
            else if(candidates.isEmpty())Text("No hay personal de origen en esta página.")
            if(!transporterLoading && !transporterError) candidates.forEach {person -> TextButton(modifier=Modifier.testTag("transporter:"+person.text("id")),onClick={responsible=person.text("id");responsibleName=person.text("username");choosingTransporter=false}) {Text(person.text("username"))} }
            if(transporterTotal>20) Row {
                TextButton(enabled=transporterPage>1,onClick={transporterPage--}){Text("Anterior")}
                TextButton(enabled=transporterPage*20<transporterTotal,onClick={transporterPage++}){Text("Siguiente")}
            }
        }
    }
    Text("Selecciona las fechas y horas del traslado.")
    DateTimeField("salida",departure,{departure=it})
    DateTimeField("llegada prevista",eta,{eta=it})
    OutlinedTextField(reason,{reason=it},label={Text("Motivo de programación")})
    Button(enabled=!busy,onClick={val invalid=planningError(reservation,responsible,departure,eta,reason);if(invalid==null)confirm=true else status=invalid}){Text("Revisar programación")}
    if(confirm)AlertDialog(onDismissRequest={confirm=false},title={Text("Confirmar programación")},text={Text("Se comprobarán reserva, responsable, versión de ruta, tiempos y caducidad. La programación no sustituye asignación clínica.")},confirmButton={Button(onClick={confirm=false;busy=true;scope.launch{
        try{require(planningError(reservation,responsible,departure,eta,reason)==null);val result=repository.execute("transporte","/api/v1/shipments",buildJsonObject{put("reservation_id",reservation.trim());put("transport_user_id",responsible.trim());put("departure_at",departure.trim());put("eta",eta.trim());put("reason",reason.trim());put("human_confirmation",true)});status="Traslado programado · ${displayValue("status",result.text("status"))}"}
        catch(e:CancellationException){throw e}catch(e:Exception){status=if(e is ApiFailure)e.message.orEmpty() else "Sin confirmación; recupera la operación pendiente."}finally{busy=false}
    }}){Text("Confirmar")}},dismissButton={TextButton(onClick={confirm=false}){Text("Cancelar")}})
}

/** Subtitle for a nested detail; null when it would repeat the title already shown in the shell bar. */
internal fun detailSubtitle(screenTitle:String,shellTitle:String):String? = screenTitle.takeIf{it.isNotBlank() && it!=shellTitle}
