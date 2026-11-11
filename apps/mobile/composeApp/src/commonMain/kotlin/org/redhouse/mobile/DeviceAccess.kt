package org.redhouse.mobile

import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.ImageBitmap

/** Platform callbacks return cancellation/permission errors explicitly; no synthetic fallback. */
interface DeviceAccess {
    val source: String
    fun enablePush(done:(String?,String?)->Unit)
    fun disablePush()
    fun scan(done: (String?, String?) -> Unit)
    fun photograph(done: (ByteArray?, String?) -> Unit)
    fun locate(done: (PhonePosition?, String?) -> Unit)
    fun scheduleSync()
    fun clearWork()
    fun cancel()
    fun openSettings()
}
data class PhonePosition(val latitude: Double, val longitude: Double, val accuracy: Double,
                         val capturedAt: String, val simulated: Boolean)
expect fun imageBitmap(bytes: ByteArray): ImageBitmap
expect fun sha256(bytes: ByteArray): String
@Composable expect fun RegionalMap(latitude: Double?, longitude: Double?, label: String)

object MobileLifecycle { val foreground = kotlinx.coroutines.flow.MutableStateFlow(true); fun active(value:Boolean) { foreground.value=value } }

object NoticeLink {
    val pending=kotlinx.coroutines.flow.MutableStateFlow<String?>(null)
    fun receive(id:String) { pending.value=id }
}

object Connectivity {val online=kotlinx.coroutines.flow.MutableStateFlow<Boolean?>(null);fun setOnline(value:Boolean){online.value=value}}
