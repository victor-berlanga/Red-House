package org.redhouse.mobile

import androidx.compose.material3.DatePickerState
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import platform.Foundation.NSLocale

@OptIn(ExperimentalMaterial3Api::class)
@Composable internal actual fun rememberSpanishDatePickerState(initialMillis:Long):DatePickerState =
    remember(initialMillis) { DatePickerState(locale=NSLocale("es_MX"),initialSelectedDateMillis=initialMillis) }

@Composable internal actual fun SpanishPickerEnvironment(content:@Composable ()->Unit) { content() }
