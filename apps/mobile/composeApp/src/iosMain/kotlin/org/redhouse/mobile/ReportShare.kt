package org.redhouse.mobile

import androidx.compose.runtime.Composable
import platform.UIKit.UIActivityViewController
import platform.UIKit.UIApplication

/** Comparte el CSV del reporte como texto con la hoja de compartir del sistema. */
@Composable actual fun rememberReportShare(): (String) -> Unit = { text ->
    val controller = UIActivityViewController(activityItems = listOf(text), applicationActivities = null)
    var presenter = UIApplication.sharedApplication.keyWindow?.rootViewController
    while (presenter?.presentedViewController != null) presenter = presenter.presentedViewController
    presenter?.presentViewController(controller, animated = true, completion = null)
}
