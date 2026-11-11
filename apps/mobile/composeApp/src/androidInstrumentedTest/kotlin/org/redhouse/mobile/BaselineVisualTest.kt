package org.redhouse.mobile

import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

/** Only run against the isolated pre-correction APK; same backend, account and scale. */
@RunWith(AndroidJUnit4::class)
class BaselineVisualTest {
    @get:Rule val compose=createAndroidComposeRule<MainActivity>()
    private fun shot(stage:String) {compose.waitForIdle();android.util.Log.i("VisualQuality",stage);Thread.sleep(3000)}
    @Test fun compareDonorAccountAndAppointments() {
        val args=InstrumentationRegistry.getArguments()
        org.junit.Assume.assumeTrue("Requires the isolated baseline APK",args.getString("baseline")=="true")
        compose.waitUntil(60000) {compose.onAllNodesWithText("Cuenta institucional").fetchSemanticsNodes().isNotEmpty()}
        Thread.sleep(1500)
        compose.onNodeWithText("Cuenta institucional").performTextReplacement("donor1")
        compose.onNodeWithText("Contraseña").performTextReplacement(requireNotNull(args.getString("demoPassword")))
        presentationClick(compose,"Iniciar sesión")
        compose.waitUntil(60000) {compose.onAllNodesWithText("Secciones").fetchSemanticsNodes().isNotEmpty()}
        presentationClick(compose,"Cuenta");shot("baseline-account")
        presentationClick(compose,"Secciones");presentationClick(compose,"Mis citas")
        compose.waitUntil(60000) {compose.onAllNodesWithText("Consulta confirmada · página 1").fetchSemanticsNodes().isNotEmpty()}
        shot("baseline-work")
        presentationClick(compose,"Cuenta");presentationClick(compose,"Cerrar sesión")
        compose.waitUntil(60000) {compose.onAllNodesWithText("Iniciar sesión").fetchSemanticsNodes().isNotEmpty()}
    }
}
