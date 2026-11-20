package org.redhouse.mobile

import android.content.Intent
import androidx.compose.runtime.Composable
import androidx.compose.ui.platform.LocalContext

/** Comparte el CSV del reporte como texto con el selector del sistema; no requiere archivos ni permisos. */
@Composable actual fun rememberReportShare(): (String) -> Unit {
    val context = LocalContext.current
    return { text ->
        val intent = Intent(Intent.ACTION_SEND).setType("text/plain").putExtra(Intent.EXTRA_SUBJECT, "Reporte de traslados").putExtra(Intent.EXTRA_TEXT, text)
        context.startActivity(Intent.createChooser(intent, "Compartir reporte"))
    }
}
