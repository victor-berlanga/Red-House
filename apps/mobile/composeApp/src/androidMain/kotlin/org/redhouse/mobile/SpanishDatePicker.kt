package org.redhouse.mobile

import androidx.compose.material3.DatePickerState
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.platform.LocalContext
import android.content.res.Configuration
import java.util.Locale

@OptIn(ExperimentalMaterial3Api::class)
@Composable internal actual fun rememberSpanishDatePickerState(initialMillis:Long):DatePickerState =
    remember(initialMillis) { DatePickerState(locale=Locale.forLanguageTag("es-MX"),initialSelectedDateMillis=initialMillis) }

@Composable internal actual fun SpanishPickerEnvironment(content:@Composable ()->Unit) {
    val context=LocalContext.current
    val current=LocalConfiguration.current
    val configuration=remember(current) { Configuration(current).apply {setLocale(Locale.forLanguageTag("es-MX"))} }
    val localized=remember(context,configuration) {context.createConfigurationContext(configuration)}
    CompositionLocalProvider(LocalContext provides localized,LocalConfiguration provides configuration,content=content)
}
