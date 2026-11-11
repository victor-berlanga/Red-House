package org.redhouse.mobile
import androidx.compose.runtime.Composable
// iOS has no system Back button; the shared contextual action remains available.
@Composable actual fun PresentationBackHandler(enabled: Boolean, onBack: () -> Unit) { }
