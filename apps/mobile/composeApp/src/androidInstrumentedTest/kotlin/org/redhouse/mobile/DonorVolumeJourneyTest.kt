package org.redhouse.mobile

import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.Assume.assumeTrue
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

/** Requires the isolated 105-record fixture; performs no production writes. */
@RunWith(AndroidJUnit4::class)
class DonorVolumeJourneyTest {
    @get:Rule val compose=createAndroidComposeRule<MainActivity>()
    private fun capture(stage:String) {
        compose.waitForIdle()
        android.util.Log.i("VolumeVisual",stage)
        Thread.sleep(4000) // Host captures the visible emulator after the asserted state.
    }
    private fun shown(text:String) = compose.waitUntil(90000) {compose.onAllNodesWithText(text).fetchSemanticsNodes().isNotEmpty()}
    private fun nextPage(page:Int,campaigns:Boolean=false) {
        if(campaigns) {
            val next=hasContentDescription("Página siguiente de campañas, al inicio") and isEnabled()
            compose.waitUntil(90000) {compose.onAllNodes(next).fetchSemanticsNodes().isNotEmpty()}
            compose.onNode(next).performScrollTo().performClick()
        }
        else presentationClick(compose,"Siguiente")
        shown("$page / 6")
    }
    private fun openCampaigns() {
        val args=InstrumentationRegistry.getArguments()
        assumeTrue(args.containsKey("demoUser"))
        val password=args.getString("demoPassword") ?: readMobileLabFixture().text("password")
        compose.waitUntil(90000) {compose.onAllNodesWithText("Iniciar sesión").fetchSemanticsNodes().isNotEmpty() || compose.onAllNodesWithText("Cuenta").fetchSemanticsNodes().isNotEmpty()}
        if(compose.onAllNodesWithText("Iniciar sesión").fetchSemanticsNodes().isEmpty()) presentationClick(compose,"Cerrar sesión")
        shown("Cuenta")
        compose.onNodeWithText("Cuenta").performTextReplacement(requireNotNull(args.getString("demoUser")))
        compose.onNodeWithText("Contraseña").performTextReplacement(password)
        presentationClick(compose,"Iniciar sesión")
        shown("Ver mis citas")
        presentationClick(compose,"Campañas")
        shown("1 / 6")
    }
    @Test fun campaignPagination() {
        openCampaigns()
        for(page in 2..6) nextPage(page,campaigns=true)
        compose.onAllNodesWithText("6 / 6").onFirst().assertIsDisplayed()
        capture("feed-page6")
    }
    @Test fun publicFeedPersonalNameAndConsentHistory() {
        campaignPagination()
        presentationClick(compose,"Cuenta")
        presentationClick(compose,"Mi expediente")
        shown("Editar nombre")
        presentationClick(compose,"Editar nombre")
        compose.onNodeWithText("Nombre mostrado").performTextReplacement("Nombre sintético actualizado")
        presentationClick(compose,"Guardar nombre")
        shown("Nombre actualizado.")
        compose.onNodeWithText("Nombre sintético actualizado").performScrollTo();capture("personal-updated")
        shown("1 / 6")
        for(page in 2..6) nextPage(page)
        capture("consent-page6")
        presentationClick(compose,"Retirar consentimiento")
        presentationClick(compose,"Confirmar")
        shown("Consentimiento retirado.")
        compose.onNodeWithText("Consentimiento actual: retirado").performScrollTo();capture("consent-withdrawn")
    }
}
