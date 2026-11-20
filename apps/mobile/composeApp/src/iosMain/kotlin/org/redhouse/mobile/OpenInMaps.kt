package org.redhouse.mobile

import androidx.compose.runtime.Composable
import platform.Foundation.NSURL
import platform.UIKit.UIApplication

/** Abre Apple Maps con una URL https://maps.apple.com. No agrega dependencias de mapas. */
@Composable actual fun rememberOpenInMaps(): (MapTarget) -> Boolean = { target ->
    val url = if (target.isEmpty) null else NSURL.URLWithString(appleMapsUrl(target))
    if (url == null) false else { UIApplication.sharedApplication.openURL(url, emptyMap<Any?, Any>(), null); true }
}
