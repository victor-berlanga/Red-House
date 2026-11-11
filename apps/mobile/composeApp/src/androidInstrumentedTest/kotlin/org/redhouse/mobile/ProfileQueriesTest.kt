package org.redhouse.mobile

import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.semantics.SemanticsProperties
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import kotlinx.serialization.json.*
import org.junit.*
import org.junit.runner.RunWith

/** Real profile navigation and reads; these checks do not claim clinical decisions or full profile workflows. */
@RunWith(AndroidJUnit4::class)
class ProfileQueriesTest {
    @get:Rule val compose=createAndroidComposeRule<MainActivity>()
    private fun enabled(label:String){revealDestination(compose,label);compose.waitUntil(60000){compose.onAllNodesWithText(label).fetchSemanticsNodes().any{!it.config.contains(SemanticsProperties.Disabled)}}}
    private fun click(label:String){revealDestination(compose,label);enabled(label);presentationClick(compose,label)}
    private fun query(user:String,label:String){
        val lab=codec.parseToJsonElement(InstrumentationRegistry.getInstrumentation().context.assets.open("lab.json").bufferedReader().readText()).jsonObject
        enabled("Iniciar sesión")
        compose.onNodeWithText("Gateway HTTPS").performTextReplacement(lab.text("android_gateway"))
        compose.onNodeWithText("Cuenta institucional").performTextInput(user)
        compose.onNodeWithText("Contraseña").performTextInput(lab.text("password"))
        click("Iniciar sesión");click(label)
        compose.waitUntil(60000){compose.onAllNodesWithTag("loaded-records").fetchSemanticsNodes().isNotEmpty()}
        compose.onAllNodesWithText("Gestionar citas e historial").assertCountEquals(0)
        click("Cerrar sesión");enabled("Iniciar sesión")
    }
    @Test fun operatorReadsOwnInventory()=query("operator1","Inventario")
    @Test fun coordinatorReadsRegionalAvailability()=query("coordinator1","Disponibilidad regional")
    @Test fun medicalReadsAuthorizedResults()=query("medical1","Resultados autorizados")
}
