package org.redhouse.mobile

import androidx.compose.runtime.*
import androidx.compose.material3.*
import kotlinx.coroutines.*
import kotlinx.serialization.json.*

/**
 * Detalle de un aviso propio. La app móvil es solo para DONOR y TRANSPORT, así que aquí ya no hay
 * inventario, laboratorio, solicitudes ni planeación (eran de OPERATOR, MEDICAL y COORDINATOR).
 * La barra superior ya ofrece «Volver» y el título del destino; el detalle solo agrega subtítulo si difiere.
 */
@Composable fun OperationalDetail(screen:Screen,id:String,repository:MobileRepository,shellTitle:String){
    var row by remember {mutableStateOf<JsonObject?>(null)};var status by remember{mutableStateOf("")}
    var busy by remember{mutableStateOf(false)};val scope=rememberCoroutineScope()
    fun run(action:suspend ()->Unit){if(busy)return;busy=true;scope.launch{try{action()}catch(e:CancellationException){throw e}catch(e:Exception){status=if(e is ApiFailure || e is IllegalArgumentException)e.message.orEmpty() else "Sin confirmación; consulta de nuevo."}finally{busy=false}}}
    LaunchedEffect(id){try{row=repository.session.request(screen.service,screen.path+"/"+id)}catch(e:CancellationException){throw e}catch(e:Exception){status=if(e is ApiFailure)e.message.orEmpty() else "No se pudo consultar la información."}}
    detailSubtitle(screen.title,shellTitle)?.let{Text(it,style=MaterialTheme.typography.titleMedium)}
    if(status.isNotBlank())Text(status)
    row?.let{value->
        listOf("status","severity","message_code","created_at","message").forEach{key->(value[key] as? JsonPrimitive)?.contentOrNull?.takeIf{it.isNotBlank()}?.let{Text("${fieldLabel(key)}: ${displayValue(key, it)}")}}
        if(screen.service=="alertas")Button(enabled=!busy,onClick={run{repository.execute("alertas","/api/v1/alerts/$id/acknowledge");status="Aviso reconocido"}}){Text("Marcar leído")}
    }
}

/** Subtitle for a nested detail; null when it would repeat the title already shown in the shell bar. */
internal fun detailSubtitle(screenTitle:String,shellTitle:String):String? = screenTitle.takeIf{it.isNotBlank() && it!=shellTitle}
