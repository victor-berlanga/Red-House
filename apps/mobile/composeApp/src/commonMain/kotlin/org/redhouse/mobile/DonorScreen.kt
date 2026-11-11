package org.redhouse.mobile

import androidx.compose.runtime.*
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import kotlinx.coroutines.*
import kotlinx.serialization.json.*
import kotlinx.datetime.Clock
import io.ktor.http.encodeURLParameter

/** Own records only. No local eligibility calculation and no self-link by folio. */
@Composable fun DonorScreen(repository:MobileRepository,initialSection:String="Citas",onBack:()->Unit) {
    var section by remember {mutableStateOf(initialSection)}
    var appointmentId by remember {mutableStateOf<String?>(null)}
    val session=repository.session;val scope=rememberCoroutineScope()
    var donor by remember {mutableStateOf<JsonObject?>(null)}
    var ownDonors by remember {mutableStateOf<List<JsonObject>>(emptyList())}
    var slots by remember {mutableStateOf<List<JsonObject>>(emptyList())}
    var appointments by remember {mutableStateOf<List<JsonObject>>(emptyList())}
    var consents by remember {mutableStateOf<List<JsonObject>>(emptyList())}
    var sites by remember {mutableStateOf<List<JsonObject>>(emptyList())}
    var campaigns by remember {mutableStateOf<List<JsonObject>>(emptyList())}
    var publications by remember {mutableStateOf<List<JsonObject>>(emptyList())}
    var name by remember {mutableStateOf("")};var group by remember {mutableStateOf("")}
    var consent by remember {mutableStateOf(false)};var policy by remember {mutableStateOf("")};var reference by remember {mutableStateOf("")}
    var site by remember {mutableStateOf("")};var from by remember {mutableStateOf("")};var until by remember {mutableStateOf("")}
    var status by remember {mutableStateOf("")};var busy by remember {mutableStateOf(true)}
    var reschedule by remember {mutableStateOf<JsonObject?>(null)}
    var confirmation by remember {mutableStateOf<Pair<String,suspend ()->Unit>?>(null)}
    fun items(value:JsonObject)=(value["items"] as? JsonArray)?.map{it.jsonObject}?:emptyList()
    suspend fun reload(){
        ownDonors=items(session.request("donantes","/api/v1/donors?page_size=100")).filter{it.text("user_id")==session.user!!.text("id")}
        donor=ownDonors.firstOrNull{it.text("id")==donor?.text("id")}?:ownDonors.firstOrNull()
        appointments=items(session.request("donantes","/api/v1/appointments?page_size=100"))
        donor?.let{consents=items(session.request("donantes","/api/v1/donors/${it.text("id")}/consents"))}
        campaigns=items(session.request("donantes","/api/v1/campaigns?page_size=100"))
        sites=items(session.request("identidad","/api/v1/appointment-sites?page_size=100"))
        publications=items(session.request("donantes","/api/v1/public/campaigns"))
    }
    fun run(action:suspend ()->Unit){if(busy)return;busy=true;scope.launch{try{action()}catch(e:CancellationException){throw e}catch(e:Exception){status=if(e is ApiFailure || e is IllegalArgumentException)e.message.orEmpty() else "Sin confirmación; recupera la operación pendiente."}finally{busy=false}}}
    LaunchedEffect(Unit){try{reload()}catch(e:CancellationException){throw e}catch(e:Exception){status=e.message.orEmpty()}finally{busy=false}}
    PresentationBackHandler(section!=initialSection || appointmentId!=null) { if(appointmentId!=null) appointmentId=null else section=initialSection }
    TextButton(onClick={if(appointmentId!=null)appointmentId=null else if(section!=initialSection)section=initialSection else onBack()}){Text("Volver")}
    Text(if(section=="Citas") "Mis citas" else if(section=="Reservar") "Reservar horario" else "Mi expediente",style=MaterialTheme.typography.headlineMedium)
    if(status.isNotBlank())Text(status)
    if(section=="Citas") SettingRow("Buscar horarios") {section="Reservar"}
    if(section=="Reservar") SettingRow("Revisar expediente y consentimiento") {section="Expediente"}
    if(busy)LinearProgressIndicator()
    if(section=="Expediente") {
    if(ownDonors.size>1)ownDonors.forEach{row->TextButton(onClick={donor=row;run{reload()}}){Text("Expediente propio ${row.text("folio")}")}}
    donor?.let {row->
        Text("${row.text("display_name")} · ${row.text("folio")} · estado ${displayValue("status", row.text("status"))}")
        Text("La valoración corresponde al personal autorizado. Solicita correcciones del expediente a tu institución.")
        consents.forEach{Text("Consentimiento ${it.text("policy_version")} · ${if(it["granted"]?.jsonPrimitive?.booleanOrNull==true)"otorgado" else "retirado"} · ${displayDate(it.text("effective_at"))}")}
    }
    if(donor==null) {
        OutlinedTextField(name,{name=it},label={Text("Nombre para el registro preliminar")})
        OutlinedTextField(group,{group=it.uppercase()},label={Text("Grupo sanguíneo declarado; confirmar con la institución")})
    }
    Text("Consentimiento: usa la versión y referencia del documento proporcionado por tu institución. Consulta los requisitos con tu institución.")
    OutlinedTextField(policy,{policy=it},label={Text("Versión de política institucional")})
    OutlinedTextField(reference,{reference=it},label={Text("Referencia del consentimiento revisado")})
    Row {Checkbox(consent,{consent=it},modifier=Modifier.semantics{contentDescription="He revisado y acepto el consentimiento indicado"});Text("He revisado y acepto el consentimiento indicado")}
    Button(enabled=!busy && consent && policy.isNotBlank() && reference.isNotBlank(),onClick={confirmation="Registrar consentimiento" to {
        if(donor==null){
            require(name.isNotBlank() && group in setOf("O-","O+","A-","A+","B-","B+","AB-","AB+")){"Revisa nombre y grupo declarado."}
            donor=repository.execute("donantes","/api/v1/donors",buildJsonObject{put("folio","MOV-"+newId().take(20));put("display_name",name);put("blood_group",group);put("consent",true)})
        }
        val row=donor!!
        repository.execute("donantes","/api/v1/donors/${row.text("id")}/consents",buildJsonObject{
            put("version",row.getValue("version"));put("policy_version",policy);put("reference",reference);put("effective_at",Clock.System.now().toString());put("granted",true);put("human_confirmation",true);put("reason","Consentimiento explícito revisado por el titular")
        });reload();status="Consentimiento confirmado por Donantes"
    }}){Text(if(donor==null)"Registrar expediente propio" else "Actualizar consentimiento")}
    donor?.let{row->TextButton(enabled=!busy && policy.isNotBlank() && reference.isNotBlank(),onClick={confirmation="Retirar consentimiento" to {
        repository.execute("donantes","/api/v1/donors/${row.text("id")}/consents",buildJsonObject{put("version",row.getValue("version"));put("policy_version",policy);put("reference",reference);put("effective_at",Clock.System.now().toString());put("granted",false);put("human_confirmation",true);put("reason","Retiro explícito solicitado por el titular")});reload()
    }}){Text("Retirar consentimiento")}}
    }
    if(section=="Reservar") {
    Text("Campañas y sedes autorizadas",style=MaterialTheme.typography.titleMedium)
    Text("Información publicada por las instituciones; no constituye evaluación de aptitud.")
    publications.forEach {Text("${it.text("title")} · ${it.text("venue")}\n${it.text("information")}")}
    if(publications.isEmpty())Text("Sin información general publicada. Solicita requisitos y contacto a tu institución.")
    campaigns.forEach {Text("${it.text("title")} · ${displayDate(it.text("starts_at"))} / ${displayDate(it.text("ends_at"))}")}
    TextButton(onClick={site=""}){Text("Todas las sedes")}
    sites.forEach{row->TextButton(onClick={site=row.text("id")}){Text(row.text("name"))}}
    Text("Sede seleccionada: ${site.ifBlank{"Todas"}}")
    Text("Periodo opcional. Usa AAAA-MM-DDTHH:MM:SS±HH:MM; Z indica UTC. Conserva la zona comunicada por la institución.")
    OutlinedTextField(from,{from=it},label={Text("Desde · fecha, hora y zona (opcional)")})
    OutlinedTextField(until,{until=it},label={Text("Hasta · fecha, hora y zona (opcional)")})
    Button(enabled=!busy,onClick={run{
        val query=buildList{add("active=true");add("page_size=100");add("date_field=starts_at");if(site.isNotBlank())add("site_id="+site.encodeURLParameter());if(from.isNotBlank())add("from_at="+from.encodeURLParameter());if(until.isNotBlank())add("until_at="+until.encodeURLParameter())}.joinToString("&")
        slots=items(session.request("donantes","/api/v1/campaign-slots?$query"));status="Disponibilidad consultada"
    }}){Text("Consultar horarios")}
    reschedule?.let{Text("Elige nuevo horario para la cita ${it.text("id").take(8)}");TextButton(onClick={reschedule=null}){Text("Cancelar cambio")}}
    slots.forEach{slot->key("slot:"+slot.text("id")){
        Text("${displayDate(slot.text("starts_at"))} · disponibles ${slot.text("available")}")
        Button(enabled=!busy && donor!=null && (slot["available"]?.jsonPrimitive?.intOrNull?:0)>0,onClick={confirmation="Confirmar horario ${displayDate(slot.text("starts_at"))}" to {
            val old=reschedule
            if(old==null)repository.execute("donantes","/api/v1/appointments",obj("donor_id" to donor!!.text("id"),"campaign_id" to slot.text("campaign_id"),"slot_id" to slot.text("id")))
            else {val schedule=session.request("donantes","/api/v1/appointments/${old.text("id")}/schedule")
                repository.execute("donantes","/api/v1/appointments/${old.text("id")}/commands",buildJsonObject{put("action","RESCHEDULE");put("slot_id",slot.text("id"));put("version",schedule.getValue("version"));put("human_confirmation",true);put("reason","Cambio de horario solicitado por el titular")})}
            reschedule=null;reload();section="Citas";appointmentId=null;status="Cita confirmada por Donantes"
        }}){Text(if(reschedule==null)"Agendar" else "Cambiar a este horario")}
    }}
    }
    if(section=="Citas") {
    Text("Citas consultadas",style=MaterialTheme.typography.titleMedium)
    appointments.forEach{row->key("appointment:"+row.text("id")){
        Text("${row.text("id").take(8)} · ${displayValue("status", row.text("status"))} · ${displayDate(row.text("scheduled_at"))}")
        TextButton(onClick={appointmentId=if(appointmentId==row.text("id"))null else row.text("id")}){Text("Consultar cita")}
        if(appointmentId==row.text("id") && row.text("status")=="BOOKED"){
            TextButton(onClick={reschedule=row;section="Reservar"}){Text("Reprogramar")}
            TextButton(enabled=!busy,onClick={confirmation="Cancelar cita" to {repository.execute("donantes","/api/v1/appointments/${row.text("id")}/cancel");reload();status="Cancelación confirmada"}}){Text("Cancelar cita")}
            TextButton(enabled=!busy,onClick={confirmation="Confirmar asistencia prevista" to {val schedule=session.request("donantes","/api/v1/appointments/${row.text("id")}/schedule");repository.execute("donantes","/api/v1/appointments/${row.text("id")}/commands",buildJsonObject{put("action","CONFIRM");put("version",schedule.getValue("version"));put("human_confirmation",true);put("reason","Confirmación de asistencia por el titular")});reload()}}){Text("Confirmar asistencia prevista")}
        }
    }}
    }
    val pending=confirmation
    if(pending!=null)DonorConfirmationDialog(pending.first,busy,
        onConfirm={confirmation=null;run(pending.second)},onDismiss={confirmation=null})
    OutlinedButton(enabled=!busy,onClick={run{reload()}}){Text("Actualizar expediente e historial")}
}

@Composable
private fun DonorConfirmationDialog(title:String,busy:Boolean,onConfirm:()->Unit,onDismiss:()->Unit){
    AlertDialog(onDismissRequest=onDismiss,title={Text(title)},
        text={Text("El servidor revalidará identidad, versión, consentimiento y disponibilidad.")},
        confirmButton={Button(enabled=!busy,onClick=onConfirm){Text("Confirmar")}},
        dismissButton={TextButton(onClick=onDismiss){Text("Volver")}})
}
