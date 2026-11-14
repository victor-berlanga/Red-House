package org.redhouse.mobile

import androidx.compose.material3.DatePickerState
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.runtime.Composable

@OptIn(ExperimentalMaterial3Api::class)
@Composable internal expect fun rememberSpanishDatePickerState(initialMillis:Long):DatePickerState

@Composable internal expect fun SpanishPickerEnvironment(content:@Composable ()->Unit)
