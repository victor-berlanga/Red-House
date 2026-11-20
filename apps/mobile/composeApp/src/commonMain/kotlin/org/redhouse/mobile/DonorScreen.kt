package org.redhouse.mobile

import androidx.compose.runtime.*
import kotlinx.datetime.LocalDate
import kotlinx.datetime.TimeZone
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalFocusManager
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.liveRegion
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.*
import kotlinx.serialization.json.*
import io.ktor.http.encodeURLParameter
import io.ktor.http.HttpMethod

/** Own records only. No local eligibility calculation and no self-link by folio. */
@Composable fun DonorScreen(repository:MobileRepository,initialSection:String="Citas",showBack:Boolean=true,devices:DeviceAccess?=null,onExploreCampaigns:()->Unit={},onOpenAppointments:()->Unit={},onOpenNotices:()->Unit={},onBack:()->Unit) {
    var section by remember(initialSection) {mutableStateOf(initialSection)}
    val share = rememberPublicShare()
    val focusManager = LocalFocusManager.current
    var appointmentId by remember {mutableStateOf<String?>(null)}
    val session=repository.session;val scope=rememberCoroutineScope()
    var donor by remember {mutableStateOf<JsonObject?>(null)}
    var ownDonors by remember {mutableStateOf<List<JsonObject>>(emptyList())}
    var slots by remember {mutableStateOf<List<JsonObject>>(emptyList())}
    var slotsCurrent by remember {mutableStateOf(false)}
    var bookingMessage by remember {mutableStateOf("")}
    var bookingSlotId by remember {mutableStateOf("")}
    var appointments by remember {mutableStateOf<List<JsonObject>>(emptyList())}
    var nextAppointment by remember {mutableStateOf<JsonObject?>(null)}
    var nextLoaded by remember {mutableStateOf(false)}
    var unread by remember {mutableStateOf<Int?>(null)}
    var consents by remember {mutableStateOf<List<JsonObject>>(emptyList())}
    var latestConsent by remember {mutableStateOf<JsonObject?>(null)}
    var consentLoaded by remember {mutableStateOf(false)}
    var consentDoc by remember {mutableStateOf(ConsentDoc(ConsentDocStatus.Unknown))}
    var consentPage by remember {mutableIntStateOf(1)};var consentTotal by remember {mutableIntStateOf(0)}
    var editName by remember {mutableStateOf(false)};var nameDraft by remember {mutableStateOf("")}
    var sites by remember {mutableStateOf<List<JsonObject>>(emptyList())}
    var campaigns by remember {mutableStateOf<List<JsonObject>>(emptyList())}
    var publications by remember {mutableStateOf<List<JsonObject>>(emptyList())}
    var publicationsLoaded by remember {mutableStateOf(false)}
    var publicPage by remember {mutableIntStateOf(1)};var publicTotal by remember {mutableIntStateOf(0)}
    var publicQuery by remember {mutableStateOf("")};var publicFrom by remember {mutableStateOf("")};var publicUntil by remember {mutableStateOf("")}
    var queryDraft by remember {mutableStateOf("")};var fromDraft by remember {mutableStateOf<LocalDate?>(null)};var untilDraft by remember {mutableStateOf<LocalDate?>(null)}
    var publicFilters by remember {mutableStateOf(false)}
    var site by remember {mutableStateOf("")};var siteName by remember {mutableStateOf("")};var from by remember {mutableStateOf<LocalDate?>(null)};var until by remember {mutableStateOf<LocalDate?>(null)}
    var status by remember {mutableStateOf("")};var busy by remember {mutableStateOf(true)}
    fun items(value:JsonObject)=(value["items"] as? JsonArray)?.map{it.jsonObject}?:emptyList()
    var donorPage by remember {mutableIntStateOf(1)};var appointmentPage by remember {mutableIntStateOf(1)}
    var sitePage by remember {mutableIntStateOf(1)};var campaignPage by remember {mutableIntStateOf(1)};var slotPage by remember {mutableIntStateOf(1)}
    var donorListLoaded by remember {mutableStateOf(false)}
    var registrationMessage by remember {mutableStateOf("")}
    var donorTotal by remember {mutableIntStateOf(0)};var appointmentTotal by remember {mutableIntStateOf(0)}
    var siteTotal by remember {mutableIntStateOf(0)};var campaignTotal by remember {mutableIntStateOf(0)};var slotTotal by remember {mutableIntStateOf(0)}
    var slotQuery by remember {mutableStateOf("active=true&date_field=starts_at")}
    fun total(value:JsonObject)=value["total"]?.jsonPrimitive?.intOrNull ?: throw ApiFailure(502,"response_contract")
    suspend fun loadDonors(page:Int=donorPage){donorListLoaded=false;val data=checkedPage(repository.listPage("donantes","/api/v1/donors",page),page);ownDonors=items(data).filter{it.text("user_id")==session.user!!.text("id")};donorTotal=total(data);donorPage=page;donorListLoaded=true}
    suspend fun loadAppointments(page:Int=appointmentPage){val data=checkedPage(repository.listPage("donantes","/api/v1/appointments/agenda",page),page);appointments=items(data);appointmentTotal=total(data);appointmentPage=page}
    suspend fun loadSites(page:Int=sitePage){val data=checkedPage(repository.listPage("identidad","/api/v1/appointment-sites",page),page);sites=items(data);siteTotal=total(data);sitePage=page}
    suspend fun loadCampaigns(page:Int=campaignPage){val data=checkedPage(repository.listPage("donantes","/api/v1/campaigns",page),page);campaigns=items(data);campaignTotal=total(data);campaignPage=page}
    suspend fun loadSlots(page:Int=slotPage,query:String=slotQuery){slotsCurrent=false;val data=checkedPage(repository.listPage("donantes","/api/v1/campaign-slots?$query",page),page);slots=items(data);slotTotal=total(data);slotPage=page;slotQuery=query;slotsCurrent=true}
    suspend fun loadConsents(donorId:String,page:Int){
        val data=checkedPage(repository.listPage("donantes","/api/v1/donors/$donorId/consents",page),page)
        consents=items(data);consentTotal=total(data);consentPage=page
        if(page==1) {latestConsent=consents.firstOrNull();consentLoaded=true}
    }
    suspend fun loadPublications(page:Int=publicPage,query:String=publicQuery,from:String=publicFrom,until:String=publicUntil){
        val data=checkedPage(repository.publicCampaignPage(page,query,from,until),page)
        publications=items(data);publicTotal=total(data);publicPage=page
        publicQuery=query;publicFrom=from;publicUntil=until;publicationsLoaded=true
    }
    var reschedule by remember {mutableStateOf<JsonObject?>(null)}
    var confirmationDetails by remember {mutableStateOf("")}
    var confirmation by remember {mutableStateOf<Pair<String,suspend ()->Unit>?>(null)}
    suspend fun reload(){
        try {loadPublications()} catch(e:CancellationException){throw e} catch(_:Exception) {publicationsLoaded=false}
        loadDonors()
        donor=ownDonors.firstOrNull{it.text("id")==donor?.text("id")}?:ownDonors.firstOrNull()
        loadAppointments()
        nextLoaded=false
        val nextResponse=session.request("donantes","/api/v1/appointments/next")
        require(nextResponse.containsKey("appointment")) { "No se pudo consultar la próxima cita." }
        nextAppointment=nextResponse["appointment"] as? JsonObject;nextLoaded=true
        consents=emptyList();latestConsent=null;consentLoaded=false;consentPage=1;consentTotal=0
        donor?.let{loadConsents(it.text("id"),1)}
        // Documento de consentimiento (H2): si falla la consulta queda «Sin comprobar»; nunca se supone que falta.
        consentDoc=ConsentDoc(ConsentDocStatus.Unknown)
        donor?.let{d->consentDoc=try{repository.loadConsentDocument(d.text("id"))}catch(e:CancellationException){throw e}catch(_:Exception){ConsentDoc(ConsentDocStatus.Unknown)}}
        // Avisos sin leer para Inicio: si la consulta falla, simplemente no se muestra el contador.
        unread=try {unreadNotices(items(session.request("alertas","/api/v1/alerts?page=1&page_size=20")))} catch(e:CancellationException){throw e} catch(_:Exception){null}
        loadCampaigns()
        loadSites()
        if(section=="Reservar"){loadSlots(slotPage,slotQuery);bookingMessage=""}
    }
    suspend fun refreshBookingState():Boolean {
        slotsCurrent=false
        var refreshed=true
        try {loadAppointments()}catch(cancelled:CancellationException){throw cancelled}catch(_:Exception){refreshed=false}
        try {loadSlots(slotPage,slotQuery)}catch(cancelled:CancellationException){throw cancelled}catch(_:Exception){refreshed=false}
        return refreshed
    }
    fun run(action:suspend ()->Unit){if(busy)return;busy=true;scope.launch{try{action()}catch(e:CancellationException){throw e}catch(e:Exception){status=if(e is ApiFailure || e is IllegalArgumentException)e.message.orEmpty() else "Sin confirmación; recupera la operación pendiente."}finally{busy=false}}}
    LaunchedEffect(Unit){try{reload()}catch(e:CancellationException){throw e}catch(e:Exception){status=if(e is ApiFailure)e.message.orEmpty() else "No se pudo consultar la información. Inténtalo de nuevo."}finally{busy=false}}
    PresentationBackHandler(section!=initialSection || appointmentId!=null) { if(appointmentId!=null) appointmentId=null else section=initialSection }
    Row(Modifier.fillMaxWidth(),verticalAlignment=androidx.compose.ui.Alignment.CenterVertically) {
        if(showBack || section!=initialSection || appointmentId!=null) TextButton(onClick={if(appointmentId!=null)appointmentId=null else if(section!=initialSection)section=initialSection else onBack()}){Text("Volver")}
        if(section!="Inicio") Text(when(section){"Citas"->"Mis citas";"Campañas"->"Campañas públicas";"Reservar"->"Reservar horario";else->"Mi expediente"},style=MaterialTheme.typography.headlineSmall)
    }
    if(status.isNotBlank())Text(status)
    if(section=="Inicio") {
        // Siguiente paso: completar registro, ver la cita próxima o reservar. Una sola acción principal.
        val next=nextAppointment
        val baseStep=donorNextStep(donorListLoaded,donor!=null,nextLoaded,next,busy)
        val step=donorNextStepWithConsent(baseStep,donor!=null,consentDoc)
        val reminder=consentReminder(baseStep,donor!=null,consentDoc)
        Card(Modifier.fillMaxWidth(),colors=CardDefaults.cardColors(containerColor=MaterialTheme.colorScheme.primaryContainer,contentColor=MaterialTheme.colorScheme.onPrimaryContainer)) { Column(Modifier.padding(16.dp),verticalArrangement=Arrangement.spacedBy(10.dp)) {
            Text(if(step.kind==DonorStepKind.Appointment) "Tu próxima cita" else "Siguiente paso",style=MaterialTheme.typography.labelLarge)
            Text(step.title,style=MaterialTheme.typography.titleLarge)
            if(step.kind==DonorStepKind.Appointment && next!=null) {
                Text(displayBriefDate(next.text("starts_at")),style=MaterialTheme.typography.titleMedium)
                StatusChip(next.text("status"))
            }
            if(step.kind==DonorStepKind.Book) Text("Elige una campaña y un horario disponible.")
            if(step.kind==DonorStepKind.Register) Text("Tu institución revisará la información.")
            if(step.kind==DonorStepKind.Consent) Text("Tu institución lo necesita para revisar tu expediente.")
            if(step.kind!=DonorStepKind.Loading) Button(onClick={when(step.kind){
                DonorStepKind.Register, DonorStepKind.Consent -> section="Expediente"
                DonorStepKind.Appointment -> onOpenAppointments()
                DonorStepKind.Book -> section="Reservar"
                else -> run{reload()}
            }},modifier=Modifier.fillMaxWidth().heightIn(min=56.dp)) {Text(step.action,style=MaterialTheme.typography.titleMedium)}
        } }
        reminder?.let { OutlinedButton(onClick={section="Expediente"},modifier=Modifier.fillMaxWidth().heightIn(min=48.dp)) {Text(it)} }
        donor?.takeIf{it.text("status")=="PRELIMINARY"}?.let { Row(verticalAlignment=androidx.compose.ui.Alignment.CenterVertically,horizontalArrangement=Arrangement.spacedBy(8.dp)) {Text("Registro");StatusChip("PRELIMINARY")} }
        unread?.takeIf{it>0}?.let { count -> OutlinedButton(onClick=onOpenNotices,modifier=Modifier.fillMaxWidth().heightIn(min=48.dp)) {Text(if(count==1) "1 aviso sin leer" else "$count avisos sin leer")} }
        Row(Modifier.fillMaxWidth(),horizontalArrangement=Arrangement.SpaceBetween,verticalAlignment=androidx.compose.ui.Alignment.CenterVertically) {
            Text("Campañas cercanas",style=MaterialTheme.typography.titleLarge)
            TextButton(onClick=onExploreCampaigns,modifier=Modifier.heightIn(min=48.dp)) {Text("Ver todas")}
        }
    }
    if(section in setOf("Inicio","Campañas")) {
        if(section=="Campañas") {
            SettingRow("Buscar y filtrar campañas",expanded=publicFilters) {publicFilters=!publicFilters}
            if(publicFilters) {
                OutlinedTextField(queryDraft,{queryDraft=it.take(100)},label={Text("Campaña o sede")},singleLine=true,modifier=Modifier.fillMaxWidth())
                DateFilterField("Desde",fromDraft,{fromDraft=it})
                DateFilterField("Hasta",untilDraft,{untilDraft=it})
                Button(enabled=!busy,onClick={
                    focusManager.clearFocus()
                    if(fromDraft!=null && untilDraft!=null && fromDraft!!>untilDraft!!) status="La fecha final debe ser igual o posterior a la inicial."
                    else {val (start,end)=dayFilterBounds(fromDraft,untilDraft,TimeZone.currentSystemDefault());status="";run{loadPublications(1,queryDraft.trim(),start,end)}}
                }) {Text("Buscar campañas")}
            }
        }
        if(!busy && !publicationsLoaded) Text("No fue posible consultar las campañas públicas. Actualiza para intentar de nuevo.")
        if(!busy && publicationsLoaded && publications.isEmpty()) Text(if(publicQuery.isNotBlank() || publicFrom.isNotBlank() || publicUntil.isNotBlank()) "No encontramos campañas con estos filtros." else "No hay campañas publicadas en este momento.")
        if(section=="Campañas") PageControls(publicPage,publicTotal,!busy,{run{loadPublications(publicPage-1)}},{run{loadPublications(publicPage+1)}},"al inicio")
        (if(section=="Inicio") publications.take(2) else publications).forEach { publication ->
            Card(Modifier.fillMaxWidth()) { Column(Modifier.padding(16.dp),verticalArrangement=Arrangement.spacedBy(6.dp)) {
                Text(publication.text("title"),style=MaterialTheme.typography.titleMedium)
                Text("${displayBriefDate(publication.text("starts_at"))} – ${displayBriefDate(publication.text("ends_at"))}")
                Text(publication.text("venue")); Text(publication.text("information"))
                TextButton(onClick={share(publicCampaignText(publication))}) {Text("Compartir campaña")}
            } }
        }
        PageControls(publicPage,publicTotal,!busy,{run{loadPublications(publicPage-1)}},{run{loadPublications(publicPage+1)}},"al final")
        if(section=="Campañas") Button(onClick={section="Reservar"}) {Text("Buscar horarios disponibles")}
    }
    if(section=="Citas") SettingRow("Buscar horarios") {section="Reservar"}
    if(section=="Reservar") SettingRow("Revisar expediente y consentimiento") {section="Expediente"}
    if(busy)LinearProgressIndicator()
    if(section=="Expediente") {
    if(donorTotal>1)ownDonors.forEach{row->TextButton(onClick={donor=row;consents=emptyList();latestConsent=null;consentLoaded=false;consentPage=1;consentTotal=0;editName=false;run{reload()}}){Text("Expediente propio ${row.text("folio")}")}}
    if(donorTotal>20) PageControls(donorPage,donorTotal,!busy,{run{loadDonors(donorPage-1)}},{run{loadDonors(donorPage+1)}})
    donor?.let {row->
        Text(row.text("display_name"),style=MaterialTheme.typography.titleMedium)
        Text("Estado: ${displayValue("status", row.text("status"))}")
        TextButton(enabled=!busy,onClick={nameDraft=row.text("display_name");editName=!editName}) {Text(if(editName) "Cancelar cambio" else "Editar nombre")}
        if(editName) {
            OutlinedTextField(nameDraft,{nameDraft=it.take(200)},label={Text("Nombre mostrado")},singleLine=true,modifier=Modifier.fillMaxWidth())
            Button(enabled=!busy && nameDraft.isNotBlank(),onClick={run {
                val id=row.text("id")
                try {
                    repository.execute("donantes","/api/v1/donors/$id/personal",buildJsonObject {put("display_name",nameDraft.trim());put("version",row.getValue("version"))},HttpMethod.Patch)
                    loadDonors();donor=ownDonors.firstOrNull {it.text("id")==id};editName=false;status="Nombre actualizado."
                } catch(e:ApiFailure) {
                    if(e.code=="pending_operation") status="Hay un cambio pendiente. Recupéralo desde Cuenta."
                    else if(e.status==409) {loadDonors();donor=ownDonors.firstOrNull {it.text("id")==id};nameDraft=donor?.text("display_name").orEmpty();status="Tu expediente cambió. Revisa el nombre actualizado antes de guardar."}
                    else throw e
                }
            }}) {Text("Guardar nombre")}
        }
        Text("La valoración corresponde al personal autorizado. Solicita otras correcciones a tu institución.")
        val current=when((latestConsent?.get("granted") as? JsonPrimitive)?.booleanOrNull) {
            true -> "otorgado"
            false -> "retirado"
            null -> if(consentLoaded) "sin registro versionado" else "no disponible"
        }
        Spacer(Modifier.height(12.dp))
        Text("Consentimiento actual: $current",style=MaterialTheme.typography.titleMedium)
        Text("Historial de consentimiento",style=MaterialTheme.typography.titleSmall)
        consents.forEach { item ->
            val state=when((item["granted"] as? JsonPrimitive)?.booleanOrNull) {true->"Otorgado";false->"Retirado";null->"Estado no disponible"}
            Column(Modifier.fillMaxWidth().padding(vertical=6.dp)) {
                Text("$state · ${displayBriefDate(item.text("effective_at"))}",style=MaterialTheme.typography.bodyMedium)
                Text("Política: ${item.text("policy_version")}",style=MaterialTheme.typography.bodySmall,color=MaterialTheme.colorScheme.onSurfaceVariant)
            }
            HorizontalDivider()
        }
        PageControls(consentPage,consentTotal,!busy,{run{loadConsents(row.text("id"),consentPage-1)}},{run{loadConsents(row.text("id"),consentPage+1)}})
        if(devices!=null) ConsentDocumentSection(repository,devices,row.text("id"),consentDoc){run{reload()}}
        DonorReviewsSection(repository,row.text("id"))
    }
    if(donor==null) {
        val pending=repository.journal.value("command:donantes:/api/v1/donors") as? JsonObject
        if(pending!=null || (donorListLoaded && donorTotal==0)) {
            fun submitRegistration(action:suspend ()->Unit) {run {
                registrationMessage=""
                try {
                    action();registrationMessage="Expediente preliminar registrado. Tu institución revisará la información.";status=registrationMessage
                    try {loadDonors();donor=ownDonors.firstOrNull()}catch(cancelled:CancellationException){throw cancelled}
                    catch(_:Exception){registrationMessage+=" Pulsa Actualizar para consultarlo."}
                }catch(cancelled:CancellationException){throw cancelled}
                catch(error:Exception) {
                    registrationMessage=if(repository.journal.value("command:donantes:/api/v1/donors")!=null)
                        "Sin confirmación. Recupera el registro anterior; no envíes otro."
                        else if(error is ApiFailure || error is IllegalArgumentException)error.message.orEmpty()
                        else "No fue posible registrar el expediente. Inténtalo de nuevo."
                }
            }}
            PreliminaryDonorRegistrationCard(busy,pending,registrationMessage,
                onRegister={body->submitRegistration {registerPreliminaryDonor(repository,body)}},
                onRecover={command->submitRegistration {repository.recover(command)}})
        } else if(!donorListLoaded && !busy) Text("No fue posible comprobar si tienes expediente. Pulsa Actualizar antes de registrarte.")
    }
    else {
        Text("Para revisar o renovar tu consentimiento, acude a tu institución. Aún no es posible aceptarlo desde la app.")
        val latest=latestConsent
        val currentPolicy=withdrawableConsentPolicy(listOfNotNull(latestConsent))
        if(currentPolicy!=null) {
            TextButton(enabled=!busy,onClick={confirmation="Retirar consentimiento" to {
                val row=donor ?: throw IllegalArgumentException("No se pudo consultar tu expediente.")
                repository.execute("donantes","/api/v1/donors/${row.text("id")}/consents",buildJsonObject {
                    put("version",row.getValue("version"));put("policy_version",currentPolicy)
                    put("reference","Retiro móvil ${newId()}");put("effective_at",kotlinx.datetime.Clock.System.now().toString())
                    put("granted",false);put("human_confirmation",true);put("reason","Retiro solicitado por el titular")
                })
                reload();status="Consentimiento retirado."
            }}) {Text("Retirar consentimiento")}
        } else if(latest==null) Text("Para solicitar el retiro de un consentimiento anterior, acude a tu institución.")
    }
    }
    if(section=="Reservar") {
    Text("Campañas y sedes autorizadas",style=MaterialTheme.typography.titleMedium)
    Text("Información publicada por las instituciones; no constituye evaluación de aptitud.")
    campaigns.forEach {Text("${it.text("title")} · ${displayBriefDate(it.text("starts_at"))} / ${displayBriefDate(it.text("ends_at"))}")}
    PageControls(campaignPage,campaignTotal,!busy,{run{loadCampaigns(campaignPage-1)}},{run{loadCampaigns(campaignPage+1)}})
    TextButton(onClick={site="";siteName=""}){Text("Todas las sedes")}
    sites.forEach{row->TextButton(onClick={site=row.text("id");siteName=row.text("name")}){Text(row.text("name"))}}
    PageControls(sitePage,siteTotal,!busy,{run{loadSites(sitePage-1)}},{run{loadSites(sitePage+1)}})
    Text("Sede seleccionada: ${siteName.ifBlank { "Todas" }}")
    Text("Periodo opcional")
    DateFilterField("Desde",from,{from=it})
    DateFilterField("Hasta",until,{until=it})
    Button(enabled=!busy,onClick={
        if(from!=null && until!=null && from!!>until!!) status="La fecha final debe ser igual o posterior a la inicial."
        else {
            val (start,end)=dayFilterBounds(from,until,TimeZone.currentSystemDefault())
            run {val query=buildList{add("active=true");add("date_field=starts_at");if(site.isNotBlank())add("site_id="+site.encodeURLParameter());if(start.isNotBlank())add("from_at="+start.encodeURLParameter());if(end.isNotBlank())add("until_at="+end.encodeURLParameter())}.joinToString("&");loadSlots(1,query);bookingMessage="";status="Disponibilidad consultada"}
        }
    }){Text("Consultar horarios")}
    reschedule?.let{Text("Elige un nuevo horario para ${it.text("title")}");TextButton(onClick={reschedule=null}){Text("Cancelar cambio")}}
    val pendingAppointments=repository.journal.pendingCommands().values.map {it.jsonObject}.filter(::isAppointmentCommand)
    pendingAppointments.forEach {command->key(command.text("id")) {
        AppointmentRecoveryCard(repository,command,busy,scope,onBusyChange={busy=it}) {message,slotId->
            bookingSlotId=slotId;bookingMessage=message
            if(!refreshBookingState())bookingMessage+=" No se pudo actualizar toda la información. Consulta los horarios de nuevo."
        }
    }}
    if(bookingMessage.isNotBlank() && slots.none {it.text("id")==bookingSlotId}) Text(bookingMessage,Modifier.semantics{liveRegion=LiveRegionMode.Polite})
    if(!slotsCurrent && slots.isNotEmpty()) Text(if(busy) "Actualizando disponibilidad…" else "La disponibilidad necesita actualizarse. Pulsa Consultar horarios.")
    slots.forEach{slot->key("slot:"+slot.text("id")){
        Card(Modifier.fillMaxWidth().padding(vertical=6.dp)) { Column(Modifier.padding(16.dp),verticalArrangement=Arrangement.spacedBy(8.dp)) {
        Text(slot.text("campaign_title"),style=MaterialTheme.typography.titleMedium)
        Text("Sede: ${slot.text("site_name")}")
        Text("${displayBriefDate(slot.text("starts_at"))} · disponibles ${slot.text("available")}")
        if(bookingSlotId==slot.text("id") && bookingMessage.isNotBlank())Text(bookingMessage,Modifier.semantics{liveRegion=LiveRegionMode.Polite})
        val commandPath=if(reschedule==null) "/api/v1/appointments" else "/api/v1/appointments/${reschedule!!.text("id")}/commands"
        val hasPending=pendingAppointments.any {it.text("path")==commandPath}
        if(hasPending)Text("Hay un intento anterior sin confirmar. Recupéralo antes de continuar.")
        Button(enabled=!busy && slotsCurrent && !hasPending && donor!=null && (slot["available"]?.jsonPrimitive?.intOrNull?:0)>0,onClick={confirmationDetails="${slot.text("campaign_title")}\nSede: ${slot.text("site_name")}";confirmation="Confirmar horario ${displayBriefDate(slot.text("starts_at"))}" to bookingAction@{
            val old=reschedule
            bookingSlotId=slot.text("id");bookingMessage="";status=""
            try {
                if(old==null)repository.execute("donantes","/api/v1/appointments",obj("donor_id" to donor!!.text("id"),"campaign_id" to slot.text("campaign_id"),"slot_id" to slot.text("id")))
                else {val schedule=session.request("donantes","/api/v1/appointments/${old.text("id")}/schedule")
                    repository.execute("donantes","/api/v1/appointments/${old.text("id")}/commands",buildJsonObject{put("action","RESCHEDULE");put("slot_id",slot.text("id"));put("version",schedule.getValue("version"));put("human_confirmation",true);put("reason","Cambio de horario solicitado por el titular")})}
            } catch(cancelled:CancellationException){throw cancelled}
            catch(error:Exception) {
                bookingMessage=appointmentFailureMessage(error)
                if(error is ApiFailure && error.status in setOf(409,412)) {
                    if(!refreshBookingState())bookingMessage+=" No se pudo actualizar la disponibilidad. Pulsa Consultar horarios."
                } else slotsCurrent=false
                return@bookingAction
            }
            reschedule=null;section="Citas";appointmentId=null;status="Cita confirmada por Donantes"
            try {reload()}catch(cancelled:CancellationException){throw cancelled}
            catch(_:Exception){status="La reserva se registró. Pulsa Actualizar para consultar tus citas."}
        }}){Text(if(reschedule==null)"Agendar" else "Cambiar a este horario")}
        } }
    }}
    PageControls(slotPage,slotTotal,!busy,{run{loadSlots(slotPage-1)}},{run{loadSlots(slotPage+1)}})
    }
    if(section=="Citas") {
    if(!busy && appointments.isEmpty()) Text("Aún no tienes citas registradas.")
    appointments.forEach{row->key("appointment:"+row.text("id")){
        Card(Modifier.fillMaxWidth().padding(vertical=6.dp)) { Column(Modifier.padding(16.dp),verticalArrangement=Arrangement.spacedBy(4.dp)) {
        Text(row.text("title").ifBlank {"Cita sin campaña disponible"},style=MaterialTheme.typography.titleMedium)
        Text(if(row.text("starts_at").isBlank()) "Registro sin horario. Consulta a tu institución." else displayBriefDate(row.text("starts_at")))
        StatusChip(row.text("status"))
        TextButton(onClick={appointmentId=if(appointmentId==row.text("id"))null else row.text("id")}){Text("Consultar cita")}
        if(appointmentId==row.text("id") && row.text("status")=="BOOKED"){
            TextButton(onClick={reschedule=row;section="Reservar"}){Text("Reprogramar")}
            TextButton(enabled=!busy,onClick={confirmation="Cancelar cita" to {repository.execute("donantes","/api/v1/appointments/${row.text("id")}/cancel");reload();status="Cancelación confirmada"}}){Text("Cancelar cita")}
            TextButton(enabled=!busy,onClick={confirmation="Confirmar asistencia prevista" to {val schedule=session.request("donantes","/api/v1/appointments/${row.text("id")}/schedule");repository.execute("donantes","/api/v1/appointments/${row.text("id")}/commands",buildJsonObject{put("action","CONFIRM");put("version",schedule.getValue("version"));put("human_confirmation",true);put("reason","Confirmación de asistencia por el titular")});reload()}}){Text("Confirmar asistencia prevista")}
        }
        } }
    }}
    PageControls(appointmentPage,appointmentTotal,!busy,{run{loadAppointments(appointmentPage-1)}},{run{loadAppointments(appointmentPage+1)}})
    }
    val pending=confirmation
    if(pending!=null)DonorConfirmationDialog(pending.first,busy,details=confirmationDetails,
        onConfirm={confirmation=null;confirmationDetails="";run(pending.second)},onDismiss={confirmation=null;confirmationDetails=""})
    TextButton(enabled=!busy,onClick={run{reload()}}){Text("Actualizar")}
}

@Composable
private fun DonorConfirmationDialog(title:String,busy:Boolean,details:String="",onConfirm:()->Unit,onDismiss:()->Unit){
    AlertDialog(onDismissRequest=onDismiss,title={Text(title)},
        text={Column(verticalArrangement=Arrangement.spacedBy(8.dp)) {if(details.isNotBlank())Text(details)
            Text(if(title=="Retirar consentimiento") "Confirma que deseas retirar tu consentimiento. Tu institución recibirá el registro." else "Confirma que deseas continuar. Se comprobarán el consentimiento y la disponibilidad.")} },
        confirmButton={Button(enabled=!busy,onClick=onConfirm){Text("Confirmar")}},
        dismissButton={TextButton(onClick=onDismiss){Text("Volver")}})
}

/** The server orders consent history by version descending; never reuse a superseded grant. */
internal fun withdrawableConsentPolicy(consents:List<JsonObject>):String? {
    val latest=consents.firstOrNull() ?: return null
    if((latest["granted"] as? JsonPrimitive)?.booleanOrNull!=true) return null
    return (latest["policy_version"] as? JsonPrimitive)?.contentOrNull?.takeIf {it.isNotBlank()}
}

internal fun publicCampaignText(row:JsonObject):String = listOf(
    row.text("title"), "${displayBriefDate(row.text("starts_at"))} – ${displayBriefDate(row.text("ends_at"))}",
    row.text("venue"), row.text("information")
).filter { it.isNotBlank() }.joinToString("\n")

@Composable expect fun rememberPublicShare(): (String) -> Unit

@Composable private fun PageControls(page:Int,total:Int,enabled:Boolean,previous:()->Unit,next:()->Unit,position:String="") {
    if(total>20) Row(horizontalArrangement=Arrangement.spacedBy(8.dp)) {
        OutlinedButton(enabled=enabled && page>1,onClick=previous,modifier=if(position.isNotBlank()) Modifier.semantics { contentDescription="Página anterior de campañas, $position" } else Modifier) {Text("Anterior")}
        Text("$page / ${(total+19)/20}",modifier=Modifier.padding(top=12.dp))
        OutlinedButton(enabled=enabled && page*20<total,onClick=next,modifier=if(position.isNotBlank()) Modifier.semantics { contentDescription="Página siguiente de campañas, $position" } else Modifier) {Text("Siguiente")}
    }
}
