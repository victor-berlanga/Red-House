package org.redhouse.mobile

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.unit.dp
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.ui.focus.FocusRequester
import androidx.compose.ui.focus.focusRequester
import androidx.compose.ui.graphics.Color
import io.ktor.http.HttpMethod
import kotlinx.coroutines.*
import kotlinx.serialization.json.*

class Screen(val title: String, val service: String, val path: String)
/**
 * Pantallas de consulta por rol. La app móvil es solo para DONOR y TRANSPORT (distribución de acceso por
 * aplicación); OPERATOR, COORDINATOR, MEDICAL, ADMIN y AUDITOR usan portal o escritorio y ya no tienen pantallas aquí.
 */
fun screens(role: String): List<Screen> = buildList {
    add(Screen("Perfil", "identidad", "/api/v1/auth/me"))
    if (role == "DONOR") {
        add(Screen("Mi expediente", "donantes", "/api/v1/donors"))
        add(Screen("Campañas", "donantes", "/api/v1/campaigns"))
        add(Screen("Horarios", "donantes", "/api/v1/campaign-slots"))
        add(Screen("Mis citas", "donantes", "/api/v1/appointments"))
    }
    if (role == "TRANSPORT") add(Screen("Traslados", "transporte", "/api/v1/shipments"))
    add(Screen("Avisos", "alertas", "/api/v1/alerts"))
}
@Composable
fun RedHouseApp(store: SecureStore, localStore: SecureStore, queueStore: SecureStore, configStore: SecureStore, devices: DeviceAccess) {
    MaterialTheme(colorScheme = redHouseColors) {
        var gateway by remember { mutableStateOf(MobileEnvironment.gateway) }
        var session by remember { mutableStateOf<Session?>(null) }
        DisposableEffect(session) {
            val owned = session
            onDispose { owned?.api?.client?.close() }
        }
        var user by remember { mutableStateOf<JsonObject?>(null) }
        var username by remember { mutableStateOf("") }
        var password by remember { mutableStateOf("") }
        var otp by remember { mutableStateOf("") }
        var mfaRequired by remember { mutableStateOf(false) }
        val mfaFocus=remember {FocusRequester()}
        LaunchedEffect(mfaRequired) {if(mfaRequired) mfaFocus.requestFocus()}
        var status by remember { mutableStateOf("Inicia sesión para continuar.") }
        var busy by remember { mutableStateOf(false) }
        var rows by remember { mutableStateOf<List<JsonObject>>(emptyList()) }
        var selected by remember { mutableStateOf<Screen?>(null) }
        var page by remember { mutableStateOf(1) }
        val commandKeys = remember { mutableMapOf<String, String>() }
        val scope = rememberCoroutineScope()
        val journal=remember {LocalJournal(localStore)}
        var detail by remember {mutableStateOf<Pair<Screen,String>?>(null)}
        var syncView by remember {mutableStateOf(false)}
        var taskStage by remember {mutableIntStateOf(0)}
        var donorView by remember {mutableStateOf(false)}
        var privacyView by remember {mutableStateOf(false)}
        var accountView by remember { mutableStateOf(false) }
        var destination by remember { mutableStateOf("") }
        var destinationEpoch by remember {mutableIntStateOf(0)}
        var accountSection by remember { mutableStateOf<String?>(null) }
        var donorSection by remember { mutableStateOf("Citas") }
        var loaded by remember { mutableStateOf(false) }
        var restoringSession by remember {mutableStateOf(true)}
        var restoreFailure by remember {mutableStateOf<String?>(null)}
        var replacementLogin by remember {mutableStateOf(false)}
        var restoreAttempt by remember {mutableIntStateOf(0)}
        var taskId by remember {mutableStateOf<String?>(null)}
        var repository by remember {mutableStateOf<MobileRepository?>(null)}
        var queue by remember {mutableStateOf<ObservationQueue?>(null)}
        val noticeId by NoticeLink.pending.collectAsState()
        LaunchedEffect(noticeId,user?.text("id")) {
            if(user!=null && noticeId!=null){
                try{require(noticeId!!.matches(Regex("[0-9a-f-]{36}")));val notice=session!!.request("alertas","/api/v1/alerts/$noticeId");rows=listOf(notice);selected=Screen("Avisos","alertas","/api/v1/alerts");taskId=null;donorView=false;destination="Avisos";accountView=false;detail=null;syncView=false;loaded=true}
                catch(_:Exception){status="Aviso no disponible para esta sesión."}
                finally{NoticeLink.pending.value=null}
            }
        }
        val online by Connectivity.online.collectAsState()
        val foreground by MobileLifecycle.foreground.collectAsState()
        LaunchedEffect(user?.text("id"),foreground) {
            if(user!=null && foreground) {
                devices.scheduleSync()
                if(journal.value("push")!=null)devices.enablePush {token,_->if(token!=null)scope.launch{try{repository?.registerPush(token)}catch(_:Exception){status="No se pudo actualizar la configuración de notificaciones."}}}
                while(isActive) {try{queue?.synchronize()}catch(e:CancellationException){throw e}catch(_:Exception){};delay(30000)}
            }
        }
        LaunchedEffect(restoreAttempt) {
            restoringSession=true;restoreFailure=null;status=""
            try {
                gateway = GatewayConfiguration.prepare(configStore, store, localStore, queueStore) { devices.clearWork() }
                if(gateway.isNotBlank()) {
                    val http = platformClient()
                    try {
                        val active=Session(Api(http,gatewayBases(gateway)),store)
                        val restored=active.restore()
                        journal.bind(gateway+":"+restored.text("id")+":"+restored.text("tenant_id"))
                        val restoredRepository=MobileRepository(active,journal,devices.source)
                        val restoredQueue=ObservationQueue(queueStore,active)
                        session=active;user=restored;repository=restoredRepository;queue=restoredQueue
                        status=""
                    } catch(error:Exception) {http.close();throw error}
                }
            } catch(error:CancellationException) {throw error}
            catch(error:Exception) {
                val saved=runCatching {store.read()}
                val raw=saved.getOrNull()
                val validRecord=raw?.let {runCatching {
                    val record=codec.parseToJsonElement(it).jsonObject
                    val identity=record["user"] as? JsonObject
                    record.text("access_token").isNotBlank() && record.text("refresh_token").isNotBlank() &&
                        identity!=null && identity.text("id").isNotBlank() && identity.text("tenant_id").isNotBlank()
                }.getOrDefault(false)} ?: false
                val terminal=(error is ApiFailure && error.status !in setOf(408,429,500,502,503,504)) || error is IllegalArgumentException
                restoreFailure=when {
                    saved.isFailure -> "STORAGE"
                    // Session already clears credentials after uncertain refresh; never replay it.
                    raw==null -> null
                    !validRecord || terminal -> "TERMINAL"
                    else -> "CONNECTION"
                }
                status=when(restoreFailure) {
                    "STORAGE" -> "No pudimos leer el acceso guardado. Vuelve a intentarlo cuando el teléfono esté desbloqueado."
                    "TERMINAL" -> "No pudimos restaurar el acceso guardado. Revisa las opciones antes de iniciar otra sesión."
                    "CONNECTION" -> if(error is ApiFailure && error.status==429) "Espera antes de reintentar comprobar tu sesión." else "No pudimos comprobar tu sesión. Revisa la conexión y vuelve a intentarlo."
                    else -> "Inicia sesión para continuar."
                }
            } finally {restoringSession=false}
        }
        fun run(action: suspend () -> Unit) {
            if (busy) return
            busy = true
            scope.launch {
                try { action() }
                catch (e: CancellationException) { throw e }
                catch (e: ApiFailure) { status = failureMessage(e, signedIn = user != null); if (e.status == 401) { user = null; rows = emptyList() } }
                catch (_: Exception) { status = "No se confirmó la operación. Consulta su estado antes de intentarlo de nuevo." }
                finally { busy = false }
            }
        }
        fun load(screen: Screen, number: Int) = run {
            rows = emptyList(); selected = screen; loaded = false
            val data = session!!.request(screen.service, screen.path + if (screen.title == "Perfil" || screen.path.endsWith("/summary")) "" else "?page=$number&page_size=20")
            rows = (data["items"] as? JsonArray)?.map { it.jsonObject } ?: listOf(data)
            page = number; status = ""; loaded = true
        }
        fun navigate(target: String) {
            destinationEpoch++;destination=target; selected=null; accountView=target in setOf("Cuenta","Perfil"); accountSection=null
            taskId=null; taskStage=0; detail=null; donorView=false; syncView=target=="Pendientes"; status=""
            val role=user!!.text("role")
            // Inicio, Citas y Campañas del donante son secciones de DonorScreen; Inicio/Traslados del transportista los pinta TransportOrders.
            if(role=="DONOR" && target in setOf("Inicio","Citas","Campañas")) { donorSection=target; donorView=true }
            if(!accountView && !donorView && target !in setOf("Inicio","Traslados","Pendientes")) {
                screens(role).firstOrNull { it.title == target }?.let { load(it,1) }
            }
        }
        LaunchedEffect(user?.text("id"),busy) {
            if(user!=null && !busy && selected==null && destination.isEmpty()) navigate(primaryDestinations(user!!.text("role")).first())
        }
        val nested = accountSection!=null || taskId!=null || detail!=null || (donorView && accountView) || destination=="Pendientes" || destination=="Resumen"
        fun back() {
            when { donorView -> donorView=false; taskId!=null -> taskId=null; detail!=null -> detail=null; accountSection!=null -> accountSection=null
                destination=="Pendientes" || destination=="Resumen" -> navigate("Inicio") }
        }
        PresentationBackHandler(user!=null && nested) { back() }
        PresentationBackHandler(user==null && mfaRequired) { password="";otp="";mfaRequired=false;status="" }
        Surface(Modifier.fillMaxSize()) {
            Column(Modifier.safeDrawingPadding().imePadding()) {
                if(!donorView) Row(Modifier.fillMaxWidth().padding(horizontal=16.dp,vertical=8.dp), verticalAlignment=androidx.compose.ui.Alignment.CenterVertically) {
                    if(user==null) { RedHouseMark(); Text("Red House",style=MaterialTheme.typography.titleLarge,modifier=Modifier.padding(start=8.dp)) }
                    else {
                        if(nested) TextButton(onClick={back()}) { Text("Volver") }
                        Text(accountSection ?: destination, style=MaterialTheme.typography.titleLarge,modifier=Modifier.weight(1f))
                    }
                }
                key(accountView, accountSection, destination, destinationEpoch, selected?.title, taskId, detail, donorView) {
                Column(Modifier.weight(1f).verticalScroll(rememberScrollState()).padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                if(online==false) Text("Sin conexión validada", style = MaterialTheme.typography.labelLarge)
                if(status.isNotBlank()) Text(status, style = MaterialTheme.typography.bodyMedium)
                if (busy) LinearProgressIndicator(Modifier.fillMaxWidth())
                if (user == null) {
                    if(restoringSession) {
                        Text("Comprobando tu sesión…")
                        LinearProgressIndicator(Modifier.fillMaxWidth())
                    } else if(restoreFailure!=null) {
                        if(restoreFailure=="TERMINAL") {
                            Text("Al volver a entrar con la misma cuenta y servidor podrás recuperar tus operaciones pendientes. Una cuenta distinta elimina los datos locales anteriores.")
                            OutlinedButton(onClick={replacementLogin=true;restoreFailure=null;status=""}) {Text("Mostrar inicio de sesión")}
                        } else {
                            Text("No necesitas volver a escribir tu contraseña para reintentar.")
                            OutlinedButton(onClick={restoringSession=true;restoreAttempt++}) {Text(if(restoreFailure=="STORAGE") "Reintentar acceso guardado" else "Reintentar conexión")}
                        }
                    } else {
                    if(replacementLogin) Text("La misma cuenta y servidor conservan tus operaciones pendientes. Una cuenta distinta elimina los datos locales anteriores.")
                    OutlinedTextField(username, { username = it; if(mfaRequired){mfaRequired=false;password="";otp=""} }, modifier=Modifier.fillMaxWidth(), label = { Text("Cuenta") }, singleLine = true)
                    OutlinedTextField(password, { password = it }, modifier=Modifier.fillMaxWidth(), label = { Text("Contraseña") }, visualTransformation = PasswordVisualTransformation(), keyboardOptions=KeyboardOptions(keyboardType=KeyboardType.Password,autoCorrectEnabled=false), singleLine = true)
                    if(mfaRequired) OutlinedTextField(otp, { otp = it }, modifier=Modifier.fillMaxWidth().focusRequester(mfaFocus), label = { Text("Código de verificación") }, keyboardOptions=KeyboardOptions(keyboardType=KeyboardType.Number,autoCorrectEnabled=false), singleLine = true, supportingText = { Text("Escribe los seis dígitos de tu autenticador.") })
                    Button(enabled = !busy, onClick = { run {
                        requireHttps(gateway)
                        val bases = gatewayBases(gateway)
                        devices.clearWork()
                        val http = platformClient()
                        val active = try {
                            Session(Api(http, bases), store).also { active ->
                                authenticateAndBindOwner(gateway,journal,queueStore) {
                                    active.login(username.trim(), password, otp.trim())
                                    active.user ?: throw ApiFailure(502,"profile_contract")
                                }
                            }
                        } catch(e:ApiFailure) {
                            http.close()
                            if(e.code=="mfa_required") {status=if(mfaRequired) "El código no es válido. Intenta con uno nuevo." else "Para continuar, escribe el código de tu autenticador.";mfaRequired=true;otp="";return@run}
                            password="";otp="";mfaRequired=false;throw e
                        } catch(e:Exception) { http.close();password="";otp="";mfaRequired=false;throw e }
                        password="";otp="";mfaRequired=false
                        commandKeys.clear(); session = active; user = active.user; rows = emptyList(); selected = null
                        destination="";accountSection=null;accountView=false;taskId=null;detail=null;donorView=false;syncView=false
                        configStore.write(gateway)
                        repository=MobileRepository(active,journal,devices.source);queue=ObservationQueue(queueStore,active)
                        repository!!.device()
                        status = ""
                    } }) { Text("Iniciar sesión") }
                    if(mfaRequired) TextButton(enabled=!busy,onClick={password="";otp="";mfaRequired=false;status=""}) {Text("Cancelar verificación")}
                    OutlinedButton(enabled = !busy && username.isNotBlank(), onClick = { password="";otp="";mfaRequired=false;run {
                        requireHttps(gateway)
                        val http = platformClient()
                        try {
                            Api(http, mapOf("identidad" to gateway.trimEnd('/') + "/services/identidad-acceso")).call("identidad", "/api/v1/auth/recovery", HttpMethod.Post, obj("username" to username.trim()))
                            status = "Solicitud recibida. Revisa el contacto verificado de tu cuenta."
                        } finally { http.close() }
                    } }) { Text("Recuperar acceso") }
                    if(username.isBlank()) Text("Para recuperar el acceso, escribe tu cuenta.",style=MaterialTheme.typography.bodySmall)
                    }
                } else {
                    if(accountView && !donorView) {
                        if(accountSection==null) {
                            Text(user!!.text("display_name").ifBlank { user!!.text("username") },style=MaterialTheme.typography.headlineSmall)
                            Text(displayValue("role",user!!.text("role")),color=MaterialTheme.colorScheme.onSurfaceVariant)
                            if(user!!.text("role") !in mobileRoles) Text("Esta aplicación es para donantes y personal de traslado. Usa el portal o la consola de escritorio de tu perfil.")
                            if(user!!.text("role")=="DONOR") SettingRow("Mi expediente","Evaluaciones y consentimiento firmado") {donorSection="Expediente";donorView=true}
                            SettingRow("Notificaciones") {accountSection="Notificaciones"}
                            SettingRow("Privacidad y permisos") {accountSection="Privacidad y permisos"}
                            SettingRow("Información de la cuenta") {accountSection="Información de la cuenta"}
                            val count=repository?.journal?.pendingCommands()?.size?:0
                            if(count>0) SettingRow("Operaciones pendientes ($count)") {accountSection="Operaciones pendientes"}
                        }
                        if(accountSection=="Información de la cuenta") {
                            Text("Cuenta: ${user!!.text("username")}")
                            var showAccountReferences by remember {mutableStateOf(false)}
                            TextButton(onClick={showAccountReferences=!showAccountReferences}) {Text("Referencias de la cuenta")}
                            if(showAccountReferences) {
                                Text("Institución: ${user!!.text("tenant_id")}")
                                Text("Cuenta: ${user!!.text("id")}")
                            }
                            TextButton(enabled=!busy,onClick={load(screens(user!!.text("role")).first {it.title=="Perfil"},1)}) {Text("Consultar perfil vigente")}
                            if(selected?.title=="Perfil") rows.forEach {ResourceSummary(selected!!,it)}
                        }
                        if(accountSection=="Privacidad y permisos") {
                            Text("Cámara: solo escaneo o evidencia solicitados. Ubicación: tarea autorizada mientras la app está visible. Puedes denegar permisos; las consultas siguen disponibles.")
                            Text("Si denegaste un permiso, revísalo en Ajustes del sistema y vuelve a la tarea. Nunca envíes credenciales al contacto operativo. Una lectura sin confirmación no acredita custodia.")
                            Text("Las observaciones pendientes se conservan durante 24 horas. Al cerrar sesión se eliminan los datos de este teléfono y se solicita cerrar la sesión en el servicio.")
                            OutlinedButton(onClick={devices.openSettings()}){Text("Abrir permisos del sistema")}
                        }
                    }
                    if(donorView && repository!=null) DonorScreen(repository!!,initialSection=donorSection,showBack=accountView,devices=devices,onExploreCampaigns={navigate("Campañas")},onOpenAppointments={navigate("Citas")},onOpenNotices={navigate("Avisos")}) {donorView=false}
                    if (!accountView) {
                    if(destination=="Pendientes" && queue!=null) { Text("Observaciones por sincronizar",style=MaterialTheme.typography.titleMedium); SyncScreen(queue!!) }
                    if(detail!=null && repository!=null)OperationalDetail(detail!!.first,detail!!.second,repository!!,shellTitle=accountSection ?: destination)
                    if(taskId!=null && repository!=null && queue!=null) TransportScreen(taskId!!,repository!!,queue!!,devices,taskStage)
                    if(taskId==null && !donorView && user!!.text("role")=="TRANSPORT" && destination in setOf("Inicio","Traslados") && repository!=null && queue!=null)
                        TransportOrders(repository!!,queue!!,home=destination=="Inicio",onOpen={id,stage->taskStage=stage;taskId=id},onPending={navigate("Pendientes")},onSummary={navigate("Resumen")})
                    if(taskId==null && !donorView && user!!.text("role")=="TRANSPORT" && destination=="Resumen" && repository!=null) TransportSummaryScreen(repository!!)
                    if(!accountView && destination!="Pendientes" && taskId==null && !donorView && detail==null) selected?.let { screen ->
                        Row(Modifier.fillMaxWidth().testTag(if(loaded) "loaded-records" else "loading-records"),horizontalArrangement=Arrangement.SpaceBetween) {
                            if(screen.title != if(destination=="Citas") "Mis citas" else destination) Text(screen.title,style=MaterialTheme.typography.titleMedium,modifier=Modifier.weight(1f))
                            TextButton(enabled=!busy,onClick={load(screen,page)}) {Text("Actualizar")}
                        }
                        if (rows.isEmpty() && !busy && loaded) Text("Sin registros disponibles.")
                        rows.forEach { row ->
                            Card(Modifier.fillMaxWidth()) {
                                Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                                    ResourceSummary(screen,row)
                                    if(screen.path.endsWith("/summary")) {
                                        Text("Total: ${row.text("total")}")
                                        (row["statuses"] as? JsonArray)?.forEach {val count=it.jsonObject;Text("${displayValue("status", count.text("status"))}: ${count.text("value")}")}
                                    }
                                    if(screen.title=="Avisos")TextButton(onClick={detail=screen to row.text("id")}){Text("Ver detalle")}
                                    if (screen.title == "Avisos") TextButton(enabled = !busy, onClick = { run {
                                        session!!.request("alertas", "/api/v1/alerts/${row.text("id")}/acknowledge", HttpMethod.Post, key = commandKeys.getOrPut(screen.path + row.text("id")) { newId() })
                                        status = "Aviso reconocido."
                                    } }) { Text("Marcar leído") }
                                }
                            }
                        }
                        if (screen.title != "Perfil" && !screen.path.endsWith("/summary")) Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            OutlinedButton(enabled = !busy && page > 1, onClick = { load(screen, page - 1) }) { Text("Anterior") }
                            OutlinedButton(enabled = !busy && rows.size == 20, onClick = { load(screen, page + 1) }) { Text("Siguiente") }
                        }
                    }
                    }
                    if (accountView && accountSection=="Notificaciones") {
                    OutlinedButton(enabled=!busy,onClick={devices.enablePush {token,error->if(token!=null)run{repository!!.registerPush(token);status="Notificaciones activadas."}else status=error.orEmpty()}}){Text("Activar notificaciones")}
                    TextButton(enabled=!busy,onClick={run{devices.disablePush();repository?.revokePush();status="Notificaciones desactivadas"}}){Text("Desactivar notificaciones")}
                    }
                    if ((accountView && accountSection=="Operaciones pendientes") || destination=="Pendientes") {
                    Text("Operaciones por confirmar", style = MaterialTheme.typography.titleMedium)
                    repository?.journal?.pendingCommands()?.forEach {(_,command)->
                        if(isAppointmentCommand(command.jsonObject)) {
                            AppointmentRecoveryCard(repository!!,command.jsonObject,busy,scope,onBusyChange={busy=it}) {message,_->status=message}
                        } else {
                        var showReference by remember(command.jsonObject.text("id")) { mutableStateOf(false) }
                        Text("Pendiente · ${displayBriefDate(command.jsonObject.text("captured_at"))}")
                        TextButton(onClick = { showReference = !showReference }) { Text("Referencia de la operación") }
                        if (showReference) Text(command.jsonObject.text("id"), style = MaterialTheme.typography.bodySmall)
                        Button(enabled=!busy,onClick={run{repository!!.recover(command.jsonObject);status="Operación pendiente recuperada"}}){Text("Consultar y recuperar operación pendiente")}
                        }
                    }
                    }
                    if(accountView && accountSection==null && !donorView) {
                    TextButton(enabled = !busy, onClick = { run {
                        devices.cancel();devices.clearWork();devices.disablePush();val pushConfirmed=runCatching{repository?.revokePush()}.isSuccess;val deviceConfirmed=runCatching{repository?.revokeDevice()}.isSuccess;taskId=null;donorView=false;detail=null;syncView=false;NoticeLink.pending.value=null
                        queue?.clear();journal.clear();configStore.write(null)
                        rows = emptyList(); selected = null; user = null
                        val confirmed = session!!.logout()
                        session = null;privacyView=false;accountView=false;destination="";accountSection=null
                        status = (if (confirmed) "Sesión cerrada en este teléfono y en el servicio." else "Sesión cerrada en este teléfono; no se pudo confirmar el cierre en el servicio.") + (if(pushConfirmed) "" else " No se pudo confirmar la desactivación de notificaciones.") + (if(deviceConfirmed) "" else " No se pudo confirmar la baja del dispositivo.")
                    } }) { Text("Cerrar sesión") }
                    }
                }
            }
        }
                if(user!=null) {
                    val destinations=primaryDestinations(user!!.text("role"))
                    val largeLabels=androidx.compose.ui.platform.LocalDensity.current.fontScale>=1.8f
                    Column {
                        destinations.chunked(if(largeLabels) 2 else destinations.size).forEach { group ->
                            NavigationBar {
                                group.forEach {target ->
                                    NavigationBarItem(selected=destination==target,onClick={navigate(target)},enabled=!busy,
                                        colors=NavigationBarItemDefaults.colors(selectedIconColor=MaterialTheme.colorScheme.primary,selectedTextColor=MaterialTheme.colorScheme.primary,indicatorColor=MaterialTheme.colorScheme.primaryContainer),
                                        icon={DestinationIcon(target)},label={Text(target,modifier=Modifier.wrapContentWidth(unbounded=true),softWrap=false)})
                                }
                            }
                        }
                    }
                }
        }
        }
    }
}
