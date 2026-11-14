package org.redhouse.mobile

import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.ExperimentalComposeUiApi
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.UIKitInteropProperties
import androidx.compose.ui.viewinterop.UIKitView
import kotlinx.cinterop.ExperimentalForeignApi
import kotlinx.datetime.*
import platform.Foundation.*
import platform.UIKit.UIDatePicker
import platform.UIKit.UIDatePickerMode
import platform.UIKit.UIDatePickerStyle
import platform.UIKit.UIColor
import platform.UIKit.UIUserInterfaceStyle

@OptIn(ExperimentalForeignApi::class,ExperimentalComposeUiApi::class)
@Composable internal actual fun SpanishDateDialog(label:String,initial:LocalDate,onDismiss:()->Unit,onSelected:(LocalDate)->Unit) {
    val primary=MaterialTheme.colorScheme.primary
    val surface=MaterialTheme.colorScheme.surface
    val zone=remember {TimeZone.currentSystemDefault()}
    val picker=remember(initial,primary,surface,zone) {UIDatePicker().apply {
        datePickerMode=UIDatePickerMode.UIDatePickerModeDate
        preferredDatePickerStyle=UIDatePickerStyle.UIDatePickerStyleInline
        locale=NSLocale("es_MX")
        calendar=NSCalendar(calendarIdentifier=NSCalendarIdentifierGregorian)
        timeZone=requireNotNull(NSTimeZone.timeZoneWithName(zone.id))
        overrideUserInterfaceStyle=UIUserInterfaceStyle.UIUserInterfaceStyleLight
        backgroundColor=UIColor(red=surface.red.toDouble(),green=surface.green.toDouble(),blue=surface.blue.toDouble(),alpha=1.0)
        tintColor=UIColor(red=primary.red.toDouble(),green=primary.green.toDouble(),blue=primary.blue.toDouble(),alpha=primary.alpha.toDouble())
        date=NSDate.dateWithTimeIntervalSince1970(initial.atStartOfDayIn(zone).toEpochMilliseconds().toDouble()/1000.0)
    }}
    Column(Modifier.fillMaxWidth().padding(vertical=8.dp)) {
        Text("Elegir fecha · $label")
        UIKitView(factory={picker},modifier=Modifier.fillMaxWidth().height(340.dp),properties=UIKitInteropProperties(isNativeAccessibilityEnabled=true))
        Row(Modifier.fillMaxWidth(),horizontalArrangement=Arrangement.End) {
            TextButton(onClick=onDismiss){Text("Cancelar")}
            TextButton(onClick={onSelected(Instant.fromEpochMilliseconds((picker.date.timeIntervalSince1970*1000.0).toLong()).toLocalDateTime(zone).date)}){Text("Elegir hora")}
        }
    }
}
