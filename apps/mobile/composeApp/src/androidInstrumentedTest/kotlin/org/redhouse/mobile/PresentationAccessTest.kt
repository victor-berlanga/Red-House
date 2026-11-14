package org.redhouse.mobile

import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

/** No credentials, writes or disabled screen protections. */
@RunWith(AndroidJUnit4::class)
class PresentationAccessTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()
    @Test fun accessAndRecoveryRemainReachable() {
        compose.waitUntil(60000) { compose.onAllNodesWithText("Cuenta").fetchSemanticsNodes().isNotEmpty() }
        compose.onNodeWithText("Gateway HTTPS").assertDoesNotExist()
        compose.onNodeWithText("Recuperar acceso").performScrollTo().assertIsNotEnabled()
        compose.onNodeWithText("Cuenta").performScrollTo().performTextInput("cuenta-sintetica-no-enviada")
        compose.onAllNodesWithText("Código de verificación").assertCountEquals(0)
        compose.onNodeWithText("Recuperar acceso").performScrollTo().assertIsEnabled()
        compose.onNodeWithText("Iniciar sesión").performScrollTo().assertIsDisplayed()
    }
}
