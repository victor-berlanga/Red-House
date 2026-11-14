package org.redhouse.mobile

import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import androidx.test.uiautomator.UiDevice
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

/** Access, keyboard and rotation only: no credentials or login requests. */
@RunWith(AndroidJUnit4::class)
class VisualScaleTest {
    @get:Rule val compose=createAndroidComposeRule<MainActivity>()
    private fun shot(name:String) {compose.waitForIdle();android.util.Log.i("VisualQuality",name);Thread.sleep(4000)}
    @Test fun accessAtSystemScale() {
        compose.waitUntil(60000) {compose.onAllNodesWithText("Cuenta").fetchSemanticsNodes().isNotEmpty()}
        Thread.sleep(1500)
        shot("access")
        compose.onNodeWithText("Cuenta").performScrollTo()
        compose.onNodeWithText("Cuenta").performClick()
        compose.onNodeWithText("Cuenta").performTextInput("prueba-no-enviada")
        shot("keyboard")
        val device=UiDevice.getInstance(InstrumentationRegistry.getInstrumentation())
        device.pressBack()
        compose.onNodeWithText("Recuperar acceso").performScrollTo().assertIsEnabled()
        compose.onNodeWithText("Iniciar sesión").performScrollTo().assertIsDisplayed()
        device.setOrientationLeft()
        compose.waitUntil(60000) {
            compose.activity.resources.configuration.orientation==android.content.res.Configuration.ORIENTATION_LANDSCAPE &&
                compose.onAllNodesWithText("Cuenta").fetchSemanticsNodes(atLeastOneRootRequired=false).isNotEmpty()
        }
        compose.onNodeWithText("Iniciar sesión").performScrollTo().assertIsDisplayed()
        Thread.sleep(1500) // Allow the host emulator surface to redraw after Activity recreation.
        shot("landscape")
        device.setOrientationNatural();device.unfreezeRotation()
    }
}
