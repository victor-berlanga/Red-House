package org.redhouse.mobile

import androidx.compose.runtime.*
import androidx.compose.material3.*
import kotlinx.coroutines.*
import kotlinx.serialization.json.*
import kotlinx.datetime.Clock

@Composable fun OperationalDetail(screen:Screen,id:String,repository:MobileRepository,devices:DeviceAccess,onBack:()->Unit){
    var row by remember {mutableStateOf<JsonObject?>(null)};var status by remember{mutableStateOf("")}
    var temperature by remember{mutableStateOf("")};var reference by remember{mutableStateOf("")};var confirmed by remember{mutableStateOf(false)}
    var busy by remember{mutableStateOf(false)};val scope=rememberCoroutineScope()
    fun run(action:suspend ()->Unit){if(busy)return;busy=true;scope.launch{try{action()}catch(e:CancellationException){throw e}catch(e:Exception){status=if(e is ApiFailure || e is IllegalArgumentException)e.message.orEmpty() else "Sin confirmación; consulta resultados pendientes."}finally{busy=false}}}
    LaunchedEffect(id){try{row=repository.session.request(screen.service,screen.path+"/"+id)}catch(e:Exception){status=e.message.orEmpty()}}
    TextButton(onClick=onBack){Text("Volver")};Text(screen.title);Text(status)
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

@Composable fun CoordinatorPlanning(repository:MobileRepository,onBack:()->Unit){
    var reservation by remember{mutableStateOf("")};var responsible by remember{mutableStateOf("")}
    var departure by remember{mutableStateOf("")};var eta by remember{mutableStateOf("")};var reason by remember{mutableStateOf("")}
    var status by remember{mutableStateOf("")};var busy by remember{mutableStateOf(false)};var confirm by remember{mutableStateOf(false)}
    val scope=rememberCoroutineScope()
    TextButton(onClick=onBack){Text("Volver")};Text("Programar traslado sobre reserva autorizada");Text(status)
    OutlinedTextField(reservation,{reservation=it},label={Text("Referencia de reserva confirmada")})
    OutlinedTextField(responsible,{responsible=it},label={Text("Referencia del transportista de origen")})
    Text("Copia las referencias completas del registro autorizado. Fechas: AAAA-MM-DDTHH:MM:SS±HH:MM; Z indica UTC.")
    OutlinedTextField(departure,{departure=it},label={Text("Salida · fecha, hora y zona")})
    OutlinedTextField(eta,{eta=it},label={Text("Llegada prevista · fecha, hora y zona")})
    OutlinedTextField(reason,{reason=it},label={Text("Motivo de programación")})
    Button(enabled=!busy,onClick={val invalid=planningError(reservation,responsible,departure,eta,reason);if(invalid==null)confirm=true else status=invalid}){Text("Revisar programación")}
    if(confirm)AlertDialog(onDismissRequest={confirm=false},title={Text("Confirmar programación")},text={Text("Se comprobarán reserva, responsable, versión de ruta, tiempos y caducidad. La programación no sustituye asignación clínica.")},confirmButton={Button(onClick={confirm=false;busy=true;scope.launch{
        try{require(planningError(reservation,responsible,departure,eta,reason)==null);val result=repository.execute("transporte","/api/v1/shipments",buildJsonObject{put("reservation_id",reservation.trim());put("transport_user_id",responsible.trim());put("departure_at",departure.trim());put("eta",eta.trim());put("reason",reason.trim());put("human_confirmation",true)});status="Traslado ${result.text("id")} · ${result.text("status")}"}
        catch(e:CancellationException){throw e}catch(e:Exception){status=if(e is ApiFailure)e.message.orEmpty() else "Sin confirmación; recupera la operación pendiente."}finally{busy=false}
    }}){Text("Confirmar")}},dismissButton={TextButton(onClick={confirm=false}){Text("Cancelar")}})
}
