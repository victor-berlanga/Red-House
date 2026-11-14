@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class)
package org.redhouse.mobile

import platform.Foundation.*
import io.ktor.client.*
import io.ktor.client.engine.darwin.*
import io.ktor.client.plugins.*
import io.ktor.client.plugins.websocket.*
import androidx.compose.ui.window.ComposeUIViewController

/** Compare the host with the linked framework before native stores or UI can start. */
fun iosHostEnvironmentMatches(bundleIdentifier: String, variant: String, gateway: String,
                              backgroundTask: String): Boolean =
    bundleIdentifier == MobileEnvironment.iosBundleIdentifier &&
    variant == MobileEnvironment.iosVariant &&
    gateway == MobileEnvironment.gateway &&
    backgroundTask == MobileEnvironment.iosBackgroundTask

/** Host-owned Security.framework evaluator. A missing or failing lab evaluator rejects. */
interface IosLabTrustEvaluator {
    // 0: system evaluation for another origin; 1: verified lab trust; 2: reject.
    fun decide(task: NSURLSessionTask, challenge: NSURLAuthenticationChallenge): Int
}
private var labTrustEvaluator: IosLabTrustEvaluator? = null
fun installIosLabTrustEvaluator(evaluator: IosLabTrustEvaluator) {
    require(MobileEnvironment.iosVariant == "lab")
    check(labTrustEvaluator == null)
    labTrustEvaluator = evaluator
}

actual fun newId() = NSUUID().UUIDString.lowercase()
actual fun platformClient() = HttpClient(Darwin) {
    followRedirects = false
    if (MobileEnvironment.iosVariant == "lab") engine {
        handleChallenge { _, task, challenge, completion ->
            val decision = try { labTrustEvaluator?.decide(task, challenge) ?: 2 } catch (_: Exception) { 2 }
            val trust = challenge.protectionSpace.serverTrust
            when {
                decision == 0 -> completion(NSURLSessionAuthChallengePerformDefaultHandling, null)
                decision == 1 && trust != null -> completion(NSURLSessionAuthChallengeUseCredential, NSURLCredential.create(trust))
                else -> completion(NSURLSessionAuthChallengeCancelAuthenticationChallenge, null)
            }
        }
    }
    install(HttpTimeout) { requestTimeoutMillis = 15000; connectTimeoutMillis = 10000; socketTimeoutMillis = 20000 }
    install(WebSockets)
}
fun MainViewController(store: SecureStore, localStore: SecureStore, queueStore: SecureStore, configStore: SecureStore, devices: DeviceAccess) = ComposeUIViewController { RedHouseApp(store,localStore,queueStore,configStore,devices) }
