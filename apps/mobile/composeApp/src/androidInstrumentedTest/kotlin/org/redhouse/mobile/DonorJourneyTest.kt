package org.redhouse.mobile

import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.semantics.SemanticsProperties
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import kotlinx.serialization.json.*
import org.junit.*
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class DonorJourneyTest {
    @get:Rule val compose=createAndroidComposeRule<MainActivity>()
    private fun enabled(label:String){revealDestination(compose,label);compose.waitUntil(60000){compose.onAllNodesWithText(label).fetchSemanticsNodes().any{!it.config.contains(SemanticsProperties.Disabled)}}}
    private fun click(label:String){revealDestination(compose,label);
        android.util.Log.i("MobileJourney","before_click="+label)
        enabled(label)
        val node=compose.onAllNodes(hasText(label) and hasClickAction())[0]
        when(label){
            "Confirmar" -> node.assertIsDisplayed().performClick()
            else -> presentationClick(compose,label)
        }
    }
    private fun shown(label:String){
        try{compose.waitUntil(60000){compose.onAllNodesWithText(label).fetchSemanticsNodes().isNotEmpty()}}
        catch(e:Exception){if(label!="Iniciar sesión")compose.onRoot().printToLog("MobileJourney");throw e}
    }
    @Test fun donorBooksAndCancelsUsingComposeAndRealServices(){
        val context=InstrumentationRegistry.getInstrumentation().context
        val lab=codec.parseToJsonElement(context.assets.open("lab.json").bufferedReader().readText()).jsonObject
        shown("Iniciar sesión")
        compose.onNodeWithText("Gateway HTTPS").performTextReplacement(lab.text("android_gateway"))
        compose.onNodeWithText("Cuenta institucional").performTextInput("donor1")
        compose.onNodeWithText("Contraseña").performTextInput(lab.text("password"))
        click("Iniciar sesión");enabled("Mi expediente")
        compose.onAllNodesWithText("Traslados").assertCountEquals(0)
        click("Campañas")
        click("Consultar horarios");click("Consultar horarios");shown("Disponibilidad consultada")
        enabled("Agendar")
        val nodes=compose.onAllNodesWithText("Agendar").fetchSemanticsNodes()
        val index=nodes.indexOfFirst{!it.config.contains(SemanticsProperties.Disabled)}
        compose.onAllNodesWithText("Agendar")[index].performScrollTo().performClick()
        click("Confirmar");shown("Cita confirmada por Donantes");android.util.Log.i("MobileJourney","booked")
        click("Consultar cita");click("Cancelar cita");click("Confirmar");shown("Cancelación confirmada");android.util.Log.i("MobileJourney","cancelled")
        click("Cerrar sesión");enabled("Iniciar sesión")
        Assert.assertNull(AndroidSecureStore(compose.activity).read())
    }
}
