package org.redhouse.mobile
import androidx.compose.runtime.Composable
import androidx.activity.compose.BackHandler
@Composable actual fun PresentationBackHandler(enabled: Boolean, onBack: () -> Unit) { BackHandler(enabled, onBack) }
