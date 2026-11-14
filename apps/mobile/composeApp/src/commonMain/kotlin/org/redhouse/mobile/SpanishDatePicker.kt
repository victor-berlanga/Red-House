package org.redhouse.mobile

import androidx.compose.runtime.Composable
import kotlinx.datetime.LocalDate

@Composable internal expect fun SpanishDateDialog(label:String,initial:LocalDate,onDismiss:()->Unit,onSelected:(LocalDate)->Unit)
