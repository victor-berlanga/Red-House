package org.redhouse.mobile

import android.app.Activity
import android.content.ActivityNotFoundException
import android.content.Intent
import android.net.Uri
import androidx.compose.runtime.Composable
import androidx.compose.ui.platform.LocalContext

/** Lanza la app de mapas del sistema con un URI geo:. No agrega dependencias de mapas. */
@Composable actual fun rememberOpenInMaps(): (MapTarget) -> Boolean {
    val context = LocalContext.current
    return { target ->
        if (target.isEmpty) false
        else try {
            val intent = Intent(Intent.ACTION_VIEW, Uri.parse(geoUri(target)))
            // Fuera de una Activity (contexto de aplicación) Android exige una tarea nueva; dentro de ella no se agrega.
            if (context !is Activity) intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            context.startActivity(intent)
            true
        } catch (_: ActivityNotFoundException) { false }
    }
}
