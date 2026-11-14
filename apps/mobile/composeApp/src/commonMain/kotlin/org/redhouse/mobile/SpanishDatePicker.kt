package org.redhouse.mobile

import androidx.compose.runtime.Composable
import kotlinx.datetime.LocalDate

@Composable internal expect fun SpanishDateDialog(label:String,initial:LocalDate,confirmLabel:String,onDismiss:()->Unit,onSelected:(LocalDate)->Unit)
