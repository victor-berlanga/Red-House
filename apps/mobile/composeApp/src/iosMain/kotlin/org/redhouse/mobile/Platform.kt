package org.redhouse.mobile

import platform.Foundation.NSUUID
import io.ktor.client.*
import io.ktor.client.engine.darwin.*
import io.ktor.client.plugins.*
import io.ktor.client.plugins.websocket.*
import androidx.compose.ui.window.ComposeUIViewController

actual fun newId() = NSUUID().UUIDString.lowercase()
actual fun platformClient() = HttpClient(Darwin) {
    followRedirects = false
    install(HttpTimeout) { requestTimeoutMillis = 15000; connectTimeoutMillis = 10000; socketTimeoutMillis = 20000 }
    install(WebSockets)
}
fun MainViewController(store: SecureStore, localStore: SecureStore, queueStore: SecureStore, configStore: SecureStore, devices: DeviceAccess) = ComposeUIViewController { RedHouseApp(store,localStore,queueStore,configStore,devices) }
