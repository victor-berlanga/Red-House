package org.redhouse.mobile

import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.test.ext.junit.runners.AndroidJUnit4
import io.ktor.client.request.*
import io.ktor.client.statement.*
import kotlinx.coroutines.runBlocking
import kotlinx.serialization.json.*
import org.junit.*
import org.junit.runner.RunWith

/** Public HTTPS smoke test on the installed app; no credentials or business writes. */
@RunWith(AndroidJUnit4::class)
class GcpGatewayTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()
    private fun shown(text: String) = compose.waitUntil(90000) {
        compose.onAllNodesWithText(text, substring = true).fetchSemanticsNodes().isNotEmpty()
    }
    @Test fun defaultGatewayShowsLoginAndValidatesPublicHttpsReadiness() {
        shown("Iniciar sesión")
        compose.onAllNodesWithText("Gateway HTTPS").assertCountEquals(0)
        Assert.assertEquals("https://34.18.186.116", AndroidSecureStore(compose.activity, "gateway").read())
        compose.onNodeWithText("Cuenta").assertExists()
        compose.onNodeWithText("Contraseña").assertExists()
        compose.onAllNodesWithText("Inventario", substring = false).assertCountEquals(0)
        Assert.assertNull(AndroidSecureStore(compose.activity).read())
        runBlocking {
            val client = platformClient()
            try {
                for (service in listOf("identidad-acceso", "transporte", "inventario", "donantes")) {
                    val response = client.get(MobileEnvironment.gateway + "/services/" + service + "/health/ready")
                    Assert.assertEquals(200, response.status.value)
                    Assert.assertTrue(response.headers["Content-Type"].orEmpty().contains("application/json"))
                    codec.parseToJsonElement(response.bodyAsText()).jsonObject
                }
            } finally { client.close() }
        }
    }
}
