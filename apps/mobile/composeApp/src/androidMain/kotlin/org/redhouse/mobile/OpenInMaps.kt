package org.redhouse.mobile

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
            context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(geoUri(target))))
            true
        } catch (_: ActivityNotFoundException) { false }
    }
}
