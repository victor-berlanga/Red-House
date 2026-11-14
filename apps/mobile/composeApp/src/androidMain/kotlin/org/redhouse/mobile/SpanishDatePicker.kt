package org.redhouse.mobile

import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.ui.Modifier
import androidx.compose.foundation.layout.padding
import androidx.compose.ui.unit.dp
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.platform.LocalContext
import android.content.res.Configuration
import java.util.Locale
import kotlinx.datetime.*

@OptIn(ExperimentalMaterial3Api::class)
@Composable internal actual fun SpanishDateDialog(label:String,initial:LocalDate,confirmLabel:String,onDismiss:()->Unit,onSelected:(LocalDate)->Unit) {
    val initialMillis=initial.atStartOfDayIn(TimeZone.UTC).toEpochMilliseconds()
    val picker=remember(initialMillis) {DatePickerState(locale=Locale.forLanguageTag("es-MX"),initialSelectedDateMillis=initialMillis)}
    DatePickerDialog(onDismissRequest=onDismiss,
        confirmButton={TextButton(enabled=picker.selectedDateMillis!=null,onClick={picker.selectedDateMillis?.let {onSelected(Instant.fromEpochMilliseconds(it).toLocalDateTime(TimeZone.UTC).date)}}) {Text(confirmLabel)}},
        dismissButton={TextButton(onClick=onDismiss){Text("Cancelar")}}) {
        SpanishPickerEnvironment {DatePicker(state=picker,title={Text("Elegir fecha · $label",modifier=Modifier.padding(start=24.dp,top=16.dp,end=24.dp))},
            headline={
                val date=picker.selectedDateMillis?.let {Instant.fromEpochMilliseconds(it).toLocalDateTime(TimeZone.UTC).date}
                val months=listOf("enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre")
                Text(if(date==null) "Selecciona una fecha" else "${date.dayOfMonth} de ${months[date.monthNumber-1]} de ${date.year}",
                    modifier=Modifier.padding(horizontal=24.dp,vertical=12.dp),style=MaterialTheme.typography.headlineSmall)
            },showModeToggle=false)}
    }
}

@Composable internal fun SpanishPickerEnvironment(content:@Composable ()->Unit) {
    val context=LocalContext.current
    val current=LocalConfiguration.current
    val configuration=remember(current) { Configuration(current).apply {setLocale(Locale.forLanguageTag("es-MX"))} }
    val localized=remember(context,configuration) {context.createConfigurationContext(configuration)}
    CompositionLocalProvider(LocalContext provides localized,LocalConfiguration provides configuration,content=content)
}
