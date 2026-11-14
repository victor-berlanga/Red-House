package org.redhouse.mobile

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import kotlinx.datetime.*
import kotlin.time.Duration.Companion.days
import kotlin.time.Duration.Companion.seconds

/** Date and time chosen in the phone's zone; the API receives an unambiguous UTC instant. */
@OptIn(ExperimentalMaterial3Api::class)
@Composable fun DateTimeField(label:String,value:String,onChange:(String)->Unit,optional:Boolean=false) {
    DateTimeFieldContent(label,value,onChange,optional)
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable private fun DateTimeFieldContent(label:String,value:String,onChange:(String)->Unit,optional:Boolean) {
    val zone=TimeZone.currentSystemDefault()
    var initial by remember(value) {mutableStateOf(runCatching {Instant.parse(value).toLocalDateTime(zone)}.getOrNull() ?: Clock.System.now().toLocalDateTime(zone))}
    var opening by remember {mutableIntStateOf(0)}
    var hour by remember {mutableStateOf(initial.hour.toString().padStart(2,'0'))}
    var minute by remember {mutableStateOf(initial.minute.toString().padStart(2,'0'))}
    var stage by remember {mutableStateOf(0)}
    var selectedDate by remember {mutableStateOf<LocalDate?>(null)}
    var seconds by remember(value) {mutableStateOf(initial.second.toString().padStart(2,'0'))}
    var fraction by remember(value) {mutableStateOf(initial.nanosecond.toString().padStart(9,'0').trimEnd('0'))}
    var error by remember {mutableStateOf("")}
    var ambiguous by remember {mutableStateOf<List<Instant>>(emptyList())}
    Column {
        OutlinedButton(onClick={
            initial=runCatching {Instant.parse(value).toLocalDateTime(zone)}.getOrNull() ?: Clock.System.now().toLocalDateTime(zone)
            hour=initial.hour.toString().padStart(2,'0');minute=initial.minute.toString().padStart(2,'0')
            seconds=if(value.isBlank()) "00" else initial.second.toString().padStart(2,'0');fraction=if(value.isBlank()) "" else initial.nanosecond.toString().padStart(9,'0').trimEnd('0')
            selectedDate=null;ambiguous=emptyList();error="";opening++;stage=1
        },modifier=Modifier.fillMaxWidth()) {
            Text(if(value.isBlank()) "Elegir $label" else "$label · ${displayBriefDate(value)}")
        }
        if(optional && value.isNotBlank()) TextButton(onClick={onChange("")}) {Text("Quitar $label")}
        if(error.isNotBlank()) Text(error,color=MaterialTheme.colorScheme.error)
    }
    if(stage==1) key(opening) {SpanishDateDialog(label,initial.date,onDismiss={stage=0},onSelected={selectedDate=it;stage=2})}
    if(stage==2) AlertDialog(onDismissRequest={stage=0},title={Text("Elegir hora · $label")},
        text={Column {
            Text("Se usará la zona horaria de este teléfono.")
            Row(horizontalArrangement=Arrangement.spacedBy(12.dp)) {
                OutlinedTextField(hour,{hour=it.filter(Char::isDigit).take(2)},label={Text("Hora")},singleLine=true,keyboardOptions=KeyboardOptions(keyboardType=KeyboardType.Number),modifier=Modifier.weight(1f))
                OutlinedTextField(minute,{minute=it.filter(Char::isDigit).take(2)},label={Text("Minuto")},singleLine=true,keyboardOptions=KeyboardOptions(keyboardType=KeyboardType.Number),modifier=Modifier.weight(1f))
            }
            if(error.isNotBlank()) Text(error,color=MaterialTheme.colorScheme.error)
        }},confirmButton={TextButton(onClick={
            val second=seconds.toIntOrNull()
            val date=selectedDate
            val selectedHour=hour.toIntOrNull();val selectedMinute=minute.toIntOrNull()
            if(date==null || second==null || second !in 0..59 || selectedHour==null || selectedHour !in 0..23 || selectedMinute==null || selectedMinute !in 0..59) error="Revisa la fecha y la hora elegidas."
            else {
                val nanosecond=if(fraction.isBlank()) 0 else fraction.padEnd(9,'0').toInt()
                val choices=localCandidates(date,selectedHour,selectedMinute,second,zone,nanosecond)
                when(choices.size) {
                    0 -> error="Esa hora no existe en la zona del teléfono. Elige otra."
                    1 -> {onChange(choices.single().toString());error="";stage=0}
                    else -> {ambiguous=choices;error="";stage=3}
                }
            }
        }){Text("Aceptar")}},dismissButton={TextButton(onClick={stage=0}){Text("Cancelar")}})
    if(stage==3) AlertDialog(onDismissRequest={stage=0},title={Text("Esta hora ocurre dos veces")},
        text={Text("El cambio de horario repite esta hora. Elige cuál corresponde a tu cita.")},
        confirmButton={TextButton(onClick={onChange(ambiguous.last().toString());stage=0}){Text("Segunda vez")}},
        dismissButton={TextButton(onClick={onChange(ambiguous.first().toString());stage=0}){Text("Primera vez")}})
}

internal fun localCandidates(date:LocalDate,hour:Int,minute:Int,second:Int,zone:TimeZone,nanosecond:Int=0):List<Instant> {
    val local=LocalDateTime(date.year,date.monthNumber,date.dayOfMonth,hour,minute,second,nanosecond)
    val first=local.toInstant(zone)
    if(first.toLocalDateTime(zone)!=local) return emptyList()
    val difference=kotlin.math.abs(zone.offsetAt(first-1.days).totalSeconds-zone.offsetAt(first+1.days).totalSeconds)
    val candidates=if(difference==0) listOf(first) else listOf(first,first-difference.seconds,first+difference.seconds)
    return candidates.filter {it.toLocalDateTime(zone)==local}.distinct().sorted()
}
