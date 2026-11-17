package org.redhouse.mobile

import androidx.compose.runtime.*
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.semantics.*
import androidx.compose.ui.unit.dp
import kotlinx.serialization.json.*

/** Presentation only: no clinical fields, inferred blood group or preselected acknowledgement. */
@Composable internal fun PreliminaryDonorRegistrationCard(
    busy:Boolean,pending:JsonObject?,message:String,
    onRegister:(JsonObject)->Unit,onRecover:(JsonObject)->Unit
) {
    var name by remember {mutableStateOf("")}
    var group by remember {mutableStateOf<String?>(null)}
    var acknowledged by remember {mutableStateOf(false)}
    var expanded by remember {mutableStateOf(false)}
    var confirmRecovery by remember {mutableStateOf(false)}
    val folio=remember {"MOB-"+newId().replace("-","").take(24)}
    Card(Modifier.fillMaxWidth()) { Column(Modifier.padding(16.dp),verticalArrangement=Arrangement.spacedBy(8.dp)) {
        Text("Registro preliminar",style=MaterialTheme.typography.titleMedium)
        Text("Inicia tu expediente con los datos que conoces. Tu institución debe revisar tu información y determinar tu aptitud para donar.")
        if(pending!=null) {
            val original=pending["body"]?.jsonObject
            Text("Hay un registro anterior sin confirmar. Recupéralo antes de enviar otro.")
            Text("Nombre: ${original?.text("display_name").orEmpty()} · Grupo: ${original?.text("blood_group").orEmpty()}")
            Button(enabled=!busy,onClick={confirmRecovery=true}) {Text("Recuperar registro anterior")}
        } else {
            OutlinedTextField(name,{name=it.take(200)},enabled=!busy,label={Text("Nombre")},singleLine=true,modifier=Modifier.fillMaxWidth())
            Box {
                OutlinedButton(enabled=!busy,onClick={expanded=true},modifier=Modifier.semantics {stateDescription=if(expanded)"Expandido" else "Contraído"}) {
                    Text("Grupo sanguíneo: ${group ?: "Seleccionar"}")
                }
                DropdownMenu(expanded=expanded,onDismissRequest={expanded=false}) {
                    donorBloodGroups.forEach {value->DropdownMenuItem(text={Text(value)},onClick={group=value;expanded=false})}
                    DropdownMenuItem(text={Text("No conozco mi grupo")},onClick={group=null;expanded=false})
                }
            }
            if(group==null) Text("Si no conoces tu grupo, acude a tu institución para establecerlo antes de completar el registro. No lo supongas.")
            Text("Este registro no sustituye el consentimiento documental ni una evaluación médica. Ambos se revisan con tu institución.")
            Row(Modifier.fillMaxWidth()) {
                Checkbox(checked=acknowledged,onCheckedChange={acknowledged=it},enabled=!busy,
                    modifier=Modifier.semantics {contentDescription="Doy mi consentimiento para registrar este expediente preliminar con los datos que proporcioné"})
                Text("Doy mi consentimiento para registrar este expediente preliminar con los datos que proporcioné.",Modifier.weight(1f).padding(top=12.dp))
            }
            Button(enabled=!busy && name.isNotBlank() && group!=null && acknowledged,onClick={
                onRegister(preliminaryDonorBody(name,group,acknowledged,folio))
            }) {Text("Registrar expediente preliminar")}
        }
        if(message.isNotBlank())Text(message,Modifier.semantics {liveRegion=LiveRegionMode.Polite})
    } }
    if(confirmRecovery && pending!=null) AlertDialog(onDismissRequest={if(!busy)confirmRecovery=false},
        title={Text("Recuperar registro anterior")},text={Text("Se consultará o reenviará el registro original con los mismos datos. No se crea una solicitud distinta.")},
        confirmButton={TextButton(enabled=!busy,onClick={confirmRecovery=false;onRecover(pending)}){Text("Recuperar")}},
        dismissButton={TextButton(enabled=!busy,onClick={confirmRecovery=false}){Text("Volver")}})
}
